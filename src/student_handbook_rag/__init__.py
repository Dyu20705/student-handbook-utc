"""Student Handbook RAG Package.
Official baseline RAG implementation for UTC Student Handbook.
"""

from student_handbook_rag.loader import ragload, ragchunking
from student_handbook_rag.vectorstore import embes, createvector, build_vector_store
from student_handbook_rag.retriever import BaselineRetriever
from student_handbook_rag.chain import (
    StudentHandbookRAG,
    createretriever,
    arise,
    load_system_prompt,
    createprompt,
    createragchain,
)
from student_handbook_rag.aragog import AragogRetriever, create_aragog_rag_chain
from student_handbook_rag.corrective import CorrectiveRAG
from student_handbook_rag.memory import conversational_rag, create_conversational_rag_chain

__all__ = [
    "ragload",
    "ragchunking",
    "embes",
    "createvector",
    "build_vector_store",
    "BaselineRetriever",
    "StudentHandbookRAG",
    "createretriever",
    "arise",
    "load_system_prompt",
    "createprompt",
    "createragchain",
    "AragogRetriever",
    "create_aragog_rag_chain",
    "CorrectiveRAG",
    "conversational_rag",
    "create_conversational_rag_chain",
]
