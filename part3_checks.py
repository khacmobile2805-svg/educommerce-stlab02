"""Kiểm chứng bằng code cho các tình huống Part 3 (STLab02). Chạy: python part3_checks.py
Kết quả mẫu: reports/part3_evidence.txt. Các kiểm tra này là thử nghiệm bổ trợ, không nằm trong 22 case của test_cases.csv."""
import csv, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from ecommerce_app import Shipping, D, fixture
from test_runner import execute_case, load_cases

stock = lambda app: {k: p.stock for k, p in app.catalog.products.items()}

print("3.1 Hai SKU, một SKU thiếu kho (cả hai thứ tự dòng)")
for order in (("A", 2, "B", 100), ("B", 100, "A", 2)):
    app, u, c = fixture("300k"); c.lines.clear(); c.add(order[0], order[1]); c.add(order[2], order[3])
    try: app.place(u, c)
    except ValueError as e: print(f"  {order}: {e}; kho={stock(app)}; orders={len(app.orders)}")

print("3.2 Voucher: declined rồi đặt lại")
app, u, c = fixture("600k")
try: app.place(u, c, voucher="SAVE10", method="ONLINE", approved=False, key="K1")
except ValueError as e: print(f"  lần 1: {e}; used_codes={u.used_codes}")
o = app.place(u, c, voucher="SAVE10", method="ONLINE", approved=True, key="K2")
print(f"  lần 2: {o.status}; discount={o.discount}; used_codes={u.used_codes}; kho={stock(app)}")

print("3.4 Giá đổi giữa add-to-cart và checkout")
app, u, c = fixture("300k"); print(f"  subtotal lúc thêm = {c.subtotal()}")
app.catalog.products["B"].price = D(350000); print(f"  subtotal sau khi đổi giá = {c.subtotal()}")

print("3.5 Cùng SKU nhập hai lần")
app, u, c = fixture("300k"); c.lines.clear(); c.add("A", 2); c.add("A", 3)
print(f"  lines={[(l.sku, l.quantity) for l in c.lines]}; subtotal={c.subtotal()}")
for q in (-1, 2.0):
    try: c.add("A", q)
    except ValueError as e: print(f"  add(A,{q!r}) -> {e}; lines={[(l.sku, l.quantity) for l in c.lines]}")
c.add("A", True); print(f"  add(A,True) được chấp nhận -> lines={[(l.sku, l.quantity) for l in c.lines]}")
c.add("A", 30)
try: app.place(u, c)
except ValueError as e: print(f"  tổng 36 sản phẩm A tại checkout -> {e}")

print("3.6 Shared fixture vs fixture mới")
app, u, c = fixture("600k")
for p in app.catalog.products.values(): p.stock = 0
try: app.place(u, c, method="ONLINE", key="S2")
except ValueError as e: print(f"  case 2 trên fixture DÙNG CHUNG -> {e}")
app2, u2, c2 = fixture("600k"); print(f"  case 2 trên fixture MỚI -> {app2.place(u2, c2, method='ONLINE', key='S2').status}")

print("3.7 Tính đầy đủ dữ liệu: 17 case hợp lệ + 3 dòng lỗi")
rows = load_cases(ROOT / "test_cases.csv")[:17]
bad = [dict(rows[0], test_case_id="TC-BAD-01", fixture_key="999k"),
       dict(rows[0], test_case_id="TC-BAD-02", input_json="{oops"),
       dict(rows[0], test_case_id="TC-BAD-03", input_json='{"op":"refund"}')]
res = [execute_case(r) for r in rows + bad]
print(f"  {len(res)} dòng -> {dict(Counter(r['execution_status'] for r in res))}")
for r in res:
    if r["execution_status"] == "BLOCKED": print(f"  {r['test_case_id']}: {r['error_message']}")

print("3.8 Ngưỡng miễn ship hiện tại (code dùng 500.000, cứng)")
for s in (499999, 500000, 600000, 699999, 700000):
    print(f"  nội thành {s}: phí = {Shipping().calculate(D(s), 'inner')}")
