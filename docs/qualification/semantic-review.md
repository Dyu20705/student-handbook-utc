# PR #1 — đối chiếu ngữ nghĩa sau review

Người đối chiếu: Codex, cùng agent tham gia sửa và kiểm chứng runtime;
**đánh giá phát triển, không độc lập (`independent=false`)**. Đã đọc từng câu
với PDF K67 và rubric, không dùng keyword/page proxy làm verdict ngữ nghĩa.
Không phải phê duyệt nghiệp vụ UTC hoặc đánh giá trên câu hỏi blind.

Bảng dưới giữ nguyên verdict lịch sử của ba lần chạy. [Summary được CI kiểm tra](evidence-summary.md)
ghi tổng hợp verdict và SHA-256 **public/raw riêng biệt**. [Manifest](evidence-manifest.json)
gắn từng file với commit audit; response và excerpt đầy đủ nằm trong audit theo
[chính sách công bố](evidence-policy.md). JSON công khai hiện là summary schema v2,
không phải output máy nguyên byte. Output gốc có `semantic_verdict: not_reviewed`;
verdict đọc tay vẫn tách biệt với proxy tự động.

Lần [c3b96c6](benchmark-c3b96c6.json) không đạt q06, q07 và q15. Lần
[d540993](benchmark-d540993.json) đạt nội dung trong benchmark đó, nhưng
[integration tiếp theo](integration-d540993-retry.xml) tái hiện q15 thiếu 5,0;
không dùng làm qualification cuối. Lần [8b71494](benchmark-8b71494.json) được
Codex đọc lại ngày 2026-10-14 theo [rubric](semantic-rubric.md), verdict chỉ áp dụng
cho những cặp câu hỏi/câu trả lời đã quan sát. Một lần đạt không chứng minh ổn định.

| Câu | Kiểm tra bắt buộc | c3b96c6 | d540993 | 8b71494 | PDF |
| --- | --- | --- | --- | --- | --- |
| q01 | URL utc.edu.vn đúng | Đạt | Đạt | Đạt | 8 |
| q02 | URL qldt.utc.edu.vn đúng | Đạt | Đạt | Đạt | 8 |
| q03 | Fanpage dhgtvtcaugiay đúng | Đạt | Đạt | Đạt | 8 |
| q04 | Đủ 3 khu và đủ 3 địa chỉ khác nhau | Đạt | Đạt | Đạt | 71 |
| q05 | Nhỏ hơn 1,0 thì F; không đổi dấu so sánh | Đạt | Đạt | Đạt | 20 |
| q06 | F=0, F+=0,5; không thêm số Điều sai | Không đạt: thêm Điều 2 | Đạt | Đạt | 20, 22 |
| q07 | A+=9,5–10/4,0; không thêm số Điều sai | Không đạt: thêm Điều 4 | Đạt | Đạt | 20 |
| q08 | Năm 1985 đổi tên thành Đại học GTVT | Đạt | Đạt | Đạt | 7 |
| q09 | Đủ D,D+,C,C+; học đổi chỉ với tự chọn | Đạt | Đạt | Đạt | 21 |
| q10 | Điểm cao nhất, không phải lần cuối | Đạt | Đạt | Đạt | 21 |
| q11 | Cử nhân chính quy bậc 3/B1 | Đạt | Đạt | Đạt | 31 |
| q12 | eUTC; phân biệt bằng chứng bổ sung với gold | Đạt nội dung, trượt page proxy | Đạt nội dung, trượt page proxy | Đạt nội dung, trượt page proxy | 4, 84 |
| q13 | Nhà sách tầng 1/A8 | Đạt | Đạt | Đạt | 71 |
| q14 | Cả tầng 6 và tầng 7/A8 | Đạt | Đạt | Đạt | 71 |
| q15 | Khá; không bị Khiển trách trở lên; >=15 tín chỉ lần đầu trừ NN tăng cường; >=5,0 lần đầu cả GDTC/GDQP; chỉ là điều kiện xét | Không đạt: thiếu 15 tín chỉ và 5,0 | Đạt | Đạt | 45–46 |
| q16 | Từng học kỳ, 10 tháng/năm | Đạt | Đạt | Đạt | 46 |
| q17 | Vẫn được xét như SV khác, không tự động cấp | Đạt | Đạt | Đạt | 46 |
| q18 | Đủ 5 mức và mọi mốc 90/100,80/89,70/79,50/69,<50 | Đạt | Đạt | Đạt | 36 |
| q19 | Khiển trách: không vượt quá Khá | Đạt | Đạt | Đạt | 36 |
| q20 | Cảnh cáo trở lên: không vượt quá Trung bình | Đạt | Đạt | Đạt | 36 |
| q21 | Cả Kỹ sư và chương trình chất lượng cao bậc4/B2 | Đạt | Đạt | Đạt | 31 |
| q22 | Miễn học và điểm10 cho B1, không mọi học phần | Đạt | Đạt | Đạt | 32 |

## Ghi chú đối chiếu

- q06 bản cũ có đúng F=0 và F+=0,5 nhưng gán sai Điều 2 khoản 2; nguồn là khoản 2 Điều 10 (PDF 21–22). q07 gán nhầm số thứ tự bảng 4 thành Điều 4; bảng ở khoản 4 Điều 9 (PDF 20). Bản sửa không còn hai khẳng định đó.
- q15 trong benchmark d540993 đủ các điều kiện trong rubric; dùng từ được xét, không cam kết tự động cấp học bổng. Tuy vậy, danh sách citation thiếu chunk 183 chứa điều kiện 15 tín chỉ dù chunk này có trong retrieved context; việc dẫn đúng trang 45 chưa chứng minh citation bao phủ mọi ý. Bản cuối yêu cầu và kiểm thử ID của cả chunk 183/184.
- q12: gold vẫn là PDF 4/trang in 2; source trả về là PDF 84/trang in 82 có hướng dẫn eUTC. Nội dung đạt, page proxy không đạt; không đổi gold. q06 của c3b96c6 cũng trượt page proxy vì dẫn PDF 22 thay vì gold PDF 20, nhưng lý do fail ngữ nghĩa là số Điều thêm sai.
- q14 ở d540993 có một nguồn bổ sung PDF 70 mô tả phòng đọc. Ở 8b71494, cả hai citation là chunk 271/272 trang 71, đều chứa trực tiếp vị trí tầng 6 và tầng 7.
- q19/q20 bản cuối trả lời ngắn, giữ đúng không vượt quá Khá/Trung bình. Đối tượng Khiển trách/Cảnh cáo trở lên trong kỳ được xác định bởi câu hỏi và excerpt trang 36; verdict áp dụng cho cặp câu hỏi/câu trả lời, không diễn giải thành quy tắc chung cho mọi sinh viên.
- q15 bản cuối dẫn đủ chunk 181/182/183/184: ngưỡng 15 tín chỉ lần đầu, ngoại lệ ngoại ngữ tăng cường, mức 5,0 cho GDTC/GDQP và học phần tính lần thứ nhất đều hiện diện. Phần phân biệt mức Khá/Giỏi/Xuất sắc dài hơn cần thiết nhưng đúng nguồn.
- q06/q07 bản cuối dẫn PDF 20 và 22, không còn tự gán số Điều; q21 có bằng chứng cho cả Kỹ sư và chương trình chất lượng cao ở trang 31.
- q23–q25 đều từ chối, sources rỗng, không có lỗi vận hành.

Artifact [legacy](local-benchmark-2026-10-13.json) đã gắn q15=fail và bị rút
khỏi qualification. Bản raw được giữ nguyên trong audit; summary công khai không
đăng lại metric chưa đủ provenance.

Gate trước tuyên bố chất lượng rộng hơn: câu hỏi blind chưa dùng để điều chỉnh,
người review độc lập và kiểm thử q15 lặp lại theo kế hoạch định trước. Gate này còn
mở, là follow-up riêng ngoài remediation evidence publishing/CI.
