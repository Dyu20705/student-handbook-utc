import os
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from student_handbook_rag.config import RAW_DATA_PATH, CHUNK_SIZE, CHUNK_OVERLAP

def resolve_data_path(filename: str = RAW_DATA_PATH) -> str:
    if os.path.exists(filename):
        return filename
    candidates = [
        os.path.join("data", "raw", os.path.basename(filename)),
        os.path.join("data", "raw", filename),
        str(Path(__file__).resolve().parent.parent.parent / "data" / "raw" / os.path.basename(filename)),
        str(Path(__file__).resolve().parent.parent.parent / filename),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return filename

def ragload(filename: str = RAW_DATA_PATH):
    print("File Reading...")
    resolved_path = resolve_data_path(filename)
    loader = TextLoader(resolved_path, encoding="utf-8")
    documents = loader.load()
    return documents
# print(f"Origin contents have {len(documents[0].page_content)} characters.")

# RecursiveCharacterTextSplitter: this func break large documents into smaller, manageable chunks of text
# chunk_size: max characters of 1 chunk
# chunk_overlap: how many characters (or tokens) of overlapping text are shared between consecutive chunks during text splitting
def ragchunking(documents, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunk = splitter.split_documents(documents)
    return chunk

if __name__ == "__main__":
    document = ragload("data/raw/handbook.txt")
    chunk = ragchunking(document)
    print(f"\nSplit to  {len(chunk)}. Let's see first and second chunk!!!!")
    print("Chunk 1: ")
    print(chunk[0].page_content)
    print("Chunk 2: ")
    print(chunk[1].page_content)