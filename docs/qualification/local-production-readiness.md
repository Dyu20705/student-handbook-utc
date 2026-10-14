# Kiểm chứng UTC RAG local sau review PR #1

Cập nhật: 2026-10-14 (Asia/Bangkok). Phạm vi: một máy Windows, API loopback, Chroma embedded, một inference đồng thời, PDF K67 có sẵn. PR vẫn Draft để người dùng review. Source Intake không thuộc vòng sửa này.

Runtime cuối được kiểm chứng tại **`8b7149441362540085793001f2f1ea5b2fdb2cbc`**. Commit công bố evidence sau đó chỉ thay đổi tài liệu, đóng gói evidence và quy tắc giữ nguyên byte artifact. Hash từng file runtime trong evidence được đối chiếu lại trước khi push.

## Bằng chứng benchmark

- [Tái hiện đúng commit c3b96c6](benchmark-c3b96c6.json): đủ 25 response, `excerpt` và toàn bộ retrieved context; không thay đổi code checkout được kiểm thử.
- [Lần chạy trung gian d540993](benchmark-d540993.json): giữ nguyên output và kết quả của lần chạy đó. Không dùng làm qualification cuối vì kiểm thử tích hợp sau đó tái hiện q15 thiếu 5,0.
- [Runtime cuối 8b71494](benchmark-8b71494.json): đủ 25 response, `inputs_unchanged_during_run=true`, thời gian 776,41 giây.
- [Đối chiếu ngữ nghĩa từng câu](semantic-review.md), theo [rubric 22 câu](semantic-rubric.md), tách khỏi keyword/page proxies.

| Chỉ số | c3b96c6 tái hiện | d540993 trung gian | 8b71494 cuối |
| --- | --- | --- | --- |
| Hit@1 / Hit@3 / Hit@5 | 59,09% / 95,45% / 95,45% | 59,09% / 95,45% / 95,45% | 59,09% / 95,45% / 95,45% |
| MRR | 0,7652 | 0,7652 | 0,7652 |
| Keyword proxy | 22/22 | 22/22 | 22/22 |
| Citation gold-page proxy | 20/22 | 21/22 | 21/22 |
| Từ chối câu ngoài phạm vi | 3/3 | 3/3 | 3/3 |
| Lỗi vận hành trong benchmark | 0 | 0 | 0 |
| Đối chiếu ngữ nghĩa bởi Codex | 19/22 | 22/22 trong lần benchmark này | 22/22 trong phạm vi các câu hỏi này |

Bản c3b96c6 tái hiện không đạt q06/q07 do tự gán sai số Điều, và q15 do thiếu điều kiện 15 tín chỉ và 5,0. Các bản sửa giữ đoạn tiếp danh sách trang 46 cạnh đoạn cuối trang 45, bỏ heading ước tính khỏi prompt và chỉ dùng nhãn điều khoản có trong văn bản nguồn. Giữ nguyên cách tính retrieval; không đổi gold hoặc chỉnh metric thủ công.

**Kết quả một lần chạy không chứng minh tính ổn định.** Dù benchmark d540993 có đủ 22 câu, [lượt integration sau đó](integration-d540993-retry.xml) cho kết quả 8 passed/1 failed: q15 lại thiếu 5,0 với context giống hệt benchmark. Commit 8b71494 thêm nhãn liên kết danh sách tiếp trang và yêu cầu citation bao phủ các ý trong câu trả lời. Sau sửa, q15 đã qua ba lần kiểm tra chẩn đoán liên tiếp (gồm tải lại model), rồi qua kiểm thử tích hợp; các lần này không được cộng vào metric benchmark.

q12 có gold **PDF 4/trang in 2**; bằng chứng bổ sung ở **PDF 84/trang in 82** có hướng dẫn eUTC. Nội dung được nguồn hỗ trợ vẫn có thể trượt page proxy. q06 của lần tái hiện c3b96c6 dẫn PDF 22 thay vì gold PDF 20, nên trượt page proxy riêng; lý do không đạt ngữ nghĩa là số Điều thêm sai.

Artifact lịch sử [local-benchmark-2026-10-13.json](local-benchmark-2026-10-13.json) không chứng minh HEAD: thiếu SHA và `excerpt`. Đã rút khỏi qualification, gắn q15=fail; mọi metric/output lịch sử được giữ nguyên. Không dùng 22 keyword matches để kết luận 22 câu đúng.

## Provenance và tái lập

Các artifact mới ghi commit sạch, hash các file runtime/lockfile/benchmark, Python và dependency versions, Ollama version, model digest, nguồn PDF, cấu hình, manifest và output đầy đủ. Thời gian UTC trong artifact do máy thực thi ghi tự động; không sửa lại theo ngày cập nhật báo cáo. Các lần chạy c3b96c6/d540993 diễn ra ngày 13/10 UTC; lần cuối vào ngày 14/10 UTC. Bản tái hiện dùng môi trường hiện tại đã ghi rõ, không khẳng định tái tạo được môi trường cũ chưa lưu digest.

- Python 3.12.10; Ollama 0.40.3; Chroma 1.5.9; dependency versions đầy đủ trong JSON.
- Model sinh: `qwen3.5:9b-q4_K_M`, digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`.
- Embedding: `qwen3-embedding:0.6b`, digest `ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d`.
- PDF SHA-256: `2ee1e3970b65cd36d8e6fe2e9e406965c4a20cc32b816a3b199341561dda208a`.
- 324 chunks, 600 ký tự/overlap 100, cosine + BM25, k=5; generation có tối đa 2 đoạn tiếp trang, giữ ID/trang riêng; temperature 0, thinking off, context 8192, output tối đa 768 token.
- `benchmark-c3b96c6.json` SHA-256: `a6ac4d9a1d4165fbd4bb075056052e43163adf0aa8e14cb6bcf128158ea969a1`.
- `benchmark-d540993.json` SHA-256: `9d541fd7859ce22c5f9b8b2c5f7032fb44c1ac2d2e75544be4571ace342e9cd0`.
- `benchmark-8b71494.json` SHA-256: `fcad3aa99e17021b99e2869e20ff54e6a8e054c723e35e717978bf0437d49b56`.

Các JSON evidence được copy nguyên byte từ runtime. `.gitattributes` tắt chuyển line endings riêng cho evidence để hash không đổi khi checkout. Harness từ chối ghi đè artifact và yêu cầu commit trước khi chạy:

```powershell
uv run --locked python scripts/run_qualification.py --output data/runtime/qualification-new-run.json
```

Dùng `--repo <checkout-cua-commit>` để tái hiện commit cũ. Cài đúng lockfile, đặt `RAG_DATA_PATH` và `RAG_CHROMA_DIR` cùng cấu hình, kiểm tra model digest trước khi so sánh. Worktree c3b96c6 dùng cho vòng kiểm chứng đã được archive sau khi lưu output.

## Xử lý phản hồi và kiểm thử

| Phản hồi | Phân loại | Thay đổi/bằng chứng |
| --- | --- | --- |
| P1: artifact không khớp HEAD | Sửa | Chạy đúng c3b96c6 và runtime mới, full responses/excerpts, provenance; đối chiếu hash runtime (`0589a78`, artifact cuối `8b71494`) |
| P1: keyword chấm sai tính đầy đủ | Sửa | Đổi nhãn thành proxy; verdict máy luôn `not_reviewed`; review riêng đủ 22 câu, sửa q15 và lỗi số Điều phát hiện thêm (`0589a78`, `21da6bf`, `8b71494`) |
| P1: ghi đè PID khi đổi port | Sửa | PID guard trước doctor/start, khóa độc quyền start/stop; regression Windows start hai port và start đồng thời (`e0b0af5`) |
| P2: custom ingestion path | Sửa | Export cả `RAG_DATA_PATH`/`RAG_CHROMA_DIR`; flags CLI chỉ áp dụng ingestion và in cảnh báo; test Chroma thật qua các process ingest/doctor/API (`f34385f`) |
| P2: q12/remote Ollama | Sửa | Gold 4/2 được giữ nguyên; loopback mặc định, remote cần `RAG_ALLOW_REMOTE_OLLAMA=1`; tests loopback/LAN/hostname/opt-in (`4ca81bf`, `f34385f`) |
| CI và smoke sau sửa | Đạt | CI đa nền tảng và [smoke 8b71494](http-smoke-8b71494.json) đều pass; hoàn tất 6/6 mục exit checklist |

- [Offline trên Windows](offline-8b71494.xml): **68 passed, 9 integration skipped**.
- [Integration với Ollama thật](integration-8b71494.xml): **9 passed, 68 deselected**, 199,13 giây; gồm q15 đủ điều kiện và ID nguồn cho cả hai đoạn.
- Ruff, PowerShell parse và wheel/sdist: passed. Sdist chứa harness và evidence; không chứa runtime data, cache, virtualenv hoặc `.env`.
- [CI pull_request 8b71494](https://github.com/Dyu20705/student-handbook-utc/actions/runs/38493841522) và [CI push 8b71494](https://github.com/Dyu20705/student-handbook-utc/actions/runs/38493837698): passed, Windows/Linux và Python 3.11/3.12, cùng dependency audit theo ngoại lệ embedded đã công bố.
- Trước lượt integration d540993 nói trên, lần chạy đầu sau khi tiếp tục phiên có 5 failed/4 passed vì Ollama đã dừng. Đã khởi động lại, xác nhận version/digest không đổi rồi mới kiểm thử tiếp; không diễn giải lỗi kết nối thành refusal thành công.
- Smoke API/lifecycle thật: **passed**; [output đầy đủ](http-smoke-8b71494.json), gắn SHA benchmark và kiểm tra runtime/model không đổi. Start 8000 → start 8001 bị từ chối, PID không đổi → stop hết listener → restart sẵn sàng. `/health`, `/ready`, `/docs`, `/openapi.json` trả 200; input/Origin/body limit trả 422/403/413. q15 trả đủ điều kiện và nguồn 183/184 (51,22 giây); q24 từ chối, sources rỗng (5,00 giây), `Cache-Control: no-store`. API được để chạy tại `http://127.0.0.1:8000` sau smoke.

Hoàn tất **6/6 review exit checklist** trong phạm vi vận hành local; chờ người dùng review/merge PR. Commit evidence không thay đổi runtime đã kiểm chứng.

## Giới hạn

Đây là kiểm chứng kỹ thuật và đối chiếu nội dung bởi agent, không phải phê duyệt nghiệp vụ UTC hay đánh giá độc lập trên câu hỏi chưa thấy. 22 câu không chứng minh 100% độ đúng tổng quát. Model vẫn có thể bỏ sót điều kiện; kiểm thử lặp giảm rủi ro đã quan sát, không bảo đảm mọi lần sinh đều giống nhau. Xem ghi chú từng trường hợp trong báo cáo ngữ nghĩa.

Chỉ áp dụng local với model/digest/cấu hình đã ghi. Không dùng kết quả này cho LAN/Internet, nhiều worker, Chroma HTTP server hoặc remote Ollama. Dependency audit vẫn có bốn ngoại lệ Chroma server cho embedded mode; xem [security](../security.md). Máy chạy model trên CPU; thời gian benchmark/smoke không phải p95 hay load test. Chạy lại qualification khi đổi model, tài liệu hoặc runtime.
