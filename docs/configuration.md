# Configuration

Settings come from process environment variables. `.env.example` documents them;
the application does not automatically load `.env`. Export values before running
ingestion, doctor, the CLI or the server, and restart after changing them.

| Variable | Default / purpose |
| --- | --- |
| `RAG_OLLAMA_URL` | `http://127.0.0.1:11434` |
| `RAG_ALLOW_REMOTE_OLLAMA` | `0`; set `1` explicitly to send questions/context to a remote endpoint |
| `RAG_LLM_MODEL` | `qwen3.5:9b-q4_K_M` |
| `RAG_EMBEDDING_MODEL` | `qwen3-embedding:0.6b` |
| `RAG_OLLAMA_TIMEOUT` | 120 seconds per I/O operation; range greater than 0 through 600 |
| `RAG_MAX_OUTPUT_TOKENS` | 768; range 1–4096 |
| `RAG_TEMPERATURE` | 0; range 0–2 |
| `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | 600 / 100 characters; size > 0, overlap >= 0 and < size |
| `RAG_RETRIEVAL_K` | 5; range 1–10 |
| `RAG_DATA_DIR` | Project `data/` directory |
| `RAG_DATA_PATH` | `data/raw/sotaysvk67.pdf` under the configured data directory |
| `RAG_CHROMA_DIR` | `data/chroma/v1_baseline` under the configured data directory |
| `RAG_API_KEY` | Empty; a nonempty value enables bearer authentication for `/ask` |
| `RAG_ALLOWED_ORIGINS` | Empty; comma-separated exact HTTP(S) frontend origins |

Default Ollama URLs must use loopback IPs or `localhost`. Credentials in the URL
are rejected. Remote operation invalidates the local-only privacy claim. Ollama
HTTP clients ignore environment proxies. See [security](security.md).

## Custom source and index

Set both paths in the same shell for every command:

```powershell
$env:RAG_DATA_PATH = 'D:\UTC\handbook.pdf'
$env:RAG_CHROMA_DIR = 'D:\UTC\index'
uv run --locked utc-ingest
uv run --locked utc-doctor
.\scripts\start-local.ps1 -Background
```

Ingestion flags `--data-path` and `--persist-dir` apply to that one command and do
not save settings for later processes. A new shell must export them again. Relative
paths are resolved from the working directory; launch scripts change to the project
root. Installed wheels contain code, not the PDF/benchmark; supply absolute paths
when running outside a source checkout.

Source, embedding or chunk-setting changes require an explicit rebuild followed by
an API restart. Model/prompt/retrieval changes require fresh benchmark and semantic
review. The context size and reasoning flag are fixed baseline settings in code.
