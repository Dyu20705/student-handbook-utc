"""
Why mem?

Toi uu memory

"""
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from student_handbook_rag.chain import createretriever, load_system_prompt, arise


def load_mem_prompt():
    """Nạp system prompt cho việc tái diễn đạt câu hỏi dựa trên lịch sử hội thoại."""
    return (
        "Dựa vào lịch sử chat và câu hỏi mới của người dùng, "
        "hãy viết lại câu hỏi này thành một câu hỏi độc lập có thể tự hiểu được. "
        "CHỈ trả về câu hỏi đã được viết lại, KHÔNG trả lời nó."
    )


def create_conversational_rag_chain(retriever=None, llm=None):
    """Khởi tạo chuỗi RAG có khả năng thấu hiểu ngữ cảnh lịch sử chat."""
    if retriever is None:
        retriever = createretriever()
    if llm is None:
        llm = arise()

    # Contextualize Question 
    mem_prompt = load_mem_prompt()
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", mem_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # QA Chain
    base_prompt = load_system_prompt()
    qa_system_prompt = (
        f"{base_prompt}\n\n"
        "Dựa vào các đoạn thông tin ngữ cảnh được cung cấp sau đây, hãy trả lời câu hỏi: {context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # Kết hợp Retriever và QA Chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain


# Global Session Store
session_store = {}

def get_session_history(session_id: str):
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]


# Bọc chain vào lớp quản lý lịch sử trò chuyện
conversational_rag = RunnableWithMessageHistory(
    create_conversational_rag_chain(),
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)


if __name__ == "__main__":
    print("\n--- HỆ THỐNG RAG CÓ BỘ NHỚ ĐÃ SẴN SÀNG ---")
    session_id = "phien_chat_cua_duy_01"

    while True:
        user_input = input("\nBạn hỏi gì (gõ 'exit' để thoát): ")
        if user_input.strip().lower() == "exit":
            break
        if not user_input.strip():
            continue

        response = conversational_rag.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )

        print(f"\nQwen2.5: {response['answer']}")