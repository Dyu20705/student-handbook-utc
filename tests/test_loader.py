import pytest 
from student_handbook_rag.loader import ragload, ragchunking

def test_load():
    assert len(ragload("data/raw/handbook.txt")[0].page_content) == 8126

def test_load_fallback():
    assert len(ragload("handbook.txt")[0].page_content) == 8126

def test_chunk():
    assert len(ragchunking(ragload("data/raw/handbook.txt"))) == 113