from langchain_core.documents import Document
from student_handbook_rag.retriever import BaselineRetriever
from student_handbook_rag.chain import build_context_text


def test_format_retrieval_debug():
    """Test debug formatting of retrieved chunks."""
    doc = Document(
        page_content="Nội dung điều khoản đào tạo.",
        metadata={
            "document": "sotaysvk67.pdf",
            "source": "/data/raw/sotaysvk67.pdf",
            "page": 20,
            "book_page": 18,
            "section": "Điều 9",
            "chunk_id": "sotaysvk67_p20_c001",
        }
    )
    results = [(doc, 0.42)]
    debug_text = BaselineRetriever.format_retrieval_debug("thang điểm", results)

    assert "QUERY: 'thang điểm'" in debug_text
    assert "Score:       0.4200" in debug_text
    assert "PDF Page:    20 (Book Page: 18)" in debug_text
    assert "Điều 9" in debug_text
    assert "sotaysvk67_p20_c001" in debug_text
    assert "Nội dung điều khoản đào tạo." in debug_text


def test_build_context_text():
    """Test context string builder with metadata headers."""
    doc1 = Document(page_content="Đoạn 1", metadata={"document": "sotaysvk67.pdf", "page": 10, "book_page": 8, "section": "Mục A", "chunk_id": "c1"})
    doc2 = Document(page_content="Đoạn 2", metadata={"document": "sotaysvk67.pdf", "page": 15, "book_page": 13, "section": "Mục B", "chunk_id": "c2"})

    context = build_context_text([(doc1, 0.3), (doc2, 0.5)])
    assert "--- [ĐOẠN 1]" in context
    assert "--- [ĐOẠN 2]" in context
    assert "Trang PDF: 10" in context
    assert "Trang PDF: 15" in context
    assert "Đoạn 1" in context
    assert "Đoạn 2" in context
    # Estimated page headings are not evidence of which section a chunk belongs to.
    assert "Mục A" not in context and "Mục B" not in context
