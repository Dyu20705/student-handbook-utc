"""Run a committed checkout with full, machine-collected benchmark provenance.

The harness may live outside the tested checkout (e.g. when reproducing an old
commit). Its own hash is recorded separately from the application commit.
"""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from urllib.request import ProxyHandler, build_opener


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def code_snapshot(repo):
    paths = git(
        repo, "ls-files", "src", "pyproject.toml", "uv.lock", "data/benchmark/evaluation_set.json"
    ).splitlines()
    return {path: sha256(repo / path) for path in paths}


def model_snapshot(url, names):
    opener = build_opener(ProxyHandler({}))

    def get(endpoint):
        with opener.open(url.rstrip("/") + endpoint, timeout=10) as response:
            return json.load(response)

    tags = get("/api/tags")["models"]
    models = []
    for name in names:
        match = next((m for m in tags if m["name"] in {name, name + ":latest"}), None)
        if match is None:
            raise RuntimeError(f"Missing model: {name}")
        models.append(match)
    return {"version": get("/api/version")["version"], "models": models}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output path; qualification artifacts must not be overwritten.")
    repo = args.repo.resolve()
    if git(repo, "status", "--porcelain", "--untracked-files=no"):
        parser.error(
            "Commit tracked changes before qualification; the tested checkout must be clean."
        )
    sys.path.insert(0, str(repo / "src"))
    from student_handbook_rag import config, evaluate
    from student_handbook_rag.chain import StudentHandbookRAG
    from student_handbook_rag.retriever import BaselineRetriever
    from student_handbook_rag.vectorstore import read_manifest

    if not Path(evaluate.__file__).resolve().is_relative_to(repo / "src"):
        raise RuntimeError("Evaluator imported from a different checkout")
    config.validate_config()
    started = datetime.now(UTC).isoformat()
    clock = time.monotonic()
    before = code_snapshot(repo)
    source_hash = sha256(config.RAW_DATA_PATH)
    manifest = read_manifest()
    models = model_snapshot(config.OLLAMA_BASE_URL, [config.LLM_MODEL, config.EMBEDDING_MODEL])
    settings = {
        key: getattr(config, key)
        for key in (
            "RAW_DATA_PATH",
            "CHROMA_DEFAULT_DIR",
            "LLM_MODEL",
            "EMBEDDING_MODEL",
            "OLLAMA_BASE_URL",
            "OLLAMA_TIMEOUT",
            "CHUNK_SIZE",
            "CHUNK_OVERLAP",
            "RETRIEVAL_K",
            "TEMPERATURE",
            "MAX_OUTPUT_TOKENS",
        )
    }
    settings.update({"num_ctx": 8192, "reasoning": False})
    provenance = {
        "commit": git(repo, "rev-parse", "HEAD"),
        "tracked_worktree_clean": True,
        "runtime_file_sha256": before,
        "source_sha256": source_hash,
        "benchmark_sha256": sha256(config.BENCHMARK_PATH),
        "python": sys.version,
        "platform": platform.platform(),
        "harness_sha256": sha256(__file__),
        "dependencies": dict(
            sorted((d.metadata["Name"], d.version) for d in metadata.distributions())
        ),
        "ollama": models,
        "configuration": settings,
        "index_manifest": manifest,
    }
    benchmark = evaluate.load_benchmark()
    retriever = BaselineRetriever()
    retrieval = evaluate.evaluate_retrieval(benchmark, retriever, max_k=5)
    engine = StudentHandbookRAG(retriever=retriever)
    responses = []

    class RecordingEngine:
        def query(self, question, k):
            result = engine.query(question, k=k)
            # Preserve the complete response, including all retrieved context.
            responses.append(
                json.loads(
                    json.dumps(result, ensure_ascii=False, default=lambda doc: doc.model_dump())
                )
            )
            return result

    generation = evaluate.evaluate_generation(benchmark, RecordingEngine(), k=config.RETRIEVAL_K)
    stable = (
        before == code_snapshot(repo)
        and source_hash == sha256(config.RAW_DATA_PATH)
        and manifest == read_manifest()
        and models
        == model_snapshot(config.OLLAMA_BASE_URL, [config.LLM_MODEL, config.EMBEDDING_MODEL])
        and provenance["commit"] == git(repo, "rev-parse", "HEAD")
        and not git(repo, "status", "--porcelain", "--untracked-files=no")
    )
    result = {
        "schema_version": 1,
        "started_at": started,
        "completed_at": datetime.now(UTC).isoformat(),
        "duration_seconds": round(time.monotonic() - clock, 2),
        "provenance": provenance,
        "inputs_unchanged_during_run": stable,
        "metric_semantics": "Keyword and gold-page matches are proxies, not semantic correctness. Legacy is_correct/has_grounded_citation fields have the same proxy meaning.",
        "retrieval": retrieval,
        "generation": generation,
        "responses": responses,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"Saved {args.output}; inputs unchanged: {stable}", flush=True)
    return 0 if stable and generation["operational_errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
