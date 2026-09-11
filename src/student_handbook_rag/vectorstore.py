"""ChromaDB vector store management for Student Handbook RAG.
Provides reproducible indexing, persistence, and similarity retrieval.
"""

import os
import shutil
from typing import List, Tuple, Optional
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from student_handbook_rag.loader import ragload, ragchunking
from student_handbook_rag.config import (
    EMBEDDING_MODEL,
    CHROMA_DEFAULT_DIR,
    RAW_DATA_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


def get_embedding_function(model: str = EMBEDDING_MODEL) -> OllamaEmbeddings:
    """Initialize local Ollama embeddings."""
    return OllamaEmbeddings(model=model)


def embes():
    """Backward-compatible alias for embedding function."""
    return get_embedding_function()


def build_vector_store(
    persist_dir: str = CHROMA_DEFAULT_DIR,
    data_path: str = RAW_DATA_PATH,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    force_rebuild: bool = False,
    collection_name: str = "utc_handbook",
) -> Chroma:
    """Build or load a Chroma vector store from handbook documents.
    
    Args:
        persist_dir: Directory to save Chroma files.
        data_path: Path to handbook source file (PDF or TXT).
        chunk_size: Maximum chunk character size.
        chunk_overlap: Overlap characters between chunks.
        force_rebuild: If True, deletes existing index and rebuilds from scratch.
        collection_name: Name of Chroma collection.
    """
    embedding = get_embedding_function()

    exists = os.path.exists(persist_dir) and bool(os.listdir(persist_dir))

    if exists and not force_rebuild:
        print(f"[VectorStore] Loading existing index from {persist_dir}...")
        return Chroma(
            persist_directory=persist_dir,
            embedding_function=embedding,
            collection_name=collection_name,
        )

    if force_rebuild and os.path.exists(persist_dir):
        print(f"[VectorStore] Rebuilding index: clearing {persist_dir}...")
        shutil.rmtree(persist_dir)
    os.makedirs(persist_dir, exist_ok=True)

    print(f"[VectorStore] Ingesting documents from {data_path}...")
    documents = ragload(data_path)
    chunks = ragchunking(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"[VectorStore] Indexing {len(chunks)} chunks into Chroma at {persist_dir}...")

    # Index in batches of 50 to avoid memory spikes and report progress
    batch_size = 50
    vector_db = Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding,
        collection_name=collection_name,
    )
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vector_db.add_documents(batch)
        print(f"  Indexed chunks {i+1} to {min(i+batch_size, len(chunks))} / {len(chunks)}")

    print(f"[VectorStore] Index built successfully with {len(chunks)} chunks.")
    return vector_db


def createvector(persist_dir: str = CHROMA_DEFAULT_DIR, force_rebuild: bool = False) -> Chroma:
    """Backward-compatible vector store creator."""
    return build_vector_store(persist_dir=persist_dir, force_rebuild=force_rebuild)


def similarity_search_with_scores(
    vector_db: Chroma,
    query: str,
    k: int = 3,
) -> List[Tuple[Document, float]]:
    """Retrieve top-k documents along with similarity scores (distance/similarity)."""
    return vector_db.similarity_search_with_score(query, k=k)


if __name__ == "__main__":
    db = build_vector_store(force_rebuild=False)
    query = "Quy định đánh giá rèn luyện sinh viên"
    results = similarity_search_with_scores(db, query, k=2)
    print(f"\nQuery: '{query}'")
    for idx, (doc, score) in enumerate(results):
        print(f"\n--- Result #{idx+1} (score: {score:.4f}) ---")
        print(f"Page: {doc.metadata.get('page')}, Section: {doc.metadata.get('section')}")
        print(doc.page_content[:200])