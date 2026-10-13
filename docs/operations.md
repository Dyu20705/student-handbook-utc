# Vận hành local

## Quy trình phát hành

1. Giữ `uv.lock` cùng mã nguồn; cài `uv sync --locked --python 3.12`. Không nâng dependencies ngầm khi khởi động.
2. Chạy Ruff, offline tests, integration tests, dependency audit và benchmark `--check-proxies` theo README. Commit runtime rồi chạy `scripts/run_qualification.py` trên checkout sạch để lưu provenance.
3. Đọc toàn bộ 22 câu answerable với trang PDF nguồn; ghi verdict từng câu và SHA-256 artifact. Kiểm tra đầy đủ điều kiện bắt buộc, phủ định, đối tượng và ngưỡng số. Proxy tự động không thay thế đánh giá này; q15 từng khớp keyword nhưng thiếu điều kiện 5,0 nên không đạt.
4. Dừng API trước khi đổi dữ liệu/model. Sao lưu dữ liệu, chạy ingestion, `utc-doctor`, rồi `scripts/start-local.ps1`.
5. Kiểm tra `/health`, `/ready`, một câu có nguồn và một câu ngoài phạm vi. Lưu kết quả, phiên bản model và hash nguồn.

## Logs và tài nguyên

Một PID được quản lý cho cả dự án. Start trên port khác vẫn bị từ chối khi PID hiện tại còn sống; stop trước khi đổi port. Các lệnh start/stop dùng khóa file độc quyền; lệnh chạy trùng báo lỗi và không thay đổi PID. PID không thuộc API trong `.venv` bị từ chối dừng; kiểm tra process trước khi xử lý PID file. Foreground giữ khóa đến khi Ctrl+C; stop script dành cho background.

Chạy nền ghi `data/runtime/server.stdout.log` và `server.stderr.log`. Log ứng dụng chỉ có request ID, mã HTTP, thời gian, loại lỗi; không ghi câu hỏi, nội dung PDF hoặc API key. Chế độ `--debug` và benchmark có nội dung, chỉ dùng cục bộ. Di chuyển/xóa log khi server đã dừng; runtime không tự xoay log.

Theo dõi 503, 429, thời gian phản hồi và `/ready`. Nếu `/ready` lỗi, không tiếp tục gửi tải: chạy `utc-doctor`, kiểm tra Ollama, model và manifest. Timeout HTTP là timeout I/O, không phải hạn tổng thời gian của một luồng sinh token. Ollama giới hạn số token; chờ tác vụ hoàn tất trước khi bảo trì.

SLO nội bộ ban đầu: 0 lỗi vận hành trong benchmark/smoke; p95 đo trên máy thực, lưu cùng báo cáo. Chưa có SLA nhiều người dùng. Khi benchmark tụt ngưỡng hoặc smoke sai, quay lại bản đã kiểm chứng; không phát hành thêm tính năng đến khi phục hồi.

## Sao lưu và khôi phục

Dừng API và mọi tiến trình ingestion trước khi copy. Sao lưu toàn bộ thư mục `data/chroma/v1_baseline` (SQLite, WAL nếu còn và tất cả segment), PDF nguồn, `uv.lock`, biến môi trường và mã nguồn tương ứng. Không chỉ copy `chroma.sqlite3` khi DB đang mở.

Ví dụ PowerShell, backup vào thư mục mới, không ghi đè backup cũ:

```powershell
.\scripts\stop-local.ps1
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $env:USERPROFILE "utc-backup-$stamp"
New-Item -ItemType Directory -Path $backup
Copy-Item -LiteralPath data/chroma/v1_baseline -Destination $backup -Recurse
Copy-Item -LiteralPath data/raw/sotaysvk67.pdf,uv.lock -Destination $backup
```

Restore vào thư mục mới rồi đặt `RAG_CHROMA_DIR` tới bản phục hồi, chọn đúng embedding model, chạy `utc-doctor`, khởi động và smoke. Không xóa DB đang chạy. Kiểm tra phục hồi định kỳ trên bản copy.

## Tái tạo và rollback chỉ mục

`utc-ingest --force` tạo collection mới, thêm toàn bộ chunks bằng ID xác định, xác nhận count, fsync manifest tạm rồi `os.replace` manifest hiện hành. Lock file đảm bảo một writer. Nếu nạp lỗi, manifest cũ còn nguyên. Crash trước publish có thể để lại collection chưa tham chiếu; không ảnh hưởng reader. Các generation cũ được giữ để rollback, vì vậy dung lượng tăng mỗi lần rebuild.

Trước rebuild, copy `utc_handbook.manifest.json` sang file backup có timestamp. Để rollback: dừng API/ingest, phục hồi manifest đã sao lưu trỏ tới collection cũ còn tồn tại, bảo đảm cùng embedding model, chạy doctor rồi start. Để rollback cả runtime, dùng bản mã nguồn + lockfile đã kiểm chứng và cài lại `uv sync --locked`.

Reader đã mở giữ generation cũ đến khi restart. `/ready` sẽ trả 503 nếu manifest đã đổi. Không chạy ingestion song song với phục vụ thông thường. Chưa có tự động xóa generation: chỉ dọn bằng công cụ quản trị khi đã backup và xác định collection không còn được dùng.

## Nguồn triển khai

- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/): khởi tạo engine khi service start.
- [Chroma Python client](https://docs.trychroma.com/reference/python/client): persistent collections, không bật HTTP server.
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs): ràng buộc JSON; ứng dụng vẫn kiểm tra ID và schema.
