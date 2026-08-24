from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def ragload(filename):
    print("File Reading...")
    loader = TextLoader(filename, encoding="utf-8")
    documents = loader.load()
    return documents
# print(f"Origin contents have {len(documents[0].page_content)} characters.")

# RecursiveCharacterTextSplitter: this func break large documents into smaller, manageable chunks of text
# chunk_size: max characters of 1 chunk
# chunk_overlap: how many characters (or tokens) of overlapping text are shared between consecutive chunks during text splitting
def ragchunking(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size = 100, chunk_overlap = 20)
    chunk = splitter.split_documents(documents)
    return chunk

if __name__ == "__main__":
    document = ragload("handbook.txt")
    chunk = ragchunking(document)
    print(f"\nSplit to  {len(chunk)}. Let's see first and second chunk!!!!")
    print("Chunk 1: ")
    print(chunk[0].page_content)
    print("Chunk 2: ")
    print(chunk[1].page_content)