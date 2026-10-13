# Changelog

## 0.2.0 — 2026-10-13

- Add loopback-only API, readiness doctor, PowerShell lifecycle scripts, locked dependencies and CI.
- Publish versioned indexes atomically; preserve previous generations and reject missing/mismatched indexes on startup.
- Require structured model output and validated citation IDs; separate operational failures from refusals.
- Qualify qwen3.5:9b-q4_K_M with five context chunks (three dense plus two lexical candidates); return source excerpts for verification.
- Fix missing-source fallback and evaluation false positives; distinguish keyword/page proxies from semantic correctness.
- Isolate optional research modules and document backup, rollback and embedded Chroma security exceptions.

Migration: Python 3.11–3.12, `uv sync --locked`, then `utc-ingest --force`. Readers no longer build indexes automatically. Responses add `status` and errors; refusal sources are empty. Generation evaluation metric names change to `answer_keyword_match_rate` and `citation_page_match_rate`.
