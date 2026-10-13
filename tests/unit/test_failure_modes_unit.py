from unittest.mock import MagicMock
from langchain_core.documents import Document
from student_handbook_rag.chain import StudentHandbookRAG


def test_empty_query():
    """Verify system handles empty/blank query without error."""
    mock_retriever = MagicMock()
    mock_llm = MagicMock()
    rag = StudentHandbookRAG(retriever=mock_retriever, llm=mock_llm)

    res = rag.query("   ")
    assert res["is_insufficient_context"] is True
    assert "Vui lòng nhập câu hỏi" in res["answer"]
    assert len(res["sources"]) == 0
    mock_retriever.retrieve.assert_not_called()


def test_no_documents_indexed():
    """Verify system handles empty vector DB gracefully."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []
    mock_llm = MagicMock()
    rag = StudentHandbookRAG(retriever=mock_retriever, llm=mock_llm)

    res = rag.query("Quy định đào tạo")
    assert res["status"] == "error"
    assert res["is_insufficient_context"] is False
    assert "Không tìm thấy dữ liệu" in res["answer"]
    assert len(res["sources"]) == 0


def test_unanswerable_refusal_detection():
    """Verify that refusal response is correctly classified as is_insufficient_context."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        (Document(page_content="Nội dung không liên quan.", metadata={"document": "sotaysvk67.pdf", "page": 1, "section": "Chung"}), 1.2)
    ]
    mock_llm = MagicMock()
    rag = StudentHandbookRAG(retriever=mock_retriever, llm=mock_llm)

    # Mock chain invocation returning standard refusal phrase
    rag.chain = MagicMock()
    rag.chain.invoke.return_value = '{"answer":"Tôi không tìm thấy đủ thông tin trong Sổ tay sinh viên để trả lời câu hỏi này.","citation_ids":[],"insufficient_context":true}'

    res = rag.query("Giá vé máy bay đi Hà Nội?")
    assert res["is_insufficient_context"] is True
    assert "không tìm thấy đủ thông tin" in res["answer"]
    assert len(res["sources"]) == 0
