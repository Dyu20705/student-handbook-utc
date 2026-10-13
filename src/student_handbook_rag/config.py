"""Configuration constants for Student Handbook RAG.
Pure declarative configuration with environment fallbacks. No business logic.
"""
import os
from pathlib import Path

# Paths
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent

DATA_DIR = Path(os.getenv("RAG_DATA_DIR", str(PROJECT_ROOT / "data"))).resolve()
RAW_PDF_PATH = str(DATA_DIR / "raw" / "sotaysvk67.pdf")
LEGACY_TXT_PATH = str(DATA_DIR / "raw" / "handbook.txt")
RAW_DATA_PATH = os.getenv("RAG_DATA_PATH", RAW_PDF_PATH)

CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_BASELINE_DIR = str(CHROMA_DIR / "v1_baseline")
CHROMA_DEFAULT_DIR = os.getenv("RAG_CHROMA_DIR", CHROMA_BASELINE_DIR)
CHROMA_LEGACY_DIR = str(CHROMA_DIR / "default")
CHROMA_ARAGOG_DIR = str(CHROMA_DIR / "aragog")
PROMPTS_DIR = PACKAGE_DIR / "prompts"
BENCHMARK_PATH = str(DATA_DIR / "benchmark" / "evaluation_set.json")

# Model Identifiers
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "qwen3.5:9b-q4_K_M")
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
RERANKER_MODEL = os.getenv("RAG_RERANKER_MODEL", "BAAI/bge-reranker-base")

# Chunking Parameters (Baseline defaults)
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

# Retrieval & Evaluation Parameters
RETRIEVAL_K = int(os.getenv("RAG_RETRIEVAL_K", "5"))
WINDOW_SIZE = int(os.getenv("RAG_WINDOW_SIZE", "2"))
TOP_K_INITIAL = int(os.getenv("RAG_TOP_K_INITIAL", "8"))
TOP_N_FINAL = int(os.getenv("RAG_TOP_N_FINAL", "3"))

# LLM Generation Parameters
TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.0"))

OLLAMA_BASE_URL = os.getenv("RAG_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_TIMEOUT = float(os.getenv("RAG_OLLAMA_TIMEOUT", "120"))
MAX_QUESTION_LENGTH = 2000
MAX_RETRIEVAL_K = 10
MAX_OUTPUT_TOKENS = int(os.getenv("RAG_MAX_OUTPUT_TOKENS", "768"))


def validate_config():
    """Fail before connecting to services when settings are invalid."""
    import math
    from urllib.parse import urlparse

    if CHUNK_SIZE <= 0 or not 0 <= CHUNK_OVERLAP < CHUNK_SIZE:
        raise ValueError("Require CHUNK_SIZE > 0 and 0 <= CHUNK_OVERLAP < CHUNK_SIZE")
    if not 1 <= RETRIEVAL_K <= MAX_RETRIEVAL_K:
        raise ValueError("RAG_RETRIEVAL_K must be between 1 and 10")
    if not math.isfinite(OLLAMA_TIMEOUT) or not 0 < OLLAMA_TIMEOUT <= 600:
        raise ValueError("RAG_OLLAMA_TIMEOUT must be between 0 and 600 seconds")
    if not math.isfinite(TEMPERATURE) or not 0 <= TEMPERATURE <= 2:
        raise ValueError("RAG_TEMPERATURE must be between 0 and 2")
    if not 1 <= MAX_OUTPUT_TOKENS <= 4096:
        raise ValueError("RAG_MAX_OUTPUT_TOKENS must be between 1 and 4096")
    url = urlparse(OLLAMA_BASE_URL)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
        raise ValueError("RAG_OLLAMA_URL must be an HTTP(S) URL without credentials")

