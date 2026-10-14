"""Publish/verify the fixed PR #1 evidence bundle, offline and with stdlib only.

The immutable audit baseline is already in public Git history. Verification reads
it in memory, never prints responses, and never imports or runs the RAG runtime.
New qualification runs require a separately reviewed baseline, not an automatic
replacement of these development results.
"""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tomllib
import xml.etree.ElementTree as ET
import zipfile


AUDIT_COMMIT = "ef1d506f9d2d3d9e09bf88933d5fa5550187e326"
QUALIFIED_COMMIT = "8b7149441362540085793001f2f1ea5b2fdb2cbc"
RUNS = {
    "c3b96c6": "c3b96c699dfab085642a3d08cca70ea238a51205",
    "d540993": "d5409933026fa5fbbed2cf61ea37a6ec7ddd26b4",
    "8b71494": QUALIFIED_COMMIT,
}
BENCHMARK = "data/benchmark/evaluation_set.json"
SCOPE = ("src", "pyproject.toml", "uv.lock", BENCHMARK)
DIRECTORY = "docs/qualification"
REPORTS = ("local-production-readiness.md", "semantic-review.md",
           "semantic-rubric.md", "evidence-policy.md")
XML_RUNS = {
    "integration-d540993-retry.xml": RUNS["d540993"],
    "integration-8b71494.xml": QUALIFIED_COMMIT,
    "offline-8b71494.xml": QUALIFIED_COMMIT,
}
LEGACY = "local-benchmark-2026-10-13.json"
SMOKE = "http-smoke-8b71494.json"
NAMES = tuple(f"benchmark-{short}.json" for short in RUNS) + tuple(XML_RUNS) + (LEGACY, SMOKE)
SETTINGS = ("LLM_MODEL", "EMBEDDING_MODEL", "OLLAMA_TIMEOUT", "CHUNK_SIZE", "CHUNK_OVERLAP",
            "RETRIEVAL_K", "TEMPERATURE", "MAX_OUTPUT_TOKENS", "num_ctx", "reasoning")
DEPENDENCIES = ("chromadb", "httpx", "langchain-chroma", "langchain-core", "langchain-ollama")

# Adding a distributable file requires an explicit review of this inventory.
# Do not derive it from archive members, local globs or generated SOURCES.txt.
WHEEL_FILES = {
    f"student_handbook_rag/{name}" for name in (
        "__init__.py", "api.py", "aragog.py", "ask.py", "chain.py", "config.py",
        "corrective.py", "doctor.py", "evaluate.py", "ingest.py", "lexical.py",
        "loader.py", "memory.py", "retriever.py", "vectorstore.py",
        "prompts/reduce_stupidity.txt", "prompts/respond.txt", "prompts/workflow.txt",
    )
}
SDIST_FILES = {f"src/{name}" for name in WHEEL_FILES} | {
    "README.md", "CHANGELOG.md", "MANIFEST.in", "pyproject.toml", "uv.lock",
    "docs/operations.md", "docs/security.md",
    "scripts/evidence.py", "scripts/run_qualification.py", "scripts/local-server-state.ps1",
    "scripts/setup-local.ps1", "scripts/start-local.ps1", "scripts/stop-local.ps1",
    "tests/conftest.py", "tests/integration/test_baseline_rag.py",
    "tests/test_aragog.py", "tests/test_chain.py", "tests/test_corrective.py", "tests/test_evidence.py",
    "tests/test_loader.py", "tests/test_memory.py", "tests/test_rerank.py", "tests/test_vectorstore.py",
    "tests/unit/test_api.py", "tests/unit/test_evaluation_proxies.py", "tests/unit/test_failure_modes_unit.py",
    "tests/unit/test_lexical.py", "tests/unit/test_local_config.py", "tests/unit/test_page_continuation.py",
    "tests/unit/test_production.py", "tests/unit/test_retriever_unit.py", "tests/unit/test_windows_lifecycle.py",
}
WHEEL_METADATA = {"METADATA", "WHEEL", "RECORD", "entry_points.txt", "top_level.txt"}
SDIST_METADATA = {"PKG-INFO", "setup.cfg"} | {
    f"src/student_handbook_rag.egg-info/{name}" for name in (
        "PKG-INFO", "SOURCES.txt", "dependency_links.txt", "entry_points.txt", "requires.txt", "top_level.txt",
    )
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lf(data):
    return data.replace(b"\r\n", b"\n")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def read_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


@lru_cache(maxsize=512)
def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def blob(repo, commit, path):
    return git(repo, "show", f"{commit}:{path}")


def raw_artifacts(repo):
    return {name: blob(repo, AUDIT_COMMIT, f"{DIRECTORY}/{name}") for name in NAMES}


def runtime_files(repo, commit):
    return git(repo, "ls-tree", "-r", "--name-only", commit, "--", *SCOPE).decode().splitlines()


def citations(response):
    return [{key: source[key] for key in ("page", "book_page", "chunk_id")}
            for source in response["sources"]]


def metrics(cases, gold):
    """Recompute the existing page/keyword proxies, not semantic correctness."""
    require([c["id"] for c in cases] == [g["id"] for g in gold], "Case IDs/order differ from gold")
    answerable = [(c, g) for c, g in zip(cases, gold) if g["answerable"]]
    unanswerable = [(c, g) for c, g in zip(cases, gold) if not g["answerable"]]
    ranks, keyword, page = [], 0, 0
    for case, item in answerable:
        # This fixed gold has a PDF page for every answerable case and book=PDF-2.
        # Do not silently substitute this calculation for a future keyword-only gold.
        require(item["expected_page"] == item["book_page"] + 2, "Unsupported gold page mapping")
        ranks.append(next((i for i, p in enumerate(case["retrieved_pages"], 1)
                           if p == item["expected_page"]), 0))
        indices = case["keyword_indices"]
        require(indices == sorted(set(indices)) and all(type(i) is int and 0 <= i < len(item["gold_keywords"])
                                                       for i in indices), "Invalid keyword indices")
        eligible = case["status"] != "error" and not case["is_insufficient_context"]
        keyword += int(bool(indices) and eligible)
        page += int(eligible and any(s["page"] == item["expected_page"] or s["book_page"] == item["book_page"]
                                    for s in case["citations"]))
    # Preserve the evaluator's addition order on both supported Python versions.
    mrr_sum = 0.0
    for rank in ranks:
        mrr_sum += 1 / rank if rank else 0.0
    return {
        "answerable": len(answerable), "unanswerable": len(unanswerable),
        **{f"hit_at_{k}": sum(0 < r <= k for r in ranks) / len(ranks) for k in (1, 3, 5)},
        "mrr": mrr_sum / len(ranks),
        "keyword_matches": keyword, "citation_page_matches": page,
        "refusals": sum(c["status"] == "refused" for c, _ in unanswerable),
        "operational_errors": sum(c["status"] == "error" for c in cases),
    }


def benchmark_summary(repo, raw, commit):
    source = read_json(raw)
    provenance = source["provenance"]
    require(source["schema_version"] == 1 and provenance["commit"] == commit, "Raw schema/commit mismatch")
    require(provenance["tracked_worktree_clean"] is True and source["inputs_unchanged_during_run"] is True,
            "Unstable qualification inputs")
    gold = read_json(blob(repo, commit, BENCHMARK))
    retrieval = {item["id"]: item for item in source["retrieval"]["details"]}
    require(len(source["responses"]) == len(gold), "Missing raw responses")
    cases = []
    for item, response in zip(gold, source["responses"]):
        require(response["query"] == item["question"], "Raw question/order mismatch")
        require(response["status"] in {"answered", "refused", "error"}, "Invalid response status")
        require(type(response["is_insufficient_context"]) is bool, "Invalid refusal flag")
        cases.append({
            "id": item["id"], "status": response["status"],
            "is_insufficient_context": response["is_insufficient_context"],
            "answer_sha256": sha(response["answer"].encode("utf-8")),
            "keyword_indices": [i for i, kw in enumerate(item.get("gold_keywords", []))
                                if kw.lower() in response["answer"].lower()],
            "citations": citations(response),
            "retrieved_pages": retrieval[item["id"]]["retrieved_pages"] if item["answerable"] else [],
        })
    computed = metrics(cases, gold)
    for key in ("hit_at_1", "hit_at_3", "hit_at_5", "mrr"):
        require(abs(source["retrieval"][key] - computed[key]) < 1e-12, f"Raw retrieval metric mismatch: {key}")
    generation = source["generation"]
    for key, value in {
        "total_answerable": computed["answerable"], "total_unanswerable": computed["unanswerable"],
        "answer_keyword_match_rate": computed["keyword_matches"] / computed["answerable"],
        "citation_page_match_rate": computed["citation_page_matches"] / computed["answerable"],
        "unanswerable_refusal_rate": computed["refusals"] / computed["unanswerable"],
        "operational_errors": computed["operational_errors"],
    }.items():
        require(abs(generation[key] - value) < 1e-12, f"Raw generation metric mismatch: {key}")
    paths = runtime_files(repo, commit)
    require(set(paths) == set(provenance["runtime_file_sha256"]), "Incomplete runtime hash inventory")
    index = provenance["index_manifest"]
    require(index["source_sha256"] == provenance["source_sha256"], "Index/source mismatch")
    require(sha(blob(repo, commit, "data/raw/sotaysvk67.pdf")) == provenance["source_sha256"], "PDF hash mismatch")
    return {
        "schema_version": 2, "kind": "benchmark_summary", "commit": commit,
        "started_at": source["started_at"], "completed_at": source["completed_at"],
        "duration_seconds": source["duration_seconds"], "inputs_unchanged_during_run": True,
        "provenance": {
            "tracked_worktree_clean": True,
            "runtime_sha256_lf": {path: sha(lf(blob(repo, commit, path))) for path in paths},
            "source_sha256": provenance["source_sha256"],
            "python_version": provenance["python"].split()[0],
            "dependencies": {key: provenance["dependencies"][key] for key in DEPENDENCIES},
            "ollama": {"version": provenance["ollama"]["version"],
                       "models": [{key: model[key] for key in ("name", "digest")}
                                  for model in provenance["ollama"]["models"]]},
            "configuration": {key: provenance["configuration"][key] for key in SETTINGS},
            "index": {key: index[key] for key in ("chunk_count", "chunk_size", "chunk_overlap", "distance_metric")},
        },
        "metrics": computed, "cases": cases,
    }


def xml_summary(raw):
    """Keep test identities/outcomes; never export tracebacks, messages or host data."""
    original = ET.fromstring(raw)
    require(original.tag == "testsuites", "Expected JUnit testsuites")
    root = ET.Element("testsuites")
    for suite in original:
        require(suite.tag == "testsuite", "Expected testsuite")
        target = ET.SubElement(root, "testsuite", {key: suite.attrib[key]
                              for key in ("name", "tests", "errors", "failures", "skipped", "time")})
        totals = dict.fromkeys(("tests", "errors", "failures", "skipped"), 0)
        for case in suite:
            require(case.tag == "testcase", "Unexpected suite content")
            totals["tests"] += 1
            # Parameters may contain local paths, so identify parameterized cases by ordinal.
            name = case.attrib["name"].split("[", 1)[0]
            if "[" in case.attrib["name"]:
                name += f"[case-{totals['tests']}]"
            child = ET.SubElement(target, "testcase", {"classname": case.attrib["classname"],
                                  "name": name, "time": case.attrib["time"]})
            for outcome in case:
                require(outcome.tag in {"failure", "error", "skipped"}, "Unexpected testcase content")
                totals[{"failure": "failures", "error": "errors", "skipped": "skipped"}[outcome.tag]] += 1
                ET.SubElement(child, outcome.tag)
        require(all(int(suite.attrib[key]) == count for key, count in totals.items()), "JUnit count mismatch")
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def development_verdicts(report):
    result = {short: {} for short in RUNS}
    for line in report.splitlines():
        if re.match(r"\| q\d{2} \|", line):
            columns = [c.strip() for c in line.split("|")[1:-1]]
            require(len(columns) == 6, "Malformed semantic review table")
            for short, cell in zip(RUNS, columns[2:5]):
                verdict = "pass" if cell.startswith("Đạt") else "fail" if cell.startswith("Không đạt") else None
                require(verdict and columns[0] not in result[short], "Invalid/duplicate semantic verdict")
                result[short][columns[0]] = verdict
    require(all(list(v) == [f"q{i:02}" for i in range(1, 23)] for v in result.values()), "Incomplete semantic review")
    return result


def export(repo):
    raw = raw_artifacts(repo)
    outputs, entries = {}, {}
    for short, commit in RUNS.items():
        name = f"benchmark-{short}.json"
        outputs[name] = json_bytes(benchmark_summary(repo, raw[name], commit))
    for name in XML_RUNS:
        outputs[name] = xml_summary(raw[name])
    outputs[LEGACY] = json_bytes({
        "schema_version": 2, "kind": "legacy_summary", "qualification": False,
        "artifact_status": "superseded_unverified_provenance", "commit": None,
        "development_review": {"q15": "fail", "independent": False},
    })
    smoke = read_json(raw[SMOKE])
    require(smoke["commit"] == QUALIFIED_COMMIT, "Smoke commit mismatch")
    require(smoke["benchmark_sha256"] == sha(raw["benchmark-8b71494.json"]), "Raw smoke benchmark SHA mismatch")
    outputs[SMOKE] = json_bytes({
        "schema_version": 2, "kind": "http_smoke_summary", "commit": smoke["commit"],
        "started_at": smoke["started_at"], "completed_at": smoke["completed_at"],
        "benchmark_sha256": sha(outputs["benchmark-8b71494.json"]),
        "benchmark_raw_sha256": smoke["benchmark_sha256"],
        "checks": smoke["checks"],
        "cases": [{"id": case["id"], "seconds": case["seconds"],
                   "status": case["response"]["status"],
                   "is_insufficient_context": case["response"]["is_insufficient_context"],
                   "citations": citations(case["response"])} for case in smoke["responses"]],
    })
    for name in NAMES:
        entries[name] = {"sha256": sha(outputs[name]), "raw_sha256": sha(raw[name])}
    review = blob(repo, AUDIT_COMMIT, f"{DIRECTORY}/semantic-review.md").decode("utf-8")
    manifest = {
        "schema_version": 1, "audit_source_commit": AUDIT_COMMIT,
        "qualified_runtime_commit": QUALIFIED_COMMIT,
        "artifacts": entries, "junit_runtime_commits": XML_RUNS,
        "development_review": {"reviewer": "Codex", "independent": False,
                               "verdicts": development_verdicts(review)},
    }
    return outputs, manifest


def render_summary(outputs, manifest):
    lines = ["# Evidence summary (generated)", "",
             "Do not edit: `python scripts/evidence.py publish --raw-dir data/runtime/evidence-private`.", "",
             f"Qualified local runtime: `{QUALIFIED_COMMIT}`.", "",
             "These are development observations on known questions. The Codex review is not independent.", "",
             "| Run | Hit@1 / @3 / @5 | MRR | Keyword proxy | Gold-page proxy | Refusals | Errors | Codex content review |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for short in RUNS:
        m = read_json(outputs[f"benchmark-{short}.json"])["metrics"]
        passed = sum(v == "pass" for v in manifest["development_review"]["verdicts"][short].values())
        lines.append(f"| {short} | {m['hit_at_1']:.2%} / {m['hit_at_3']:.2%} / {m['hit_at_5']:.2%} | "
                     f"{m['mrr']:.4f} | {m['keyword_matches']}/{m['answerable']} | "
                     f"{m['citation_page_matches']}/{m['answerable']} | {m['refusals']}/{m['unanswerable']} | "
                     f"{m['operational_errors']} | {passed}/{m['answerable']} |")
    lines += ["", "Local test observations (CI does not rerun Ollama):", "",
              "| JUnit artifact | Passed | Failed | Errors | Skipped |", "| --- | --- | --- | --- | --- |"]
    for name in XML_RUNS:
        suites = ET.fromstring(outputs[name])
        totals = {key: sum(int(s.attrib[key]) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
        passed = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
        lines.append(f"| [{name}]({name}) | {passed} | {totals['failures']} | {totals['errors']} | {totals['skipped']} |")
    lines += ["", "SHA-256: public files are minimized exports; raw hashes identify the original audit inputs.", "",
              "| Artifact | Public SHA-256 | Raw SHA-256 |", "| --- | --- | --- |"]
    for name, entry in manifest["artifacts"].items():
        lines.append(f"| [{name}]({name}) | `{entry['sha256']}` | `{entry['raw_sha256']}` |")
    lines += ["", "See [publishing policy](evidence-policy.md), [local scope](local-production-readiness.md),",
              "[semantic review](semantic-review.md) and [rubric](semantic-rubric.md).", ""]
    return "\n".join(lines).encode("utf-8")


def preserve_raw(repo, directory):
    """Preserve exact raw evidence and prove the LF mapping before publishing."""
    directory = directory.resolve()
    private_root = (repo / "data/runtime").resolve()
    require(directory.is_relative_to(private_root), "Private audit directory must be under ignored data/runtime")
    git(repo, "check-ignore", "--quiet", str(directory / "audit.json"))
    for name, data in raw_artifacts(repo).items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            require(target.read_bytes() == data, f"Private raw mismatch: {name}")
        else:
            target.write_bytes(data)
    for short, commit in RUNS.items():
        raw = read_json((directory / f"benchmark-{short}.json").read_bytes())
        for path, observed in raw["provenance"]["runtime_file_sha256"].items():
            saved = directory / "runtime-files" / observed
            committed = blob(repo, commit, path)
            candidates = [committed, lf(committed), lf(committed).replace(b"\n", b"\r\n")]
            for candidate in (saved, repo / path):
                if candidate.is_file():
                    candidates.append(candidate.read_bytes())
            match = next((data for data in candidates if sha(data) == observed), None)
            require(match is not None and lf(match) == lf(committed), f"Cannot prove raw runtime hash: {short}/{path}")
            saved.parent.mkdir(parents=True, exist_ok=True)
            if saved.exists():
                require(saved.read_bytes() == match, "Private runtime snapshot mismatch")
            else:
                saved.write_bytes(match)


def report_hashes(directory):
    return {name: sha(lf((directory / name).read_bytes())) for name in REPORTS}


def check_archive_members(members, allowed, archive_name):
    directories = {str(parent) for name in allowed for parent in PurePosixPath(name).parents
                   if str(parent) != "."}
    seen = set()
    for name, is_directory, is_regular in members:
        require(is_directory or is_regular, f"Unsupported distribution member type: {archive_name}/{name}")
        canonical = name.removesuffix("/") if is_directory else name
        require(canonical in (directories if is_directory else allowed),
                f"Unapproved distribution member: {archive_name}/{name}")
        require(canonical not in seen, f"Duplicate distribution member: {archive_name}/{name}")
        seen.add(canonical)


def verify_archives(directory):
    """Reject unapproved files/types; this is not a secret scan of approved text."""
    project = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    stem = f"student_handbook_rag-{project['project']['version']}"
    wheel_allowed = WHEEL_FILES | {f"{stem}.dist-info/{name}" for name in WHEEL_METADATA}
    sdist_allowed = {f"{stem}/{name}" for name in SDIST_FILES | SDIST_METADATA}
    archives = sorted(directory.glob("*.whl")) + sorted(directory.glob("*.tar.gz"))
    require(any(p.suffix == ".whl" for p in archives) and any(p.name.endswith(".tar.gz") for p in archives),
            "Expected both wheel and sdist")
    for path in archives:
        if path.suffix == ".whl":
            with zipfile.ZipFile(path) as archive:
                members = []
                for member in archive.infolist():
                    mode = stat.S_IFMT(member.external_attr >> 16)
                    is_directory = member.is_dir() and mode in (0, stat.S_IFDIR)
                    is_regular = not member.is_dir() and mode in (0, stat.S_IFREG)
                    members.append((member.filename, is_directory, is_regular))
                check_archive_members(members, wheel_allowed, path.name)
        else:
            with tarfile.open(path) as archive:
                check_archive_members(((m.name, m.isdir(), m.isfile()) for m in archive), sdist_allowed, path.name)


def verify(repo, directory=None, raw_directory=None, dist=None):
    directory = directory or repo / DIRECTORY
    # A shallow or unrelated checkout must fail, not silently omit provenance checks.
    for commit in (AUDIT_COMMIT, *RUNS.values()):
        git(repo, "merge-base", "--is-ancestor", commit, "HEAD")
    outputs, expected = export(repo)
    manifest = read_json((directory / "evidence-manifest.json").read_bytes())
    expected["report_sha256_lf"] = report_hashes(directory)
    require(json_bytes(manifest) == json_bytes(expected), "Manifest schema/SHA/provenance/report hash mismatch")
    for name, data in outputs.items():
        actual = (directory / name).read_bytes()
        require(sha(actual) == manifest["artifacts"][name]["sha256"], f"Artifact SHA mismatch: {name}")
        require(actual == data, f"Artifact schema/content/metric mismatch: {name}")
    summary = render_summary(outputs, manifest)
    require(lf((directory / "evidence-summary.md").read_bytes()) == summary, "Generated report mismatch")
    review = (directory / "semantic-review.md").read_text(encoding="utf-8")
    require(development_verdicts(review) == manifest["development_review"]["verdicts"], "Semantic report verdict drift")
    for name in (*REPORTS, "evidence-summary.md"):
        report = (directory / name).read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", report):
            if not re.match(r"https?://|#", target):
                require((directory / target.split("#")[0]).is_file(), f"Broken report reference: {name}")
    paths = runtime_files(repo, QUALIFIED_COMMIT)
    require(paths == runtime_files(repo, "HEAD"), "Runtime inventory changed since qualification")
    for path in paths:
        tested = lf(blob(repo, QUALIFIED_COMMIT, path))
        require(lf(blob(repo, "HEAD", path)) == tested and lf((repo / path).read_bytes()) == tested,
                f"Runtime changed since qualification: {path}")
    require(sha((repo / "data/raw/sotaysvk67.pdf").read_bytes()) ==
            read_json(outputs["benchmark-8b71494.json"])["provenance"]["source_sha256"], "Current PDF changed")
    if raw_directory:
        for name, data in raw_artifacts(repo).items():
            require((raw_directory / name).read_bytes() == data, f"Private raw mismatch: {name}")
        for short in RUNS:
            provenance = read_json((raw_directory / f"benchmark-{short}.json").read_bytes())["provenance"]
            for path, observed in provenance["runtime_file_sha256"].items():
                saved = (raw_directory / "runtime-files" / observed).read_bytes()
                require(sha(saved) == observed and lf(saved) == lf(blob(repo, RUNS[short], path)), "Private runtime hash mismatch")
    if dist:
        verify_archives(dist)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("publish", "verify"))
    parser.add_argument("--raw-dir", type=Path, help="Ignored private audit directory; required for publish")
    parser.add_argument("--dist", type=Path, help="Also inspect built wheel and sdist")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    try:
        if args.action == "publish":
            require(args.raw_dir is not None, "Publish requires --raw-dir data/runtime/evidence-private")
            preserve_raw(repo, args.raw_dir)
            outputs, manifest = export(repo)
            directory = repo / DIRECTORY
            manifest["report_sha256_lf"] = report_hashes(directory)
            outputs["evidence-manifest.json"] = json_bytes(manifest)
            outputs["evidence-summary.md"] = render_summary(outputs, manifest)
            for name, data in outputs.items():
                (directory / name).write_bytes(data)
        verify(repo, raw_directory=args.raw_dir, dist=args.dist)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError, ET.ParseError) as error:
        # Do not echo raw response content or private paths through parser tracebacks.
        print(f"Evidence check failed ({type(error).__name__}): {error if isinstance(error, ValueError) else 'invalid/missing input or Git history'}", file=sys.stderr)
        return 1
    print(f"Evidence verified: {len(NAMES)} artifacts, reports, metrics and runtime provenance; no Ollama calls.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
