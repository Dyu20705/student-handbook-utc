import os

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from student_handbook_rag.config import CHROMA_DEFAULT_DIR, EMBEDDING_MODEL
from student_handbook_rag.vectorstore import build_vector_store, get_embedding_function


def test_embedding_model():
    embedding = get_embedding_function()
    assert embedding is not None
    assert isinstance(embedding, OllamaEmbeddings)
    assert embedding.model == EMBEDDING_MODEL


def test_load_existing_vector_store():
    vector_db = build_vector_store(load_only=True)
    assert vector_db is not None
    assert isinstance(vector_db, Chroma)
    assert os.path.exists(CHROMA_DEFAULT_DIR)


def test_similarity_search():
    vector_db = build_vector_store(load_only=True)
    query = "Quy định và Quy trình Đào tạo bao gom nhung gi?"
    results = vector_db.similarity_search(query, k=2)
    assert len(results) == 2
    assert all(hasattr(res, "page_content") and len(res.page_content) > 0 for res in results)
