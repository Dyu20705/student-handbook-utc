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
