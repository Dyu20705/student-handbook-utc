import importlib.resources
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain

from student_handbook_rag.vectorstore import createvector
from student_handbook_rag.config import LLM_MODEL, TEMPERATURE, RETRIEVAL_K, PROMPTS_DIR

# Đổi Vector DB thành một "Retriever" (Bộ truy xuất)
def createretriever(k: int = RETRIEVAL_K):
    retriever = createvector().as_retriever(search_kwargs={"k": k})
    return retriever

# arise qwen2.5
def arise():
    print(f"Loading {LLM_MODEL}....")
    llm = ChatOllama(model=LLM_MODEL, temperature=TEMPERATURE) # temperature=0 để nó trả lời chính xác, không sáng tạo bậy bạ
    return llm

# Tạo prompt từ package resources
def load_system_prompt() -> str:
    prompts = []
    # 1. Nạp qua importlib.resources (chuẩn package data)
    try:
        resource_dir = importlib.resources.files("student_handbook_rag").joinpath("prompts")
        if resource_dir.is_dir():
            for item in sorted(resource_dir.iterdir()):
                if item.name.endswith(".txt"):
                    content = item.read_text(encoding="utf-8").strip()
                    if content:
                        prompts.append(content)
    except Exception:
        pass

    # 2. Fallback đường dẫn thư mục PROMPTS_DIR
    if not prompts and PROMPTS_DIR.exists():
        for prompt_file in sorted(PROMPTS_DIR.glob("*.txt")):
            try:
                content = prompt_file.read_text(encoding="utf-8").strip()
                if content:
                    prompts.append(content)
            except Exception:
                pass

    if prompts:
        return "\n\n".join(prompts)
    return (
        "Bạn là trợ lý AI. Dựa vào {context} được cung cấp, hãy trả lời câu hỏi của người dùng.\n"
        "Nếu không biết, hãy nói là không biết, tuyệt đối không bịa đặt."
    )

def createprompt():
    system_prompt = load_system_prompt()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    return prompt

# workflows
def createragchain(retriever=None, llm=None, prompt=None):
    if retriever is None:
        retriever = createretriever()
    if llm is None:
        llm = arise()
    if prompt is None:
        prompt = createprompt()
        
    # Đọc context và trả lời
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    # Nhận câu hỏi -> Đi tìm vector -> Đưa vào dây chuyền
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    return rag_chain

# test
if __name__ == "__main__":
    rag_chain = createragchain()
    print("\n--- HỆ THỐNG ĐÃ SẴN SÀNG ---")
    while True:
        user_input = input("\nBạn hỏi gì (gõ 'exit' để thoát): ")
        if user_input.lower() == 'exit':
            break
        
        # call RAG
        response = rag_chain.invoke({"input": user_input})
        
        print(f"\nQwen2.5: {response['answer']}")
    