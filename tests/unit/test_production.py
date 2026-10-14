import json
import subprocess
import sys
from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from student_handbook_rag import vectorstore
from student_handbook_rag.chain import StudentHandbookRAG
from student_handbook_rag.evaluate import evaluate_generation, evaluate_retrieval
from student_handbook_rag.loader import ragchunking, ragload


def test_import_has_no_model_side_effects():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import student_handbook_rag; assert 'student_handbook_rag.memory' not in sys.modules; assert 'sentence_transformers' not in sys.modules; assert 'chromadb' not in sys.modules",
        ],
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def test_missing_source_does_not_load_default(tmp_path):
    with pytest.raises(FileNotFoundError):
        ragload(str(tmp_path / "missing.pdf"))


@pytest.mark.parametrize("size,overlap", [(0, 0), (10, 10), (10, -1)])
def test_invalid_chunk_parameters(size, overlap):
    with pytest.raises(ValueError):
        ragchunking([], size, overlap)


@pytest.fixture
def index_fixture(tmp_path, monkeypatch):
    embedding = DeterministicFakeEmbedding(size=8)
    monkeypatch.setattr(vectorstore, "get_embedding_function", lambda: embedding)
    source = tmp_path / "handbook.txt"
    source.write_text("Quy chế đào tạo sinh viên UTC. " * 20, encoding="utf-8")
    return str(tmp_path / "index"), str(source), embedding


def test_reader_never_creates_missing_index(index_fixture):
    path, source, _ = index_fixture
    with pytest.raises(vectorstore.IndexNotReadyError):
        vectorstore.build_vector_store(path, source, load_only=True)
    from pathlib import Path

    assert not Path(path).exists()


def test_rebuild_failure_preserves_previous_generation(index_fixture, monkeypatch):
    path, source, embedding = index_fixture
    original = vectorstore.build_vector_store(path, source)
    manifest = vectorstore.read_manifest(path)
    monkeypatch.setattr(
        type(embedding), "embed_documents", MagicMock(side_effect=RuntimeError("offline"))
    )
    with pytest.raises(RuntimeError, match="offline"):
        vectorstore.build_vector_store(path, source, force_rebuild=True)
    assert vectorstore.read_manifest(path) == manifest
    assert original._collection.count() == manifest["chunk_count"]
    assert vectorstore.build_vector_store(path, source, load_only=True)._collection.count() > 0


def test_repeated_ingestion_is_idempotent(index_fixture):
    path, source, _ = index_fixture
    first = vectorstore.build_vector_store(path, source)
    second = vectorstore.build_vector_store(path, source)
    assert first._collection.name == second._collection.name
    rebuilt = vectorstore.build_vector_store(path, source, force_rebuild=True)
    assert rebuilt._collection.name != first._collection.name
    assert rebuilt._collection.count() == first._collection.count()


def test_manifest_publication_failure_preserves_reader(index_fixture, monkeypatch):
    path, source, _ = index_fixture
    vectorstore.build_vector_store(path, source)
    previous = vectorstore.read_manifest(path)
    monkeypatch.setattr(vectorstore.os, "replace", MagicMock(side_effect=OSError("disk full")))
    with pytest.raises(OSError, match="disk full"):
        vectorstore.build_vector_store(path, source, force_rebuild=True)
    assert vectorstore.read_manifest(path) == previous
    assert (
        vectorstore.build_vector_store(path, source, load_only=True)._collection.name
        == previous["collection"]
    )


def test_source_change_requires_explicit_rebuild(index_fixture):
    from pathlib import Path

    path, source, _ = index_fixture
    vectorstore.build_vector_store(path, source)
    Path(source).write_text("New content", encoding="utf-8")
    with pytest.raises(vectorstore.IndexNotReadyError, match="changed"):
        vectorstore.build_vector_store(path, source)
    with pytest.raises(vectorstore.IndexNotReadyError, match="snapshot"):
        vectorstore.build_vector_store(path, source, load_only=True)


def test_writer_lock_prevents_concurrent_ingestion(index_fixture):
    from pathlib import Path

    from filelock import FileLock, Timeout

    path, source, _ = index_fixture
    Path(path).mkdir()
    with FileLock(str(Path(path) / "ingest.lock")):
        with pytest.raises(Timeout):
            vectorstore.build_vector_store(path, source)


@pytest.fixture
def rag():
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        (Document(page_content="Học phí", metadata={"chunk_id": "c1", "page": 2}), 0.2)
    ]
    engine = StudentHandbookRAG(retriever=retriever, llm=MagicMock())
    engine.chain = MagicMock()
    return engine


def test_backend_error_is_not_refusal(rag):
    rag.chain.invoke.side_effect = RuntimeError("secret path and key")
    result = rag.query("học phí")
    assert result["status"] == "error"
    assert not result["is_insufficient_context"]
    assert "secret" not in result["answer"]


@pytest.mark.parametrize(
    "answer",
    [
        "not json",
        '{"answer":"test","citation_ids":["invented"],"insufficient_context":false}',
        '{"answer":"test","citation_ids":[],"insufficient_context":false}',
    ],
)
def test_invalid_generation_is_rejected(rag, answer):
    rag.chain.invoke.return_value = answer
    result = rag.query("học phí")
    assert result["status"] == "error"
    assert result["sources"] == []


def test_only_validated_citations_are_returned(rag):
    rag.chain.invoke.return_value = json.dumps(
        {"answer": "Học phí", "citation_ids": ["c1"], "insufficient_context": False}
    )
    result = rag.query("học phí")
    assert result["status"] == "answered"
    assert [s["chunk_id"] for s in result["sources"]] == ["c1"]


def test_evaluation_does_not_count_outage_as_refusal_or_none_page_as_citation():
    engine = MagicMock()
    engine.query.return_value = StudentHandbookRAG._error("q", "offline")
    metrics = evaluate_generation(
        [
            {"id": "a", "question": "q", "answerable": True},
            {"id": "b", "question": "q", "answerable": False},
        ],
        engine,
    )
    assert metrics["unanswerable_refusal_rate"] == 0
    assert metrics["citation_page_match_rate"] == 0
    assert metrics["answer_keyword_match_rate"] == 0
    assert metrics["operational_errors"] == 2


def test_retrieval_common_keyword_cannot_override_wrong_page():
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        (Document(page_content="sinh viên", metadata={"page": 1}), 0.1)
    ]
    result = evaluate_retrieval(
        [{"id": "a", "question": "q", "expected_page": 20, "gold_keywords": ["sinh viên"]}],
        retriever,
    )
    assert result["hit_at_1"] == 0
