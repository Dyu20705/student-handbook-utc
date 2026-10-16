# Data inventory and provenance

| Location | Purpose | Versioned? |
| --- | --- | --- |
| `raw/sotaysvk67.pdf` | Operator-supplied UTC K67 source handbook | Yes, in Git; excluded from wheel/sdist |
| `benchmark/evaluation_set.json` | Reviewed 25-question gold benchmark, including Vietnamese questions/answers | Yes, in Git; excluded from wheel/sdist |
| `chroma/` | Local vectors, collections and active-generation manifests | No |
| `runtime/` | Logs, process state, raw evaluation, snapshots and archived audit/research material | No |

The owner confirmed permission to retain and redistribute the K67 PDF on
2026-10-14. The supplied file's SHA-256 is
`2ee1e3970b65cd36d8e6fe2e9e406965c4a20cc32b816a3b199341561dda208a`.
This records the release input and owner confirmation, not an independently
established download provenance or a claim that its policies are current.

The former `raw/handbook.txt` contained an unverified Academic Year 2026–2027 text.
It was not established as an extract of the PDF and was removed from the release.
TXT loader tests now create explicitly synthetic fixtures in temporary directories.
Do not ingest those fixtures as policy content.

Generated benchmark results belong under `runtime/`, never beside the gold set.
The old `benchmark/eval_results.json`, research PDFs/report, experimental modules,
and qualification bundle were preserved in a local hash inventory before removal.
The [operations policy](../docs/operations.md) explains retention and reproduction.
Removing files from the current tree does not remove their Git history.
