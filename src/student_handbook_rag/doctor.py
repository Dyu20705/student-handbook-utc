"""Read-only local dependency checks; exits nonzero when not ready."""

import json
import sys

import httpx

from student_handbook_rag.config import EMBEDDING_MODEL, LLM_MODEL, OLLAMA_BASE_URL, validate_config
from student_handbook_rag.vectorstore import build_vector_store, read_manifest


def check_models():
    with httpx.Client(timeout=3, trust_env=False) as client:
        response = client.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
        response.raise_for_status()
        names = {model["name"] for model in response.json()["models"]}
    missing = [
        name
        for name in (LLM_MODEL, EMBEDDING_MODEL)
        if name not in names and f"{name}:latest" not in names
    ]
    if missing:
        raise RuntimeError("Missing Ollama models: " + ", ".join(missing))


def main():
    try:
        validate_config()
        check_models()
        db = build_vector_store(load_only=True)
        manifest = read_manifest()
        # Exercise embedding and vector dimension compatibility, without generation.
        if not db.similarity_search("quy chế đào tạo", k=1):
            raise RuntimeError("Retrieval returned no documents")
        print(
            json.dumps(
                {
                    "status": "ready",
                    "chunks": manifest["chunk_count"],
                    "source_sha256": manifest["source_sha256"],
                    "embedding_model": EMBEDDING_MODEL,
                    "llm_model": LLM_MODEL,
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "not_ready",
                    "error_type": type(exc).__name__,
                    "action": "Check Ollama, pull configured models, then run utc-ingest --force",
                }
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
