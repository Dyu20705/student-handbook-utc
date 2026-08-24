import pytest
from step3_final import createretriever, arise, createprompt, createragchain

def test_createretriever():
    retriever = createretriever()
    assert retriever is not None
    assert retriever.search_kwargs.get("k") == 2

def test_arise():
    llm = arise()
    assert llm is not None
    assert llm.model == "qwen2.5:7b"
    assert llm.temperature == 0

def test_createprompt():
    prompt = createprompt()
    assert prompt is not None
    assert "context" in prompt.input_variables or "input" in prompt.input_variables

def test_createragchain():
    chain = createragchain()
    assert chain is not None

def test_rag_invoke():
    chain = createragchain()
    response = chain.invoke({"input": "Quy định và Quy trình Đào tạo"})
    assert response is not None
    assert "answer" in response
    assert len(response["answer"]) > 0
