import pytest
from langchain_core.messages import HumanMessage, AIMessage
from student_handbook_rag.memory import (
    load_mem_prompt,
    get_session_history,
    create_conversational_rag_chain,
    conversational_rag,
    session_store,
)

def test_load_mem_prompt():
    prompt = load_mem_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "lịch sử chat" in prompt.lower() or "viết lại" in prompt.lower()

def test_get_session_history_isolation():
    session_id_1 = "test_unit_session_01"
    session_id_2 = "test_unit_session_02"

    history1 = get_session_history(session_id_1)
    history2 = get_session_history(session_id_2)

    assert history1 is not None
    assert history2 is not None
    assert history1 is not history2  # Hai session phải hoàn toàn độc lập

    # Ghi tin nhắn vào session 1
    history1.add_message(HumanMessage(content="Xin chào"))
    history1.add_message(AIMessage(content="Chào bạn, tôi là trợ lý ảo UTC."))

    # Kiểm tra session 1 có dữ liệu, session 2 vẫn rỗng
    assert len(get_session_history(session_id_1).messages) == 2
    assert len(get_session_history(session_id_2).messages) == 0

def test_create_conversational_rag_chain():
    chain = create_conversational_rag_chain()
    assert chain is not None

def test_conversational_rag_multi_turn():
    test_session = "test_multi_turn_flow"

    # Turn 1: Câu hỏi ban đầu
    res1 = conversational_rag.invoke(
        {"input": "Quy định và Quy trình Đào tạo"},
        config={"configurable": {"session_id": test_session}},
    )
    assert res1 is not None
    assert "answer" in res1
    assert len(res1["answer"]) > 0

    # Kiểm tra lịch sử sau Turn 1 (1 câu hỏi + 1 câu trả lời)
    history = get_session_history(test_session)
    assert len(history.messages) == 2

    # Turn 2: Câu hỏi tiếp nối sử dụng từ quy chiếu ("nó")
    res2 = conversational_rag.invoke(
        {"input": "Nội dung chính của nó gồm những phần nào?"},
        config={"configurable": {"session_id": test_session}},
    )
    assert res2 is not None
    assert "answer" in res2
    assert len(res2["answer"]) > 0

    # Kiểm tra lịch sử sau Turn 2 (2 câu hỏi + 2 câu trả lời)
    assert len(history.messages) == 4