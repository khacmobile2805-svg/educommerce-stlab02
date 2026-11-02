"""Test của chính framework: runner không bao giờ được che giấu vấn đề."""
import copy

import pytest

import test_runner as tr

DONG_HOP_LE = {"test_case_id": "T-1", "requirement_id": "REQ-09", "condition_id": "C", "scenario_id": "S", "title": "t",
               "priority": "P1", "precondition": "", "fixture_key": "500k", "input_json": '{"op":"ship","area":"inner"}',
               "expected_type": "value", "expected_json": '{"shipping_fee":"0"}', "evidence_reference": ""}


def chay(**thay_doi):
    row = copy.deepcopy(DONG_HOP_LE); row.update(thay_doi)
    return tr.execute_case(row)


def test_dong_hop_le_pass():
    assert chay()["execution_status"] == "PASS"


def test_expected_sai_phai_la_fail_khong_phai_pass():
    r = chay(expected_json='{"shipping_fee":"30000"}')
    assert r["execution_status"] == "FAIL" and "shipping_fee" in r["mismatch"]


@pytest.mark.parametrize("thay_doi,ly_do", [
    ({"fixture_key": "999k"}, "UNKNOWN_FIXTURE"),
    ({"input_json": "{oops"}, "BAD_JSON"),
    ({"input_json": '{"op":"refund"}'}, "UNKNOWN_OP"),
])
def test_du_lieu_hong_thanh_blocked_kem_ly_do_khong_bi_bo_qua(thay_doi, ly_do):
    r = chay(**thay_doi)
    assert r["execution_status"] == "BLOCKED" and ly_do in r["error_message"]


def test_khoa_expected_khong_co_trong_actual_la_fail():
    assert chay(expected_json='{"no_such_key":"x"}')["execution_status"] == "FAIL"


def test_id_trung_bi_tu_choi(tmp_path):
    import csv
    p = tmp_path / "dup.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(DONG_HOP_LE)); w.writeheader(); w.writerows([DONG_HOP_LE, DONG_HOP_LE])
    with pytest.raises(ValueError, match="DUPLICATE_TEST_IDS"):
        tr.load_cases(p)


def test_thieu_cot_bat_buoc_bi_tu_choi(tmp_path):
    p = tmp_path / "bad.csv"; p.write_text("test_case_id\nT-1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="MISSING_COLUMNS"):
        tr.load_cases(p)
