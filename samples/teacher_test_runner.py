"""CSV-driven execution, requirement traceability and Excel/HTML reporting."""
# NGUỒN: STLab02 Instruction mục 4.2 (bản mẫu của thầy, 12 case REQ-06/08/11).
# Bài làm của em sẽ mở rộng execute_case() cho các REQ mới -> làm trên bản sao, không đè file này.
from pathlib import Path
import csv, datetime, html, json
from collections import Counter
import pandas as pd
from ecommerce_app import fixture

ROOT = Path(__file__).resolve().parent

def execute_case(row):
    app, user, cart = fixture(row['fixture'])
    op = row['operation']; actual_error = ''; actual = ''; order = None
    before = {k: p.stock for k, p in app.catalog.products.items()}
    try:
        if op == 'voucher':
            order = app.place(user, cart, voucher=row.get('voucher') or None, key=row['case_id'])
            actual = f'{order.discount:.0f}'
        elif op == 'payment_failure':
            app.place(user, cart, method='ONLINE', approved=False, key=row['case_id'])
            actual = 'NO_ERROR'
        elif op == 'payment_success':
            order = app.place(user, cart, method='ONLINE', approved=True, key=row['case_id'])
            actual = order.status
        elif op == 'stock_failure':
            for p in app.catalog.products.values(): p.stock = 0
            app.place(user, cart, key=row['case_id']); actual = 'NO_ERROR'
        elif op == 'retry':
            order = app.place(user, cart, key=row['case_id'])
            app.place(user, cart, key=row['case_id'])
            actual = str(len(app.orders))
        else: raise ValueError('UNKNOWN_TEST_OPERATION')
    except ValueError as exc:
        actual_error = str(exc)
        actual = f'ERROR:{actual_error}'
    after = {k: p.stock for k, p in app.catalog.products.items()}
    expectation = row['expected_value']
    if row['assertion'] == 'equals': passed = actual == expectation
    elif row['assertion'] == 'stock_unchanged':
        actual = 'UNCHANGED' if before == after else 'CHANGED'
        passed = actual == expectation and actual_error == row['expected_error']
    elif row['assertion'] == 'retry_stock_once':
        expected_stock = dict(before)
        for line in cart.lines: expected_stock[line.sku] -= line.quantity
        actual = 'ONCE' if after == expected_stock else 'MULTIPLE'
        passed = actual == expectation and len(app.orders) == 1
    else: raise ValueError('UNKNOWN_ASSERTION')
    return {**row, 'actual_value': actual, 'actual_error': actual_error, 'status': 'PASS' if passed else 'FAIL',
            'observed_before': json.dumps(before), 'observed_after': json.dumps(after),
            'executed_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def run_suite(csv_path=None, out_dir=None):
    csv_path = Path(csv_path or ROOT / 'STLab03_Ecommerce_TestCases.csv')
    output = Path(out_dir or ROOT / 'reports'); output.mkdir(exist_ok=True, parents=True)
    with csv_path.open(newline='', encoding='utf-8-sig') as f: testcases = list(csv.DictReader(f))
    ids = [x['case_id'] for x in testcases]
    if len(ids) != len(set(ids)): raise ValueError('DUPLICATE_TEST_IDS')
    results = [execute_case(x) for x in testcases]
    df = pd.DataFrame(results); summary = df.groupby(['requirement_id', 'status']).size().unstack(fill_value=0).reset_index()
    counts = Counter(df.status)
    totals = pd.DataFrame([{'executed': len(df), 'passed': counts['PASS'], 'failed': counts['FAIL'], 'pass_rate': round(100 * counts['PASS'] / len(df), 1)}])
    df.to_csv(output / 'test_execution.csv', index=False, encoding='utf-8-sig')
    with pd.ExcelWriter(output / 'test_report.xlsx', engine='openpyxl') as xls:
        df.to_excel(xls, index=False, sheet_name='Execution')
        summary.to_excel(xls, index=False, sheet_name='Traceability')
        totals.to_excel(xls, index=False, sheet_name='Summary')
    rows = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(row.get(key, "")))}</td>' for key in ['case_id', 'requirement_id', 'scenario_id', 'expected_value', 'actual_value', 'status']) + '</tr>' for row in results)
    page = '''<!DOCTYPE html><html><head><meta charset="utf-8"><title>EduCommerce Test Report</title><style>body{font:15px Arial;margin:35px;color:#14233c}h1{color:#17385f}table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;padding:9px;text-align:left}th{background:#16385e;color:white}tr:nth-child(even){background:#f1f5f9}.metric{display:inline-block;margin:12px;padding:16px;border-radius:12px;background:#edf3f9;font-size:22px}</style></head><body><h1>EduCommerce – Automated Test Execution</h1>''' + f'<div class="metric">Total: {len(df)}</div><div class="metric">PASS: {counts["PASS"]}</div><div class="metric">FAIL: {counts["FAIL"]}</div><h2>Traceability & Execution</h2><table><tr><th>Case</th><th>Requirement</th><th>Scenario</th><th>Expected</th><th>Actual</th><th>Status</th></tr>{rows}</table></body></html>'
    (output / 'test_dashboard.html').write_text(page, encoding='utf-8')
    print(f'Executed {len(df)} | PASS {counts["PASS"]} | FAIL {counts["FAIL"]}')
    print(df.loc[df.status == 'FAIL', ['case_id', 'expected_value', 'actual_value']].to_string(index=False))
    return df, output

if __name__ == '__main__': run_suite()
