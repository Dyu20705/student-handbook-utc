# Chính sách công bố evidence PR #1

Phạm vi là demo/vận hành nội bộ trên máy hiện tại. PR giữ Draft để người dùng
review; chưa công bố production readiness tổng quát. Không thay retrieval,
prompt, model, runtime, metric hoặc gold trong remediation này.

## Bản công khai và bản audit

- JSON schema v2 công khai chỉ chứa ID câu, status, hash câu trả lời, chỉ số keyword
  đã khớp trong gold, thứ tự trang retrieval, ID/trang citation, metric và provenance
  tối thiểu. Không chứa câu trả lời, context PDF, excerpt, đường dẫn tuyệt đối,
  hostname, PID hoặc URL dịch vụ local. Legacy không đủ provenance chỉ giữ trạng
  thái bị loại và verdict q15 thất bại.
- JUnit công khai giữ danh tính test, thời gian, số lượng và outcome. Bỏ hostname,
  timestamp máy, thông báo, traceback và nội dung tham số. Lần integration
  d540993 thất bại vẫn được giữ nguyên outcome.
- Bản gốc nguyên byte và snapshot runtime tương ứng lưu tại
  `data/runtime/evidence-private/`, được Git bỏ qua. Không đưa thư mục này vào
  commit, CI artifacts hoặc gói phát hành. Audit đầy đủ cần quyền truy cập bản gốc.
- **Không đóng gói bất kỳ file `docs/qualification/` nào vào wheel/sdist**, kể cả
  bản tóm tắt. Đây là tài liệu review trong source checkout. Chưa xác lập quyền
  phân phối lại các đoạn PDF trong evidence; vì vậy không công bố lại excerpt
  trong bộ evidence mới. Chính sách này không đánh giá lại quyền của PDF/gold đã
  có trong repository.

Raw evidence từng được công khai ở commit `ef1d506`. Remediation không viết lại
lịch sử Git và không thu hồi bản clone/distribution đã tải xuống. CI cần full
Git history để đọc baseline này **trong bộ nhớ**, kiểm tra phép chuyển đổi và tính
lại metric từ response gốc; không xuất raw ra log, workspace hay artifact. Không
tự động dùng cách công bố raw vào Git này cho lần qualification mới. Nếu cần xóa
khỏi lịch sử hoặc phân phối lại tài liệu, đó là quyết định riêng của chủ repo.

## Phạm vi kiểm tra distribution

Gate dùng danh sách **tên file cụ thể** trong [verifier](../../scripts/evidence.py):
`WHEEL_FILES` cho module/prompt đã duyệt; `SDIST_FILES` thêm các file build,
README/changelog, hai tài liệu vận hành, script và test đã duyệt. File mới phải
được thêm vào allowlist qua code review, không tự nhận từ glob, archive hoặc
`SOURCES.txt`. Do đó `private_snapshot.json` hoặc `.py` trong thư mục package/test
vẫn bị từ chối dù đường dẫn không chứa từ khóa riêng tư.

Ngoại lệ metadata cũng giới hạn theo tên: wheel cho phép `METADATA`, `WHEEL`,
`RECORD`, `entry_points.txt`, `top_level.txt` trong thư mục dist-info đúng version;
sdist cho phép `PKG-INFO`, `setup.cfg` và sáu file egg-info được liệt kê trong
`SDIST_METADATA`. Không cho phép tùy ý thêm file vào thư mục metadata. Chỉ chấp
nhận file thường và thư mục cha cần thiết; từ chối link, member trùng tên hoặc
đường dẫn khác allowlist, không giải nén archive khi kiểm tra.

Gate này kiểm soát file nào được đóng gói, **không quét bí mật trong nội dung các
file đã được phép**, kể cả metadata do build sinh. Review source/metadata vẫn
cần thiết; không dùng CI xanh làm tuyên bố rằng mọi dữ liệu riêng tư đều được
phát hiện. Full-history verification ở cả bốn matrix jobs được giữ nguyên để
đối chiếu audit/provenance, chấp nhận chi phí checkout tăng theo lịch sử repo.

## SHA và provenance

[Manifest](evidence-manifest.json) ghi SHA-256 byte của từng file công khai và
`raw_sha256` riêng của đầu vào audit. [Báo cáo sinh tự động](evidence-summary.md)
hiển thị cả hai; hash raw cũ không được dùng làm hash file công khai mới.

`runtime_sha256_lf` là SHA-256 sau khi thay CRLF bằng LF, bao phủ mọi file Git
trong `src/`, `pyproject.toml`, `uv.lock` và gold. Hash byte runtime nguyên gốc nằm
trong raw artifact. Publisher kiểm tra byte thực thi khớp hash raw và nội dung
chuẩn hóa khớp commit được kiểm thử trước khi xuất bản. Cách này xử lý cả file
Windows có line ending trộn; không sửa runtime chỉ để đổi line ending. Snapshot
nguyên byte được lưu theo SHA trong private audit. JSON/XML công khai giữ nguyên
byte qua checkout; hash Markdown dùng LF.

## Lệnh tái lập và kiểm tra

Từ source checkout có đầy đủ lịch sử Git, dùng Python 3.11 hoặc 3.12; verifier chỉ
dùng thư viện chuẩn, không cần dependency RAG, Ollama, Chroma đang chạy hoặc GPU:

```powershell
python scripts/evidence.py verify
python scripts/evidence.py verify --raw-dir data/runtime/evidence-private
python scripts/evidence.py publish --raw-dir data/runtime/evidence-private
uv build
python scripts/evidence.py verify --dist dist
```

`publish` chỉ tái xuất bộ evidence cố định của PR #1 từ audit baseline; không chạy
model, không cập nhật verdict hay tự duyệt một lần qualification mới. Nó từ chối
ghi đè raw khác hash hoặc công bố khi không chứng minh được hash byte runtime.
Sau khi thay tài liệu, chạy publish để cập nhật hash báo cáo và summary.
Fresh clone có thể chạy `verify` ngay; `publish` cần snapshot private đã lưu nếu
line ending byte gốc không thể tái tạo từ Git. Không bỏ qua bước chứng minh hash
để xuất lại artifact trên máy khác.

Verifier kiểm tra schema bằng cách tái tạo chính xác allowlist và đối chiếu byte,
SHA từng artifact, commit ancestry, inventory/hash runtime, source PDF, phép tính
lại Hit@k/MRR/keyword/page/refusal/error, số test XML, liên kết và hash báo cáo,
verdict từng câu và bảng tổng hợp sinh tự động. HEAD và working tree phải giữ
nguyên nội dung runtime đã kiểm chứng. Lịch sử thiếu hoặc runtime thay đổi sẽ fail
và cần qualification mới, không bỏ qua kiểm tra. CI chạy kiểm tra này trong bốn
jobs Windows/Linux × Python 3.11/3.12; dependency audit là job thứ năm.

CI xác nhận **tính nhất quán của evidence đã ghi**, không xác thực máy từng chạy
model hay chạy lại integration. Tính lại keyword từ raw giúp phát hiện drift của
proxy, không chứng minh câu trả lời đầy đủ. Hash không phải chữ ký của một người
đánh giá độc lập. Thay lời nhận xét trong Markdown vẫn cần người review nội dung;
CI kiểm tra bảng verdict, tham chiếu và bản hash tương ứng.

## Gate chất lượng còn mở

Verdict của Codex là bằng chứng phát triển do cùng agent tham gia sửa và kiểm
chứng, `independent=false`. Trước khi tuyên bố chất lượng rộng hơn cần tập câu hỏi
blind chưa dùng để điều chỉnh hệ thống, người đánh giá độc lập và kiểm tra q15
lặp lại theo kế hoạch đã định trước. Không suy ra độ ổn định từ một lần 22/22.
Gate này là follow-up riêng, không nằm trong remediation evidence/CI hiện tại.
