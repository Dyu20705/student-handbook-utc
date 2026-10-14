"""Evaluation Engine for Student Handbook RAG V1.
Measures retrieval (Hit@k, MRR), generation proxies and refusal rate.

Usage:
    python -m student_handbook_rag.evaluate [--output data/runtime/eval_results.json]
"""

import argparse
import json
import os
import sys
import time
from typing import Any

from student_handbook_rag.chain import StudentHandbookRAG
from student_handbook_rag.config import (
    BENCHMARK_PATH,
    DATA_DIR,
    RETRIEVAL_K,
)
from student_handbook_rag.retriever import BaselineRetriever


def load_benchmark(filepath: str = BENCHMARK_PATH) -> list[dict[str, Any]]:
    """Load gold evaluation dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Benchmark file not found: {filepath}")
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def evaluate_retrieval(
    benchmark: list[dict[str, Any]],
    retriever: BaselineRetriever,
    max_k: int = 5,
) -> dict[str, Any]:
    """Evaluate retrieval quality (Hit@1, Hit@3, Hit@5, MRR) against gold questions."""
    answerable_items = [q for q in benchmark if q.get("answerable", True)]
    total = len(answerable_items)

    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    mrr_sum = 0.0

    detailed_results = []

    for item in answerable_items:
        q_id = item["id"]
        query = item["question"]
        gold_page = item.get("expected_page")
        gold_book_page = item.get("book_page")
        gold_keywords = [kw.lower() for kw in item.get("gold_keywords", [])]

        scored_docs = retriever.retrieve(query, k=max_k)
        retrieved_pages = [doc.metadata.get("page") for doc, _ in scored_docs]

        # Determine the rank of the first hit
        rank_hit = 0
        for rank, (doc, _) in enumerate(scored_docs, start=1):
            doc_text = doc.page_content.lower()
            doc_page = doc.metadata.get("page")
            doc_book_page = doc.metadata.get("book_page")

            page_match = (gold_page and doc_page == gold_page) or (
                gold_book_page and doc_book_page == gold_book_page
            )
            keyword_match = any(kw in doc_text for kw in gold_keywords) if gold_keywords else False

            if page_match or (gold_page is None and gold_book_page is None and keyword_match):
                rank_hit = rank
                break

        if rank_hit == 1:
            hit_1 += 1
        if 1 <= rank_hit <= 3:
            hit_3 += 1
        if 1 <= rank_hit <= 5:
            hit_5 += 1

        reciprocal_rank = 1.0 / rank_hit if rank_hit > 0 else 0.0
        mrr_sum += reciprocal_rank

        detailed_results.append(
            {
                "id": q_id,
                "query": query,
                "category": item.get("category"),
                "gold_page": gold_page,
                "gold_book_page": gold_book_page,
                "retrieved_pages": retrieved_pages,
                "rank_hit": rank_hit,
                "reciprocal_rank": reciprocal_rank,
                "top_score": float(scored_docs[0][1]) if scored_docs else None,
            }
        )

    return {
        "total_answerable": total,
        "hit_at_1": hit_1 / total if total else 0.0,
        "hit_at_3": hit_3 / total if total else 0.0,
        "hit_at_5": hit_5 / total if total else 0.0,
        "mrr": mrr_sum / total if total else 0.0,
        "details": detailed_results,
    }


def evaluate_generation(
    benchmark: list[dict[str, Any]],
    rag_engine: StudentHandbookRAG,
    k: int = 3,
) -> dict[str, Any]:
    """Measure keyword/page proxies; semantic completeness needs a separate review."""
    answerable_items = [q for q in benchmark if q.get("answerable", True)]
    unanswerable_items = [q for q in benchmark if not q.get("answerable", True)]

    keyword_matches = 0
    page_matches = 0
    errors = 0
    detailed_qa = []

    print(f"\n[Generation Eval] Evaluating {len(answerable_items)} answerable questions...")
    for idx, item in enumerate(answerable_items, start=1):
        q = item["question"]
        gold_kw = [kw.lower() for kw in item.get("gold_keywords", [])]
        expected_page = item.get("expected_page")
        expected_book_page = item.get("book_page")

        res = rag_engine.query(q, k=k)
        ans = res["answer"]
        ans_lower = ans.lower()

        # Keyword recall in generated answer
        kw_matched = [kw for kw in gold_kw if kw in ans_lower]
        failed = res.get("status") == "error"
        errors += int(failed)
        keyword_match = (
            bool(gold_kw and kw_matched) and not failed and not res["is_insufficient_context"]
        )
        if keyword_match:
            keyword_matches += 1

        # A matching gold page does not prove that the cited text supports every claim.
        cited_pages = [s.get("page") for s in res["sources"]]
        cited_book_pages = [s.get("book_page") for s in res["sources"]]
        citation_page_match = (
            (
                (expected_page is not None and expected_page in cited_pages)
                or (expected_book_page is not None and expected_book_page in cited_book_pages)
            )
            and not failed
            and not res["is_insufficient_context"]
        )
        if citation_page_match:
            page_matches += 1

        print(
            f"  [{idx}/{len(answerable_items)}] Keyword proxy: {keyword_match} | Page proxy: {citation_page_match} | Q: {q[:50]}..."
        )

        detailed_qa.append(
            {
                "id": item["id"],
                "category": item.get("category"),
                "question": q,
                "generated_answer": ans,
                "expected_answer": item.get("expected_answer"),
                "keyword_match": keyword_match,
                "matched_keywords": kw_matched,
                "citation_page_match": citation_page_match,
                "semantic_verdict": "not_reviewed",
                "status": res.get("status"),
                "sources": res["sources"],
            }
        )

    # Evaluate refusal behavior on unanswerable questions
    print(f"\n[Generation Eval] Evaluating {len(unanswerable_items)} unanswerable questions...")
    correct_refusals = 0
    refusal_details = []

    for idx, item in enumerate(unanswerable_items, start=1):
        q = item["question"]
        res = rag_engine.query(q, k=k)
        errors += int(res.get("status") == "error")
        is_refused = res.get("status") == "refused"
        if is_refused:
            correct_refusals += 1

        print(
            f"  [{idx}/{len(unanswerable_items)}] Properly Refused: {is_refused} | Q: {q[:50]}..."
        )

        refusal_details.append(
            {
                "id": item["id"],
                "question": q,
                "generated_answer": res["answer"],
                "properly_refused": is_refused,
                "status": res.get("status"),
                "sources": res["sources"],
            }
        )

    total_ans = len(answerable_items)
    total_unans = len(unanswerable_items)

    return {
        "answer_keyword_match_rate": keyword_matches / total_ans if total_ans else 0.0,
        "citation_page_match_rate": page_matches / total_ans if total_ans else 0.0,
        "operational_errors": errors,
        "unanswerable_refusal_rate": correct_refusals / total_unans if total_unans else 0.0,
        "total_answerable": total_ans,
        "total_unanswerable": total_unans,
        "detailed_qa": detailed_qa,
        "detailed_refusals": refusal_details,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Student Handbook RAG V1.")
    parser.add_argument(
        "--benchmark-path",
        type=str,
        default=BENCHMARK_PATH,
        help=f"Path to evaluation JSON (default: {BENCHMARK_PATH})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATA_DIR / "runtime" / "eval_results.json"),
        help="Path to save evaluation results JSON.",
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip LLM generation evaluation (run retrieval evaluation only).",
    )
    parser.add_argument(
        "--check-proxies",
        "--check",
        dest="check",
        action="store_true",
        help="Check automated proxies only: Hit@3 >= .90, keyword match >= .80, citation page match >= .90, refusal = 1, no operational errors. Does NOT establish semantic correctness or release approval.",
    )
    args = parser.parse_args()
    if args.check and args.skip_generation:
        parser.error("--check requires generation evaluation")

    print("=== Student Handbook RAG - Evaluation Benchmark ===")

    benchmark = load_benchmark(args.benchmark_path)
    print(f"Loaded {len(benchmark)} questions from {args.benchmark_path}")

    results_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "benchmark_file": args.benchmark_path,
        "total_questions": len(benchmark),
    }

    print("\n--- RETRIEVAL EVALUATION (BASELINE) ---")
    retriever = BaselineRetriever()
    ret_metrics = evaluate_retrieval(benchmark, retriever, max_k=5)
    results_data["retrieval"] = {
        "total_answerable": ret_metrics["total_answerable"],
        "hit_at_1": round(ret_metrics["hit_at_1"], 4),
        "hit_at_3": round(ret_metrics["hit_at_3"], 4),
        "hit_at_5": round(ret_metrics["hit_at_5"], 4),
        "mrr": round(ret_metrics["mrr"], 4),
    }

    print(f"Total Answerable Questions: {ret_metrics['total_answerable']}")
    print(f"Hit@1:  {ret_metrics['hit_at_1'] * 100:.1f}%")
    print(f"Hit@3:  {ret_metrics['hit_at_3'] * 100:.1f}%")
    print(f"Hit@5:  {ret_metrics['hit_at_5'] * 100:.1f}%")
    print(f"MRR:    {ret_metrics['mrr']:.4f}")

    # Generation evaluation is optional for retrieval-only diagnostics.
    if not args.skip_generation:
        print("\n--- GENERATION EVALUATION (LLM GROUNDEDNESS) ---")
        rag_engine = StudentHandbookRAG(retriever=retriever)
        gen_metrics = evaluate_generation(benchmark, rag_engine, k=RETRIEVAL_K)
        results_data["generation"] = {
            "answer_keyword_match_rate": round(gen_metrics["answer_keyword_match_rate"], 4),
            "citation_page_match_rate": round(gen_metrics["citation_page_match_rate"], 4),
            "operational_errors": gen_metrics["operational_errors"],
            "unanswerable_refusal_rate": round(gen_metrics["unanswerable_refusal_rate"], 4),
            "total_answerable": gen_metrics["total_answerable"],
            "total_unanswerable": gen_metrics["total_unanswerable"],
        }
        results_data["detailed_qa"] = gen_metrics["detailed_qa"]
        results_data["detailed_refusals"] = gen_metrics["detailed_refusals"]

        print("\n--- Generation Metrics Summary ---")
        print(f"  Answer Keyword Match:     {gen_metrics['answer_keyword_match_rate'] * 100:.1f}%")
        print(f"  Citation Page Match:      {gen_metrics['citation_page_match_rate'] * 100:.1f}%")
        print(f"  Refusal on Unanswerable:  {gen_metrics['unanswerable_refusal_rate'] * 100:.1f}%")

    # Save to JSON
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    print(f"\nEvaluation results saved to: {args.output}")
    if args.check:
        print(
            "Checking automated proxies only. Review all answerable responses against the PDF before qualification."
        )
        passed = (
            ret_metrics["total_answerable"] > 0
            and ret_metrics["hit_at_3"] >= 0.90
            and gen_metrics["total_unanswerable"] > 0
            and gen_metrics["answer_keyword_match_rate"] >= 0.80
            and gen_metrics["citation_page_match_rate"] >= 0.90
            and gen_metrics["unanswerable_refusal_rate"] == 1
            and gen_metrics["operational_errors"] == 0
        )
        return 0 if passed else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
