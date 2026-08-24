from step1_chunking import ragchunking, ragload
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

import os

def embes():
    print("embesnef!")
    embedding = OllamaEmbeddings(model="nomic-embed-text")
    return embedding

def createvector():
    print("wordtovec -> save ChromaDb")
    persist_dir = "./duy_chroma_db"
    embedding = embes()
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        vector_db = Chroma(
            persist_directory=persist_dir,
            embedding_function=embedding
        )
    else:
        vector_db = Chroma.from_documents(
            documents=ragchunking(ragload("handbook.txt")),
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