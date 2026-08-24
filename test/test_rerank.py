import pytest
from sentence_transformers import CrossEncoder

def test_cross_encoder_reranker():
    model = CrossEncoder("BAAI/bge-reranker-base")
    assert model is not None
    query = "Quy định cảnh cáo học tập UTC"
    docs = [
        "Sinh viên có điểm trung bình chung tích lũy dưới 1.20 sẽ bị cảnh cáo học tập mức 1.",
        "Trường Đại học Giao thông Vận tải có khuôn viên xanh sạch đẹp.",
        "Quy trình đăng ký học phần trực tuyến qua cổng thông tin sinh viên."
    ]
    pairs = [[query, doc] for doc in docs]
    scores = model.predict(pairs)
    assert len(scores) == 3
    # Đoạn văn về cảnh cáo học tập phải có điểm cao nhất
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]
