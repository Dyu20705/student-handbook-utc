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
    print("\n" + "=" * 60)
    print("❓ CÂU HỎI:")
    print(f"   {result['query']}")
    print("=" * 60)
    print("💡 CÂU TRẢ LỜI:")
    print(f"   {result['answer']}")
    print("\n📚 NGUỒN TRÍCH DẪN (SOURCES):")
    if result["sources"]:
        for s in result["sources"]:
            print(f"   • {s['document']} | Trang PDF: {s['page']} (Trang in: {s['book_page']}) | Mục: {s['section']} | Score: {s['score']:.4f}")
    else:
        print("   (Không có nguồn dẫn chứng)")
    print("=" * 60)

    if debug:
        print("\n🔍 DEBUG: CHI TIẾT CÁC CHUNK ĐƯỢC RETRIEVE:")
        scored_pairs = [(doc, s["score"]) for doc, s in zip(result["retrieved_chunks"], result["sources"])]
        if retriever:
            print(retriever.format_retrieval_debug(result["query"], scored_pairs))
        print("=" * 60)


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

    print("🤖 Đang khởi tạo Student Handbook RAG V1...")
    retriever = BaselineRetriever(k=args.top_k)
    rag = StudentHandbookRAG(retriever=retriever)
    print("✅ Hệ thống đã sẵn sàng!\n")

    if args.query:
        result = rag.query(args.query, k=args.top_k)
        print_response(result, debug=args.debug, retriever=retriever)
    else:
        print("--- CHẾ ĐỘ HỎI ĐÁP TƯƠNG TÁC (Gõ 'exit' hoặc 'quit' để thoát) ---")
        while True:
            try:
                user_input = input("\n👤 Bạn muốn hỏi gì: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nTạm biệt!")
                break

            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "thoát"]:
                print("Tạm biệt!")
                break

            result = rag.query(user_input, k=args.top_k)
            print_response(result, debug=args.debug, retriever=retriever)


if __name__ == "__main__":
    main()
