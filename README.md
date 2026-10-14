# UTC Student Handbook RAG

A local Vietnamese question-answering backend for the UTC **K67 student handbook**.
It retrieves PDF excerpts, generates an answer with Ollama, and validates citation
IDs before returning them. K67 content does not establish current rules for other
cohorts or campuses.

Python 3.11–3.12 · FastAPI · LangChain · embedded Chroma · Ollama

## Quick start

Install Python, uv and Ollama. Start Ollama, then run from this checkout in PowerShell:

```powershell
uv sync --locked --python 3.12
ollama pull qwen3-embedding:0.6b
ollama pull qwen3.5:9b-q4_K_M
uv run --locked utc-ingest
uv run --locked utc-doctor
.\scripts\start-local.ps1
```

Open [API docs](http://127.0.0.1:8000/docs), or ask from another terminal:

```powershell
uv run --locked utc-ask 'Quy định điểm F?'
```

For a background server, use `start-local.ps1 -Background` and `stop-local.ps1`.
On Linux/macOS, run `bash scripts/setup.sh`, then `uv run --locked utc-serve`.
The API binds to loopback. A separate frontend must be explicitly allowed through
`RAG_ALLOWED_ORIGINS`; `.env` files are not loaded automatically.

## Checks and documentation

```powershell
uv run --locked python -m ruff check src tests scripts/check_distribution.py scripts/run_qualification.py
uv run --locked python -m ruff format --check src tests scripts/check_distribution.py scripts/run_qualification.py
uv run --locked python -m pytest -q
```

The default suite needs no Ollama. Real-model checks are a separate local release gate.

- [Architecture](docs/architecture.md) and [API contract](docs/api.md)
- [Configuration](docs/configuration.md) and [operations](docs/operations.md)
- [Security](docs/security.md), [limitations](docs/limitations.md) and [data provenance](data/README.md)

Answers can omit or misinterpret conditions even with valid citations. Check the
source PDF for academic decisions. Automatic benchmark scores are proxies, not a
guarantee of correctness. This release targets one trusted local operator.
