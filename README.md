# UTC Student Handbook RAG V1 (Baseline)

Hệ thống **RAG Baseline (V1)** phục vụ tra cứu thông tin học vụ, quy chế đào tạo và đời sống sinh viên dựa trên tài liệu chính thức **Sổ tay sinh viên Trường Đại học Giao thông Vận tải (UTC) Khoá 67** (`data/raw/sotaysvk67.pdf`).

---

## 1. Bài toán giải quyết (What problem does this solve?)

Sinh viên trường Đại học Giao thông Vận tải thường gặp khó khăn khi tra cứu các quy định đào tạo theo tín chỉ, cách tính điểm, thang điểm quy đổi, điều kiện nhận học bổng, kỷ luật và các thủ tục hành chính sinh viên (ký túc xá, thư viện, chuẩn đầu ra ngoại ngữ). 

Hệ thống RAG V1 cung cấp một kênh hỏi đáp tự động cục bộ (local offline), có độ tin cậy cao với các nguyên tắc:
- **Trung thực với tài liệu (Factuality & Groundedness):** Câu trả lời hoàn toàn dựa trên các đoạn trích xuất từ Sổ tay sinh viên chính thức.
- **Minh bạch nguồn gốc (Source Traceability):** Mọi câu trả lời đều cung cấp đầy đủ dẫn chứng gồm: Tên tài liệu, Trang PDF, Trang in và Mục/Điều khoản tương ứng.
- **Từ chối thông minh (Explicit Uncertainty):** Nếu câu hỏi nằm ngoài phạm vi Sổ tay sinh viên hoặc không có đủ dữ liệu, hệ thống từ chối dứt khoát, không suy diễn hoặc bịa đặt tri thức bên ngoài.

---

## 2. Kiến trúc RAG V1 Baseline (Architecture)

Hệ thống tuân thủ triết lý **"Baseline First, Optimization Second"**, tập trung vào đường ống truy xuất và sinh văn bản tối thiểu nhưng có thể đo lường khoa học:

```
Tài liệu chính thức (sotaysvk67.pdf)
       │
       ▼
[PDF Parser & Cleaner]  ─── Trích xuất từng trang, loại bỏ header/footer rác, phát hiện Section/Điều
       │
       ▼
[Semantic Chunker]      ─── Tách chunk (600 ký tự, overlap 100) kèm metadata đầy đủ
       │
       ▼
[Ollama Embeddings]     ─── qwen3-embedding:0.6b (1024 dimensions)
       │
       ▼
[Chroma Vector Store]   ─── Lưu trữ cục bộ tại data/chroma/v1_baseline
       │
       ▼
[Top-k Dense Retrieval] ─── Cosine / L2 distance search (expose scores & metadata)
       │
       ▼
[Strict Grounded Prompt]─── Ràng buộc LLM chỉ trả lời trong ngữ cảnh, từ chối khi thiếu dữ liệu
       │
       ▼
[Local LLM Generation]  ─── Ollama qwen2.5:3b (Temperature 0.0)
       │
       ▼
[Structured Response]   ─── Answer + Source Evidence (Page, Book Page, Section, Chunk ID)
```

> **Lưu ý về các module nâng cao:** Các module thử nghiệm trước đây như `aragog.py` (Sentence-window, HyDE, Cross-encoder), `corrective.py` (CRAG, Web fallback) và `memory.py` (Multi-turn conversational memory) đã được tách biệt (isolate/decouple) khỏi critical path của V1 để đảm bảo tính tinh gọn, có thể đo lường và kiểm soát được rủi ro ảo giác.

---

## 3. Dữ liệu & Mô hình sử dụng (Data & Models)

- **Ground Truth Source:** `data/raw/sotaysvk67.pdf` (97 trang, 176.953 ký tự, ấn bản chính thức Sổ tay sinh viên K67 - ĐH Giao thông Vận tải).
- **Embedding Model:** `qwen3-embedding:0.6b` chạy local qua Ollama (1024 chiều, độ trễ trung bình ~150ms/truy vấn, hỗ trợ tiếng Việt xuất sắc).
- **Generation Model:** `qwen2.5:3b` chạy local qua Ollama (temperature = 0.0, suy luận nhanh, nhẹ và đáp ứng định dạng prompt nghiêm ngặt).
- **Vector Database:** `ChromaDB` (chạy local file-based, hỗ trợ tái lập và sao lưu dễ dàng).

---

## 4. Cài đặt & Chuẩn bị môi trường (Setup)

### Bước 1: Chuẩn bị môi trường ảo và thư viện

```bash
# Tạo venv và cài đặt dependencies
python3 -m venv rag_env
source rag_env/bin/activate
pip install --upgrade pip
pip install -e .
```

### Bước 2: Cài đặt và tải các local models của Ollama

Đảm bảo tiến trình Ollama đang chạy (`ollama serve`), sau đó tải các mô hình:

```bash
ollama pull qwen3-embedding:0.6b
ollama pull qwen2.5:3b
```

---

## 5. Hướng dẫn sử dụng (User Flow)

### 5.1. Ingestion — Trích xuất và xây dựng chỉ mục Vector

Chạy lệnh sau để đọc file PDF chính thức, phân tách chunk và lưu vào ChromaDB:

```bash
# Tái xây dựng toàn bộ cơ sở dữ liệu vector
python -m student_handbook_rag.ingest --force
```

Tùy chọn:
- `--chunk-size <int>`: Kích thước chunk (mặc định: 600)
- `--chunk-overlap <int>`: Độ gối đầu (mặc định: 100)
- `--data-path <path>`: Đường dẫn tới file nguồn (mặc định: `data/raw/sotaysvk67.pdf`)

### 5.2. Hỏi đáp (Querying)

#### Hỏi đáp trực tiếp một câu hỏi (Single-shot):
```bash
python -m student_handbook_rag.ask "Sinh viên có điểm thi kết thúc học phần nhỏ hơn bao nhiêu thì nhận điểm F?"
```

#### Bật chế độ Debug xem chi tiết các chunk và similarity scores:
```bash
python -m student_handbook_rag.ask "Điều kiện nhận học bổng khuyến khích học tập?" --debug
```

#### Chế độ hội thoại tương tác (Interactive Mode):
```bash
python -m student_handbook_rag.ask
```

---

## 6. Kiểm thử tự động (Testing)

Hệ thống được thiết kế phân tách rõ ràng giữa Unit Tests (không cần model/mạng, chạy trong vài giây) và Integration Tests:

```bash
# 1. Chạy nhanh toàn bộ Unit Tests (loader, cleaner, chunker, failure modes)
PYTHONPATH=src rag_env/bin/pytest tests/unit/ tests/test_loader.py -v

# 2. Chạy Integration Tests (kiểm tra retriever, chain và Ollama)
PYTHONPATH=src rag_env/bin/pytest tests/integration/ -v

# 3. Chạy toàn bộ 39 tests của dự án
PYTHONPATH=src rag_env/bin/pytest tests/ -v
```

---

## 7. Đánh giá thực nghiệm & Benchmark (Evaluation)

Hệ thống đi kèm bộ Benchmark chuẩn gồm **25 câu hỏi** (`data/benchmark/evaluation_set.json`) trải đều trên 9 chủ đề thực tế của sinh viên UTC:
1. Tra cứu trực tiếp (Website, fanpage, ký túc xá)
2. Quy chế đào tạo (Thang điểm, điểm F, đổi điểm)
3. Quy trình học vụ (Học lại, cải thiện điểm, chuẩn ngoại ngữ)
4. Dịch vụ sinh viên (Thư viện, nhà sách, app eUTC)
5. Học bổng & Chế độ chính sách (Học bổng khuyến khích, miễn giảm)
6. Kỷ luật & Đánh giá rèn luyện (Khung điểm rèn luyện, các mức kỷ luật)
7. Câu hỏi đa điều kiện (Phối hợp nhiều điều khoản)
8. Câu hỏi đặc thù theo mục
9. Câu hỏi ngoài phạm vi (Kiểm thử từ chối suy đoán/ảo giác)

### 7.1. Chạy đánh giá Benchmark

```bash
python -m student_handbook_rag.evaluate --output data/benchmark/eval_results.json
```

### 7.2. Kết quả thực nghiệm Baseline V1

Dựa trên kết quả đo lường thực tế trên bộ Benchmark 25 câu hỏi:

| Metric | Kết quả Baseline V1 | Ý nghĩa / Tiêu chuẩn đánh giá |
| :--- | :---: | :--- |
| **Hit@1** | **81.8%** | Đoạn văn chứa thông tin chính xác đứng ở vị trí số 1 |
| **Hit@3** | **95.5%** | Đoạn văn chứa thông tin chính xác nằm trong Top 3 |
| **Hit@5** | **95.5%** | Đoạn văn chứa thông tin chính xác nằm trong Top 5 |
| **MRR (Mean Reciprocal Rank)** | **0.8864** | Thứ hạng trung bình của kết quả đúng rất cao |
| **Answer Correctness** | **90.9%** | Trả lời chính xác các câu hỏi có trong sổ tay (20/22) |
| **Citation Groundedness** | **95.5%** | Trích dẫn đúng số trang và điều khoản tài liệu (21/22) |
| **Unanswerable Refusal Rate** | **100.0%** | Từ chối chính xác 100% các câu hỏi ngoài sổ tay (3/3) |

### 7.3. Thí nghiệm siêu tham số Chunking (Chunk Size Experiment)

Chạy so sánh 3 cấu hình kích thước chunk khác nhau (`python -m student_handbook_rag.evaluate --experiment-chunking`):

| Cấu hình | Chunk Size | Overlap | Tổng số Chunks | Hit@1 | Hit@3 | Hit@5 | MRR | Đánh giá |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Config A (Small)** | 400 | 80 | 476 | 86.4% | 95.5% | 95.5% | 0.9091 | Rất nét cho câu hỏi tra cứu ngắn, nhưng xé vụn các điều khoản dài |
| **Config B (Medium - V1 Default)** | **600** | **100** | **325** | **81.8%** | **95.5%** | **95.5%** | **0.8864** | **Cân bằng tối ưu giữa ngữ cảnh điều khoản và số lượng chunk** |
| **Config C (Large)** | 1000 | 150 | 215 | 86.4% | 95.5% | 95.5% | 0.9091 | Giữ trọn điều khoản lớn, thời gian nạp nhanh |

---

## 8. Giới hạn đã biết (Known Limitations)

1. **Bảng biểu phức tạp trong PDF:** Các bảng điểm quy đổi hoặc bảng danh mục đơn vị chức năng khi trích xuất dạng văn bản thuần có thể bị mất cấu trúc hàng/cột nếu không sử dụng parser chuyên dụng cho bảng.
2. **Từ khoá viết tắt đặc thù:** Retrieval thuần dense embedding (`qwen3-embedding:0.6b`) có thể bỏ sót các từ viết tắt rất ngắn hoặc mã số phòng ban nếu không có hỗ trợ từ bộ tìm kiếm từ khoá (BM25 Hybrid Search).
3. **Phạm vi của model nhỏ (3B):** `qwen2.5:3b` hoạt động rất tốt với các câu hỏi trực tiếp và rõ ràng, nhưng với các câu hỏi phối hợp 3-4 điều kiện quy chế cùng lúc thì cần ngữ cảnh cô đọng và rõ ràng hơn.

---

## 9. Định hướng nâng cấp kế tiếp (Next Experiments)

Theo nguyên tắc khoa học: **Baseline -> Measure -> Bottleneck -> Single Intervention -> Measure again**:

- **Experiment 1 (Hybrid Search BM25 + Dense):**
  - *Giả thuyết:* Bổ sung BM25 kết hợp Dense Retrieval bằng Reciprocal Rank Fusion (RRF) sẽ cải thiện Hit@1 cho các truy vấn tra cứu mã hiệu, tên phòng ban và từ khoá viết tắt.
- **Experiment 2 (BGE Reranker tích hợp):**
  - *Giả thuyết:* Kích hoạt Cross-Encoder (`BAAI/bge-reranker-base` từ `src/student_handbook_rag/aragog.py`) lên Top-10 ứng viên sẽ tăng Hit@1 và MRR lên trên 0.92.
