from student_handbook_rag.config import RAW_PDF_PATH
from student_handbook_rag.loader import (
    clean_page_text,
    detect_section_heading,
    ragchunking,
    ragload,
)


def test_load_utf8_text(tmp_path):
    source = tmp_path / "fixture.txt"
    content = "Synthetic test fixture: sinh viên sử dụng thư viện.\n" * 30
    source.write_text(content, encoding="utf-8")
    docs = ragload(str(source))
    assert len(docs) == 1
    assert docs[0].page_content == content
    assert docs[0].metadata["document"] == "fixture.txt"


def test_chunk_text_preserves_metadata(tmp_path):
    source = tmp_path / "fixture.txt"
    source.write_text(
        "Synthetic test fixture: sinh viên sử dụng thư viện.\n" * 30, encoding="utf-8"
    )
    docs = ragload(str(source))
    chunks = ragchunking(docs, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(chunk.metadata["document"] == "fixture.txt" for chunk in chunks)
    assert "chunk_id" in chunks[0].metadata


def test_clean_page_text():
    """Verify removal of STSV header/footer artifacts and space normalization."""
    dirty = "   8 * STSV \n\nNội dung chính của trang.  \nSTSV * 29\n\n\n\nKết luận."
    cleaned = clean_page_text(dirty)
    assert "STSV" not in cleaned
    assert "Nội dung chính của trang." in cleaned
    assert "Kết luận." in cleaned
    assert "\n\n\n" not in cleaned


def test_detect_section_heading():
    """Verify section heading detection regex."""
    assert (
        detect_section_heading("PHẦN 2.1. QUY CHẾ ĐÀO TẠO ĐẠI HỌC")
        == "PHẦN 2.1. QUY CHẾ ĐÀO TẠO ĐẠI HỌC"
    )
    assert (
        detect_section_heading("Điều 9. Đánh giá và tính điểm học phần")
        == "Điều 9. Đánh giá và tính điểm học phần"
    )
    assert (
        detect_section_heading("VIII. THƯ VIỆN TRƯỜNG ĐH GTVT") == "VIII. THƯ VIỆN TRƯỜNG ĐH GTVT"
    )
    assert detect_section_heading("1. GIỚI THIỆU CHUNG") == "1. GIỚI THIỆU CHUNG"
    assert detect_section_heading("Chỉ là một dòng văn bản bình thường.") is None


def test_load_official_pdf():
    """Verify official sotaysvk67.pdf loads pages with full metadata."""
    docs = ragload(RAW_PDF_PATH)
    assert len(docs) > 80  # 93 non-empty pages out of 97
    pages = [d.metadata["page"] for d in docs]
    assert 10 in pages
    doc_10 = next(d for d in docs if d.metadata["page"] == 10)
    assert doc_10.metadata["document"] == "sotaysvk67.pdf"
    assert doc_10.metadata["page"] == 10
    assert doc_10.metadata["book_page"] == 8
    assert "section" in doc_10.metadata
    assert len(doc_10.page_content) > 0


def test_chunk_official_pdf():
    """Verify chunks have unique chunk_ids and preserve page metadata."""
    docs = ragload(RAW_PDF_PATH)[:5]
    chunks = ragchunking(docs, chunk_size=600, chunk_overlap=100)
    assert len(chunks) >= 5
    for idx, c in enumerate(chunks):
        assert "chunk_id" in c.metadata
        assert "page" in c.metadata
        assert "book_page" in c.metadata
        assert "section" in c.metadata
        assert c.metadata["chunk_index"] == idx
