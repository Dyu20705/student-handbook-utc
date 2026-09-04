# Mini Student Handbook

> **Note:** I just jotted down some random notes in `data/raw/handbook.txt`; do not mistake it for the actual UTC handbook.

A lightweight RAG (Retrieval-Augmented Generation) system built with LangChain, ChromaDB, and Ollama.

---

## Cài đặt & Chuẩn bị (Setup)

### 1. Cấp quyền và chạy Setup
Cài đặt môi trường ảo (`rag_env`), các thư viện cần thiết và tải model Ollama (`qwen3-embedding:0.6b`, `qwen2.5:3b`):

```bash
chmod +x scripts/setup.sh scripts/verify_ok_setup.sh
bash scripts/setup.sh
```

### 2. Kiểm tra môi trường (Verify Setup)
Kiểm tra virtual environment, các packages và Ollama models:

```bash
bash scripts/verify_ok_setup.sh
```

---

## Chạy Tests (Pytest)

Đảm bảo server Ollama đang chạy (`ollama serve`) trước khi chạy test:

- **Chạy toàn bộ Tests:**
  ```bash
  rag_env/bin/pytest tests/
  ```
