# HTTP API

Base URL: `http://127.0.0.1:8000`. `/openapi.json` is the generated typed schema;
`/docs` is the interactive client. Running the service requires a valid existing index.

| Endpoint | Result |
| --- | --- |
| `GET /health` | `{"status":"ok","version":"0.2.0"}` |
| `GET /ready` | `{"status":"ready"}`, or 503 when dependencies/index are unavailable |
| `POST /ask` | A typed answer or refusal |

## Requests and responses

```json
{"question":"Quy định điểm F?","k":5}
```

`question` is trimmed and must contain 1–2,000 characters. `k` is a strict integer
from 1 to 10 (default 5); booleans and unknown fields are rejected. Bodies over
16 KiB are rejected before JSON parsing, including streamed bodies.

Success retains the existing fields: `query`, `answer`, `sources`,
`is_insufficient_context`, and `status` (`answered` or `refused`). A refusal returns
HTTP 200, `is_insufficient_context=true`, and an empty `sources` list. Operational
failures return 503; clients must not count them as refusals. Raw retrieved chunks
are never included in the HTTP response.

Each cited source contains:

| Field | Meaning |
| --- | --- |
| `document`, `document_id` | Portable source filename, such as `sotaysvk67.pdf`; a single-document identifier, not a version hash |
| `source` | Existing field, now an alias of `document_id` instead of a machine path |
| `page` | One-based PDF page |
| `book_page` | Printed-page estimate: PDF page minus two, or zero for front matter; explicitly loaded text uses page 1 |
| `section` | Page-level heading estimate; may be null or inaccurate |
| `chunk_id` | ID validated against generation context; meaningful for this indexed source version |
| `excerpt` | Exact trimmed chunk text used as supporting context |
| `retrieval_rank` | Original one-based retrieval position; null for added continuation chunks |
| `context_rank` | Position after continuation expansion; cited sources may have gaps |
| `score` | Preserved float field: legacy context order, not similarity, probability or confidence |

Use the manifest source SHA-256 when distinguishing document revisions. A valid
citation is not proof that all answer claims are correct. The excerpt, PDF page
and [limitations](limitations.md) remain part of the client contract.

## Errors and resource limits

Errors retain the `detail` envelope. Ordinary errors use a string; model/retrieval
errors use `{"detail":{"code":"generation_unavailable","message":"..."}}`.
Validation errors use FastAPI's documented list of validation details. Unknown
exceptions are replaced by a generic service message, without stack traces or paths.

| HTTP | Meaning |
| --- | --- |
| 400 | Untrusted Host, or invalid preflight method/header |
| 401 | Missing or invalid bearer token when `RAG_API_KEY` is set |
| 403 | Browser Origin is neither the backend origin nor explicitly allowed |
| 413 | Body exceeds 16 KiB |
| 422 | Invalid JSON/request fields |
| 429 | Inference busy (retry after 5 seconds) or 30/minute limit (60 seconds) |
| 503 | Index/model unavailable or invalid model output |

Responses include `X-Request-ID`, `Cache-Control: no-store`, `nosniff`, and
`Referrer-Policy: no-referrer`. Rate limits are process-wide, not per user. Failed
inference attempts and busy requests consume the minute budget; preflights do not.

## Frontend origin and authentication policy

The default cross-origin allowlist is empty. Same-origin and clients without an
Origin header continue to work. Configure exact origins before starting the API:

```powershell
$env:RAG_ALLOWED_ORIGINS = 'http://localhost:5173,http://127.0.0.1:5173'
$env:RAG_API_KEY = 'your-private-random-token'
```

Only explicitly listed origins receive CORS access. Wildcards, `null`, URL paths,
credentials, trailing slashes and malformed ports are invalid configuration.
The two example hostnames are different browser origins. An untrusted Origin is
rejected before inference, including simple requests that do not need preflight.

`OPTIONS` preflight permits GET/POST and Authorization/Content-Type headers without
requiring a token. Actual `/ask` calls still require `Authorization: Bearer <token>`
when configured. Trusted browsers can read error bodies, `X-Request-ID` and
`Retry-After`. Cookie credentials are not enabled; use a bearer header with
`credentials: "omit"`. CORS is not authentication against non-browser clients.

Implementation reference: [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/).
