# -*- coding: utf-8 -*-
"""
Giao diện dòng lệnh (CLI) cho Lõi xử lý Pharta (UR.F001.02, AC-01).
Cách dùng:
    python -m Core --file <đường_dẫn_csv_hoặc_xlsx> [--iv Cột1] [--dv Cột2] [--paired] [--alpha 0.05]
"""

import argparse
import sys
from Core.engine import PhartaCoreEngine


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pharta Core Engine CLI - Tự động hóa phân tích thống kê Y Dược theo Cây quyết định (Phụ lục A)"
    )
    parser.add_argument("--file", "-f", required=True, help="Đường dẫn tệp dữ liệu (.csv, .xlsx)")
    parser.add_argument("--iv", nargs="*", default=[], help="Danh sách cột biến độc lập (Independent Variables)")
    parser.add_argument("--dv", nargs="*", default=[], help="Danh sách cột biến phụ thuộc / biến chính (Dependent Variables)")
    parser.add_argument("--third-var", default=None, help="Biến rời rạc thứ 3 (phân tầng cho Mantel-Haenszel)")
    parser.add_argument("--paired", action="store_true", help="Dữ liệu bắt cặp (Paired data)")
    parser.add_argument("--proportion", action="store_true", help="Báo cáo dạng tỷ lệ phần trăm (Panel A)")
    parser.add_argument("--pop-var-known", action="store_true", help="Đã biết phương sai quần thể (Z-test)")
    parser.add_argument("--sigma1", type=float, default=1.0, help="Độ lệch chuẩn quần thể σ1 (cho Z-test)")
    parser.add_argument("--mu0", type=float, default=0.0, help="Giá trị trung bình kiểm định μ0 (cho 1-sample t-test/Z-test)")
    parser.add_argument("--p0", type=float, default=0.5, help="Tỷ lệ kiểm định p0 (cho 1-sample Z-test tỷ lệ)")
    parser.add_argument("--alpha", type=float, default=0.05, help="Mức ý nghĩa thống kê α (mặc định: 0.05)")
    parser.add_argument("--format-mode", default="auto", choices=["auto", "preselected", "free", "compare_groups"], help="Chế độ định dạng phân tích")

    args = parser.parse_args()
    df = PhartaCoreEngine.load_file(args.file)
    req = {
        "dataframe": df,
        "independent_vars": args.iv,
        "dependent_vars": args.dv,
        "third_var": args.third_var,
        "paired": args.paired,
        "is_proportion_outcome": args.proportion,
        "pop_variance_known": args.pop_var_known,
        "pop_sigma1": args.sigma1,
        "mu0": args.mu0,
        "p0": args.p0,
        "alpha": args.alpha,
        "format_mode": args.format_mode,
    }
    resp = PhartaCoreEngine.analyze(req)
    sys.stdout.reconfigure(encoding="utf-8")
    print(PhartaCoreEngine.to_json(resp, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
