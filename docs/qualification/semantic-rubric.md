# Đối chiếu ngữ nghĩa — rubric 22 câu

Áp dụng cho `data/benchmark/evaluation_set.json` hiện hành; không sửa gold page sau khi chấm. Đọc cả câu trả lời và đoạn nguồn với trang PDF gốc. Một câu đạt khi trả lời đủ những ý bắt buộc dưới đây, giữ đúng đối tượng/phủ định/ngưỡng số và không thêm khẳng định trái nguồn. Nội dung bổ sung không liên quan trực tiếp không bắt buộc. Citation hợp lệ về ID hoặc trùng gold page không tự chứng minh các ý này.

Đây là kiểm tra nội dung do người/agent đọc, không phải bộ dò keyword mới. Mỗi báo cáo phải ghi ai đối chiếu, SHA-256 artifact và verdict từng câu; không tái sử dụng verdict khi model, code hoặc artifact đổi. Agent review không phải phê duyệt nghiệp vụ của UTC.

| Câu | Ý bắt buộc; điểm dễ sai cần kiểm tra | Trang PDF đối chiếu |
| --- | --- | --- |
| q01 | Website chính thức `utc.edu.vn`; URL đúng, không nhầm cổng QLĐT | 8 |
| q02 | Cổng QLĐT `qldt.utc.edu.vn` | 8 |
| q03 | Fanpage `facebook.com/dhgtvtcaugiay` | 8 |
| q04 | Đủ 3 khu: số 99 Nguyễn Chí Thanh; ngõ số 3 Cầu Giấy; khu lưu trú trong trường số 3 Cầu Giấy | 71 |
| q05 | Điểm thi kết thúc học phần **nhỏ hơn** 1,0 thì không đạt/F; không đổi thành nhỏ hơn hoặc bằng | 20 |
| q06 | F = 0; F+ = 0,5, đúng từng ánh xạ thang 4 | 20, 22 |
| q07 | A+ tương ứng 9,5–10 trên thang 10 (4,0 thang 4) | 20 |
| q08 | Năm 1985 đổi thành Trường Đại học Giao thông vận tải | 7 |
| q09 | D, D+, C, C+ đều được cải thiện; **học đổi chỉ với học phần tự chọn** | 21 |
| q10 | **Điểm cao nhất** của các lần học là điểm chính thức, không phải điểm lần cuối | 21 |
| q11 | Sinh viên chính quy trình độ Cử nhân: bậc 3/B1 | 31 |
| q12 | Tên app eUTC. Gold vẫn là PDF 4/trang in 2; PDF 84/trang in 82 là bằng chứng bổ sung hợp lệ | 4, 84 |
| q13 | Nhà sách ở tầng 1 nhà A8 | 71 |
| q14 | Dịch vụ tìm tin/tài liệu: **cả tầng 6 và tầng 7** nhà A8 | 71 |
| q15 | Chính quy, học tập **và** rèn luyện từ Khá; không bị kỷ luật từ Khiển trách trở lên trong kỳ xét; từ **15 tín chỉ đăng ký lần đầu**, không tính ngoại ngữ tăng cường; kết quả GDTC, GDQP và học phần tính điểm lần thứ nhất **từ 5,0/10**. Đủ điều kiện xét, không bảo đảm tự động nhận vì còn quỹ học bổng | 45–46 |
| q16 | Cấp theo từng học kỳ, **10 tháng/năm học** | 46 |
| q17 | Vẫn **được xét** KKHT như sinh viên khác khi hưởng học bổng chính sách/trợ cấp; không tự động được cấp, không bị loại | 46 |
| q18 | Đủ 5 mức: 90–100 xuất sắc; 80–89 tốt; 70–79 khá; 50–69 trung bình; **dưới 50** yếu | 36 |
| q19 | Khiển trách trong kỳ: **không vượt quá Khá** | 36 |
| q20 | Cảnh cáo **trở lên** trong kỳ: **không vượt quá Trung bình** | 36 |
| q21 | Bậc 4/B2 áp dụng **cả Kỹ sư và chương trình chất lượng cao** | 31 |
| q22 | Bằng Đại học Ngoại ngữ: **miễn học và ghi điểm 10 cho học phần B1**, không khái quát mọi học phần | 32 |

Phân biệt hai đánh giá về nguồn: page proxy chỉ nhận gold gốc; đối chiếu ngữ nghĩa có thể ghi nhận trang khác thật sự hỗ trợ câu trả lời nhưng không sửa điểm proxy. Với q15, gold page 45 chưa bao phủ hết điều kiện; phải đọc tiếp trang 46. Giữ nguyên benchmark để so sánh trước/sau, ghi giới hạn này công khai.
