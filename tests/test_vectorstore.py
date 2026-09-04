import pytest
import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from student_handbook_rag.vectorstore import embes, createvector
from student_handbook_rag.config import CHROMA_DEFAULT_DIR, EMBEDDING_MODEL

def test_embes():
    embedding = embes()
    assert embedding is not None
    assert isinstance(embedding, OllamaEmbeddings)
    assert embedding.model == EMBEDDING_MODEL

def test_createvector():
    vector_db = createvector()
    assert vector_db is not None
    assert isinstance(vector_db, Chroma)
    assert os.path.exists(CHROMA_DEFAULT_DIR)

def test_similarity_search():
    vector_db = createvector()
    query = "Quy định và Quy trình Đào tạo bao gom nhung gi?"
    results = vector_db.similarity_search(query, k=2)
    assert len(results) == 2
    assert all(hasattr(res, "page_content") and len(res.page_content) > 0 for res in results)