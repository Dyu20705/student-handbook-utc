import json
from unittest.mock import MagicMock

from langchain_core.documents import Document

from student_handbook_rag.chain import StudentHandbookRAG, build_context_text
from student_handbook_rag.retriever import BaselineRetriever


def doc(index, page, text, source="handbook.pdf"):
    return Document(page_content=text, metadata={"chunk_index": index, "page": page,
                    "chunk_id": f"{source}-{index}", "source": source, "document": source})


def retriever(documents):
    db = MagicMock()
    db.get.return_value = {"documents": [d.page_content for d in documents],
                           "metadatas": [d.metadata for d in documents]}
    return BaselineRetriever(vector_db=db)


def test_cross_page_condition_is_available_and_cited_with_its_own_page():
    first = doc(1, 45, "+ Số tín chỉ lần đầu từ 15 trở lên.")
    next_page = doc(2, 46, "+ Các học phần tính lần thứ nhất đạt từ 5,0 trở lên.")
    search = retriever([first, next_page])
    search.retrieve = MagicMock(return_value=[(first, 1.)])
    engine = StudentHandbookRAG(retriever=search, llm=MagicMock())
    engine.chain = MagicMock()
    engine.chain.invoke.return_value = json.dumps({"answer": "Từ 15 tín chỉ, điểm lần thứ nhất từ 5,0.",
        "citation_ids": [first.metadata["chunk_id"], next_page.metadata["chunk_id"]], "insufficient_context": False})
    result = engine.query("Điều kiện?", k=1)
    assert result["status"] == "answered"
    assert [s["page"] for s in result["sources"]] == [45, 46]
    assert "5,0" in engine.chain.invoke.call_args.args[0]["context"]
    assert "TIẾP NỐI DANH SÁCH từ ID: handbook.pdf-1." in engine.chain.invoke.call_args.args[0]["context"]
    assert len(search.retrieve.return_value) == 1  # Original rankings are unmodified.


def test_context_does_not_label_unrelated_bullets_as_continuations():
    first = doc(1, 45, "+ First condition")
    for unrelated in (doc(3, 46, "+ Gap"), doc(2, 47, "+ Other page"),
                      doc(2, 46, "+ Different source", "other.pdf"),
                      doc(2, 46, "New section")):
        context = build_context_text([(first, 1.), (unrelated, 2.)])
        assert "TIẾP NỐI DANH SÁCH" not in context


def test_no_duplicate_or_cross_document_or_non_adjacent_expansion():
    first = doc(1, 45, "+ One")
    following = doc(2, 46, "+ Two")
    search = retriever([first, following, doc(2, 46, "+ Other source", "other.pdf")])
    assert search.complete_page_bullets([(first, 1.), (following, 2.)]) == [(first, 1.), (following, 2.)]
    for wrong in (doc(3, 46, "+ Gap"), doc(2, 47, "+ Page gap"),
                  doc(2, 46, "PHẦN 2.6. New section"), doc(2, 46, "+ Other", "other.pdf")):
        assert retriever([first, wrong]).complete_page_bullets([(first, 1.)]) == [(first, 1.)]


def test_context_growth_is_bounded():
    documents = [doc(i, i, "+ A condition") for i in range(1, 9)]
    selected = [(documents[i], float(i + 1)) for i in (0, 2, 4, 6)]
    result = retriever(documents).complete_page_bullets(selected)
    assert len(result) == len(selected) + 2
    assert [d.metadata["chunk_index"] for d, _ in result] == [1, 2, 3, 4, 5, 7]
    assert [score for _, score in result] == list(range(1, 7))
