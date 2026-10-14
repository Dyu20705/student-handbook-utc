"""Environment settings and validation for the local handbook service."""

import os
from pathlib import Path
from urllib.parse import urlsplit

# Paths
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent

DATA_DIR = Path(os.getenv("RAG_DATA_DIR", str(PROJECT_ROOT / "data"))).resolve()
RAW_PDF_PATH = str(DATA_DIR / "raw" / "sotaysvk67.pdf")
RAW_DATA_PATH = os.getenv("RAG_DATA_PATH", RAW_PDF_PATH)

CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_BASELINE_DIR = str(CHROMA_DIR / "v1_baseline")
CHROMA_DEFAULT_DIR = os.getenv("RAG_CHROMA_DIR", CHROMA_BASELINE_DIR)
BENCHMARK_PATH = str(DATA_DIR / "benchmark" / "evaluation_set.json")

# Model Identifiers
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "qwen3.5:9b-q4_K_M")
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "qwen3-embedding:0.6b")

# Chunking Parameters (Baseline defaults)
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

# Retrieval & Evaluation Parameters
RETRIEVAL_K = int(os.getenv("RAG_RETRIEVAL_K", "5"))

# LLM Generation Parameters
TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.0"))

OLLAMA_BASE_URL = os.getenv("RAG_OLLAMA_URL", "http://127.0.0.1:11434")
ALLOW_REMOTE_OLLAMA = os.getenv("RAG_ALLOW_REMOTE_OLLAMA", "0")
OLLAMA_TIMEOUT = float(os.getenv("RAG_OLLAMA_TIMEOUT", "120"))
MAX_QUESTION_LENGTH = 2000
MAX_RETRIEVAL_K = 10
MAX_OUTPUT_TOKENS = int(os.getenv("RAG_MAX_OUTPUT_TOKENS", "768"))


def frontend_origins() -> tuple[str, ...]:
    """Read exact browser origins; wildcards, credentials and URL paths are invalid."""
    origins = tuple(
        part.strip() for part in os.getenv("RAG_ALLOWED_ORIGINS", "").split(",") if part.strip()
    )
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or "*" in origin
            or any(char.isspace() for char in origin)
        ):
            raise ValueError(
                "RAG_ALLOWED_ORIGINS requires exact HTTP(S) origins without paths or wildcards"
            )
        # Accessing port also rejects nonnumeric and out-of-range values.
        if parsed.port == 0 or parsed.netloc.endswith(":"):
            raise ValueError("RAG_ALLOWED_ORIGINS contains an invalid port")
    return origins


def validate_config():
    """Fail before connecting to services when settings are invalid."""
    import ipaddress
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
    if ALLOW_REMOTE_OLLAMA not in {"0", "1"}:
        raise ValueError("RAG_ALLOW_REMOTE_OLLAMA must be 0 or 1")
    try:
        is_loopback = ipaddress.ip_address(url.hostname).is_loopback
    except ValueError:
        is_loopback = url.hostname == "localhost"
    if not is_loopback and ALLOW_REMOTE_OLLAMA != "1":
        raise ValueError(
            "Remote Ollama sends questions and context off this machine; set RAG_ALLOW_REMOTE_OLLAMA=1 to opt in"
        )
