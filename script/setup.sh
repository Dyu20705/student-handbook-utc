#!/usr/bin/env bash

echo "🚀 Bắt đầu quá trình setup..."

# 1. Tạo và kích hoạt môi trường ảo (virtual environment)
echo "🐍 Đang tạo virtual environment 'rag_env'..."
python3 -m venv rag_env
source rag_env/bin/activate

# 2. Cài đặt các thư viện Python
echo "📦 Đang cài đặt các thư viện Python..."
pip install --upgrade pip
pip install langchain langchain-community langchain-core langchain-ollama langchain-chroma sentence-transformers bs4 pytest arxiv

# 3. Tải các model của Ollama
echo "🦙 Đang tải các model Ollama (qwen2.5:7b và nomic-embed-text)..."
# Dùng 'pull' thay cho 'run' để script không bị dừng lại chờ nhập liệu
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

echo "✅ Setup hoàn tất thành công!"
echo "👉 Để bắt đầu làm việc, hãy chạy lệnh: source rag_env/bin/activate"