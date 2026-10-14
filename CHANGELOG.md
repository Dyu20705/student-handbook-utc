# Changelog

## PR #1 evidence publishing — 2026-10-14

- Restrict wheel/sdist members to reviewed file allowlists with explicit metadata exceptions; reject unlisted snapshots even inside package/test/metadata directories, links and duplicate members.
- Reproduce the previous packaging gap with six failing regressions before the fix; preserve full-history evidence verification and its existing provenance gates.
- Replace public raw artifacts with minimized summaries, preserve exact audit inputs locally, and distinguish public/raw SHA-256 values.
- Exclude qualification evidence from wheel/sdist; retain historical failures and disclose that previously published Git history remains accessible.
- Add a stdlib-only offline verifier for artifact schemas/hashes, recomputed proxies, Git/runtime provenance, JUnit outcomes and report references, including distribution checks in CI.
- Label the Codex semantic review as non-independent development evidence; keep blind questions, independent review and repeated q15 testing as a separate gate before broader quality claims.

## PR #1 review fixes — 2026-10-13–14

- Serialize Windows start/stop and reject a second managed server on any port.
- Reject remote Ollama by default; require an explicit opt-in and document shared custom-path environment variables.
- Rename per-answer correctness/grounding labels to keyword/page proxies; leave semantic verdict unreviewed until source comparison.
- Record exact commit, runtime hashes, model digests, dependency versions and full responses in qualification runs.
- Preserve adjacent bullet-list continuations across PDF pages for generation, with bounded context growth and separate page citations. Retrieval scoring is unchanged.
- Keep continuations beside their preceding chunk, omit inferred section headings from the prompt, and prohibit inferring article numbers from list numbering.
- Label cross-page list continuations explicitly and request citations for every answer condition after a repeated integration run exposed an intermittent omission.
- Withdraw the original artifact as HEAD qualification, mark historical q15 semantically failed, correct q12's gold page and add a 22-question semantic rubric.

## 0.2.0 — 2026-10-13

- Add loopback-only API, readiness doctor, PowerShell lifecycle scripts, locked dependencies and CI.
- Publish versioned indexes atomically; preserve previous generations and reject missing/mismatched indexes on startup.
- Require structured model output and validated citation IDs; separate operational failures from refusals.
- Qualify qwen3.5:9b-q4_K_M with five context chunks (three dense plus two lexical candidates); return source excerpts for verification.
- Fix missing-source fallback and evaluation false positives; distinguish keyword/page proxies from semantic correctness.
- Isolate optional research modules and document backup, rollback and embedded Chroma security exceptions.

Migration: Python 3.11–3.12, `uv sync --locked`, then `utc-ingest --force`. Readers no longer build indexes automatically. Responses add `status` and errors; refusal sources are empty. Generation evaluation metric names change to `answer_keyword_match_rate` and `citation_page_match_rate`.
