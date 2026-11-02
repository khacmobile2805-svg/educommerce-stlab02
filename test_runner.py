"""STLab02 - CSV-driven test execution for EduCommerce (REQ-07, 09, 10, 14, 16).

Luồng: CSV -> validate schema -> fixture riêng -> dispatcher (op) -> so sánh expected/actual
       -> PASS / FAIL / BLOCKED -> CSV + Excel + HTML dashboard + chart.
ecommerce_app.py là code của thầy, KHÔNG sửa; mọi expected lấy từ acceptance criteria.
"""
import base64, csv, datetime, html, io, json, time
from collections import Counter
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import importlib, os
_app = importlib.import_module(os.environ.get("APP_MODULE", "ecommerce_app"))  # đổi sang ecommerce_app_fixed để regression
Cart, Checkout, Customer, fixture = _app.Cart, _app.Checkout, _app.Customer, _app.fixture

ROOT = Path(__file__).resolve().parent
REQUIRED_COLUMNS = ["test_case_id", "requirement_id", "condition_id", "scenario_id", "title", "priority",
                    "precondition", "fixture_key", "input_json", "expected_type", "expected_json",
                    "evidence_reference"]


class Blocked(Exception):
    """Test không thể chạy (dữ liệu/fixture hỏng) - khác với FAIL của sản phẩm."""


def make_fixture(key):
    """Mỗi case một môi trường mới: (service, customer, cart)."""
    if key == "empty":
        service = Checkout()
        return service, Customer("U_NEW"), Cart(service.catalog)
    if key == "used_save10":
        service, customer, cart = fixture("600k")
        customer.used_codes.add("SAVE10")
        return service, customer, cart
    try:
        return fixture(key)          # 300k, 500k, 499999, 600k, 1000k, 1500k của thầy
    except ValueError as exc:
        raise Blocked(f"UNKNOWN_FIXTURE:{key}") from exc


def stock_of(app):
    return {k: p.stock for k, p in app.catalog.products.items()}


def run_operation(app, user, cart, spec):
    """Dispatcher: gọi hàm nghiệp vụ theo spec['op']. Trả về (order, error_code)."""
    op = spec.get("op")
    try:
        if op == "ship":
            fee = app.shipping.calculate(cart.subtotal(), spec["area"])
            return {"shipping_fee": f"{fee:.0f}"}, ""
        if op in ("place", "place_twice"):
            kwargs = dict(area=spec.get("area", "inner"), voucher=spec.get("voucher"),
                          method=spec.get("method", "COD"), approved=spec.get("approved", True))
            order = app.place(user, cart, key=spec.get("key", "K1"), **kwargs)
            if op == "place_twice":                       # lần 2: khác key, cùng giỏ
                order = app.place(user, cart, key=spec.get("key", "K1") + "-2", **kwargs)
            return order, ""
        raise Blocked(f"UNKNOWN_OP:{op}")
    except ValueError as exc:                             # lỗi nghiệp vụ -> ghi lại để so với expected
        return None, str(exc)


def observe(app, user, order, error, before):
    """Gom actual: giá trị trả về + STATE sau thao tác (stock, orders, charges, used_codes)."""
    obs = {"error": error or "NONE", "orders": len(app.orders), "charges": len(app.payments.charges),
           "stock_unchanged": stock_of(app) == before, "used_codes": sorted(user.used_codes)}
    if isinstance(order, dict):
        obs.update(order)
    elif order is not None:
        obs.update(status=order.status, shipping=f"{order.shipping:.0f}", discount=f"{order.discount:.0f}",
                   total=f"{order.total:.0f}")
    return obs


def execute_case(row):
    started = time.perf_counter()
    result = {**row, "execution_status": "", "actual_result": "", "error_message": "", "mismatch": ""}
    try:
        try:
            spec, expected = json.loads(row["input_json"]), json.loads(row["expected_json"])
        except json.JSONDecodeError as exc:
            raise Blocked(f"BAD_JSON:{exc.msg}") from exc
        app, user, cart = make_fixture(row["fixture_key"])          # fixture mới cho từng case
        before = stock_of(app)
        order, error = run_operation(app, user, cart, spec)
        actual = observe(app, user, order, error, before)
        mismatches = [f"{k}: expected {v!r} but actual {actual.get(k)!r}"
                      for k, v in expected.items() if actual.get(k) != v]
        result["actual_result"] = json.dumps({k: actual.get(k) for k in expected}, ensure_ascii=False)
        result["error_message"] = actual["error"] if actual["error"] != "NONE" else ""
        result["mismatch"] = "; ".join(mismatches)
        result["execution_status"] = "PASS" if not mismatches else "FAIL"
    except Blocked as exc:
        result.update(execution_status="BLOCKED", error_message=str(exc))
    except Exception as exc:                                         # lỗi bất ngờ của app: FAIL, không nuốt
        result.update(execution_status="FAIL", error_message=f"UNEXPECTED:{type(exc).__name__}:{exc}")
    result["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
    result["executed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    return result


def load_cases(csv_path):
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"MISSING_COLUMNS:{missing}")
        rows = list(reader)
    ids = [r["test_case_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_TEST_IDS")
    return rows


def chart_png(df):
    table = df.groupby(["requirement_id", "execution_status"]).size().unstack(fill_value=0)
    for col in ("PASS", "FAIL", "BLOCKED"):
        if col not in table:
            table[col] = 0
    fig, ax = plt.subplots(figsize=(7, 4))
    table[["PASS", "FAIL", "BLOCKED"]].plot(kind="bar", stacked=True, ax=ax,
                                            color=["#16a34a", "#dc2626", "#f59e0b"])
    ax.set_title("EduCommerce - test results by requirement"); ax.set_ylabel("Test cases"); ax.set_xlabel("")
    plt.xticks(rotation=0); fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=130); plt.close(fig)
    return buf.getvalue()


def write_reports(df, out):
    counts = Counter(df.execution_status)
    total = len(df)
    summary = df.groupby(["requirement_id", "execution_status"]).size().unstack(fill_value=0).reset_index()
    totals = pd.DataFrame([{"executed": total, "passed": counts["PASS"], "failed": counts["FAIL"],
                            "blocked": counts["BLOCKED"], "pass_rate_%": round(100 * counts["PASS"] / total, 1),
                            "requirements": df.requirement_id.nunique(), "conditions": df.condition_id.nunique(),
                            "scenarios": df.scenario_id.nunique()}])
    trace = df[["requirement_id", "condition_id", "scenario_id", "test_case_id", "execution_status"]]
    df.to_csv(out / "test_execution.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(out / "test_report.xlsx", engine="openpyxl") as xls:
        df.to_excel(xls, index=False, sheet_name="Execution")
        summary.to_excel(xls, index=False, sheet_name="By requirement")
        trace.to_excel(xls, index=False, sheet_name="Traceability")
        totals.to_excel(xls, index=False, sheet_name="Summary")
    png = chart_png(df)
    (out / "chart_by_requirement.png").write_bytes(png)
    cols = ["test_case_id", "requirement_id", "scenario_id", "expected_json", "actual_result", "execution_status", "duration_ms"]
    rows = "".join("<tr class='" + str(r["execution_status"]) + "'>" +
                   "".join(f"<td>{html.escape(str(r[c]))}</td>" for c in cols) + "</tr>"
                   for _, r in df.iterrows())
    page = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>EduCommerce STLab02 Report</title><style>"
        "body{font:14px Arial;margin:30px;color:#14233c}h1{color:#17385f}.m{display:inline-block;margin:8px;"
        "padding:12px 18px;border-radius:10px;background:#edf3f9;font-size:20px}.row{display:flex;gap:24px;"
        "flex-wrap:wrap;align-items:flex-start}table{border-collapse:collapse;font-size:12px}"
        "td,th{border:1px solid #cbd5e1;padding:6px;text-align:left}th{background:#16385e;color:#fff}"
        "tr.FAIL td{background:#fee2e2}tr.BLOCKED td{background:#fef3c7}</style></head><body>"
        "<h1>EduCommerce - STLab02 automated test execution</h1>"
        f"<div class='m'>Total {total}</div><div class='m'>PASS {counts['PASS']}</div>"
        f"<div class='m'>FAIL {counts['FAIL']}</div><div class='m'>BLOCKED {counts['BLOCKED']}</div>"
        f"<div class='m'>Pass rate {100 * counts['PASS'] / total:.1f}%</div>"
        "<div class='row'><img src='data:image/png;base64," + base64.b64encode(png).decode() + "' width='520'>"
        "<table><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr>" + rows + "</table></div></body></html>")
    (out / "test_dashboard.html").write_text(page, encoding="utf-8")
    return counts


def run_suite(csv_path=None, out_dir=None):
    csv_path = Path(csv_path or ROOT / "test_cases.csv")
    out = Path(out_dir or ROOT / "reports"); out.mkdir(parents=True, exist_ok=True)
    cases = load_cases(csv_path)
    df = pd.DataFrame([execute_case(c) for c in cases])
    counts = write_reports(df, out)
    print(f"Executed {len(df)} | PASS {counts['PASS']} | FAIL {counts['FAIL']} | BLOCKED {counts['BLOCKED']}")
    pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 70)
    print(df[["test_case_id", "requirement_id", "execution_status", "duration_ms", "mismatch"]].to_string(index=False))
    return df, out


if __name__ == "__main__":
    import sys
    run_suite(out_dir=sys.argv[1] if len(sys.argv) > 1 else None)   # python test_runner.py [thư_mục_report]
