from unittest.mock import MagicMock

from langchain_core.documents import Document

from student_handbook_rag.lexical import LexicalIndex
from student_handbook_rag.retriever import BaselineRetriever


def test_unicode_and_exact_terms():
    docs = [Document(page_content="Giới thiệu trường"), Document(page_content="Cài đặt APP eUTC")]
    index = LexicalIndex(docs)
    assert index.search("app EUTC", 1)[0][0] == docs[1]
    assert index.search("zzzz", 2) == []
    assert LexicalIndex([]).search("app", 1) == []


def test_preserves_dense_top_three_and_adds_lexical_without_duplicates():
    docs = [
        Document(page_content=text, metadata={"chunk_id": str(i)})
        for i, text in enumerate(
            ["Trường học", "Quy chế đào tạo", "Học phí", "Ứng dụng APP eUTC", "Tải APP eUTC"]
        )
    ]
    db = MagicMock()
    db.get.return_value = {
        "documents": [d.page_content for d in docs],
        "metadatas": [d.metadata for d in docs],
    }
    db.similarity_search_with_score.return_value = [(d, 0.1 * i) for i, d in enumerate(docs)]
    retriever = BaselineRetriever(db)
    assert [d for d, _ in retriever.retrieve("APP eUTC", k=3)] == docs[:3]
    all_docs = [d.metadata["chunk_id"] for d, _ in retriever.retrieve("APP eUTC", k=5)]
    assert len(all_docs) == len(set(all_docs)) == 5
    assert "3" in all_docs
