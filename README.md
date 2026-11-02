# EduCommerce – Requirement-based Test Automation

[![tests](https://github.com/khacmobile2805-svg/educommerce-stlab02/actions/workflows/tests.yml/badge.svg)](https://github.com/khacmobile2805-svg/educommerce-stlab02/actions/workflows/tests.yml)

A small **data-driven test framework** (Python + CSV) built for the *Software Testing* course (MTH10332, VNU-HCM University of Science), lab **STLab02 – Test Case Execution**. It tests an in-memory checkout service ("EduCommerce") against written acceptance criteria and **found a real defect** in it.

Author: Nguyễn Khắc Trọng (23110217).

## Highlights

| | |
|---|---|
| Scope | 5 requirements (promotion, shipping, payment, cart integrity, payment safety) |
| Test design | 13 conditions → 13 scenarios → **22 test cases** (15 negative/boundary), full REQ→COND→TS→TC→RUN traceability |
| Result | 20 PASS / **2 FAIL** / 0 BLOCKED on the original app; **22/22 PASS** after the fix |
| Defect found | `DEF-PMS-001`: a rejected payment method still deducts stock (reservation happens before payment validation, no rollback) |
| Outputs | CSV, Excel (4 sheets), HTML dashboard with chart, runnable Colab notebook |
| CI | GitHub Actions runs the suite and asserts the expected results on every push |

## Design principles

- **Independent oracle.** Expected results come from the acceptance criteria, never from the application's current output. Failing tests are findings, not something to "fix" by editing expectations.
- **State assertions, not only return values.** Each case checks the returned value *and* the state afterwards (orders, charges, stock, used voucher codes). The defect above is invisible if only the error message is checked.
- **Test isolation.** A fresh `Checkout`/`Customer`/`Cart` is built per test case.
- **No silent skips.** Malformed rows become `BLOCKED` with a reason, so `PASS + FAIL + BLOCKED` always equals the number of CSV rows and the pass rate cannot be inflated.
- **Regression built in.** `APP_MODULE=ecommerce_app_fixed` re-runs the same suite against the fixed copy.

## Repository layout

| Path | Purpose |
|---|---|
| `ecommerce_app.py` | Application under test (provided by the instructor, **not modified**) |
| `ecommerce_app_fixed.py` | Copy with the rollback fix, used only for regression |
| `test_runner.py` | CSV reader, fixtures, dispatcher, assertions, PASS/FAIL/BLOCKED, reports |
| `test_cases.csv` | The 22 test cases (preconditions, steps, input and expected as JSON) |
| `reports/` | Results on the original app: CSV, Excel, HTML dashboard, chart |
| `reports_after_fix/` | Results after the fix, plus the instructor's 12 sample cases (`sample_regression/`) |
| `part3_checks.py` | Scripts that verify the Part 3 scenarios (output in `reports/part3_evidence.txt`) |
| `regression_sample.py` | Runs the instructor's sample suite against the fixed copy |
| `STLab02_EduCommerce.ipynb` | Google Colab notebook that reproduces everything |
| `samples/` | Instructor's sample runner and test data (REQ-06, 08, 11), for comparison |

## Run it

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python test_runner.py reports                          # 22 cases: 20 PASS, 2 FAIL (the defect)
APP_MODULE=ecommerce_app_fixed python test_runner.py reports_after_fix   # 22 PASS
```

Or open `STLab02_EduCommerce.ipynb` in Colab and choose *Runtime → Run all*.

## The defect in one paragraph

`Checkout.place()` calls `inventory.reserve()` **before** `payments.collect()`. When the payment step raises (for example `method="WALLET"`), the reserved stock is never released: the call fails with the right error and creates no order, but stock drops from 20 to 17. `TC-PMS-002` and `TC-PMS-004` catch this by asserting that stock is unchanged after a rejection. The fixed copy wraps `collect` in `try/except` and releases the stock before re-raising.

## Notes

- Developed with the assistance of Claude Code (Anthropic) for test design, runner code and documentation; every result in this repository is reproducible with the commands above.
- Full written report (Vietnamese, PDF) was submitted separately to the instructor.
