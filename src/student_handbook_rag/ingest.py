"""CLI for ingesting official handbook documents and building the Chroma vector store.

Usage:
    python -m student_handbook_rag.ingest [--force] [--chunk-size 600] [--chunk-overlap 100]
"""

import argparse
import sys
import time
from student_handbook_rag.config import (
    RAW_DATA_PATH,
    CHROMA_DEFAULT_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from student_handbook_rag.vectorstore import build_vector_store


def main():
    parser = argparse.ArgumentParser(description="Ingest UTC Student Handbook into Chroma vector store.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Build a new index generation and publish only after success.",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=RAW_DATA_PATH,
        help=f"Path to handbook source file (default: {RAW_DATA_PATH})",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default=CHROMA_DEFAULT_DIR,
        help=f"Path to Chroma persistence directory (default: {CHROMA_DEFAULT_DIR})",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help=f"Chunk character size (default: {CHUNK_SIZE})",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=CHUNK_OVERLAP,
        help=f"Chunk overlap character size (default: {CHUNK_OVERLAP})",
    )

    args = parser.parse_args()

    print("=== Student Handbook RAG - Ingestion Pipeline ===")
    print(f"Source Document:  {args.data_path}")
    print(f"Vector Store Dir: {args.persist_dir}")
    print(f"Chunk Size:       {args.chunk_size}")
    print(f"Chunk Overlap:    {args.chunk_overlap}")
    print(f"Force Rebuild:    {args.force}\n")

    start_time = time.time()
    try:
        vector_db = build_vector_store(
            persist_dir=args.persist_dir,
            data_path=args.data_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            force_rebuild=args.force,
        )
        total_docs = vector_db._collection.count()
        duration = time.time() - start_time
        print(f"\nIngestion completed in {duration:.2f}s.")
        print(f"Total indexed chunks: {total_docs}")
    except Exception as e:
        print(f"Error: Ingestion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
