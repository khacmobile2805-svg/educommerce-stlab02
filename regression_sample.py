"""Regression chéo: chạy bộ 12 case mẫu của thầy (samples/) trên bản sửa ecommerce_app_fixed.py."""
import importlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "samples"))
sys.modules["ecommerce_app"] = importlib.import_module("ecommerce_app_fixed")   # test runner của thầy sẽ import bản sửa
import teacher_test_runner as t
t.run_suite(ROOT / "samples" / "teacher_TestCases.csv", ROOT / "reports_after_fix" / "sample_regression")
