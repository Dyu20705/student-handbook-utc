# Kiểm chứng UTC RAG local sau review PR #1

Cập nhật: 2026-10-14 (Asia/Bangkok). Phạm vi: một máy Windows, API loopback,
Chroma embedded, một inference đồng thời, PDF K67 có sẵn. PR vẫn Draft để người
dùng review. Source Intake không thuộc vòng sửa này.

Runtime được kiểm chứng tại `8b7149441362540085793001f2f1ea5b2fdb2cbc`. Remediation
evidence/CI không thay retrieval, prompt, model, gold hoặc runtime. Xem
[báo cáo sinh tự động](evidence-summary.md) cho metric, số test và SHA public/raw;
đây là nơi ghi số liệu tổng hợp, được verifier đối chiếu trong CI.

## Bằng chứng và cách diễn giải

- [c3b96c6](benchmark-c3b96c6.json): lần tái hiện commit cũ; q06/q07 thêm số Điều
  sai, q15 thiếu điều kiện 15 tín chỉ và 5,0 theo đối chiếu của Codex.
- [d540993](benchmark-d540993.json): nội dung đạt trong lần benchmark, nhưng
  [integration tiếp theo](integration-d540993-retry.xml) tái hiện q15 thiếu 5,0
  với cùng context. Giữ nguyên thất bại; không dùng làm qualification cuối.
- [8b71494](benchmark-8b71494.json): runtime cuối trong phạm vi local; xem
  [đối chiếu từng câu](semantic-review.md) và [rubric](semantic-rubric.md).
- [Legacy](local-benchmark-2026-10-13.json): đã loại khỏi qualification do thiếu
  commit/excerpt. Chỉ giữ trạng thái và q15=fail ở bản công khai.

q12 giữ gold PDF 4/trang in 2; câu trả lời dùng nguồn eUTC tại PDF 84/trang in 82.
Nội dung có thể được nguồn hỗ trợ dù trượt page proxy. Không đổi gold hoặc sửa
metric để biến page proxy thành đánh giá ngữ nghĩa.

Sau sửa runtime, q15 từng qua ba lần chẩn đoán liên tiếp (gồm tải lại model), rồi
qua [integration với Ollama](integration-8b71494.xml). Các lần chẩn đoán không cộng
vào benchmark và không chứng minh độ ổn định tổng quát. [Offline JUnit](offline-8b71494.xml)
là kết quả local lịch sử, không phải số test của remediation CI hiện tại.

[HTTP smoke](http-smoke-8b71494.json) giữ kết quả lifecycle: start port thứ hai bị
từ chối và không ghi đè PID, stop hết listener, restart sẵn sàng; kiểm tra health,
readiness, tài liệu API, input, Origin và giới hạn body; q15 có nguồn qua hai trang,
q24 từ chối. Trạng thái service trong một smoke không chứng minh service vẫn đang
chạy tại thời điểm người đọc báo cáo.

Các JSON hiện là bản công khai tối thiểu; response đầy đủ, excerpt và metadata máy
được giữ trong audit cục bộ. Xem [chính sách công bố và lệnh verifier](evidence-policy.md).
Wheel/sdist không chứa evidence. Hash mới của public summary và hash raw cũ được
ghi riêng trong [manifest](evidence-manifest.json).

## Xử lý review hiện tại

| Phản hồi | Phân loại | Xử lý |
| --- | --- | --- |
| P2: metadata local, excerpt trong evidence và sdist | Sửa | Xuất bản allowlist tối thiểu, giữ raw trong thư mục Git bỏ qua; loại qualification khỏi distribution |
| P2: CI chưa kiểm chứng evidence | Sửa | Verifier offline kiểm tra schema/SHA/metric/provenance/runtime/report; kiểm tra archive trong bốn matrix jobs |
| P2/P3: packaging chỉ chặn đường dẫn quen thuộc | Sửa | Allowlist từng file với metadata ngoại lệ rõ ràng; regression tái hiện file lạ trong package/test/metadata lọt qua gate cũ và bị gate mới từ chối |
| P3: full history ở bốn matrix jobs | Giữ trade-off | Giữ nguyên để xác minh audit/provenance trên từng OS/Python; chấp nhận chi phí checkout |
| P2: verdict chưa độc lập | Follow-up có giới hạn | Ghi rõ cùng Codex, `independent=false`; gate blind + đánh giá độc lập + lặp q15 trước tuyên bố rộng hơn |
| P3: JSON lớn, khó review | Sửa | Bỏ text/context/dependency dump; summary tự sinh, tách hash raw/public |

Những lỗi runtime trong review trước đã được sửa tại `0589a78`, `21da6bf`,
`e0b0af5`, `f34385f`, `4ca81bf` và `8b71494`. Các thay đổi gồm nhãn proxy,
liên kết đoạn tiếp trang, citation bao phủ điều kiện, PID guard, đường dẫn
ingestion và opt-in remote Ollama. Lịch sử chi tiết vẫn ở các commit đó.

## Giới hạn

Đây là bằng chứng phát triển bởi cùng agent, không phải phê duyệt nghiệp vụ UTC
hay đánh giá độc lập trên câu hỏi chưa thấy. Kết quả trên câu hỏi đã biết không
chứng minh độ đúng tổng quát; model vẫn có thể bỏ sót điều kiện như lịch sử q15.
Gate blind/độc lập/lặp lại còn mở, tách khỏi phạm vi demo local.

Chỉ áp dụng với model/digest/cấu hình đã ghi trong artifact. Không dùng kết quả
này cho LAN/Internet, nhiều worker, Chroma HTTP server hoặc remote Ollama.
Dependency audit có bốn ngoại lệ Chroma server cho embedded mode; xem
[security](../security.md). Thời gian benchmark/smoke không phải p95 hoặc load
test. Đổi model, tài liệu hoặc runtime phải chạy qualification mới.
