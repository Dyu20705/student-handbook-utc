import pytest
from langchain_core.documents import Document
from student_handbook_rag.aragog import (
    split_into_sentences,
    create_sentence_window_docs,
    get_aragog_vector_db,
    generate_hypothetical_answer,
    AragogRetriever,
    create_aragog_rag_chain,
)


def test_split_into_sentences():
    sample_text = (
        "Trường Đại học Giao thông Vận tải áp dụng quy chế tín chỉ. "
        "Sinh viên cần tích lũy đủ số tín chỉ quy định. "
        "Thời gian đào tạo chuẩn là 4 năm."
    )
    sentences = split_into_sentences(sample_text)
    assert len(sentences) == 3
    assert sentences[0] == "Trường Đại học Giao thông Vận tải áp dụng quy chế tín chỉ."
    assert sentences[1] == "Sinh viên cần tích lũy đủ số tín chỉ quy định."
    assert sentences[2] == "Thời gian đào tạo chuẩn là 4 năm."


def test_create_sentence_window_docs():
    raw_docs = [
        Document(
            page_content=(
                "Câu thứ nhất của tài liệu. "
                "Câu thứ hai quan trọng. "
                "Câu thứ ba cần chú ý. "
                "Câu thứ tư là kết luận."
            ),
            metadata={"source": "test_source.txt"}
        )
    ]
    window_docs = create_sentence_window_docs(raw_docs, window_size=1)
    assert len(window_docs) == 4

    # Kiểm tra doc thứ hai (index 1): page_content là câu 2, window gồm câu 1 + 2 + 3
    assert window_docs[1].page_content == "Câu thứ hai quan trọng."
    assert window_docs[1].metadata["sentence_idx"] == 1
    assert "Câu thứ nhất của tài liệu." in window_docs[1].metadata["window"]
    assert "Câu thứ hai quan trọng." in window_docs[1].metadata["window"]
    assert "Câu thứ ba cần chú ý." in window_docs[1].metadata["window"]


def test_get_aragog_vector_db():
    vector_db = get_aragog_vector_db()
    assert vector_db is not None


def test_generate_hypothetical_answer():
    query = "Điều kiện nhận học bổng khuyến khích học tập UTC là gì?"
    hypo_ans = generate_hypothetical_answer(query)
    assert isinstance(hypo_ans, str)
    assert len(hypo_ans.strip()) > 0


def test_aragog_retriever():
    retriever = AragogRetriever()
    query = "Quy định cảnh cáo học tập mức 1"
    docs = retriever.retrieve(query, top_k_initial=5, top_n_final=2)
    assert len(docs) <= 2
    assert all("rerank_score" in d.metadata for d in docs)
    assert all("window" in d.metadata for d in docs)


def test_create_aragog_rag_chain():
    rag_chain = create_aragog_rag_chain()
    assert callable(rag_chain)
    res = rag_chain("Quy định đào tạo theo hệ thống tín chỉ UTC")
    assert "answer" in res
    assert "context_documents" in res
    assert len(res["answer"]) > 0
