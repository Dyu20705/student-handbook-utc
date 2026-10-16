from unittest.mock import MagicMock

import pytest

from student_handbook_rag.evaluate import evaluate_generation


@pytest.mark.parametrize(
    "question,answer,keywords",
    [
        (
            "Điều kiện học bổng?",
            "Học tập và rèn luyện Khá trở lên, không bị kỷ luật từ Khiển trách.",
            ["Khá trở lên", "5,0"],
        ),
        (
            "Khiển trách thì rèn luyện tối đa loại nào?",
            "Bị khiển trách vẫn có thể vượt quá loại Khá.",
            ["Khá", "khiển trách"],
        ),
    ],
)
def test_keyword_match_never_claims_semantic_correctness(question, answer, keywords):
    engine = MagicMock()
    engine.query.return_value = {
        "answer": answer,
        "is_insufficient_context": False,
        "status": "answered",
        "sources": [{"page": 45, "excerpt": "source text"}],
    }
    metrics = evaluate_generation(
        [{"id": "q", "question": question, "gold_keywords": keywords, "expected_page": 45}], engine
    )
    record = metrics["detailed_qa"][0]
    assert record["keyword_match"] is True
    assert record["citation_page_match"] is True
    assert record["semantic_verdict"] == "not_reviewed"
    assert "is_correct" not in record
    assert "has_grounded_citation" not in record
    assert record["sources"][0]["excerpt"] == "source text"
