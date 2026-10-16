"""Dedicated Baseline Retriever for Student Handbook RAG.
Encapsulates dense top-k similarity retrieval, score tracking, and debug formatting.
"""

import re

from langchain_chroma import Chroma
from langchain_core.documents import Document

from student_handbook_rag.config import MAX_RETRIEVAL_K, RETRIEVAL_K
from student_handbook_rag.lexical import LexicalIndex
from student_handbook_rag.vectorstore import build_vector_store, similarity_search_with_scores


class BaselineRetriever:
    """Baseline dense retriever querying ChromaDB with top-k similarity."""

    def __init__(self, vector_db: Chroma | None = None, k: int = RETRIEVAL_K):
        if not 1 <= k <= MAX_RETRIEVAL_K:
            raise ValueError("k must be between 1 and 10")
        self.vector_db = vector_db if vector_db is not None else build_vector_store(load_only=True)
        self.k = k
        records = self.vector_db.get(include=["documents", "metadatas"])
        documents = [
            Document(page_content=text, metadata=metadata)
            for text, metadata in zip(records["documents"], records["metadatas"], strict=True)
        ]
        self.lexical = LexicalIndex(documents)
        self._chunks = {
            (
                doc.metadata.get("source", doc.metadata.get("document")),
                doc.metadata["chunk_index"],
            ): doc
            for doc in documents
            if isinstance(doc.metadata.get("chunk_index"), int)
        }

    def retrieve(self, query: str, k: int | None = None) -> list[tuple[Document, float]]:
        """Retrieve top-k relevant documents with their similarity scores.

        Returns:
            List of (Document, score) tuples.
        """
        top_k = k if k is not None else self.k
        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or not 1 <= top_k <= MAX_RETRIEVAL_K
        ):
            raise ValueError("k must be between 1 and 10")
        if not query or not query.strip():
            return []
        dense = similarity_search_with_scores(self.vector_db, query.strip(), k=max(5, top_k))
        lexical = self.lexical.search(query, max(5, top_k))
        # Preserve the measured top-three dense recall. Reserve the next two
        # context slots for lexical matches, useful for app names/abbreviations.
        candidates = dense[:3] + lexical[:2] + dense[3:] + lexical[2:]
        selected, seen = [], set()
        for doc, _ in candidates:
            identity = doc.metadata["chunk_id"]
            if identity not in seen:
                seen.add(identity)
                selected.append((doc, float(len(selected) + 1)))
            if len(selected) == top_k:
                break
        return selected

    def complete_page_bullets(
        self, selected: list[tuple[Document, float]]
    ) -> list[tuple[Document, float]]:
        """Add at most two adjacent chunks when a bullet list crosses a PDF page.

        Generation uses this context; retrieval metrics still score the original
        ranked candidates. Keep the next page's own citation ID and page metadata.
        """
        expanded = []
        added = 0
        seen = {doc.metadata.get("chunk_id") for doc, _ in selected}
        chunks = getattr(self, "_chunks", {})
        for doc, _ in selected:
            expanded.append((doc, float(len(expanded) + 1)))
            meta = doc.metadata
            index, page = meta.get("chunk_index"), meta.get("page")
            if added == 2 or not isinstance(index, int) or not isinstance(page, int):
                continue
            following = chunks.get((meta.get("source", meta.get("document")), index + 1))
            if (
                following is None
                or following.metadata.get("page") != page + 1
                or following.metadata.get("chunk_id") in seen
                or not re.match(r"^[+•-]\s", following.page_content.lstrip())
            ):
                continue
            expanded.append((following, float(len(expanded) + 1)))
            seen.add(following.metadata["chunk_id"])
            added += 1
        return expanded

    def retrieve_documents(self, query: str, k: int | None = None) -> list[Document]:
        """Retrieve top-k documents (without scores, for standard LangChain interfaces)."""
        scored_docs = self.retrieve(query, k=k)
        return [doc for doc, _ in scored_docs]

    @staticmethod
    def format_retrieval_debug(query: str, results: list[tuple[Document, float]]) -> str:
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
            lines.append(
                f"  Score:       {score:.4f} (retrieval rank; lower = earlier; not confidence)"
            )
            lines.append(f"  Document:    {document} (Path: {source})")
            lines.append(f"  PDF Page:    {page} (Book Page: {book_page})")
            lines.append(f"  Section:     {section}")
            lines.append(f"  Chunk ID:    {chunk_id}")
            lines.append(f"  Content:\n    {doc.page_content.strip()}")
            lines.append("-" * 50)
        return "\n".join(lines)
