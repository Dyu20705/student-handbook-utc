"""Evaluation Engine for Student Handbook RAG V1.
Measures Retrieval (Hit@k, MRR) and Generation (Groundedness, Refusal Rate).
Supports Chunk Size Hyperparameter Experimentation.

Usage:
    python -m student_handbook_rag.evaluate [--output eval_results.json] [--experiment-chunking]
"""

import argparse
import json
import os
import shutil
import sys
import time
from typing import List, Dict, Any

from student_handbook_rag.config import (
    BENCHMARK_PATH,
    RAW_DATA_PATH,
    DATA_DIR,
)
from student_handbook_rag.loader import ragload
from student_handbook_rag.vectorstore import build_vector_store
from student_handbook_rag.retriever import BaselineRetriever
from student_handbook_rag.chain import StudentHandbookRAG


def load_benchmark(filepath: str = BENCHMARK_PATH) -> List[Dict[str, Any]]:
    """Load gold evaluation dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Benchmark file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_retrieval(
    benchmark: List[Dict[str, Any]],
    retriever: BaselineRetriever,
    max_k: int = 5,
) -> Dict[str, Any]:
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
        retrieved_book_pages = [doc.metadata.get("book_page") for doc, _ in scored_docs]

        # Determine the rank of the first hit
        rank_hit = 0
        for rank, (doc, _) in enumerate(scored_docs, start=1):
            doc_text = doc.page_content.lower()
            doc_page = doc.metadata.get("page")
            doc_book_page = doc.metadata.get("book_page")

            page_match = (gold_page and doc_page == gold_page) or (gold_book_page and doc_book_page == gold_book_page)
            keyword_match = any(kw in doc_text for kw in gold_keywords) if gold_keywords else False

            if page_match or keyword_match:
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

        detailed_results.append({
            "id": q_id,
            "query": query,
            "category": item.get("category"),
            "gold_page": gold_page,
            "gold_book_page": gold_book_page,
            "retrieved_pages": retrieved_pages,
            "rank_hit": rank_hit,
            "reciprocal_rank": reciprocal_rank,
            "top_score": float(scored_docs[0][1]) if scored_docs else None,
        })

    return {
        "total_answerable": total,
        "hit_at_1": hit_1 / total if total else 0.0,
        "hit_at_3": hit_3 / total if total else 0.0,
        "hit_at_5": hit_5 / total if total else 0.0,
        "mrr": mrr_sum / total if total else 0.0,
        "details": detailed_results,
    }


def evaluate_generation(
    benchmark: List[Dict[str, Any]],
    rag_engine: StudentHandbookRAG,
    k: int = 3,
) -> Dict[str, Any]:
    """Evaluate end-to-end generation quality: correctness, citation, refusal rate."""
    answerable_items = [q for q in benchmark if q.get("answerable", True)]
    unanswerable_items = [q for q in benchmark if not q.get("answerable", True)]

    correct_answers = 0
    grounded_citations = 0
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
        is_correct = len(kw_matched) > 0 or not gold_kw
        if is_correct:
            correct_answers += 1

        # Check citation accuracy
        cited_pages = [s.get("page") for s in res["sources"]]
        cited_book_pages = [s.get("book_page") for s in res["sources"]]
        has_grounded_citation = (
            (expected_page in cited_pages) or (expected_book_page in cited_book_pages)
        )
        if has_grounded_citation:
            grounded_citations += 1

        print(f"  [{idx}/{len(answerable_items)}] Correct: {is_correct} | Cited: {has_grounded_citation} | Q: {q[:50]}...")

        detailed_qa.append({
            "id": item["id"],
            "category": item.get("category"),
            "question": q,
            "generated_answer": ans,
            "expected_answer": item.get("expected_answer"),
            "is_correct": is_correct,
            "has_grounded_citation": has_grounded_citation,
            "sources": res["sources"],
        })

    # Evaluate refusal behavior on unanswerable questions
    print(f"\n[Generation Eval] Evaluating {len(unanswerable_items)} unanswerable questions...")
    correct_refusals = 0
    refusal_details = []

    for idx, item in enumerate(unanswerable_items, start=1):
        q = item["question"]
        res = rag_engine.query(q, k=k)
        is_refused = res["is_insufficient_context"]
        if is_refused:
            correct_refusals += 1

        print(f"  [{idx}/{len(unanswerable_items)}] Properly Refused: {is_refused} | Q: {q[:50]}...")

        refusal_details.append({
            "id": item["id"],
            "question": q,
            "generated_answer": res["answer"],
            "properly_refused": is_refused,
        })

    total_ans = len(answerable_items)
    total_unans = len(unanswerable_items)

    return {
        "answer_correctness_rate": correct_answers / total_ans if total_ans else 0.0,
        "citation_groundedness_rate": grounded_citations / total_ans if total_ans else 0.0,
        "unanswerable_refusal_rate": correct_refusals / total_unans if total_unans else 0.0,
        "total_answerable": total_ans,
        "total_unanswerable": total_unans,
        "detailed_qa": detailed_qa,
        "detailed_refusals": refusal_details,
    }


def run_chunking_experiment(benchmark: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare retrieval performance across different chunk sizes (400 vs 600 vs 1000)."""
    configs = [
        {"name": "Config_A_Small", "chunk_size": 400, "chunk_overlap": 80},
        {"name": "Config_B_Medium", "chunk_size": 600, "chunk_overlap": 100},
        {"name": "Config_C_Large", "chunk_size": 1000, "chunk_overlap": 150},
    ]

    exp_results = []
    print("\n=== Chunking Hyperparameter Experiment ===")

    docs = ragload(RAW_DATA_PATH)

    for cfg in configs:
        c_size = cfg["chunk_size"]
        c_overlap = cfg["chunk_overlap"]
        exp_dir = str(DATA_DIR / "chroma" / f"exp_chunk_{c_size}")

        print(f"\nEvaluating {cfg['name']}: chunk_size={c_size}, chunk_overlap={c_overlap}...")
        t0 = time.time()
        # Build collection for this experiment
        db = build_vector_store(
            persist_dir=exp_dir,
            data_path=RAW_DATA_PATH,
            chunk_size=c_size,
            chunk_overlap=c_overlap,
            force_rebuild=True,
            collection_name=f"exp_{c_size}",
        )
        total_chunks = db._collection.count()
        retriever = BaselineRetriever(vector_db=db)
        ret_metrics = evaluate_retrieval(benchmark, retriever, max_k=5)
        build_time = time.time() - t0

        cfg_res = {
            "config": cfg["name"],
            "chunk_size": c_size,
            "chunk_overlap": c_overlap,
            "total_chunks": total_chunks,
            "hit_at_1": ret_metrics["hit_at_1"],
            "hit_at_3": ret_metrics["hit_at_3"],
            "hit_at_5": ret_metrics["hit_at_5"],
            "mrr": ret_metrics["mrr"],
            "build_time_seconds": round(build_time, 2),
        }
        exp_results.append(cfg_res)

        print(f"  Result: Total Chunks={total_chunks} | Hit@1={cfg_res['hit_at_1']:.2f} | Hit@3={cfg_res['hit_at_3']:.2f} | Hit@5={cfg_res['hit_at_5']:.2f} | MRR={cfg_res['mrr']:.4f}")

        # Clean up experiment directory to save disk space
        try:
            if os.path.exists(exp_dir):
                shutil.rmtree(exp_dir)
        except Exception:
            pass

    return {"experiment": exp_results}


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
        default=str(DATA_DIR / "benchmark" / "eval_results.json"),
        help="Path to save evaluation results JSON.",
    )
    parser.add_argument(
        "--experiment-chunking",
        action="store_true",
        help="Run chunk size comparison experiment.",
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip LLM generation evaluation (run retrieval evaluation only).",
    )
    args = parser.parse_args()

    print("=== Student Handbook RAG - Evaluation Benchmark ===")

    benchmark = load_benchmark(args.benchmark_path)
    print(f"Loaded {len(benchmark)} questions from {args.benchmark_path}")

    results_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "benchmark_file": args.benchmark_path,
        "total_questions": len(benchmark),
    }

    # 1. Chunking Experiment (if requested)
    if args.experiment_chunking:
        exp_data = run_chunking_experiment(benchmark)
        results_data["chunking_experiment"] = exp_data["experiment"]

    # 2. Retrieval Evaluation on Baseline
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

    # 3. Generation Evaluation (if not skipped)
    if not args.skip_generation:
        print("\n--- GENERATION EVALUATION (LLM GROUNDEDNESS) ---")
        rag_engine = StudentHandbookRAG(retriever=retriever)
        gen_metrics = evaluate_generation(benchmark, rag_engine, k=3)
        results_data["generation"] = {
            "answer_correctness_rate": round(gen_metrics["answer_correctness_rate"], 4),
            "citation_groundedness_rate": round(gen_metrics["citation_groundedness_rate"], 4),
            "unanswerable_refusal_rate": round(gen_metrics["unanswerable_refusal_rate"], 4),
            "total_answerable": gen_metrics["total_answerable"],
            "total_unanswerable": gen_metrics["total_unanswerable"],
        }
        results_data["detailed_qa"] = gen_metrics["detailed_qa"]
        results_data["detailed_refusals"] = gen_metrics["detailed_refusals"]

        print("\n--- Generation Metrics Summary ---")
        print(f"  Answer Correctness:       {gen_metrics['answer_correctness_rate'] * 100:.1f}%")
        print(f"  Citation Groundedness:    {gen_metrics['citation_groundedness_rate'] * 100:.1f}%")
        print(f"  Refusal on Unanswerable:  {gen_metrics['unanswerable_refusal_rate'] * 100:.1f}%")

    # Save to JSON
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    print(f"\nEvaluation results saved to: {args.output}")


if __name__ == "__main__":
    main()
