import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

from student_handbook_rag.loader import ragchunking, ragload
from student_handbook_rag.config import EMBEDDING_MODEL, CHROMA_DEFAULT_DIR, RAW_DATA_PATH

def embes():
    print("embesnef!")
    embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)
    return embedding

def createvector(persist_dir: str = CHROMA_DEFAULT_DIR):
    print("wordtovec -> save ChromaDb")
    embedding = embes()
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        vector_db = Chroma(
            persist_directory=persist_dir,
            embedding_function=embedding
        )
    else:
        vector_db = Chroma.from_documents(
            documents=ragchunking(ragload(RAW_DATA_PATH)),
            embedding=embedding,
            persist_directory=persist_dir # Lưu DB ra một thư mục trên ổ cứng
        )
    return vector_db

if __name__ == "__main__":
    vector_db = createvector()
    query = "Quy định Đào tạo?"
    print(f"\nQuestion: '{query}'")
    results = vector_db.similarity_search(query, k=2)
    for i, res in enumerate(results):
        print(f"--- Ans {i+1} ---")
        print(res.page_content)