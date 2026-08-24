import os
import re
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain
from step2_vector import createvector

# Đổi Vector DB thành một "Retriever" (Bộ truy xuất)
def createretriever():
    retriever = createvector().as_retriever(search_kwargs={"k": 2})
    return retriever

# arise qwen2.5
def arise():
    print("Loading qwen2.5....")
    llm = ChatOllama(model="qwen2.5:7b", temperature=0) # temperature=0 để nó trả lời chính xác, không sáng tạo bậy bạ
    return llm

# Tạo promt
def load_system_prompt():
    skills_dir = Path("skills")
    skill_files = sorted(skills_dir.rglob("*.html")) if skills_dir.exists() else []

    prompts = []
    for skill_file in skill_files:
        if os.path.exists(skill_file):
            try:
                with open(skill_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    clean_text = re.sub(r"<[^>]+>", " ", content)
                    clean_text = re.sub(r"\s+", " ", clean_text).strip()
                    if clean_text:
                        prompts.append(clean_text)
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
    