"""Versioned Chroma indexes with atomic publication and a single writer lock."""

import hashlib
import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from filelock import FileLock
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from student_handbook_rag.config import (
    CHROMA_DEFAULT_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_TIMEOUT,
    RAW_DATA_PATH,
    validate_config,
)
from student_handbook_rag.loader import ragchunking, ragload, resolve_data_path


class IndexNotReadyError(RuntimeError):
    """No complete, compatible index is available."""


def get_embedding_function(model=EMBEDDING_MODEL):
    validate_config()
    return OllamaEmbeddings(
        model=model,
        base_url=OLLAMA_BASE_URL,
        client_kwargs={"timeout": OLLAMA_TIMEOUT, "trust_env": False},
    )


def _manifest_path(persist_dir, collection_name):
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,63}", collection_name):
        raise ValueError("Invalid collection name")
    return Path(persist_dir).resolve() / f"{collection_name}.manifest.json"


def read_manifest(
    persist_dir=CHROMA_DEFAULT_DIR,
    collection_name="utc_handbook",
    *,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
):
    path = _manifest_path(persist_dir, collection_name)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if (
            manifest["schema_version"] != 1
            or manifest["chunk_count"] <= 0
            or manifest["embedding_model"] != EMBEDDING_MODEL
            or manifest["chunk_size"] != chunk_size
            or manifest["chunk_overlap"] != chunk_overlap
            or not re.fullmatch(
                re.escape(collection_name) + r"_[0-9a-f]{32}", manifest["collection"]
            )
        ):
            raise ValueError("Incompatible manifest")
        return manifest
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise IndexNotReadyError("Index missing or incompatible; run utc-ingest --force") from exc


def _open_index(persist_dir, collection_name, embedding, chunk_size, chunk_overlap):
    manifest = read_manifest(
        persist_dir, collection_name, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    db = Chroma(
        persist_directory=str(Path(persist_dir).resolve()),
        embedding_function=embedding,
        collection_name=manifest["collection"],
        create_collection_if_not_exists=False,
    )
    if db._collection.count() != manifest["chunk_count"]:
        raise IndexNotReadyError("Index count differs from manifest; rebuild required")
    return db


def validate_source(manifest, data_path=RAW_DATA_PATH):
    """Ensure displayed page references still refer to the indexed source bytes."""
    try:
        digest = hashlib.sha256(Path(resolve_data_path(data_path)).read_bytes()).hexdigest()
        if digest != manifest["source_sha256"]:
            raise ValueError("Source changed")
    except (OSError, KeyError, ValueError) as exc:
        raise IndexNotReadyError("Source differs from indexed snapshot; rebuild required") from exc


def build_vector_store(
    persist_dir=CHROMA_DEFAULT_DIR,
    data_path=RAW_DATA_PATH,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    force_rebuild=False,
    collection_name="utc_handbook",
    load_only=False,
):
    """Publish an immutable generation after every batch succeeds; preserve the old one.

    Readers never ingest. Failed generations are deleted, previous generations stay
    available for rollback. Existing unversioned indexes require explicit --force.
    """
    embedding = get_embedding_function()
    path = _manifest_path(persist_dir, collection_name)
    if load_only:
        validate_source(
            read_manifest(
                persist_dir, collection_name, chunk_size=chunk_size, chunk_overlap=chunk_overlap
            ),
            data_path,
        )
        return _open_index(persist_dir, collection_name, embedding, chunk_size, chunk_overlap)
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(path.parent / "ingest.lock"), timeout=0):
        if path.exists() and not force_rebuild:
            manifest = read_manifest(
                persist_dir, collection_name, chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            source = Path(resolve_data_path(data_path))
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if (
                digest != manifest["source_sha256"]
                or chunk_size != manifest["chunk_size"]
                or chunk_overlap != manifest["chunk_overlap"]
            ):
                raise IndexNotReadyError("Source or chunk settings changed; run utc-ingest --force")
            return _open_index(persist_dir, collection_name, embedding, chunk_size, chunk_overlap)
        if (path.parent / "chroma.sqlite3").exists() and not path.exists() and not force_rebuild:
            raise IndexNotReadyError("Unversioned index found; run utc-ingest --force")
        source = Path(resolve_data_path(data_path))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        chunks = ragchunking(ragload(str(source)), chunk_size, chunk_overlap)
        if not chunks:
            raise ValueError("Source contains no extractable text")
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise ValueError("Source changed during extraction; retry ingestion")
        generation = f"{collection_name}_{uuid.uuid4().hex}"
        db = Chroma(
            persist_directory=str(path.parent),
            embedding_function=embedding,
            collection_name=generation,
            collection_metadata={"hnsw:space": "cosine"},
        )
        temp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            for i in range(0, len(chunks), 50):
                batch = chunks[i : i + 50]
                db.add_documents(batch, ids=[c.metadata["chunk_id"] for c in batch])
            if db._collection.count() != len(chunks):
                raise IndexNotReadyError("Incomplete index; previous generation preserved")
            manifest = {
                "schema_version": 1,
                "collection": generation,
                "embedding_model": EMBEDDING_MODEL,
                "source_sha256": digest,
                "source_document": source.name,
                "chunk_count": len(chunks),
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "distance_metric": "cosine",
                "created_at": datetime.now(UTC).isoformat(),
            }
            validate_source(manifest, str(source))
            with temp.open("w", encoding="utf-8") as handle:
                json.dump(manifest, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        except BaseException:
            db.delete_collection()
            raise
        finally:
            temp.unlink(missing_ok=True)
        return db


def similarity_search_with_scores(vector_db, query, k=3):
    return vector_db.similarity_search_with_score(query, k=k)
