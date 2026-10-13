"""CLI for querying Student Handbook RAG V1 with retrieved chunk inspection.

Usage:
    python -m student_handbook_rag.ask "Sinh viên có điểm thi kết thúc học phần dưới bao nhiêu thì nhận điểm F?" [--debug]
    python -m student_handbook_rag.ask (interactive mode)
"""

import argparse
import sys
from student_handbook_rag.chain import StudentHandbookRAG
from student_handbook_rag.retriever import BaselineRetriever
from student_handbook_rag.config import RETRIEVAL_K


def print_response(result: dict, debug: bool = False, retriever: BaselineRetriever = None):
    print("\n--- Result ---")
    print(f"Question: {result['query']}\n")
    print(f"Answer:\n{result['answer']}\n")
    print("Sources:")
    if result["sources"]:
        for s in result["sources"]:
            print(f"  - {s['document']} | Page: {s['page']} (Book page: {s['book_page']}) | Section: {s['section']} | Score: {s['score']:.4f}")
    else:
        print("  (No relevant sources found)")

    if debug:
        print("\n--- Debug: Retrieved Chunks ---")
        # Sources are a cited subset, not a one-to-one map of all retrieved chunks.
        scored_pairs = [(doc, float(rank)) for rank, doc in enumerate(result["retrieved_chunks"], 1)]
        if retriever:
            print(retriever.format_retrieval_debug(result["query"], scored_pairs))


def main():
    parser = argparse.ArgumentParser(description="Query UTC Student Handbook RAG V1.")
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default=None,
        help="Question to ask (if omitted, starts interactive chat mode).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Display detailed retrieved chunks, similarity scores, and metadata.",
    )
    parser.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=RETRIEVAL_K,
        help=f"Number of top chunks to retrieve (default: {RETRIEVAL_K})",
    )

    args = parser.parse_args()
    if not 1 <= args.top_k <= 10:
        parser.error("--top-k must be between 1 and 10")

    print("[Init] Loading Student Handbook RAG...")
    try:
        retriever = BaselineRetriever(k=args.top_k)
        rag = StudentHandbookRAG(retriever=retriever)
    except Exception as exc:
        print(f"Startup failed ({type(exc).__name__}). Run utc-doctor and utc-ingest.", file=sys.stderr)
        return 1
    print("[Init] System ready.\n")

    if args.query:
        result = rag.query(args.query, k=args.top_k)
        print_response(result, debug=args.debug, retriever=retriever)
        return 1 if result.get("status") == "error" else 0
    else:
        print("--- Interactive Mode (type 'exit' to quit) ---")
        while True:
            try:
                user_input = input("\nQuery: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break

            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "thoát"]:
                print("Goodbye!")
                break

            result = rag.query(user_input, k=args.top_k)
            print_response(result, debug=args.debug, retriever=retriever)


if __name__ == "__main__":
    sys.exit(main())
