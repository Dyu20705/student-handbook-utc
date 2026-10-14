import pytest

from student_handbook_rag.chain import StudentHandbookRAG
from student_handbook_rag.retriever import BaselineRetriever


def test_baseline_retriever():
    """Verify BaselineRetriever returns top-k documents with scores and metadata."""
    retriever = BaselineRetriever()
    results = retriever.retrieve("Quy định đánh giá rèn luyện", k=3)
    assert len(results) == 3
    doc, score = results[0]
    assert score >= 0.0
    assert "sotaysvk67.pdf" in doc.metadata.get("document", "")
    assert doc.metadata.get("page") is not None
    assert doc.metadata.get("section") is not None


def test_baseline_rag_answerable():
    """Verify StudentHandbookRAG returns grounded answer with sources for handbook question."""
    rag = StudentHandbookRAG()
    res = rag.query("Sinh viên có điểm thi kết thúc học phần nhỏ hơn bao nhiêu thì nhận điểm F?")
    assert len(res["answer"]) > 0
    assert "1,0" in res["answer"] or "1.0" in res["answer"]
    assert len(res["sources"]) > 0
    assert any("sotaysvk67.pdf" in s["document"] for s in res["sources"])


def test_baseline_rag_unanswerable():
    """Verify StudentHandbookRAG refuses to answer out-of-domain questions."""
    rag = StudentHandbookRAG()
    res = rag.query("Hôm nay căn tin trường UTC bán món gì?")
    assert res["is_insufficient_context"] is True
    assert (
        "không tìm thấy đủ thông tin" in res["answer"].lower() or "không" in res["answer"].lower()
    )


@pytest.mark.parametrize(
    "question",
    [
        "Sinh viên hệ chính quy cần đáp ứng các điều kiện gì về học tập, rèn luyện và kỷ luật để được xét cấp học bổng khuyến khích học tập?",
        "Để được xét học bổng khuyến khích học tập, sinh viên chính quy cần thỏa mãn những điều kiện nào? Nêu đủ cả yêu cầu về tín chỉ và điểm học phần.",
        "Những điều kiện bắt buộc để xét học bổng khuyến khích học tập đối với sinh viên hệ chính quy là gì?",
    ],
)
def test_scholarship_keeps_cross_page_thresholds(question):
    """Regression for q15 omissions; full semantic review is still a separate gate."""
    rag = StudentHandbookRAG()
    result = rag.query(question)
    answer = result["answer"].lower()
    assert result["status"] == "answered"
    assert "5,0" in answer or "5.0" in answer, answer
    assert "15" in answer and "ngoại ngữ tăng cường" in answer
    assert "lần thứ nhất" in answer or "lần đầu" in answer
    assert "giáo dục thể chất" in answer and "giáo dục quốc phòng" in answer
    assert "khá" in answer and "khiển trách" in answer
    assert {45, 46} <= {source["page"] for source in result["sources"]}
    assert {"sotaysvk67.pdf_p45_c0183", "sotaysvk67.pdf_p46_c0184"} <= {
        source["chunk_id"] for source in result["sources"]
    }
