# EduCommerce – Kiểm thử tự động theo requirement

[![tests](https://github.com/khacmobile2805-svg/educommerce-stlab02/actions/workflows/tests.yml/badge.svg?branch=portfolio-v2)](https://github.com/khacmobile2805-svg/educommerce-stlab02/actions/workflows/tests.yml)

Bộ kiểm thử hướng dữ liệu (Python, CSV, pytest) cho một dịch vụ thanh toán chạy trong bộ nhớ, làm cho môn *Kiểm thử phần mềm* (MTH10332, ĐH Khoa học Tự nhiên – ĐHQG-HCM), bài thực hành **STLab02 – Test Case Execution**. Tác giả: Nguyễn Khắc Trọng.

> **Nguồn gốc, nói rõ.** Ứng dụng cần kiểm thử (`ecommerce_app.py`) và các requirement do giảng viên cung cấp; ứng dụng chứa **các lỗi cài sẵn có chủ đích** để thực hành. Lỗi được báo cáo ở đây (`DEF-PMS-001`) cùng nguyên nhân gốc với một lỗi trong bộ mẫu của thầy (thiếu rollback tồn kho khi thanh toán thất bại). Bài làm chỉ ra lỗi này cũng xảy ra với một *nhóm input mới* (phương thức thanh toán không hỗ trợ) mà bộ mẫu chưa phủ. Repo không tuyên bố đây là lỗi tìm thấy trong phần mềm thật.

## Thể hiện được những gì

| Kỹ năng | Bằng chứng |
|---|---|
| Thiết kế test từ requirement | 5 requirement → 13 condition → 13 scenario → 22 test case (15 case negative/boundary), truy vết đầy đủ REQ→COND→TS→TC→RUN |
| Oracle độc lập | Expected lấy từ acceptance criteria, không bao giờ lấy từ output hiện tại của ứng dụng |
| Assertion theo state | Mỗi case kiểm cả giá trị trả về **và** state sau thao tác (số đơn, số charge, thay đổi kho, mã voucher đã dùng) |
| Phân tích lỗi | Truy ra nguyên nhân ở `Checkout.place()`: `reserve()` chạy trước `payments.collect()` và không ai gọi `release()` (hàm `Inventory.release()` có sẵn nhưng là code chết ở bản gốc) |
| Chất lượng của chính bộ test | **Mutation check: bắt được 9/9 lỗi cài sẵn.** Phiên bản đầu của bộ test chỉ bắt 7/9 (chưa assert `total` và `discount` ở nhánh thành công); xem bên dưới |
| Kỷ luật kỹ thuật | Lớp pytest với `xfail(strict=True)` cho lỗi đã biết, JUnit XML, CI GitHub Actions, file patch cho bản sửa |

## Kết quả

| Lần chạy | Kết quả |
|---|---|
| App gốc, `pytest` | 28 passed, **2 xfailed** (hai case phơi bày DEF-PMS-001); đã gồm test của chính framework |
| Bản sửa, `APP_MODULE=ecommerce_app_fixed pytest` | 30 passed |
| 12 case mẫu của thầy trên bản sửa | 7 PASS / 5 FAIL → 9 PASS / 3 FAIL (hai case rollback được sửa; 3 case còn lại là lỗi khác, không liên quan) |
| Độ phủ `ecommerce_app.py` (dòng + nhánh) | 92 % |

### Mutation check

`python mutation_check.py` cài chín lỗi một dòng vào bản sửa (tổng sai, tỷ lệ giảm giá sai, không trừ kho, `>` thay vì `>=`, trạng thái COD sai, voucher không bao giờ được đánh dấu đã dùng, và ba kiểm tra bị gỡ) rồi yêu cầu bộ test phải FAIL với từng lỗi.

```
Điểm mutation:  bộ test hiện tại 9/9 = 100%   |   bộ test đã nộp lần đầu 7/9 = 78%
Mutant sống sót của bộ đầu: M1 (total quên cộng phí ship), M2 (sai tỷ lệ giảm giá)
```

Bài học ghi lại: chỉ assert mã lỗi hoặc số đơn ở nhánh thành công thì lỗi tính toán lọt qua được. Bộ test hiện tại assert `total`, `discount`, `shipping` và mức thay đổi kho chính xác.

## Nguyên tắc thiết kế

- **Oracle độc lập** – test FAIL là một phát hiện; không bao giờ sửa expected để biến FAIL thành PASS.
- **Cô lập** – mỗi case dựng `Checkout`/`Customer`/`Cart` mới.
- **Không bỏ qua âm thầm** – dòng dữ liệu hỏng thành `BLOCKED` kèm lý do (`UNKNOWN_FIXTURE`, `BAD_JSON`, `UNKNOWN_OP`), nên `PASS + FAIL + BLOCKED` luôn bằng số dòng CSV. Có test trong `tests/test_runner_behaviour.py`.
- **Lỗi đã biết luôn hiển thị** – `xfail(strict=True)` làm build thất bại nếu lỗi đã được sửa mà chưa gỡ dấu xfail.

## Cấu trúc thư mục

| Đường dẫn | Mục đích |
|---|---|
| `ecommerce_app.py` | Ứng dụng cần kiểm thử (do thầy cung cấp, không sửa) |
| `ecommerce_app_fixed.py`, `fixes/DEF-PMS-001.patch` | Bản sao đã sửa và cùng thay đổi đó dưới dạng patch để review |
| `test_runner.py` | Đọc CSV, fixture, dispatcher, assertion, PASS/FAIL/BLOCKED, báo cáo CSV/Excel/HTML |
| `test_cases.csv` | 22 test case (precondition, bước thực hiện, input/expected dạng JSON) |
| `tests/` | Lớp pytest và test của chính framework |
| `mutation_check.py`, `docs/mutation_report.txt` | Mutation check và kết quả đã ghi lại |
| `part3_checks.py`, `regression_sample.py` | Script kiểm chứng các tình huống Part 3 và regression trên bộ mẫu của thầy |
| `reports/`, `reports_after_fix/` | Báo cáo sinh ra (CSV, Excel, dashboard HTML, biểu đồ) |
| `STLab02_EduCommerce.ipynb` | Notebook Google Colab chạy lại toàn bộ |
| `samples/` | Runner và dữ liệu mẫu của thầy, để đối chiếu |

## Cách chạy

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest                                                    # 28 passed, 2 xfailed (lỗi đã biết)
APP_MODULE=ecommerce_app_fixed pytest                     # 30 passed
python test_runner.py reports                             # báo cáo CSV/Excel/HTML
python mutation_check.py                                  # điểm mutation
```

## Giới hạn

- Chỉ ở mức service: không có concurrency, không lưu trữ bền vững, không có tầng UI/API.
- Expected cho trường hợp từ chối thanh toán dựa trên cách đọc chéo requirement (quy tắc rollback của REQ-08 áp dụng cho REQ-16); văn bản requirement không nói rõ, nên được ghi nhận là câu hỏi mở chứ không phải sự thật đã chốt.
- Mutation testing dùng chín mutant viết tay, không dùng công cụ tự động (ví dụ `mutmut`).
- Phần sinh báo cáo Excel/HTML trong `test_runner.py` được CI chạy nhưng chưa có unit test (độ phủ của file này khoảng 70 %).
- Thời gian thực thi ở mức micro giây, không có ý nghĩa về hiệu năng; vẫn ghi lại vì đề bài yêu cầu.

## Lịch sử dự án

Trạng thái đã nộp cho giảng viên ngày 02/11/2026 được đánh dấu bằng tag `submitted-2026-11-02` (nhánh `main`). Nhánh `portfolio-v2` này bổ sung các assertion mạnh hơn, lớp pytest, mutation check, file patch và CI. Báo cáo tiếng Việt (PDF) đã nộp riêng.

## Ghi chú về hỗ trợ của AI

Thực hiện với sự hỗ trợ của Claude Code (Anthropic) cho việc thiết kế test, viết runner và tài liệu. Mọi con số trong repo đều tái hiện được bằng các lệnh ở trên.
