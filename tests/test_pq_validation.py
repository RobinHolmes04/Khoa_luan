# -*- coding: utf-8 -*-
"""
Bộ kịch bản Kiểm thử Thẩm định Chất lượng Vận hành (Performance Qualification - PQ Test Suite)
theo Mô hình chữ V trong Tài liệu URS Dự án Pharta (Mục 5: AC-01, AC-02, AC-03, AC-04, AC-06).
Chạy hoàn toàn độc lập ở chế độ dòng lệnh (Headless CLI) không cần nạp GUI.
"""

import ast
import os
import sys
import time
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Core.engine import PhartaCoreEngine
from Core.sample_datasets import get_sample_datasets


class TestPhartaURSValidation(unittest.TestCase):
    """Kiểm thử thẩm định tự động theo ma trận truy vết URS Pharta."""

    def test_ac01_architecture_decoupling(self):
        """
        AC-01: Phân tách GUI và Lõi (Decoupling).
        - 0 cuộc gọi thư viện GUI từ Lõi xử lý (Core/).
        - 0 dòng code tính toán thống kê (scipy/numpy) nằm trong mô-đun UI (main.py, giao_dien/chart_widget.py).
        """
        forbidden_gui_modules = {"PySide6", "PyQt5", "PyQt6", "tkinter", "wx"}
        core_dir = ROOT_DIR / "Core"
        for py_file in core_dir.glob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root_mod = alias.name.split(".")[0]
                        self.assertNotIn(
                            root_mod, forbidden_gui_modules,
                            f"Vi phạm AC-01: Tệp Core '{py_file.name}' import thư viện GUI '{root_mod}'"
                        )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    root_mod = node.module.split(".")[0]
                    self.assertNotIn(
                        root_mod, forbidden_gui_modules,
                        f"Vi phạm AC-01: Tệp Core '{py_file.name}' import từ thư viện GUI '{root_mod}'"
                    )

        # Kiểm tra các tệp UI không import scipy hay numpy để tính toán thống kê
        forbidden_math_in_ui = {"scipy", "numpy", "statsmodels"}
        ui_files = [ROOT_DIR / "main.py", ROOT_DIR / "giao_dien" / "chart_widget.py"]
        for ui_file in ui_files:
            tree = ast.parse(ui_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root_mod = alias.name.split(".")[0]
                        self.assertNotIn(
                            root_mod, forbidden_math_in_ui,
                            f"Vi phạm AC-01: Tệp UI '{ui_file.name}' chứa thư viện toán thống kê '{root_mod}'"
                        )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    root_mod = node.module.split(".")[0]
                    self.assertNotIn(
                        root_mod, forbidden_math_in_ui,
                        f"Vi phạm AC-01: Tệp UI '{ui_file.name}' import từ thư viện toán thống kê '{root_mod}'"
                    )

    def test_ac02_appendix_a_full_coverage_and_ac06_output_quality(self):
        """
        AC-02 & AC-06: Độ bao phủ 100% các nhánh phép kiểm Phụ lục A (Panel A, B, C, D)
        và chất lượng đầu ra (Bảng chuẩn APA, câu diễn giải tiếng Việt lâm sàng, thông số biểu đồ).
        """
        samples = get_sample_datasets()
        expected_test_ids = {
            "Panel A: Z-test tỷ lệ (Tỷ lệ khỏi bệnh 2 phác đồ)": "z_test_proportion_2sample",
            "Panel B: Kiểm định t 1 mẫu (Glucose máu so với μ0 = 5.6)": "one_sample_t_test",
            "Panel B: Z-test 2 mẫu (Biết phương sai quần thể σ = 10)": "z_test",
            "Panel B: Kiểm định t 2 mẫu độc lập (Huyết áp - Đạt chuẩn ND/H)": "two_sample_t_test",
            "Panel B: Mann-Whitney U & Median Test (Ngày nằm viện - Không chuẩn)": "mann_whitney_u_test",
            "Panel B: Kiểm định t bắt cặp (Huyết áp Trước & Sau điều trị)": "paired_t_test",
            "Panel B: Wilcoxon & Sign Test (Điểm đau VAS Trước & Sau - Không chuẩn)": "wilcoxon_signed_rank_test",
            "Panel B: One-way ANOVA (Hiệu quả giảm LDL-C theo 3 mức liều)": "one_way_anova",
            "Panel B: Kruskal-Wallis (Nồng độ CRP ở 3 mức độ viêm phổi)": "kruskal_wallis",
            "Panel B: Thiết kế khối ngẫu nhiên hoàn chỉnh RCBD (3 thời điểm bắt cặp)": "randomized_complete_block_design",
            "Panel B: Two-way ANOVA (Phác đồ × Giới tính - Đạt chuẩn ND/H)": "two_way_anova",
            "Panel B: Friedman Two-way ANOVA (2 yếu tố vi phạm ND/H)": "friedman_two_way_anova",
            "Panel C: Yates' Chi-Square (Bảng 2x2 Hút thuốc & COPD, E > 5)": "yates_chi_square",
            "Panel C: Kiểm định chính xác Fisher (Bảng có kỳ vọng <= 5)": "fisher_exact_test",
            "Panel C: Chi-Square độc lập (Bảng 3x2 Nhóm tuổi & Tuân thủ thuốc)": "chi_square_test_of_independence",
            "Panel C: Kiểm định McNemar (Dữ liệu định tính 2x2 bắt cặp)": "mcnemar_test",
            "Panel C: Kiểm định Cochran's Q (Tỷ lệ triệu chứng qua 3 thời điểm bắt cặp)": "cochran_q_test",
            "Panel C: Mantel-Haenszel Chi-Square (Kiểm soát biến thứ 3: Bệnh viện)": "mantel_haenszel_chi_square",
            "Panel D: Tương quan Pearson (Tuổi & Huyết áp - Đạt chuẩn)": "pearson_correlation",
            "Panel D: Tương quan từng phần Partial Correlation (Huyết áp, Cholesterol kiểm soát Tuổi)": "partial_correlation",
            "Panel D: Tương quan hạng Spearman Rho (CRP & Ngày hồi phục - Không chuẩn)": "spearman_rho",
            "Panel D: Hồi quy tuyến tính đơn biến (Dự báo Huyết áp từ Tuổi)": "regression_analysis",
            "Panel D: Hồi quy tuyến tính đa biến (Dự báo Cholesterol từ Tuổi & BMI)": "multiple_regression",
        }

        for name, expected_id in expected_test_ids.items():
            item = samples[name]
            req = {"dataframe": item["df"], **item["config"]}
            resp = PhartaCoreEngine.analyze(req)
            self.assertEqual(resp["status"], "success")
            res = resp["result"]
            self.assertEqual(
                res["test_id"], expected_id,
                f"Nhánh '{name}' kích hoạt sai phép kiểm: nhận '{res['test_id']}', kỳ vọng '{expected_id}'"
            )
            # Kiểm tra AC-06: Câu diễn giải tiếng Việt & Bảng chuẩn APA
            self.assertTrue(len(res.get("interpretation_vi", "")) > 30)
            self.assertIn("ý nghĩa thống kê", res["interpretation_vi"])
            apa = res.get("apa_table", {})
            self.assertTrue(len(apa.get("headers", [])) >= 3)
            self.assertTrue(len(apa.get("rows", [])) >= 1)
            self.assertIn("type", res.get("chart", {}))
            # Kiểm tra cảnh báo tự động phân loại biến khi không truyền var_types (UR.F001.02 NOTE)
            self.assertTrue(any("UR.F001.02" in w for w in resp.get("warnings", [])))

    def test_ac03_accuracy_against_minitab_benchmarks(self):
        """
        AC-03: Độ chính xác tính toán lõi (sai số làm tròn <= 0.001 so với chuẩn Minitab / Scipy chuẩn).
        Kiểm tra trên các bộ dữ liệu thực tế trong thư mục `du_lieu_chay_thu_AI`.
        """
        # 1. Kiểm tra bộ dữ liệu paired_ttest_100_rows.csv
        paired_csv = ROOT_DIR / "du_lieu_chay_thu_AI" / "paired t test" / "paired_ttest_100_rows.csv"
        if paired_csv.exists():
            df_p = PhartaCoreEngine.load_file(str(paired_csv))
            resp_p = PhartaCoreEngine.analyze({
                "dataframe": df_p,
                "dependent_vars": ["Truoc_Can_Thiep", "Sau_Can_Thiep"],
                "paired": True,
            })
            res_p = resp_p["result"]
            self.assertEqual(res_p["test_id"], "paired_t_test")
            # Giá trị chuẩn Minitab trên tập paired_ttest_100_rows.csv (đã làm tròn 1 chữ số thập phân):
            # t = 28.1941, df = 99, p < 0.0001
            self.assertAlmostEqual(res_p["statistic"], 28.1941, delta=0.001)
            self.assertEqual(res_p["df"], 99)
            self.assertAlmostEqual(res_p["p_value"], 0.0, delta=0.001)

        # 2. Kiểm tra bộ dữ liệu ztest_1_mau_data.csv
        z1_csv = ROOT_DIR / "du_lieu_chay_thu_AI" / "z test 1 mau" / "ztest_1_mau_data.csv"
        if z1_csv.exists():
            df_z = PhartaCoreEngine.load_file(str(z1_csv))
            resp_z = PhartaCoreEngine.analyze({
                "dataframe": df_z,
                "dependent_vars": ["KetQua_DieuTri"],
                "is_proportion_outcome": True,
                "p0": 0.5,
            })
            res_z = resp_z["result"]
            self.assertEqual(res_z["test_id"], "z_test_proportion_1sample")
            # Với 68/100 ca = 0.68 so với p0 = 0.50: Z = (0.68 - 0.50) / 0.05 = 3.6000, p = 0.000318
            self.assertAlmostEqual(res_z["statistic"], 3.6000, delta=0.001)
            self.assertAlmostEqual(res_z["p_value"], 0.000318, delta=0.001)

    def test_ac04_performance_under_5_seconds_for_45000_rows(self):
        """
        AC-04: Thời gian thực thi <= 5 giây trên tập dữ liệu lớn (45.000 dòng < 50.000 dòng).
        """
        rng = np.random.default_rng(123)
        n_rows = 45000
        df_large = pd.DataFrame({
            "Nhom": rng.choice(["Nhóm_A", "Nhóm_B"], size=n_rows),
            "Chi_So": rng.normal(loc=120.0, scale=15.0, size=n_rows)
        })
        t0 = time.perf_counter()
        resp = PhartaCoreEngine.analyze({
            "dataframe": df_large,
            "independent_vars": ["Nhom"],
            "dependent_vars": ["Chi_So"],
        })
        elapsed_sec = time.perf_counter() - t0
        self.assertEqual(resp["status"], "success")
        self.assertLessEqual(
            elapsed_sec, 5.0,
            f"Vi phạm AC-04: Thời gian thực thi {elapsed_sec:.2f}s vượt quá ngưỡng 5.0 giây."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
