"""Document ingestion and chunking for Student Handbook RAG.
Supports PDF (sotaysvk67.pdf) with page-level extraction and section tracking,
as well as fallback plain text.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from student_handbook_rag.config import (
    RAW_DATA_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    PROJECT_ROOT,
)


def resolve_data_path(filename: str = RAW_DATA_PATH) -> str:
    """Resolve data file path against project root and standard directories."""
    if os.path.exists(filename):
        return os.path.abspath(filename)

    base = os.path.basename(filename)
    candidates = [
        os.path.join(str(PROJECT_ROOT), "data", "raw", base),
        os.path.join(str(PROJECT_ROOT), "data", "raw", "sotaysvk67.pdf"),
        os.path.join(str(PROJECT_ROOT), "data", "raw", "Sổ tay SV K67.pdf"),
        os.path.join(str(PROJECT_ROOT), filename),
        os.path.join("data", "raw", base),
        os.path.join("data", "raw", "sotaysvk67.pdf"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    return filename


def clean_page_text(text: str) -> str:
    """Clean extracted page text by removing recurring headers/footers and excess whitespace.
    
    Examples of footers in UTC handbook:
        '8 * STSV', 'STSV * 29', '0 * STSV'
    """
    if not text:
        return ""

    # Remove running footer patterns: e.g., 'STSV * 5', '5 * STSV', 'STSV * 29'
    text = re.sub(r'(?i)\bSTSV\s*\*\s*\d+\b', '', text)
    text = re.sub(r'(?i)\b\d+\s*\*\s*STSV\b', '', text)

    # Normalize whitespace
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def detect_section_heading(text: str) -> Optional[str]:
    """Detect section or chapter heading in a page to maintain section context."""
    patterns = [
        r'^\s*(PHẦN\s+[0-9IVX]+(?:\.[0-9]+)?[:.]?\s*[^\n]+)',
        r'^\s*(Chương\s+[IVXLCDM0-9]+[:.]?\s*[^\n]+)',
        r'^\s*(Điều\s+[0-9]+[:.]?\s*[^\n]+)',
        r'^\s*([I|V|XLCDM]+\.\s+[A-ZÀ-Ỹ\s]{3,}[^\n]*)',
        r'^\s*([0-9]+\.\s+[A-ZÀ-Ỹ\s]{3,}[^\n]*)',
    ]

    for line in text.split('\n'):
        line_clean = line.strip()
        if not line_clean:
            continue
        for pat in patterns:
            match = re.match(pat, line_clean, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return None


def _extract_pdf_pages_text(file_path: str) -> List[str]:
    """Extract raw text of each page from PDF using pypdf, falling back to pdftotext."""
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        if any(t.strip() for t in pages_text):
            return pages_text
    except Exception as e:
        print(f"[PDF Loader] pypdf failed or unavailable ({e}), attempting pdftotext fallback...")

    try:
        output = subprocess.check_output(["pdftotext", file_path, "-"], text=True)
        return output.split('\x0c')
    except Exception as e:
        raise RuntimeError(f"Could not load PDF {file_path} using pypdf or pdftotext: {e}")


def load_pdf_pages(file_path: str) -> List[Document]:
    """Extract pages from PDF and wrap into Document instances with metadata."""
    raw_pages = _extract_pdf_pages_text(file_path)
    documents: List[Document] = []
    doc_name = os.path.basename(file_path)
    current_section = "Mở đầu"

    for idx, raw_text in enumerate(raw_pages):
        cleaned = clean_page_text(raw_text)
        if not cleaned:
            continue

        page_num = idx + 1
        book_page = page_num - 2 if page_num >= 3 else 0

        detected = detect_section_heading(cleaned)
        if detected:
            current_section = detected

        doc = Document(
            page_content=cleaned,
            metadata={
                "source": file_path,
                "document": doc_name,
                "page": page_num,
                "book_page": book_page,
                "section": current_section,
            }
        )
        documents.append(doc)

    return documents


def ragload(filename: str = RAW_DATA_PATH) -> List[Document]:
    """Universal document loader for handbook files (.pdf or .txt)."""
    resolved_path = resolve_data_path(filename)
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Handbook file not found at: {resolved_path}")

    ext = os.path.splitext(resolved_path)[1].lower()
    if ext == ".pdf":
        return load_pdf_pages(resolved_path)
    else:
        loader = TextLoader(resolved_path, encoding="utf-8")
        docs = loader.load()
        # Add basic metadata to text documents
        for doc in docs:
            doc.metadata["document"] = os.path.basename(resolved_path)
            doc.metadata.setdefault("page", 1)
            doc.metadata.setdefault("book_page", 1)
            doc.metadata.setdefault("section", "Chung")
        return docs


def ragchunking(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """Split documents into semantic chunks with unique chunk_id and full metadata preservation."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\nĐiều ",
            "\nChương ",
            "\nPHẦN ",
            "\n\n",
            "\n",
            ". ",
            "; ",
            " ",
            "",
        ],
    )
    raw_chunks = splitter.split_documents(documents)

    final_chunks: List[Document] = []
    for idx, chunk in enumerate(raw_chunks):
        doc_name = chunk.metadata.get("document", "doc")
        page = chunk.metadata.get("page", 1)
        chunk_id = f"{doc_name}_p{page}_c{idx:04d}"

        metadata = {
            **chunk.metadata,
            "chunk_id": chunk_id,
            "chunk_index": idx,
        }
        final_chunks.append(Document(page_content=chunk.page_content, metadata=metadata))

    return final_chunks


if __name__ == "__main__":
    docs = ragload()
    print(f"Loaded {len(docs)} pages from {RAW_DATA_PATH}")
    chunks = ragchunking(docs)
    print(f"Generated {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    if chunks:
        print("\nSample Chunk 0 Metadata:", chunks[0].metadata)
        print("Sample Chunk 0 Content preview:\n", chunks[0].page_content[:200])