import pytest
import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from step2_vector import embes, createvector

def test_embes():
    embedding = embes()
    assert embedding is not None
    assert isinstance(embedding, OllamaEmbeddings)
    assert embedding.model == "nomic-embed-text"

def test_createvector():
    vector_db = createvector()
    assert vector_db is not None
    assert isinstance(vector_db, Chroma)
    assert os.path.exists("./duy_chroma_db")

def test_similarity_search():
    vector_db = createvector()
    query = "Quy định và Quy trình Đào tạo bao gom nhung gi?"
    results = vector_db.similarity_search(query, k=2)
    assert len(results) == 2
    assert all(hasattr(res, "page_content") and len(res.page_content) > 0 for res in results)