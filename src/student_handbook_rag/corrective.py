"""
Why corrective?

Toi uu

1.  Retrieval Evaluator
2.  Knowledge Refinement (Decompose-then-Recompose)
3. Query Rewriting & Web Fallback
"""

import json
import re
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from student_handbook_rag.chain import arise, load_system_prompt
from student_handbook_rag.aragog import AragogRetriever


class RetrievalEvaluator:
    def __init__(self, llm=None):
        self.llm = llm or arise()

    def evaluate(self, query: str, documents: List[Document]) -> Dict[str, Any]:
        if not documents:
            return {"label": "INCORRECT", "explanation": "Không tìm thấy tài liệu nào trong DB."}
        context_sample = "\n---\n".join([f"Đoạn {i+1}: {d.page_content}" for i, d in enumerate(documents[:5])])
        eval_prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "Bạn là Giám khảo đánh giá dữ liệu RAG (Retrieval Evaluator).\n"
             "Hãy kiểm tra xem nội dung tài liệu có chứa thông tin trả lời cho câu hỏi hay không.\n"
             "Đầu tiên hãy giải thích ngắn gọn, sau đó ở dòng cuối cùng ghi rõ:\n"
             "Kết luận: [CORRECT / AMBIGUOUS / INCORRECT]"
            ),
            ("human", "Câu hỏi: {query}\n\nNội dung tài liệu:\n{context}")
        ])
        chain = eval_prompt | self.llm | StrOutputParser()
        response_text = chain.invoke({"query": query, "context": context_sample}).strip()

        # Parse JSON an toàn
        try:
            # Tìm khối JSON trong phản hồi của LLM
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                label = result.get("label", "").upper()
                if label in ["CORRECT", "INCORRECT", "AMBIGUOUS"]:
                    return result
        except Exception:
            pass

        # Fallback nếu parsing lỗi: kiểm tra từ khóa
        label_match = re.search(r'Kết luận:\s*\[?(CORRECT|AMBIGUOUS|INCORRECT)\]?', response_text, re.IGNORECASE)
        if not label_match:
            label_match = re.search(r'\b(CORRECT|INCORRECT|AMBIGUOUS)\b', response_text, re.IGNORECASE)
            
        if label_match:
            label_val = label_match.group(1).upper()
            return {"label": label_val, "explanation": response_text.strip()}
        return {"label": "AMBIGUOUS", "explanation": "Tài liệu chưa đủ độ tin cậy."}


def refine_documents(query: str, documents: List[Document], llm=None) -> str:
    if llm is None:
        llm = arise()
    raw_text = "\n".join([d.page_content for d in documents])
    strips = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', raw_text) if len(s.strip()) > 10]
    if not strips:
        return raw_text
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Bạn là Bộ lọc dữ liệu tinh gọn (Knowledge Refiner). "
                   "Dưới đây là danh sách các câu trích xuất từ tài liệu. "
                   "Hãy CHỈ giữ lại các câu trực tiếp liên quan đến câu hỏi và ghép chúng lại thành một đoạn văn súc tích. "
                   "Loại bỏ toàn bộ câu chào hỏi, thông tin ngoài lề không liên quan."),
        ("human", "Câu hỏi: {query}\n\nDanh sách các câu:\n{strips}")
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"query": query, "strips": "\n".join(f"- {s}" for s in strips)})


def rewrite_query_for_search(query: str, llm=None) -> str:
    if llm is None:
        llm = arise()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia tìm kiếm thông tin. "
                   "Hãy chuyển đổi câu hỏi sau thành 1 câu truy vấn từ khóa tìm kiếm (Search Query) ngắn gọn (3-6 từ), "
                   "tập trung vào thực thể và từ khóa cốt lõi. CHỈ trả về từ khóa tìm kiếm, không giải thích."),
        ("human", "{query}")
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"query": query}).strip()


def perform_web_search(search_query: str) -> str:
    print(f"   [Web Search] Đang tra cứu internet với từ khóa: '{search_query}'...")
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=3))
            if results:
                web_snippets = "\n\n".join([f"Nguồn ({r.get('href')}):\n{r.get('body')}" for r in results])
                return web_snippets
    except Exception as e:
        print(f"   [Web Search Warning]: Không thể gọi DuckDuckGo ({e}). Sử dụng tri thức dự phòng.")
    # Fallback giả định mô phỏng khi môi trường offline
    return f"[Web Search Knowledge Base]: Thông tin tra cứu mới nhất về '{search_query}' tại cổng thông tin sinh viên."


class CorrectiveRAG:
    def __init__(self, retriever=None, llm=None):
        self.retriever = retriever or AragogRetriever()
        self.llm = llm or arise()
        self.evaluator = RetrievalEvaluator(self.llm)
        self.system_prompt = load_system_prompt()

    def run(self, query: str) -> Dict[str, Any]:
        # Lấy tài liệu từ ARAGOG Retriever (Sentence-Window + HyDE + Rerank)
        retrieved_docs = self.retriever.retrieve(query, top_k_initial=6, top_n_final=3)

        # Evaluator chấm điểm
        eval_result = self.evaluator.evaluate(query, retrieved_docs)
        action = eval_result["label"]

        # Phân luồng hành động theo 3 nhánh CRAG
        if action == "CORRECT":
            final_context = refine_documents(query, retrieved_docs, self.llm)
        elif action == "INCORRECT":
            search_query = rewrite_query_for_search(query, self.llm)
            web_context = perform_web_search(search_query)
            final_context = f"[Tri thức từ Web Search ngoài]:\n{web_context}"
        elif action == "AMBIGUOUS":
            refined_internal = refine_documents(query, retrieved_docs, self.llm)
            search_query = rewrite_query_for_search(query, self.llm)
            web_context = perform_web_search(search_query)
            final_context = (
                f"[Tri thức nội bộ (Đã tinh chế)]:\n{refined_internal}\n\n"
                f"[Tri thức bổ trợ từ Web Search]:\n{web_context}"
            )

        # Sinh câu trả lời cuối cùng
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", f"{self.system_prompt}\n\nNgữ cảnh xác thực (Đã qua kiểm duyệt CRAG):\n{{context}}"),
            ("human", "{input}"),
        ])
        chain = qa_prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"context": final_context, "input": query})
        return {
            "query": query,
            "action": action,
            "evaluation": eval_result,
            "context_used": final_context,
            "answer": answer
        }


if __name__ == "__main__":
    crag_system = CorrectiveRAG()
    while True:
        user_input = input("\nNhập câu hỏi kiểm tra (gõ 'exit' để thoát): ")
        if user_input.strip().lower() == "exit":
            break
        if not user_input.strip():
            continue
        res = crag_system.run(user_input)
        print(f"\nQwen2.5 [{res['action']}]:\n{res['answer']}")