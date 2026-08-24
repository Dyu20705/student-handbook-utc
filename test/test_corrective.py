import pytest
from langchain_core.documents import Document
from corrective import (
    RetrievalEvaluator,
    refine_documents,
    rewrite_query_for_search,
    perform_web_search,
    CorrectiveRAG,
)


def test_retrieval_evaluator_empty_docs():
    evaluator = RetrievalEvaluator()
    res = evaluator.evaluate("Câu hỏi bất kỳ", [])
    assert res["label"] == "INCORRECT"


def test_retrieval_evaluator_relevant():
    evaluator = RetrievalEvaluator()
    docs = [
        Document(page_content="Sinh viên bị cảnh cáo học tập mức 1 nếu ĐTB tích lũy dưới 1.20 ở kỳ 1."),
        Document(page_content="Cảnh cáo học tập mức 2 nếu ĐTB tích lũy dưới 1.40 ở kỳ 2.")
    ]
    res = evaluator.evaluate("Điều kiện bị cảnh cáo học tập mức 1 là gì?", docs)
    assert res["label"] in ["CORRECT", "AMBIGUOUS"]
    assert "explanation" in res


def test_refine_documents():
    docs = [
        Document(
            page_content=(
                "Trường UTC thành lập năm 1960. "
                "Sinh viên đạt GPA từ 3.6 trở lên được xét học bổng xuất sắc. "
                "Căn tin trường nằm ở khu nhà B."
            )
        )
    ]
    refined = refine_documents("Điều kiện xét học bổng xuất sắc?", docs)
    assert isinstance(refined, str)
    assert len(refined.strip()) > 0


def test_rewrite_query_for_search():
    query = "Làm sao để biết mình có đủ điều kiện làm đồ án tốt nghiệp UTC năm 2026 hay không?"
    search_q = rewrite_query_for_search(query)
    assert isinstance(search_q, str)
    assert len(search_q.strip()) > 0


def test_perform_web_search():
    result = perform_web_search("quy chế đào tạo đại học UTC")
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_corrective_rag_pipeline():
    crag = CorrectiveRAG()
    res = crag.run("Quy định và Quy trình Đào tạo theo tín chỉ")
    assert "action" in res
    assert res["action"] in ["CORRECT", "INCORRECT", "AMBIGUOUS"]
    assert "answer" in res
    assert len(res["answer"]) > 0
