"""Browser requests exercise the actual middleware order and public response models."""

import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from student_handbook_rag.api import create_app
from student_handbook_rag.chain import REFUSAL_ANSWER, StudentHandbookRAG

ORIGIN = "http://localhost:5173"


@pytest.fixture
def browser(monkeypatch):
    monkeypatch.setenv("RAG_ALLOWED_ORIGINS", ORIGIN)
    monkeypatch.setenv("RAG_API_KEY", "contract-test-key")
    engine = MagicMock()
    engine.query.return_value = {
        "query": "q",
        "answer": "A cited answer",
        "sources": [],
        "retrieved_chunks": [],
        "status": "answered",
        "is_insufficient_context": False,
    }
    with TestClient(
        create_app(lambda: engine, lambda: None, lambda _: None), base_url="http://127.0.0.1:8000"
    ) as client:
        yield client, engine


def test_preflight_accepts_auth_headers_without_auth_or_inference(browser):
    client, engine = browser
    for _ in range(31):
        response = client.options(
            "/ask",
            headers={
                "Origin": ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == ORIGIN
        assert "origin" in response.headers["vary"].lower()
        assert response.headers["x-request-id"]
    engine.query.assert_not_called()
    response = client.post(
        "/ask",
        json={"question": "q"},
        headers={
            "Origin": ORIGIN,
            "Authorization": "Bearer contract-test-key",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-credentials" not in response.headers
    assert "X-Request-ID" in response.headers["access-control-expose-headers"]


@pytest.mark.parametrize("origin", ["https://evil.example", "null", "http://localhost:5174", ""])
@pytest.mark.parametrize("method", ["POST", "OPTIONS"])
def test_untrusted_origins_are_denied_before_inference(browser, origin, method):
    client, engine = browser
    response = client.request(
        method,
        "/ask",
        json={"question": "q"},
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Authorization": "Bearer contract-test-key",
        },
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Origin not allowed"}
    assert "access-control-allow-origin" not in response.headers
    engine.query.assert_not_called()


@pytest.mark.parametrize(
    "requested",
    [
        {"Access-Control-Request-Method": "DELETE"},
        {"Access-Control-Request-Headers": "X-Unapproved"},
    ],
)
def test_preflight_rejects_unapproved_methods_and_headers(browser, requested):
    client, engine = browser
    response = client.options(
        "/ask",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            **requested,
        },
    )
    assert response.status_code == 400
    engine.query.assert_not_called()


def test_preflight_does_not_bypass_trusted_host(browser):
    client, engine = browser
    response = client.options(
        "/ask",
        headers={
            "Origin": ORIGIN,
            "Host": "evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400
    engine.query.assert_not_called()


@pytest.mark.parametrize("status", [401, 413, 422, 503])
def test_trusted_browser_can_read_error_responses(browser, status):
    client, engine = browser
    headers = {"Origin": ORIGIN, "Authorization": "Bearer contract-test-key"}
    kwargs = {"json": {"question": "q"}}
    if status == 401:
        headers.pop("Authorization")
    elif status == 413:
        kwargs = {"content": b"x" * 16385}
    elif status == 422:
        kwargs = {"json": {"question": " "}}
    else:
        engine.query.side_effect = RuntimeError("private filesystem path")
    response = client.post("/ask", headers=headers, **kwargs)
    assert response.status_code == status
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert response.headers["cache-control"] == "no-store"
    assert set(response.json()) == {"detail"}
    assert "private filesystem" not in response.text


def test_rate_limit_is_visible_to_trusted_browser(browser):
    client, _ = browser
    headers = {"Origin": ORIGIN, "Authorization": "Bearer contract-test-key"}
    for _ in range(30):
        assert client.post("/ask", headers=headers, json={"question": "q"}).status_code == 200
    response = client.post("/ask", headers=headers, json={"question": "q"})
    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert response.headers["retry-after"] == "60"
    assert "Retry-After" in response.headers["access-control-expose-headers"]


def test_same_origin_and_non_browser_clients_work_with_empty_allowlist(monkeypatch):
    monkeypatch.delenv("RAG_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("RAG_API_KEY", raising=False)
    with TestClient(
        create_app(lambda: MagicMock(), lambda: None, lambda _: None),
        base_url="http://127.0.0.1:8000",
    ) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/health", headers={"Origin": "http://127.0.0.1:8000"}).status_code == 200
        assert client.get("/health", headers={"Origin": ORIGIN}).status_code == 403


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "null",
        "http://*.example",
        "ftp://localhost",
        "http://user:pass@localhost",
        "http://localhost:5173/",
        "http://localhost/path",
        "http://localhost?key=1",
        "http://localhost#fragment",
        "http://localhost:0",
        "http://localhost:65536",
        "http://localhost:invalid",
        "http://localhost:",
    ],
)
def test_invalid_origin_configuration_fails_closed(monkeypatch, origin):
    monkeypatch.setenv("RAG_ALLOWED_ORIGINS", origin)
    with pytest.raises(ValueError):
        create_app()


@pytest.mark.parametrize("path", [r"C:\private\sotaysvk67.pdf", "/home/private/sotaysvk67.pdf"])
def test_citations_keep_legacy_fields_without_machine_paths(monkeypatch, path):
    monkeypatch.delenv("RAG_API_KEY", raising=False)
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        (
            Document(
                page_content="A source excerpt.",
                metadata={
                    "source": path,
                    "document": "sotaysvk67.pdf",
                    "page": 45,
                    "book_page": 43,
                    "section": "Section estimate",
                    "chunk_id": "c1",
                },
            ),
            1.0,
        )
    ]
    engine = StudentHandbookRAG(retriever=retriever, llm=MagicMock())
    engine.chain = MagicMock()
    engine.chain.invoke.return_value = json.dumps(
        {
            "answer": "A cited answer",
            "citation_ids": ["c1"],
            "insufficient_context": False,
        }
    )
    with TestClient(
        create_app(lambda: engine, lambda: None, lambda _: None), base_url="http://127.0.0.1"
    ) as client:
        response = client.post("/ask", json={"question": "q"})
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"query", "answer", "sources", "is_insufficient_context", "status"}
        citation = body["sources"][0]
        assert citation["source"] == citation["document_id"] == "sotaysvk67.pdf"
        assert citation["score"] == 1.0
        assert citation["context_rank"] == citation["retrieval_rank"] == 1
        assert citation["excerpt"] == "A source excerpt."
        assert "private" not in response.text
        engine.chain.invoke.return_value = json.dumps(
            {
                "answer": REFUSAL_ANSWER,
                "citation_ids": [],
                "insufficient_context": True,
            }
        )
        refused = client.post("/ask", json={"question": "unanswerable"})
        assert refused.status_code == 200
        assert refused.json()["status"] == "refused"
        assert refused.json()["sources"] == []
        assert refused.json()["is_insufficient_context"] is True


def test_openapi_describes_public_success_errors_and_bearer(browser):
    client, _ = browser
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/ask"]["post"]
    assert {"200", "401", "403", "413", "422", "429", "503"} <= set(operation["responses"])
    assert operation["security"] == [{"HTTPBearer": []}]
    models = schema["components"]["schemas"]
    assert models["Question"]["additionalProperties"] is False
    assert models["Answer"]["properties"]["status"]["enum"] == ["answered", "refused"]
    assert "retrieved_chunks" not in models["Answer"]["properties"]
    assert "retrieval_rank" in models["Citation"]["properties"]


@pytest.mark.parametrize("api_key", ["", "contract-test-key"])
def test_openapi_auth_matches_configured_enforcement(monkeypatch, api_key):
    monkeypatch.setenv("RAG_API_KEY", api_key)
    with TestClient(
        create_app(lambda: MagicMock(), lambda: None, lambda _: None),
        base_url="http://127.0.0.1",
    ) as client:
        operation = client.get("/openapi.json").json()["paths"]["/ask"]["post"]
        assert operation.get("security", []) == ([{"HTTPBearer": []}] if api_key else [])
        response = client.post("/ask", json={"question": ""})
        assert response.status_code == (401 if api_key else 422)
        if api_key:
            response = client.post(
                "/ask",
                json={"question": ""},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            assert response.status_code == 422
