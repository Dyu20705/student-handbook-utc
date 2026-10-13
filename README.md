# UTC Student Handbook RAG — chạy nội bộ

Tra cứu Sổ tay sinh viên UTC K67 bằng Ollama và Chroma nhúng trên máy của bạn. Phiên bản 0.2 bổ sung vận hành local, chỉ mục có phiên bản, HTTP API và kiểm thử lỗi. Phạm vi dữ liệu vẫn là PDF K67 trong repository; không mặc nhiên đại diện cho quy định đang có hiệu lực của mọi khóa/cơ sở.

## Khởi động trên Windows

Yêu cầu: Python 3.11 hoặc 3.12, uv, Ollama. Dùng PowerShell tại thư mục dự án:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
uv sync --locked --python 3.12
ollama pull qwen3-embedding:0.6b
ollama pull qwen3.5:9b-q4_K_M
uv run --locked utc-ingest
uv run --locked utc-doctor
.\scripts\start-local.ps1
```

Nếu Ollama chưa chạy, khởi động ứng dụng Ollama hoặc chạy `ollama serve` trong terminal khác. `start-local.ps1` kiểm tra model và embedding trước khi mở API. Mặc định chỉ truy cập từ máy hiện tại tại [API docs](http://127.0.0.1:8000/docs). Để chạy nền: `.\scripts\start-local.ps1 -Background`. Dừng bằng `.\scripts\stop-local.ps1`; chế độ foreground dùng Ctrl+C.

API không tự tạo chỉ mục khi khởi động. Chỉ mục cũ không có manifest cần di chuyển bằng `uv run --locked utc-ingest --force`; dữ liệu cũ vẫn được giữ lại. Khi đổi PDF, embedding hoặc cấu hình chunk, tạo lại chỉ mục rồi khởi động lại API.

## Hỏi đáp

```powershell
uv run --locked utc-ask 'Điều kiện nhận học bổng khuyến khích học tập?'
uv run --locked utc-ask 'Quy định điểm F?' --debug
$body = @{ question = 'Quy định điểm F?'; k = 3 } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/ask -Method Post -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

`POST /ask` trả về `status` (`answered` hoặc `refused`), `answer`, `sources`, `is_insufficient_context`. Nguồn gồm tài liệu, trang PDF, trang in ước tính, mục và chunk ID. Chỉ các ID được model trích và có trong retrieval mới xuất hiện trong `sources`. Việc ID hợp lệ không tự chứng minh mọi khẳng định trong câu trả lời đúng; cần kiểm tra nội dung nguồn với các quyết định học vụ quan trọng.

Lỗi model/index trả HTTP 503, không được tính là từ chối thành công. Input sai trả 422, body quá lớn trả 413, hệ thống đang bận hoặc quá 30 yêu cầu/phút trả 429. Một lần suy luận đồng thời phù hợp với máy local. `GET /health` kiểm tra tiến trình; `GET /ready` kiểm tra model, manifest và số chunk. `utc-doctor` còn chạy thử embedding/retrieval.

## Cấu hình

Xem `.env.example`. Export bằng `$env:RAG_LLM_MODEL = '...'` trong PowerShell; dự án không tự nạp `.env`. Mặc định: `qwen3.5:9b-q4_K_M`, `qwen3-embedding:0.6b`, chunk 600/100, top-k 5, timeout I/O 120 giây, tối đa 768 token đầu ra. API giới hạn 2.000 ký tự/câu hỏi và top-k 1–10. Không dùng proxy môi trường cho kết nối Ollama.

Có thể đặt `$env:RAG_API_KEY` để yêu cầu `Authorization: Bearer ...` trên `/ask`. Mặc định dành cho người dùng tin cậy trên cùng máy. Chạy nhiều worker, mở cổng LAN/Internet hoặc dùng Chroma HTTP server nằm ngoài cấu hình được kiểm chứng này.

## Kiểm chứng

```powershell
uv run --locked ruff check src tests
uv run --locked pytest -q
uv run --locked pytest --run-integration -q
uv run --locked python -m student_handbook_rag.evaluate --check --output data/runtime/eval-production.json
uv build
```

Suite mặc định không cần mạng/model, gồm test Chroma thật với embedding giả lập, API và regression. Suite integration cần hai model và chỉ mục đã nạp. Module ARAGOG/CRAG/memory là thử nghiệm: cài `uv sync --extra experimental` và opt-in `--run-experimental --run-integration`; chúng không nằm trong cam kết vận hành baseline. `scripts/arxiv.py` là tiện ích nghiên cứu tách riêng, cần môi trường arxiv riêng.

Benchmark gồm 25 câu. Các chỉ số keyword match và citation page match chỉ là proxy, không phải đánh giá ngữ nghĩa độc lập. `--check` yêu cầu Hit@3 >= 90%, keyword match >= 80%, citation page match >= 90%, từ chối đúng 100% câu ngoài phạm vi và 0 lỗi vận hành. Không giảm ngưỡng để làm báo cáo xanh. Kết quả cũ tại `data/benchmark/eval_results.json` dùng bộ chấm cũ và không phải bằng chứng phát hành hiện tại.

Chi tiết: [vận hành/backup/rollback](docs/operations.md), [dependency security](docs/security.md), [báo cáo kiểm chứng](docs/qualification/local-production-readiness.md).

## Giới hạn

- PDF được parse dạng text; bảng phức tạp và OCR chưa được xử lý chuyên biệt.
- Trang in hiện suy ra bằng trang PDF trừ 2; đối chiếu trang PDF khi kiểm chứng.
- Mục/Điều được dò ở cấp trang, có thể không chính xác với nhiều điều trên cùng trang.
- Model có thể từ chối quá mức hoặc trả lời thiếu; câu trả lời dựa trên tài liệu K67, không tự cập nhật văn bản mới.
- Source Intake v1.2 trong `docs/architecture/` là đặc tả riêng chưa triển khai; runtime hiện chỉ nạp PDF/TXT do người vận hành cung cấp.


Retrieval mặc định lấy ba đoạn dense trước, bổ sung hai đoạn BM25 không trùng để tìm tên riêng/viết tắt. `score` trong response là thứ hạng truy xuất (1 là đầu tiên), không phải xác suất đúng. Các lệnh hỏi với `k=3` chỉ lấy ba đoạn đầu; dùng mặc định `k=5` cho cấu hình đã benchmark.

Model 9B ưu tiên độ đúng của điều khoản. Trên máy không có GPU khả dụng, một câu có thể mất hàng chục giây hoặc hơn; không chạy benchmark và phục vụ người dùng đồng thời. Có thể đổi model qua biến môi trường nhưng phải chạy lại benchmark và kiểm tra ngữ nghĩa trước khi sử dụng.
