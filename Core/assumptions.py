# -*- coding: utf-8 -*-
"""
Mô-đun kiểm tra giả định thống kê và tự động phân loại biến cho Lõi xử lý Pharta (Core Engine).
Tuân thủ tuyệt đối UR.F001.02 và UR.NF003: Không phụ thuộc bất kỳ thư viện giao diện (GUI) nào.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats


def clean_series(series: pd.Series) -> pd.Series:
    """Làm sạch chuỗi dữ liệu: loại bỏ khoảng trắng thừa, chuỗi rỗng và NaN."""
    if series is None:
        return pd.Series(dtype=float)
    s = series.dropna()
    if s.dtype == object or pd.api.types.is_string_dtype(s):
        s = s.astype(str).str.strip()
        s = s[~s.isin(["", "nan", "NaN", "None", "null", "NULL"])]
        # Thử ép kiểu số nếu toàn bộ có thể chuyển sang số
        numeric_s = pd.to_numeric(s, errors="coerce")
        if numeric_s.notna().all() and len(s) > 0:
            return numeric_s
    return s


def detect_variable_type(
    df: pd.DataFrame,
    col_name: str,
    discrete_threshold: int = 5
) -> Tuple[str, int, str]:
    """
    Tự động phát hiện kiểu biến (UR.F001.02):
    - 'discrete': Rời rạc / Định tính
    - 'continuous': Liên tục / Định lượng
    Trả về: (kiểu_biến, số_mức_duy_nhất, lý_do_phân_loại)
    """
    if col_name not in df.columns:
        raise ValueError(f"Không tìm thấy cột '{col_name}' trong dữ liệu.")

    s = clean_series(df[col_name])
    if s.empty:
        return "discrete", 0, "Cột rỗng"

    n_unique = int(s.nunique())

    if not pd.api.types.is_numeric_dtype(s):
        return (
            "discrete",
            n_unique,
            f"Biến văn bản/định danh ({n_unique} mức giá trị)"
        )

    # Kiểm tra xem có phải toàn số nguyên với ít giá trị duy nhất không
    is_integer_like = np.all(np.isclose(s.values, np.round(s.values)))
    if n_unique <= discrete_threshold and is_integer_like:
        return (
            "discrete",
            n_unique,
            f"Biến số nguyên có số mức giá trị ít ({n_unique} <= {discrete_threshold})"
        )

    if n_unique <= 2:
        return (
            "discrete",
            n_unique,
            f"Biến nhị phân/ít mức ({n_unique} mức)"
        )

    return (
        "continuous",
        n_unique,
        f"Biến số định lượng liên tục ({n_unique} giá trị khác biệt)"
    )


def test_normality(
    data: Any,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Kiểm định phân phối chuẩn Shapiro-Wilk (hoặc D'Agostino/KS nếu mẫu > 5000).
    Trả về dict chứa: is_normal, statistic, p_value, method, n, message.
    """
    arr = pd.to_numeric(pd.Series(data), errors="coerce").dropna().to_numpy(dtype=float)
    n = len(arr)
    if n < 3:
        return {
            "is_normal": False,
            "statistic": None,
            "p_value": None,
            "method": "Không đủ cỡ mẫu (n < 3)",
            "n": n,
            "message": f"Cỡ mẫu quá nhỏ (n = {n} < 3), mặc định xử lý phi tham số."
        }

    # Nếu phương sai bằng 0 (mọi giá trị giống hệt nhau)
    if np.allclose(arr, arr[0]):
        return {
            "is_normal": False,
            "statistic": 0.0,
            "p_value": 0.0,
            "method": "Shapiro-Wilk",
            "n": n,
            "message": "Dữ liệu hằng số (phương sai = 0), không thỏa phân phối chuẩn."
        }

    if n <= 5000:
        stat, p_val = stats.shapiro(arr)
        method = "Shapiro-Wilk"
    else:
        stat, p_val = stats.normaltest(arr)
        method = "D'Agostino-Pearson"

    stat = float(stat)
    p_val = float(p_val)
    is_normal = bool(p_val > alpha)
    status_str = "Đạt phân phối chuẩn" if is_normal else "Vi phạm phân phối chuẩn"
    return {
        "is_normal": is_normal,
        "statistic": round(stat, 4),
        "p_value": round(p_val, 4),
        "method": method,
        "n": n,
        "message": f"{method}: statistic = {stat:.4f}, p = {p_val:.4f} ({status_str} ở mức α = {alpha})"
    }


def test_homogeneity(
    groups: List[np.ndarray],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Kiểm định tính đồng nhất phương sai Levene (center='median' - Brown-Forsythe / Levene chuẩn).
    """
    clean_groups = [
        pd.to_numeric(pd.Series(g), errors="coerce").dropna().to_numpy(dtype=float)
        for g in groups
    ]
    clean_groups = [g for g in clean_groups if len(g) >= 2]

    if len(clean_groups) < 2:
        return {
            "is_homogeneous": True,
            "statistic": None,
            "p_value": None,
            "method": "Levene",
            "message": "Không đủ nhóm để kiểm định đồng nhất phương sai."
        }

    try:
        stat, p_val = stats.levene(*clean_groups, center="mean")
        stat = float(stat)
        p_val = float(p_val)
        if np.isnan(stat) or np.isnan(p_val):
            return {
                "is_homogeneous": False,
                "statistic": 0.0,
                "p_value": 0.0,
                "method": "Levene",
                "message": "Phương sai nội nhóm bằng 0 hoặc không xác định."
            }
        is_homo = bool(p_val > alpha)
        status_str = "Phương sai đồng nhất" if is_homo else "Phương sai KHÔNG đồng nhất"
        return {
            "is_homogeneous": is_homo,
            "statistic": round(stat, 4),
            "p_value": round(p_val, 4),
            "method": "Levene",
            "message": f"Levene test: F = {stat:.4f}, p = {p_val:.4f} ({status_str} ở mức α = {alpha})"
        }
    except Exception as exc:
        return {
            "is_homogeneous": False,
            "statistic": None,
            "p_value": None,
            "method": "Levene",
            "message": f"Không thể tính Levene test ({exc})."
        }


def check_nd_h_groups(
    groups: Dict[str, np.ndarray],
    alpha: float = 0.05,
    require_homogeneity: bool = True
) -> Dict[str, Any]:
    """
    Kiểm tra đồng thời Phân phối chuẩn (Normal Distribution - ND) trên từng nhóm
    và Tính đồng nhất phương sai (Homogeneity of Variance - H).
    Trả về kết quả tổng hợp ND/H phục vụ rẽ nhánh Panel B & Panel D.
    """
    normality_details = {}
    all_normal = True
    for g_name, g_vals in groups.items():
        res = test_normality(g_vals, alpha=alpha)
        normality_details[str(g_name)] = res
        if not res["is_normal"]:
            all_normal = False

    if require_homogeneity and len(groups) >= 2:
        homo_res = test_homogeneity(list(groups.values()), alpha=alpha)
        is_homo = homo_res["is_homogeneous"]
    else:
        homo_res = {
            "is_homogeneous": True,
            "statistic": None,
            "p_value": None,
            "method": "Không áp dụng",
            "message": "Không yêu cầu kiểm định đồng nhất phương sai giữa các nhóm độc lập."
        }
        is_homo = True

    nd_h_passed = bool(all_normal and is_homo)
    summary_parts = [f"Nhóm '{k}': {v['message']}" for k, v in normality_details.items()]
    if require_homogeneity and len(groups) >= 2:
        summary_parts.append(homo_res["message"])

    return {
        "nd_h_passed": nd_h_passed,
        "all_normal": all_normal,
        "is_homogeneous": is_homo,
        "normality_by_group": normality_details,
        "homogeneity": homo_res,
        "summary": " | ".join(summary_parts)
    }
