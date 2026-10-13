# Dependency security — local baseline

Kiểm tra ngày 2026-10-13. Runtime chỉ bind 127.0.0.1, Chroma dùng embedded PersistentClient; không chạy `chroma run`, không expose `/api/v2/tenants/...`, không nhận embedding function/model repository hoặc `trust_remote_code` từ HTTP. API không có upload/ingest/admin endpoint. Không dùng cấu hình này làm multi-tenant service.

Requests được ràng buộc >=2.33 để xử lý [CVE-2026-25645](https://github.com/psf/requests/security/advisories/GHSA-gc5v-m9x4-r6x2). Tiện ích arxiv nghiên cứu không nằm trong runtime vì pin Requests cũ.

Audit thô Chroma 1.5.9 vẫn báo các advisory không có fix version trong cơ sở dữ liệu:

| ID | Phạm vi | Đánh giá cho cấu hình hiện tại |
| --- | --- | --- |
| PYSEC-2026-311 / CVE-2026-45829 | Python HTTP server tạo collection với model repository không tin cậy | Không có server/route này trong ứng dụng |
| PYSEC-2026-3814 / CVE-2026-45833 | HTTP update collection cho phép code injection | Không có update collection endpoint hoặc remote model |
| PYSEC-2026-3815 / CVE-2026-45831 | SimpleRBACAuthorizationProvider bỏ qua scope | Không dùng RBAC hoặc multi-tenant server |
| PYSEC-2026-3813 / CVE-2026-45830 | Authorization tenant của HTTP server | Không có tenant API |

Đây là ngoại lệ có phạm vi cho vận hành nhúng, không phải khẳng định package hết lỗ hổng. CI chỉ bỏ qua bốn ID này; lỗ hổng khác vẫn fail. Đánh giá lại trước mỗi release, khi đổi kiến trúc và chậm nhất 2026-11-13. Nếu bật Chroma server hoặc cho người không tin cậy cấu hình embedding, các ngoại lệ mất hiệu lực và chặn phát hành.

[Advisory gốc CVE-2026-45829](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c).

Lệnh audit đầy đủ (có thể exit 1 do advisory Chroma):

```powershell
uv run --locked pip-audit --local --skip-editable
```

Lệnh đối chiếu ngoại lệ đúng cấu hình này:

```powershell
uv run --locked pip-audit --local --skip-editable --ignore-vuln PYSEC-2026-311 --ignore-vuln PYSEC-2026-3814 --ignore-vuln PYSEC-2026-3815 --ignore-vuln PYSEC-2026-3813
```

API chống DNS rebinding bằng TrustedHost, từ chối Origin khác host, giới hạn body/câu hỏi/top-k/rate và một inference đồng thời. API key tùy chọn chỉ phù hợp máy local. Không cung cấp auth phân quyền, TLS termination hay quota phân tán để triển khai Internet.
