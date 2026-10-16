import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from student_handbook_rag.api import create_app
from student_handbook_rag.chain import StudentHandbookRAG


@pytest.fixture
def engine():
    rag = MagicMock()
    rag.query.return_value = {
        "query": "q",
        "answer": "Thông tin",
        "sources": [],
        "retrieved_chunks": [],
        "is_insufficient_context": False,
        "status": "answered",
    }
    return rag


@pytest.fixture
def client(engine):
    with TestClient(
        create_app(lambda: engine, lambda: None, lambda _: None), base_url="http://127.0.0.1"
    ) as client:
        yield client


def test_health_query_and_privacy_headers(client):
    assert client.get("/health").status_code == 200
    response = client.post("/ask", json={"question": "Học phí?"})
    assert response.status_code == 200
    assert "retrieved_chunks" not in response.json()
    assert response.headers["x-request-id"]
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "payload",
    [
        {"question": " "},
        {"question": "a" * 2001},
        {"question": "q", "k": 11},
        {"question": "q", "k": True},
        {"question": "q", "extra": "field"},
    ],
)
def test_input_validation(client, payload):
    assert client.post("/ask", json=payload).status_code == 422


def test_oversized_chunked_body(client):
    response = client.post("/ask", content=iter([b"a" * 9000, b"b" * 9000]))
    assert response.status_code == 413


def test_external_origin_and_dns_rebinding_denied(client):
    assert (
        client.post(
            "/ask", json={"question": "q"}, headers={"origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert client.get("/health", headers={"host": "evil.example"}).status_code == 400


def test_api_key_when_configured(engine, monkeypatch):
    monkeypatch.setenv("RAG_API_KEY", "test-key")
    with TestClient(
        create_app(lambda: engine, index_check=lambda _: None), base_url="http://127.0.0.1"
    ) as client:
        assert client.post("/ask", json={"question": "q"}).status_code == 401
        assert (
            client.post(
                "/ask", json={"question": "q"}, headers={"authorization": "Bearer test-key"}
            ).status_code
            == 200
        )


def test_operational_error_returns_503(client, engine):
    engine.query.return_value = StudentHandbookRAG._error("q", "generation_unavailable")
    assert client.post("/ask", json={"question": "q"}).status_code == 503


def test_ready_checks_dependencies(engine):
    def unavailable():
        raise ConnectionError("private details")

    with TestClient(create_app(lambda: engine, unavailable), base_url="http://127.0.0.1") as client:
        response = client.get("/ready")
        assert response.status_code == 503
        assert "private details" not in response.text
        assert client.get("/health").status_code == 200


def test_ready_requires_active_generation_and_source(engine, monkeypatch):
    monkeypatch.setattr(
        "student_handbook_rag.api.read_manifest", lambda: {"collection": "active", "chunk_count": 2}
    )
    monkeypatch.setattr("student_handbook_rag.api.validate_source", lambda manifest: None)
    engine.retriever.vector_db._collection.name = "active"
    engine.retriever.vector_db._collection.count.return_value = 2
    with TestClient(
        create_app(lambda: engine, lambda: None), base_url="http://127.0.0.1"
    ) as client:
        assert client.get("/ready").status_code == 200
        engine.retriever.vector_db._collection.name = "old"
        assert client.get("/ready").status_code == 503
        assert client.post("/ask", json={"question": "q"}).status_code == 503
        engine.query.assert_not_called()


@pytest.mark.parametrize("field", ["chunk_size", "chunk_overlap"])
def test_chunk_drift_blocks_readiness_and_inference(engine, monkeypatch, tmp_path, field):
    import json

    from student_handbook_rag import vectorstore

    manifest = {
        "schema_version": 1,
        "collection": "utc_handbook_" + "a" * 32,
        "chunk_count": 2,
        "embedding_model": vectorstore.EMBEDDING_MODEL,
        "chunk_size": vectorstore.CHUNK_SIZE,
        "chunk_overlap": vectorstore.CHUNK_OVERLAP,
    }
    manifest_path = tmp_path / "utc_handbook.manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(
        "student_handbook_rag.api.read_manifest", lambda: vectorstore.read_manifest(tmp_path)
    )
    monkeypatch.setattr("student_handbook_rag.api.validate_source", lambda manifest: None)
    engine.retriever.vector_db._collection.name = manifest["collection"]
    engine.retriever.vector_db._collection.count.return_value = manifest["chunk_count"]
    with TestClient(
        create_app(lambda: engine, lambda: None), base_url="http://127.0.0.1"
    ) as client:
        assert client.get("/ready").status_code == 200
        manifest[field] += 1
        manifest_path.write_text(json.dumps(manifest))
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
        assert client.post("/ask", json={"question": "Học phí?"}).status_code == 503
        engine.query.assert_not_called()


def test_busy_inference_rejected_and_slot_released(client, engine):
    entered, release = threading.Event(), threading.Event()
    answer = engine.query.return_value

    def blocking_query(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return answer

    engine.query.side_effect = blocking_query
    with ThreadPoolExecutor() as pool:
        pending = pool.submit(client.post, "/ask", json={"question": "q"})
        assert entered.wait(5)
        try:
            assert client.post("/ask", json={"question": "q"}).status_code == 429
        finally:
            release.set()
        assert pending.result().status_code == 200
    engine.query.side_effect = None
    assert client.post("/ask", json={"question": "q"}).status_code == 200


def test_rate_limit(client):
    for _ in range(30):
        assert client.post("/ask", json={"question": "q"}).status_code == 200
    response = client.post("/ask", json={"question": "q"})
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
