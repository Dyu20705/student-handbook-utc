# Security scope

The API binds to `127.0.0.1`, uses one worker and embedded Chroma, and trusts the
local operator. It has no upload, ingestion, tenant or administrative HTTP endpoints.
Do not expose it to a LAN/Internet or run a Chroma HTTP server under this policy.

Trusted Host checks limit DNS rebinding. An exact browser-origin allowlist defaults
to empty; untrusted origins are rejected before inference. Optional bearer auth
protects `/ask`, with constant-time comparison. CORS is not authentication against
non-browser clients. There is no TLS termination, role-based access control or
distributed quota. Request body, question length, top-k, rate and concurrency are
bounded. See the [API contract](api.md).

Ollama URLs must be loopback unless `RAG_ALLOW_REMOTE_OLLAMA=1` explicitly permits
sending questions/context off-machine. Clients ignore environment proxies. The
service does not accept model repository or embedding-function configuration from
HTTP callers. Keep `.env`, keys, raw answers and diagnostic artifacts out of Git.

## Dependency exceptions

The locked dependency audit retains four scoped Chroma exceptions. They apply only
to this embedded deployment, not to arbitrary use of the package.

| Advisory | Affected surface | Reason for local exception |
| --- | --- | --- |
| PYSEC-2026-311 / CVE-2026-45829 | Python HTTP collection creation with an untrusted model repository | That server/route is not exposed |
| PYSEC-2026-3814 / CVE-2026-45833 | HTTP collection update code injection | No update endpoint or untrusted remote model configuration |
| PYSEC-2026-3815 / CVE-2026-45831 | SimpleRBACAuthorizationProvider scope bypass | No RBAC/multi-tenant server |
| PYSEC-2026-3813 / CVE-2026-45830 | HTTP tenant authorization | No tenant API |

Review before every release, when deployment scope changes, and no later than
**2026-11-13**. CI fails once that review date expires. Enabling the Chroma server
or accepting untrusted embedding configuration invalidates these exceptions and
blocks release. Other vulnerabilities still fail the audit. The exceptions are
not a claim that Chroma has no vulnerabilities.

The unfiltered audit checked on 2026-10-16 returned five records for these four
unique IDs: `PYSEC-2026-311` appeared twice with the same CVE/GHSA aliases.
Thus an audit summary of `5 ignored` does not imply a fifth unique exception.
Reconcile IDs and aliases when reviewing future audit output; do not infer safety
from the count alone.

```powershell
uv run --locked python -m pip_audit --local --skip-editable
uv run --locked python -m pip_audit --local --skip-editable --ignore-vuln PYSEC-2026-311 --ignore-vuln PYSEC-2026-3814 --ignore-vuln PYSEC-2026-3815 --ignore-vuln PYSEC-2026-3813
```

Requests remains constrained to >=2.33 for its documented
[temporary-file advisory](https://github.com/psf/requests/security/advisories/GHSA-gc5v-m9x4-r6x2).
No blanket dependency upgrade is part of this hardening; removed optional research
dependencies are pruned from the lockfile.

## Repository and distribution checks

CI pins Actions to full commit SHAs, uses read-only repository permissions, runs
actionlint, and scans Git history with redacted gitleaks output. Tool binaries are
versioned and checksum-verified. These checks do not erase any historical data.
Pinning follows [GitHub's security guidance](https://docs.github.com/en/actions/reference/security/secure-use).

The first full-history scan found six `generic-api-key` false positives: SHA-256
values for `src/student_handbook_rag/api.py` in three benchmark artifacts at each
of commits `ef1d506` and `2b423df`. Each value was verified against the recorded
runtime source bytes (using preserved original line endings for the raw reports).
`.gitleaksignore` permits only those six exact commit/file/rule/line fingerprints,
not a path or rule in general. Review these exceptions by **2026-11-13** along with
the dependency exceptions. New findings still block CI. PDF text conversion is
disabled during history scanning; binary PDF contents are outside this text scan.

`scripts/check_distribution.py` allows reviewed wheel/sdist members and known
metadata only. Unknown files, symlinks, duplicate members and unsafe paths fail.
PDFs, benchmark data, evidence, research and runtime files are excluded. Inventory
validation complements secret scanning and code review; it cannot prove the contents
of an approved file are safe. Local evidence must be backed up separately.
