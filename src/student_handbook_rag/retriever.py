"""Dedicated Baseline Retriever for Student Handbook RAG.
Encapsulates dense top-k similarity retrieval, score tracking, and debug formatting.
"""

from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma

from student_handbook_rag.config import RETRIEVAL_K
from student_handbook_rag.vectorstore import build_vector_store, similarity_search_with_scores


class BaselineRetriever:
    """Baseline dense retriever querying ChromaDB with top-k similarity."""

    def __init__(self, vector_db: Optional[Chroma] = None, k: int = RETRIEVAL_K):
        self.vector_db = vector_db or build_vector_store()
        self.k = k

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Tuple[Document, float]]:
        """Retrieve top-k relevant documents with their similarity scores.
        
        Returns:
            List of (Document, score) tuples.
        """
        top_k = k if k is not None else self.k
        if not query or not query.strip():
            return []
        return similarity_search_with_scores(self.vector_db, query.strip(), k=top_k)

    def retrieve_documents(self, query: str, k: Optional[int] = None) -> List[Document]:
        """Retrieve top-k documents (without scores, for standard LangChain interfaces)."""
        scored_docs = self.retrieve(query, k=k)
        return [doc for doc, _ in scored_docs]

    @staticmethod
    def format_retrieval_debug(query: str, results: List[Tuple[Document, float]]) -> str:
        """Format retrieval results into structured debug text."""
        lines = [f"QUERY: '{query}'", f"FOUND {len(results)} CHUNKS:\n" + "=" * 50]
        for idx, (doc, score) in enumerate(results, start=1):
            meta = doc.metadata
            source = meta.get("source", "N/A")
            document = meta.get("document", "N/A")
            page = meta.get("page", "N/A")
            book_page = meta.get("book_page", "N/A")
            section = meta.get("section", "N/A")
            chunk_id = meta.get("chunk_id", "N/A")

            lines.append(f"RESULT #{idx}")
            lines.append(f"  Score:       {score:.4f} (Chroma L2 distance, lower = closer)")
            lines.append(f"  Document:    {document} (Path: {source})")
            lines.append(f"  PDF Page:    {page} (Book Page: {book_page})")
            lines.append(f"  Section:     {section}")
            lines.append(f"  Chunk ID:    {chunk_id}")
            lines.append(f"  Content:\n    {doc.page_content.strip()}")
            lines.append("-" * 50)
        return "\n".join(lines)


if __name__ == "__main__":
    retriever = BaselineRetriever()
    test_q = "Quy định về học bổng khuyến khích học tập"
    res = retriever.retrieve(test_q, k=3)
    print(retriever.format_retrieval_debug(test_q, res))
