## Change summary

Describe the behavior or contract changed and why it is needed.

## Scope and compatibility

- Affected components, API or index/schema compatibility:
- Source, benchmark, model, dependency or security implications:
- Migration or rollback considerations (if applicable):

## Verification

- [ ] Offline tests, lint, format and distribution checks pass.
- [ ] CI checks pass on the final PR commit.
- [ ] API contract and failure-path tests cover behavior changes.
- [ ] Real Ollama/HTTP qualification is repeated when runtime, retrieval,
      prompt, source, model or deployment configuration changes.
- [ ] Generated data, secrets, private evidence and transient research/audit
      notes are excluded from the committed tree.
- [ ] Documentation reflects supported behavior and known limitations.

Include reproducible commands and link to CI runs. Record private
qualification artifacts under ignored `data/runtime/`; do not paste sensitive
answers or source excerpts into the PR.

## Release decision

- [ ] Known limitations and security exceptions are accepted for this
      specific deployment scope.
- [ ] An owner has reviewed the final diff and explicitly approved merge.

Passing CI alone does not authorize a release or a merge.
