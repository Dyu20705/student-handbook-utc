#!/usr/bin/env bash

echo "🔍 Đang kiểm tra môi trường..."

# 1. Kiểm tra môi trường ảo
if [ -d "rag_env" ]; then
    echo "✅ [OK] Môi trường ảo 'rag_env' đã được tạo."
else
    echo "❌ [LỖI] Không tìm thấy môi trường ảo 'rag_env'."
    exit 1
fi

# Kích hoạt môi trường để kiểm tra thư viện
source rag_env/bin/activate

# 2. Kiểm tra các thư viện Python
echo "📦 Đang kiểm tra các thư viện Python..."
PACKAGES=("langchain" "langchain-community" "langchain-core" "langchain-ollama" "langchain-chroma" "sentence-transformers" "bs4" "pytest" "arxiv")

for pkg in "${PACKAGES[@]}"; do
    if pip show "$pkg" > /dev/null 2>&1; then
        echo "✅ [OK] Đã cài đặt thư viện '$pkg'."
    else
        echo "❌ [LỖI] Thiếu thư viện '$pkg'."
    fi
done

# 3. Kiểm tra Ollama models
echo "🦙 Đang kiểm tra các model Ollama..."
MODELS=("qwen2.5:3b" "qwen3-embedding:0.6b")

for model in "${MODELS[@]}"; do
    if ollama list | grep -q "$model"; then
        echo "✅ [OK] Đã tải model '$model'."
    else
        echo "❌ [LỖI] Chưa tải model '$model'."
    fi
done

echo "🎉 Quá trình kiểm tra kết thúc!"