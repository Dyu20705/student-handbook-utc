# Local operations

## Qualified release handoff — 2026-10-16

The qualified runtime is commit
`36dc88b17ada7aa722d1c34a5510c8d4c46b5a27`. Its scope is the K67 source PDF on
one trusted local machine, one API worker and embedded Chroma. Final owner review
is tracked in [PR #1](https://github.com/Dyu20705/student-handbook-utc/pull/1).
Documentation-only descendants can retain this runtime qualification when the
runtime, lockfile, model configuration, source, benchmark and launch/qualification
scripts are unchanged; record that comparison and run CI for the new commit.

| Recorded gate at the qualified runtime | Result |
| --- | --- |
| Offline Python 3.12 | 124 passed; 11 model-dependent cases skipped |
| Clean committed source, separate Python 3.11 environment | 124 passed; 11 skipped |
| Actual Ollama integration | 11 passed; zero skipped |
| Actual HTTP smoke | 36 checks passed, including health/readiness, auth, CORS, resource limits, q13/q15 and refusal |
| Full 25-question benchmark | Hit@3 95.45%; keyword 22/22; gold-page 21/22; refusal 3/3; operational errors 0 |
| Separate agent comparison with source PDF | 22/22 supported answers; 3/3 appropriate refusals |
| Runtime CI | 12 successful checks across [push](https://github.com/Dyu20705/student-handbook-utc/actions/runs/38870754873) and [pull request](https://github.com/Dyu20705/student-handbook-utc/actions/runs/38870759839) |
| Packaging, lint, workflow and history text scan | Passed; 34 commits scanned with no unexcepted secret finding |

Private evidence remains under `data/runtime/hardening-20261014/`:
`qualification-36dc88b-retry.json`, `independent-semantic-review-36dc88b.json`,
`integration-36dc88b.xml`, `http-smoke-36dc88b.json` and
`final-release-gate-36dc88b.json`. The full benchmark artifact SHA-256 is
`f947d3bd23d65304117912be5192afdeae19556d39eaac95e41be795b4d3cac1`.
Input hashes remained stable, and all 25 ordered retrieved contexts matched the
frozen baseline. The first interrupted attempt remains recorded as incomplete.
Back up the private evidence before removing the checkout.

The source comparison was performed by a separate agent on known questions using
PDF text extraction. It is not a blind evaluation or human approval. q12 is
supported by the eUTC instructions on PDF page 84 while its unchanged gold page
is 4. q13 retains Floor 1 A8; q15 retains its cross-page conditions. Approximate
section labels and general answer-completeness limits still apply.

Before first operational use, run doctor, start the API, check `/health` and
`/ready`, and verify one cited answer and one refusal. Set explicit frontend
origins and bearer authentication when the local workflow needs them. Keep the
API and Chroma within the [security scope](security.md).

During use, inspect 429/503 responses, readiness, latency and the local process
logs. Stop accepting new work on a readiness failure, source/configuration drift,
or an incomplete material answer; investigate against the PDF and use the rollback
procedure below if needed. Let active inference finish before maintenance.
There is no unattended monitoring service or multi-user latency SLA.

The four embedded-only Chroma exceptions and six exact secret-scan exceptions
require review by **2026-11-13**, even if feature development stops. PDF retention
follows the owner's recorded permission confirmation; independently verified
rights-holder documentation is not claimed. Owner approval and merge remain
separate from the recorded technical gates.

## Release checks

Keep `uv.lock` with the source and install with `uv sync --locked --python 3.12`.
CI runs offline unit/contract tests on Windows and Ubuntu with Python 3.11/3.12,
Ruff lint and format checks, wheel/sdist inventory checks, a dependency audit,
actionlint and a redacted Git-history secret scan. CI does not run Ollama.

Run the real-model gate on the configured local machine, without serving other
users or running another benchmark at the same time:

```powershell
uv run --locked utc-doctor
uv run --locked python -m pytest --run-integration -q
# Commit the reviewed changes first; choose a new artifact name for every run.
uv run --locked python scripts/run_qualification.py --output data/runtime/qualification-release-001.json
uv build
uv run --locked python scripts/check_distribution.py dist
```

The qualification harness requires clean tracked files and records commit, source,
runtime/lock/benchmark hashes, dependency versions, index manifest, Ollama version,
model digests and complete responses/context. It rechecks inputs at the end and
never overwrites an existing result. Untracked files are not qualification inputs;
only the reviewed runtime, benchmark, source and harness should participate.

Automatic minimums remain Hit@3 >= 90%, keyword match >= 80%, citation-page match
>= 90%, all three out-of-scope refusals, and zero operational errors. The harness
records results; its exit code checks input stability and operational errors, so
review these proxy thresholds separately. `python -m student_handbook_rag.evaluate
--check-proxies --output data/runtime/evaluation-release-001.json` provides the automatic
threshold check when a separate evaluation run is wanted. Never reduce thresholds
to obtain a pass.

Read every answerable response against the PDF, recording the artifact SHA-256 and
per-question verdict. Check mandatory conditions, subjects, exceptions, negation
and numeric thresholds. Repeat the q15 scholarship regression. Independent review
and blind questions remain necessary for claims beyond the local development scope.

Start the API and verify `/health`, `/ready`, an answer with citations and an
out-of-scope refusal over HTTP. If using a separate frontend, test OPTIONS with
Authorization/Content-Type, a real bearer-authenticated call, and a rejected Origin.
Record responses, timings and the exact source/runtime/model hashes under ignored
`data/runtime/`. A failed smoke or degraded benchmark blocks release; keep the PR
Draft for owner review.

## Evidence retention and cleanup inventory

The 2026-10-14 hardening snapshot is local at
`data/runtime/hardening-20261014/`. Its `baseline/` contains the original `049c19f`
source ZIP, file hashes, API schema, offline test result and model/index inventory.
`archive/removed/` preserves the removed files; `archive/inventory.json` records
their SHA-256 values, and `archive/raw/` retains original audit artifacts and
runtime snapshots. Back up this directory outside the checkout before discarding
the working directory; it is not included in Git or distributions.

The source ZIP retains the original committed tree with Git checkout line-ending
attributes. The 33 initially archived files retain their exact working-tree bytes;
later test moves and wrapper removals are recoverable from the source ZIP and Git.

| Disposition | Files / reason |
| --- | --- |
| Keep | K67 PDF, gold benchmark, baseline retrieval/generation, local launch/qualification scripts |
| Archive and remove | `docs/qualification/` tracked bundle, `docs/research/`, old evaluation output; historical observations are not evidence for a new runtime |
| Archive and remove | ARAGOG/CRAG/memory, their tests/dependencies, unused prompt files and paper downloader; no baseline callers |
| Remove from release input | Unverified `data/raw/handbook.txt`; replace loader-test usage with synthetic temporary fixtures |
| Replace | Historical evidence CI coupling with current offline checks and a standalone strict distribution verifier |
| Preserve separately | Pre-existing untracked source-intake design/schema files, outside this release change |

The historical verifier passed before cleanup. Its immutable snapshot at commit
`049c19fefd91466f4aa040e38e3d0347b771e5f5` still verifies the historical bundle in a
checkout of that commit with full Git history. It must not be used to certify the
new runtime. Historical metrics and failures were not rewritten, and removing the
files from HEAD does not erase previously published Git history. No old report is
silently relabeled as current qualification.

The first post-hardening run at `0765561` matched the historical automatic proxies
but failed q15 source comparison and the HTTP scholarship check. Its benchmark,
HTTP response, diagnosis and semantic review remain under the local snapshot.
The owner authorized a bounded generation-instruction follow-up; it requires its
own committed qualification. A later pass must not replace or hide those failures.

The follow-up at `49c5d91` preserved the q15 conditions but failed source comparison
for q13: the answer described the bookshop without its floor and building. This
benchmark and semantic failure are also retained. A further instruction clarifies
location answers, with bookshop and document-search regressions; it likewise needs
qualification of its committed runtime.

## Processes, logs and recovery

Windows scripts manage one API process per project. A second start on another port
is refused while that process exists. Start/stop share a file lock, and stop checks
the process identity before terminating it. Foreground uses Ctrl+C; background
uses `stop-local.ps1`.

Background logs are `data/runtime/server.stdout.log` and `server.stderr.log`.
Application logs contain request ID, status, duration and error type, not questions,
PDF content or bearer tokens. Debug CLI output and benchmark artifacts do contain
source text and must remain local. Stop the server before rotating logs; automatic
rotation is not implemented.

Monitor 429, 503, latency and `/ready`. After a readiness failure run `utc-doctor`
and check Ollama, models, source hash and manifest before sending more work.
Timeout is per I/O operation, not a total inference deadline. Let inference finish
before maintenance. Store p95 measurements with the machine and workload; there is
no multi-user latency SLA.

## Backup, rebuild and rollback

Stop API and ingestion before copying the complete index directory, including
SQLite/WAL files and vector segments, the source PDF, `uv.lock`, environment
configuration and corresponding source revision. Use a new backup directory.
Do not copy only `chroma.sqlite3` from a running service.

`utc-ingest --force` builds a new immutable collection and atomically replaces the
active manifest only after all batches succeed. Failed builds preserve the old
generation. Save the old manifest before rebuild and restart the API afterwards.

To restore, use a separate directory and point `RAG_CHROMA_DIR` at the restored
copy. For generation rollback, stop all readers/writers and restore a saved manifest
whose collection still exists, with matching source bytes and embedding model.
Run doctor, start and smoke before use. Runtime rollback also requires the matching
source revision and lockfile. Test restoration on a copy periodically. Old and
crash-orphaned collections are not automatically pruned.
