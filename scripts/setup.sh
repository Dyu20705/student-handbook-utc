#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
uv sync --locked --python 3.12
ollama pull "${RAG_EMBEDDING_MODEL:-qwen3-embedding:0.6b}"
ollama pull "${RAG_LLM_MODEL:-qwen3.5:9b-q4_K_M}"
uv run --locked utc-ingest
uv run --locked utc-doctor
