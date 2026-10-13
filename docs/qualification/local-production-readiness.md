# Kiểm chứng production nội bộ — UTC RAG 0.2.0

Ngày: 2026-10-13 (Asia/Bangkok). Phạm vi: một máy Windows, loopback 127.0.0.1, một inference đồng thời, PDF K67 có sẵn. Source Intake trong tài liệu kiến trúc là dự án riêng chưa triển khai.

## Cấu hình

- Python 3.12.10; dependencies theo uv.lock.
- Ollama local; qwen3-embedding:0.6b; qwen3.5:9b-q4_K_M, thinking off, context 8192, tối đa 768 token.
- Chroma embedded 1.5.9; 324 chunks, 600 ký tự/overlap 100, cosine dense + BM25 bổ sung; k=5.
- SHA-256 nguồn: `2ee1e3970b65cd36d8e6fe2e9e406965c4a20cc32b816a3b199341561dda208a`.
- Máy hiện chạy model 100% CPU; latency cao hơn cấu hình GPU.

## Kết quả

Báo cáo ban đầu dưới đây đã bị rút khỏi vai trò bằng chứng qualification HEAD: artifact thiếu provenance và q15 thiếu điều kiện bắt buộc. Các kết quả cũ được giữ để đối chiếu, không phải xác nhận production ready. Bản sửa đang được kiểm chứng lại trên commit xác định.

| Kiểm tra | Kết quả |
| --- | --- |
| Offline regression | 48 passed, 8 integration skipped (14,59 giây) |
| Integration với model 9B | 8 passed, 48 deselected (98,38 giây) |
| Ruff / compileall / PowerShell syntax | Passed |
| Build wheel + sdist | Passed; không chứa dữ liệu runtime, cache hoặc secrets |
| Dependency audit áp dụng ngoại lệ embedded | Passed; 4 advisory Chroma duy nhất (5 records do trùng advisory) |
| Backup/restore | Phục hồi 324 chunks, hash nguồn và truy xuất thành công |
| Lifecycle | Start, readiness, stop và restart script đã kiểm chứng |
| HTTP smoke | /health, /ready, /docs, /openapi.json = 200; input sai 422, foreign Origin 403; trả lời có nguồn và từ chối prompt injection ngoài phạm vi = passed |
| Benchmark --check | Exit 0 |

Benchmark 25 câu: Hit@1 59,09%, Hit@3 95,45%, Hit@5 95,45%, MRR 0,7652; keyword match 22/22; citation page match 21/22; refusal 3/3; lỗi vận hành 0. Kết quả chi tiết: [local-benchmark-2026-10-13.json](local-benchmark-2026-10-13.json).

Đối chiếu nội dung: q17 giữ đúng quyền được xét học bổng tại trang PDF 46; q19/q20 giữ đúng giới hạn “không vượt quá” tại trang 36. q12 trả lời eUTC và dẫn trang PDF 84/trang in 82, trong khi gold là `expected_page=4`, `book_page=2`. Trang 84 thực sự có hướng dẫn tải/đăng nhập eUTC; ghi nhận đây là bằng chứng bổ sung, giữ nguyên gold và điểm proxy cũ 21/22.

q15 **không đạt**: bỏ sót điểm học phần tính lần thứ nhất từ 5,0 (cả GDTC/GDQP) và tối thiểu 15 tín chỉ lần đầu, không tính ngoại ngữ tăng cường. Artifact cũ đã được gắn đánh giá ngữ nghĩa thất bại; không sửa các số liệu proxy lịch sử. [Rubric 22 câu](semantic-rubric.md) yêu cầu đối chiếu đủ điều kiện, phủ định và ngưỡng số cho lần chạy mới.

Các số keyword/page match là proxy, không được diễn giải thành 100% độ đúng ngữ nghĩa. Đây là kiểm chứng kỹ thuật và đối chiếu mẫu bởi agent, không phải phê duyệt nghiệp vụ của UTC. Model 3B cũ đã có câu trả lời đảo nghĩa trong thử nghiệm; kết quả phát hành chỉ áp dụng model 9B đã cấu hình. Các tag Ollama có thể thay đổi; cần lưu model cùng backup và benchmark lại sau khi pull/update.

## Cơ chế đã bổ sung

- Import không nạp model/ghi DB; optional research dependencies tách khỏi runtime.
- Index generations, writer lock, publish manifest nguyên tử, bảo toàn generation cũ khi embedding/publish lỗi.
- Kiểm tra hash nguồn, embedding model tag và chunk count; chặn API khi manifest/source thay đổi.
- JSON schema cho model output, chỉ trả citations có ID trong retrieved context; response có đoạn trích nguồn.
- Tách refusal khỏi lỗi vận hành; từ chối không có citations, HTTP 503 cho backend/index lỗi.
- API local có body/input limits, một inference đồng thời, 30 yêu cầu/phút, chặn foreign Origin/Host, tùy chọn bearer key.
- Health/readiness, doctor, scripts setup/start/stop, log không chứa câu hỏi và runbook backup/rollback.

## Giới hạn và điều kiện sử dụng

Trích dẫn có ID hợp lệ không đảm bảo câu trả lời luôn đúng về ngữ nghĩa. Benchmark nhỏ (22 câu có câu trả lời, 3 câu ngoài phạm vi), chưa chứng minh chất lượng trên mọi câu hỏi. Bảng PDF có thể mất cấu trúc. Trang in ước tính và heading ở cấp trang; ưu tiên xác minh trang PDF.

Dependency audit có bốn advisory Chroma server được đánh giá không thuộc đường chạy embedded; xem `docs/security.md`. Đây là ngoại lệ kiến trúc có phạm vi, không phải raw audit sạch. Không mở ứng dụng ra LAN/Internet hoặc bật Chroma server dựa trên báo cáo này.

CI trên GitHub đã pass ở `c3b96c6` (Windows/Linux, Python 3.11/3.12); đó là kết quả của commit cũ. Sau các sửa review phải chạy lại CI và smoke. Không tự phê duyệt nguồn mới hay triển khai Source Intake.

HTTP smoke trên CPU, hai truy vấn tuần tự: answered: 10.53 giây, refused: 27.08 giây. Đây là thời gian quan sát của hai mẫu, không phải p95 hay load test. Chi tiết runtime ở `data/runtime/http-smoke.json`.
