# Evidence summary (generated)

Do not edit: `python scripts/evidence.py publish --raw-dir data/runtime/evidence-private`.

Qualified local runtime: `8b7149441362540085793001f2f1ea5b2fdb2cbc`.

These are development observations on known questions. The Codex review is not independent.

| Run | Hit@1 / @3 / @5 | MRR | Keyword proxy | Gold-page proxy | Refusals | Errors | Codex content review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c3b96c6 | 59.09% / 95.45% / 95.45% | 0.7652 | 22/22 | 20/22 | 3/3 | 0 | 19/22 |
| d540993 | 59.09% / 95.45% / 95.45% | 0.7652 | 22/22 | 21/22 | 3/3 | 0 | 22/22 |
| 8b71494 | 59.09% / 95.45% / 95.45% | 0.7652 | 22/22 | 21/22 | 3/3 | 0 | 22/22 |

Local test observations (CI does not rerun Ollama):

| JUnit artifact | Passed | Failed | Errors | Skipped |
| --- | --- | --- | --- | --- |
| [integration-d540993-retry.xml](integration-d540993-retry.xml) | 8 | 1 | 0 | 0 |
| [integration-8b71494.xml](integration-8b71494.xml) | 9 | 0 | 0 | 0 |
| [offline-8b71494.xml](offline-8b71494.xml) | 68 | 0 | 0 | 9 |

SHA-256: public files are minimized exports; raw hashes identify the original audit inputs.

| Artifact | Public SHA-256 | Raw SHA-256 |
| --- | --- | --- |
| [benchmark-c3b96c6.json](benchmark-c3b96c6.json) | `cec7edf61a69f7f9d62be331ed4aff29e22b81ac0086753e21ff5e4758bb740e` | `a6ac4d9a1d4165fbd4bb075056052e43163adf0aa8e14cb6bcf128158ea969a1` |
| [benchmark-d540993.json](benchmark-d540993.json) | `ae4287d0c047fbf724f2aacccd6fa6e2c2c60a02b7c511927e29277b79195e17` | `9d541fd7859ce22c5f9b8b2c5f7032fb44c1ac2d2e75544be4571ace342e9cd0` |
| [benchmark-8b71494.json](benchmark-8b71494.json) | `fc59cae029f1b646b2fff80ea7ab20dcbd52d050bd41408b38e05a06263898f8` | `fcad3aa99e17021b99e2869e20ff54e6a8e054c723e35e717978bf0437d49b56` |
| [integration-d540993-retry.xml](integration-d540993-retry.xml) | `94197a74a1632a6797b676ce0acafdfc768eb38cbbd4c6db1a207ce36e6fb24b` | `d3e6e435674077108f03c58a88b51c4bd3cac9345e1761eb1ac2d17ca2258c8f` |
| [integration-8b71494.xml](integration-8b71494.xml) | `9199cf44848582717780def1a2faff8579377469926319182336660db027951a` | `8380abc949302fd10ae7aee7f4111a10f5a8f3d643f542fafc9c2b09a25699b2` |
| [offline-8b71494.xml](offline-8b71494.xml) | `65855832caf5e2aa6fcf74a61c0cdc26ae79599c7a8c7c11cadf8be5110fe388` | `96dcea388afe70aff0f08bd91c8ce4be54bea989a8b4f8f489d6f7bad5602f43` |
| [local-benchmark-2026-10-13.json](local-benchmark-2026-10-13.json) | `d591454849365b05f9ee0a6a588c73b20529ee8475fa70dfc378dc7d5c482f53` | `6894eaf0edfb1eb10c32d8906dc23a5127a9b5dbdab40b45767ac3659a0c8d06` |
| [http-smoke-8b71494.json](http-smoke-8b71494.json) | `d55c67f9314c3daf10f6b053ae47d13ad72d2c933ed2beaca339b61b2f7d6241` | `768ab88da917fb3ff727fadd9ae81184812fbb6ccb5173b7f61a90e879004cff` |

See [publishing policy](evidence-policy.md), [local scope](local-production-readiness.md),
[semantic review](semantic-review.md) and [rubric](semantic-rubric.md).
