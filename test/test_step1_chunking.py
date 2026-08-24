import pytest 
from step1_chunking import ragload, ragchunking

def test_load():
    assert len(ragload("handbook.txt")[0].page_content) == 8126
def test_chunk():
    assert len(ragchunking(ragload("handbook.txt"))) == 113