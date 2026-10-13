import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from student_handbook_rag import config


@pytest.mark.parametrize("url", ["http://127.0.0.1:11434", "http://127.2.3.4", "http://[::1]:11434", "http://localhost:11434"])
def test_loopback_ollama_is_allowed(monkeypatch, url):
    monkeypatch.setattr(config, "OLLAMA_BASE_URL", url)
    monkeypatch.setattr(config, "ALLOW_REMOTE_OLLAMA", "0")
    config.validate_config()


@pytest.mark.parametrize("url", ["https://ollama.example.org", "http://192.168.1.10:11434", "http://0.0.0.0:11434", "http://[2001:db8::1]", "http://localhost.example.org"])
def test_remote_ollama_requires_explicit_opt_in(monkeypatch, url):
    monkeypatch.setattr(config, "OLLAMA_BASE_URL", url)
    monkeypatch.setattr(config, "ALLOW_REMOTE_OLLAMA", "0")
    with pytest.raises(ValueError, match="RAG_ALLOW_REMOTE_OLLAMA=1"):
        config.validate_config()
    monkeypatch.setattr(config, "ALLOW_REMOTE_OLLAMA", "1")
    config.validate_config()


def test_invalid_remote_opt_in_is_rejected(monkeypatch):
    monkeypatch.setattr(config, "ALLOW_REMOTE_OLLAMA", "yes")
    with pytest.raises(ValueError, match="must be 0 or 1"):
        config.validate_config()


def test_custom_ingest_paths_are_shared_with_fresh_doctor_and_api(tmp_path):
    """Use a real persisted index across processes; fake only the external model."""
    source = tmp_path / "custom handbook.txt"
    source.write_text("Sinh viên UTC được sử dụng thư viện tại nhà A8. " * 20, encoding="utf-8")
    index = tmp_path / "custom index"
    env = {**os.environ, "RAG_DATA_PATH": str(source), "RAG_CHROMA_DIR": str(index),
           "RAG_OLLAMA_URL": "http://127.0.0.1:11434", "RAG_ALLOW_REMOTE_OLLAMA": "0"}
    setup = """
from langchain_core.embeddings import DeterministicFakeEmbedding
from student_handbook_rag import vectorstore
vectorstore.get_embedding_function = lambda: DeterministicFakeEmbedding(size=8)
"""
    ingest = subprocess.run([sys.executable, "-c", setup + "\nfrom student_handbook_rag.ingest import main\nmain()"], env=env, capture_output=True, text=True)
    assert ingest.returncode == 0, ingest.stderr
    manifest = json.loads((index / "utc_handbook.manifest.json").read_text())
    assert manifest["source_document"] == source.name
    probe = setup + """
from fastapi.testclient import TestClient
from langchain_core.language_models.fake import FakeListLLM
from student_handbook_rag import doctor
from student_handbook_rag.api import create_app
from student_handbook_rag.chain import StudentHandbookRAG
doctor.check_models = lambda: None
assert doctor.main() == 0
with TestClient(create_app(lambda: StudentHandbookRAG(llm=FakeListLLM(responses=['unused'])),
                           readiness_check=lambda: None), base_url='http://127.0.0.1') as client:
    assert client.get('/ready').status_code == 200
    assert client.app.state.engine.retriever.vector_db._collection.count() > 0
"""
    checked = subprocess.run([sys.executable, "-c", probe], env=env, capture_output=True, text=True)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert manifest["source_sha256"] in checked.stdout


def test_cli_path_overrides_print_runtime_environment(monkeypatch, tmp_path, capsys):
    from unittest.mock import MagicMock
    from student_handbook_rag import ingest
    source, index = tmp_path / "handbook.txt", tmp_path / "index"
    monkeypatch.setattr(sys, "argv", ["utc-ingest", "--data-path", str(source), "--persist-dir", str(index)])
    monkeypatch.setattr(ingest, "build_vector_store", MagicMock())
    ingest.main()
    output = capsys.readouterr().out
    assert "only to this ingestion" in output
    assert f"RAG_DATA_PATH={Path(source).resolve()}" in output
    assert f"RAG_CHROMA_DIR={Path(index).resolve()}" in output
