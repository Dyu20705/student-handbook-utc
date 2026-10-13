from student_handbook_rag.retriever import BaselineRetriever
from student_handbook_rag.chain import StudentHandbookRAG


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
    assert "không tìm thấy đủ thông tin" in res["answer"].lower() or "không" in res["answer"].lower()


def test_scholarship_keeps_cross_page_thresholds():
    """Regression for q15 omissions; full semantic review is still a separate gate."""
    rag = StudentHandbookRAG()
    result = rag.query("Sinh viên hệ chính quy cần đáp ứng các điều kiện gì về học tập, rèn luyện và kỷ luật để được xét cấp học bổng khuyến khích học tập?")
    answer = result["answer"].lower()
    assert result["status"] == "answered"
    assert "5,0" in answer or "5.0" in answer
    assert "15" in answer and "ngoại ngữ tăng cường" in answer
    assert "lần thứ nhất" in answer or "lần đầu" in answer
    assert "khá" in answer and "khiển trách" in answer
    assert {45, 46} <= {source["page"] for source in result["sources"]}
