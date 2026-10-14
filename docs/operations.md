# Local operations

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
