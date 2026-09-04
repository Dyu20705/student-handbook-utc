"""Configuration constants for Student Handbook RAG.
Pure declarative configuration with environment fallbacks. No business logic.
"""
import os
from pathlib import Path

# Paths
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = str(DATA_DIR / "raw" / "handbook.txt")
CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_DEFAULT_DIR = str(CHROMA_DIR / "default")
CHROMA_ARAGOG_DIR = str(CHROMA_DIR / "aragog")
PROMPTS_DIR = PACKAGE_DIR / "prompts"

# Model Identifiers
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "qwen2.5:3b")
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
RERANKER_MODEL = os.getenv("RAG_RERANKER_MODEL", "BAAI/bge-reranker-base")

# Chunking Parameters
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "100"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "20"))

# Retrieval & Evaluation Parameters
RETRIEVAL_K = int(os.getenv("RAG_RETRIEVAL_K", "2"))
WINDOW_SIZE = int(os.getenv("RAG_WINDOW_SIZE", "2"))
TOP_K_INITIAL = int(os.getenv("RAG_TOP_K_INITIAL", "8"))
TOP_N_FINAL = int(os.getenv("RAG_TOP_N_FINAL", "3"))

# LLM Generation Parameters
TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.0"))
