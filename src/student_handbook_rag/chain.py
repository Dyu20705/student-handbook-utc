"""RAG Generation Chain for Student Handbook RAG.
Enforces groundedness, explicit uncertainty on out-of-domain queries,
and source traceability back to handbook page and section.
"""

from typing import List, Dict, Any, Optional, Tuple
from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from student_handbook_rag.config import LLM_MODEL, TEMPERATURE, RETRIEVAL_K
from student_handbook_rag.retriever import BaselineRetriever


SYSTEM_PROMPT = """Bạn là trợ lý giải đáp Sổ tay sinh viên Trường Đại học Giao thông Vận tải (UTC).
Nhiệm vụ của bạn là trả lời câu hỏi của người dùng CHỈ dựa trên các đoạn ngữ cảnh (Context) được cung cấp dưới đây.

QUY TẮC BẮT BUỘC:
1. Chỉ sử dụng thông tin có trong phần Ngữ cảnh được cung cấp. Tuyệt đối không suy đoán, bịa đặt thông tin.
2. Nếu ngữ cảnh KHÔNG chứa đủ thông tin để trả lời câu hỏi, bạn PHẢI trả lời chính xác:
   "Tôi không tìm thấy đủ thông tin trong Sổ tay sinh viên để trả lời câu hỏi này."
3. Trình bày ngắn gọn, chính xác, đúng trọng tâm câu hỏi.
4. Ở cuối câu trả lời, hãy liệt kê nguồn trích dẫn từ metadata của ngữ cảnh được sử dụng (Tên tài liệu, Trang, Mục/Điều)."""

REFUSAL_PHRASES = (
    "không tìm thấy đủ thông tin",
    "không có thông tin",
    "sổ tay không cung cấp",
    "sổ tay không đề cập",
    "không đủ thông tin",
    "tôi không biết",
)


def arise(model: str = LLM_MODEL, temperature: float = TEMPERATURE) -> ChatOllama:
    """Initialize local Ollama Chat model."""
    return ChatOllama(model=model, temperature=temperature)


def build_context_text(scored_docs: List[Tuple[Document, float]]) -> str:
    """Format retrieved chunks into structured context with metadata tags."""
    if not scored_docs:
        return ""
    context_parts = []
    for idx, (doc, score) in enumerate(scored_docs, start=1):
        meta = doc.metadata
        doc_name = meta.get("document", "sotaysvk67.pdf")
        page = meta.get("page", "N/A")
        book_page = meta.get("book_page", "N/A")
        section = meta.get("section", "Chung")
        chunk_id = meta.get("chunk_id", f"c_{idx}")

        header = f"--- [ĐOẠN {idx}] Tài liệu: {doc_name} | Trang PDF: {page} (Trang in: {book_page}) | Mục: {section} | ID: {chunk_id} ---"
        context_parts.append(f"{header}\n{doc.page_content.strip()}")
    return "\n\n".join(context_parts)


class StudentHandbookRAG:
    """Complete baseline RAG pipeline for Student Handbook QA."""

    def __init__(
        self,
        retriever: Optional[BaselineRetriever] = None,
        llm: Optional[ChatOllama] = None,
        system_prompt: str = SYSTEM_PROMPT,
    ):
        self.retriever = retriever or BaselineRetriever()
        self.llm = llm or arise()
        self.system_prompt = system_prompt
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", f"{self.system_prompt}\n\nNGỮ CẢNH TRÍCH XUẤT:\n{{context}}"),
            ("human", "{query}"),
        ])
        self.chain = self.prompt_template | self.llm | StrOutputParser()

    def query(self, question: str, k: Optional[int] = None) -> Dict[str, Any]:
        """Process a user query, retrieve relevant handbook chunks, and generate a grounded answer."""
        clean_q = question.strip() if question else ""
        if not clean_q:
            return {
                "query": question,
                "answer": "Vui lòng nhập câu hỏi để tra cứu Sổ tay sinh viên UTC.",
                "sources": [],
                "retrieved_chunks": [],
                "is_insufficient_context": True,
            }

        # Retrieve relevant chunks
        scored_docs = self.retriever.retrieve(clean_q, k=k)

        if not scored_docs:
            return {
                "query": clean_q,
                "answer": "Không tìm thấy dữ liệu Sổ tay sinh viên nào được đánh chỉ mục trong cơ sở dữ liệu.",
                "sources": [],
                "retrieved_chunks": [],
                "is_insufficient_context": True,
            }

        # Build context string
        context_str = build_context_text(scored_docs)

        # Generate answer with Ollama
        try:
            raw_answer = self.chain.invoke({"context": context_str, "query": clean_q})
        except Exception as e:
            return {
                "query": clean_q,
                "answer": f"Lỗi khi kết nối với LLM local ({LLM_MODEL}): {e}. Hãy đảm bảo lệnh 'ollama serve' đang chạy.",
                "sources": [],
                "retrieved_chunks": [doc for doc, _ in scored_docs],
                "is_insufficient_context": True,
            }

        is_insufficient = any(phrase in raw_answer.lower() for phrase in REFUSAL_PHRASES)

        sources = []
        for doc, score in scored_docs:
            meta = doc.metadata
            sources.append({
                "document": meta.get("document", "sotaysvk67.pdf"),
                "source": meta.get("source", ""),
                "page": meta.get("page"),
                "book_page": meta.get("book_page"),
                "section": meta.get("section"),
                "chunk_id": meta.get("chunk_id"),
                "score": float(score),
            })

        return {
            "query": clean_q,
            "answer": raw_answer.strip(),
            "sources": sources,
            "retrieved_chunks": [doc for doc, _ in scored_docs],
            "is_insufficient_context": is_insufficient,
        }


# ==============================================================================
# Backward Compatibility Wrappers (for existing tests / modules)
# ==============================================================================

def createretriever(k: int = 2):
    """Backward-compatible retriever factory."""
    from student_handbook_rag.vectorstore import createvector
    return createvector().as_retriever(search_kwargs={"k": k})


def load_system_prompt() -> str:
    """Backward-compatible prompt loader."""
    return SYSTEM_PROMPT


def createprompt():
    """Backward-compatible ChatPromptTemplate factory."""
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT + "\n\nNgữ cảnh:\n{context}"),
        ("human", "{input}"),
    ])


class _LegacyChainWrapper:
    """Wrapper that mimics the old langchain create_retrieval_chain API for backward compatibility."""
    def __init__(self, rag_engine: StudentHandbookRAG):
        self.rag_engine = rag_engine

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query = inputs.get("input") or inputs.get("query", "")
        res = self.rag_engine.query(query)
        return {
            "input": query,
            "answer": res["answer"],
            "context": res["retrieved_chunks"],
        }


def createragchain(retriever=None, llm=None, prompt=None):
    """Backward-compatible RAG chain creator."""
    if retriever is not None and hasattr(retriever, "invoke"):
        class _WrappedRetriever(BaselineRetriever):
            def __init__(self):
                self.vector_db = None
                self.k = 2

            def retrieve(self, query: str, k=None):
                docs = retriever.invoke(query)
                return [(doc, 0.0) for doc in docs]

        b_retriever = _WrappedRetriever()
    else:
        b_retriever = BaselineRetriever()

    chat_llm = llm if llm is not None else arise()
    rag_engine = StudentHandbookRAG(retriever=b_retriever, llm=chat_llm)
    return _LegacyChainWrapper(rag_engine)


if __name__ == "__main__":
    rag = StudentHandbookRAG()
    test_q = "Sinh viên có điểm thi kết thúc học phần nhỏ hơn bao nhiêu thì nhận điểm F?"
    result = rag.query(test_q)
    print(f"Câu hỏi: {result['query']}")
    print(f"\nCâu trả lời:\n{result['answer']}")
    print("\nNguồn dẫn chứng:")
    for s in result["sources"]:
        print(f"  - {s['document']} (Trang PDF: {s['page']}, Trang in: {s['book_page']}, Mục: {s['section']}) [Score: {s['score']:.4f}]")