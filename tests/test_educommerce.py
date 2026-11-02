"""Lớp pytest cho các test case trong CSV: mỗi dòng CSV là một test pytest.

Lỗi đã biết (DEF-PMS-001) được đánh dấu xfail(strict=True) *chỉ khi* chạy trên ứng dụng gốc.
Nếu ai đó sửa lỗi, xfail nghiêm ngặt sẽ biến thành thất bại ("XPASS") và buộc phải gỡ dấu đánh dấu,
nên một lỗi đã biết không thể bị quên hay bỏ qua âm thầm.

Chạy:  pytest                                  (app gốc: 20 passed, 2 xfailed)
       APP_MODULE=ecommerce_app_fixed pytest   (bản sửa: 22 passed)
"""
import os
from pathlib import Path

import pytest

import test_runner as tr

CASES = tr.load_cases(Path(__file__).resolve().parent.parent / "test_cases.csv")
LOI_DA_BIET = {"TC-PMS-002": "DEF-PMS-001", "TC-PMS-004": "DEF-PMS-001"}
CHAY_TREN_APP_GOC = os.environ.get("APP_MODULE", "ecommerce_app") == "ecommerce_app"


def _params():
    out = []
    for row in CASES:
        defect = LOI_DA_BIET.get(row["test_case_id"])
        marks = ([pytest.mark.xfail(strict=True, reason=f"{defect}: không trả lại tồn kho khi thanh toán bị từ chối")]
                 if defect and CHAY_TREN_APP_GOC else [])
        out.append(pytest.param(row, id=row["test_case_id"], marks=marks))
    return out


@pytest.mark.parametrize("row", _params())
def test_case(row):
    """Chạy một dòng CSV bằng runner; PASS nếu mọi giá trị trong expected_json khớp với actual."""
    result = tr.execute_case(row)
    assert result["execution_status"] == "PASS", result["mismatch"] or result["error_message"]
