"""
Why ARAGOG?

Toi uu do chinh xac cho thong tin

1. Sentence-Window Retrieval

2. HyDE (Hypothetical Document Embeddings)

3. Cross-Encoder Reranking
"""
import os
import re
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sentence_transformers import CrossEncoder

from student_handbook_rag.loader import ragload
from student_handbook_rag.vectorstore import embes
from student_handbook_rag.chain import arise, load_system_prompt
from student_handbook_rag.config import (
    RAW_DATA_PATH,
    CHROMA_ARAGOG_DIR,
    RERANKER_MODEL,
    WINDOW_SIZE,
    TOP_K_INITIAL,
    TOP_N_FINAL,
)


def split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?\n])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def create_sentence_window_docs(documents: List[Document], window_size: int = 2) -> List[Document]:
    window_docs = []
    for doc in documents:
        raw_text = doc.page_content
        sentences = split_into_sentences(raw_text)
        total_sents = len(sentences)
        for i, sentence in enumerate(sentences):
            # Xác định phạm vi window[start, end]
            start_idx = max(0, i - window_size)
            end_idx = min(total_sents, i + window_size + 1)

            # Gộp window context
            window_context = " ".join(sentences[start_idx:end_idx])
            new_doc = Document(
                page_content=sentence,
                metadata={
                    "window": window_context,
                    "sentence_idx": i,
                    "source": doc.metadata.get("source", RAW_DATA_PATH)
                }
            )
            window_docs.append(new_doc)
    return window_docs


def get_aragog_vector_db(db_path: str = CHROMA_ARAGOG_DIR) -> Chroma:
    embedding = embes()
    if os.path.exists(db_path) and os.listdir(db_path):
        return Chroma(persist_directory=db_path, embedding_function=embedding)
    raw_docs = ragload(RAW_DATA_PATH)
    window_docs = create_sentence_window_docs(raw_docs, window_size=WINDOW_SIZE)
    return Chroma.from_documents(
        documents=window_docs,
        embedding=embedding,
        persist_directory=db_path
    )


def generate_hypothetical_answer(query: str, llm=None) -> str:
    if llm is None:
        llm = arise()
    hyde_prompt = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia về quy chế đào tạo sinh viên UTC. "
                   "Hãy viết một đoạn văn ngắn giả định (2-3 câu) trả lời câu hỏi sau một cách trang trọng, "
                   "chính xác theo giọng văn của quy chế đại học."),
        ("human", "{query}")
    ])
    hyde_chain = hyde_prompt | llm | StrOutputParser()
    return hyde_chain.invoke({"query": query})


class AragogRetriever:
    def __init__(self, vector_db: Chroma = None, reranker_model_name: str = RERANKER_MODEL):
        self.vector_db = vector_db or get_aragog_vector_db()
        self.llm = arise()
        self.reranker = CrossEncoder(reranker_model_name)

    def retrieve(self, query: str, top_k_initial: int = TOP_K_INITIAL, top_n_final: int = TOP_N_FINAL) -> List[Document]:
        hypo_doc = generate_hypothetical_answer(query, self.llm)
        candidate_docs = self.vector_db.similarity_search(hypo_doc, k=top_k_initial)
        if not candidate_docs:
            return []

        pairs = [[query, doc.metadata.get("window", doc.page_content)] for doc in candidate_docs]
        scores = self.reranker.predict(pairs)
        scored_docs = list(zip(candidate_docs, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        final_docs = []
        for doc, score in scored_docs[:top_n_final]:
            refined_doc = Document(
                page_content=doc.metadata.get("window", doc.page_content),
                metadata={**doc.metadata, "rerank_score": float(score)}
            )
            final_docs.append(refined_doc)
        return final_docs


def create_aragog_rag_chain(retriever: AragogRetriever = None, llm=None):
    if retriever is None:
        retriever = AragogRetriever()
    if llm is None:
        llm = arise()
    system_prompt = load_system_prompt()
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"{system_prompt}\n\nNgữ cảnh trích xuất:\n{{context}}"),
        ("human", "{input}"),
    ])
    def run_chain(query: str):
        docs = retriever.retrieve(query, top_k_initial=TOP_K_INITIAL, top_n_final=TOP_N_FINAL)
        context_text = "\n---\n".join([d.page_content for d in docs])
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({"context": context_text, "input": query})
        return {"answer": answer, "context_documents": docs}
    return run_chain


if __name__ == "__main__":
    rag = create_aragog_rag_chain()
    while True:
        q = input("\nNhập câu hỏi (gõ 'exit' để thoát): ")
        if q.strip().lower() == "exit":
            break
        if not q.strip():
            continue
        result = rag(q)
        print(f"\nQwen2.5: {result['answer']}")