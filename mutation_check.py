"""Mutation check: cài lỗi có chủ đích vào ecommerce_app_fixed.py (đường cơ sở 22/22 PASS) rồi xem bộ test có bắt được không.

Một mutant "killed" khi suite có ít nhất 1 case FAIL. Dùng để chứng minh assertion đủ mạnh:
python mutation_check.py [file_csv_khac_de_so_sanh]
"""
import csv, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MUTANTS = {
    "M1 total quên cộng phí ship":        ("subtotal - discount + shipping)", "subtotal - discount)"),
    "M2 giảm giá sai (5% thay vì 10%)":   ("subtotal * v.percent / D(100)", "subtotal * v.percent / D(200)"),
    "M3 reserve không trừ kho":            ("stock -= line.quantity", "stock -= 0"),
    "M4 ngưỡng ship '>' thay vì '>='":    ("subtotal >= D(500000)", "subtotal > D(500000)"),
    "M5 COD trả trạng thái PAID":          ("return 'PENDING_COD'", "return 'PAID'"),
    "M6 không đánh dấu voucher đã dùng":   ("if voucher: customer.used_codes.add(voucher)", "pass"),
    "M7 bỏ kiểm tra giỏ rỗng":             ("if not cart.lines: raise ValueError('EMPTY_CART')", "pass"),
    "M8 bỏ kiểm tra voucher đã dùng":      ("if code in customer.used_codes: raise ValueError('VOUCHER_USED')", "pass"),
    "M9 bỏ kiểm tra payment declined":     ("if not approved: raise ValueError('PAYMENT_DECLINED')", "pass"),
}

def run(module_dir, csv_path):
    env = dict(os.environ, APP_MODULE="mutant", CASES_CSV=str(csv_path), PYTHONPATH=str(module_dir))
    out = Path(module_dir) / "out"
    subprocess.run([sys.executable, str(ROOT / "test_runner.py"), str(out)], env=env, capture_output=True, text=True, check=True, cwd=module_dir)
    rows = list(csv.DictReader(open(out / "test_execution.csv", encoding="utf-8-sig")))
    return sum(r["execution_status"] != "PASS" for r in rows)

def main(csvs):
    src = (ROOT / "ecommerce_app_fixed.py").read_text(encoding="utf-8")   # đường cơ sở 22/22 PASS
    names = [Path(c).name for c in csvs]
    print(f"{'Mutant':42}" + "".join(f"{n[:22]:>24}" for n in names))
    killed = [0] * len(csvs)
    for label, (old, new) in MUTANTS.items():
        assert old in src, label
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mutant.py").write_text(src.replace(old, new, 1), encoding="utf-8")
            res = [run(d, c) for c in csvs]
        for i, r in enumerate(res): killed[i] += 1 if r > 0 else 0
        print(f"{label:42}" + "".join(f"{('KILLED (%d FAIL)' % r) if r else 'SURVIVED':>24}" for r in res))
    print("-" * 42 + "-" * 24 * len(csvs))
    print(f"{'Mutation score':42}" + "".join(f"{k}/{len(MUTANTS)} = {100*k/len(MUTANTS):.0f}%".rjust(24) for k in killed))
    return killed

if __name__ == "__main__":
    killed = main([str(ROOT / "test_cases.csv")] + sys.argv[1:])
    sys.exit(0 if killed[0] == len(MUTANTS) else 1)    # cổng CI: bộ test chính phải bắt được mọi mutant
