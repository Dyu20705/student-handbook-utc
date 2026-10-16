# Changelog

Notable changes to the supported local UTC K67 handbook backend are recorded
here. Development experiments and individual review iterations remain in Git
history, not in release notes.

## Unreleased

### Local release hardening (2026-10-14 to 2026-10-16)

- Added explicit browser-origin controls, optional bearer authentication,
  typed API responses and contract tests for browser clients.
- Limited the API to a single loopback worker with bounded request size,
  rate, retrieval count and inference concurrency.
- Made the index lifecycle fail closed for missing, stale or incompatible
  source, embedding and chunk configuration; rebuilds publish atomically.
- Improved cross-page list continuation and prompts for eligibility conditions
  and precise location answers, without changing the qualified retrieval
  configuration or frozen benchmark.
- Removed unused experimental RAG modules, unverified text input, generated
  evaluation results and research artifacts from the release tree.
- Added Windows lifecycle controls, locked dependencies, cross-platform
  offline tests, distribution inventory verification, pinned CI tools,
  dependency auditing and full-history text secret scanning.
- Documented the bounded local qualification, its automatic metric limitations,
  operator procedures, recovery steps and time-limited security exceptions.

## 0.2.0 — 2026-10-13

- Introduced the local FastAPI service, readiness checks, CLI entry points
  and an Ollama-backed retrieval/generation pipeline.
- Added a versioned embedded Chroma index, explicit ingestion and rollback
  procedures, structured answer/refusal responses and validated citation IDs.
- Established Python 3.11–3.12 and `uv sync --locked` as supported setup
  requirements.

**Migration:** Rebuild the index with `utc-ingest --force` after upgrading
from a previous schema. Readers no longer create an index implicitly. Clients
must handle the `status` field and API error responses. Benchmark keyword
and page matches are proxies, not verified answer correctness.
