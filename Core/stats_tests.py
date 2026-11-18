# -*- coding: utf-8 -*-
"""
Mô-đun thực thi toàn bộ các phép kiểm định thống kê theo Phụ lục A (Panel A, B, C, D).
Đảm bảo độ chính xác trùng khớp chuẩn quốc tế (Minitab/SPSS/R) với sai số <= 0.001 (UR.NF001, AC-03).
Không phụ thuộc bất kỳ thư viện giao diện đồ họa nào (UR.NF003, AC-01).
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats


def _fmt_p(p: float) -> str:
    """Định dạng giá trị p-value theo chuẩn báo cáo quốc tế APA."""
    if p is None or np.isnan(p):
        return "N/A"
    if p < 0.001:
        return "< 0.001"
    return f"{p:.4f}"


def _fmt_num(x: Optional[float], digits: int = 4) -> str:
    if x is None or (isinstance(x, (float, np.floating)) and np.isnan(x)):
        return "N/A"
    return f"{float(x):.{digits}f}"


def _summary_desc_continuous(arr: np.ndarray) -> Dict[str, float]:
    """Tính các chỉ số thống kê mô tả cho biến liên tục."""
    arr = np.asarray(arr, dtype=float)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    if n == 0:
        return {"n": 0, "mean": np.nan, "sd": np.nan, "median": np.nan, "iqr": np.nan, "q25": np.nan, "q75": np.nan}
    mean = float(np.mean(arr))
    sd = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    median = float(np.median(arr))
    q25, q75 = np.percentile(arr, [25, 75])
    iqr = float(q75 - q25)
    return {
        "n": int(n),
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "median": round(median, 4),
        "iqr": round(iqr, 4),
        "q25": round(float(q25), 4),
        "q75": round(float(q75), 4),
        "min": round(float(np.min(arr)), 4),
        "max": round(float(np.max(arr)), 4),
    }


def _build_boxplot_spec(title: str, x_label: str, y_label: str, groups: Dict[str, Any]) -> Dict[str, Any]:
    """Tạo cấu trúc thông số biểu đồ Boxplot từ Lõi xử lý (UR.F003.03) để GUI chỉ việc vẽ."""
    box_stats = {}
    serial_groups = {}
    for k, v in groups.items():
        arr = np.asarray(v, dtype=float)
        arr = arr[~np.isnan(arr)]
        serial_groups[str(k)] = arr.tolist()
        box_stats[str(k)] = _summary_desc_continuous(arr)
    return {
        "type": "boxplot",
        "title": title,
        "x_label": x_label,
        "y_label": y_label,
        "groups": serial_groups,
        "box_stats": box_stats,
    }


# ==============================================================================
# PANEL A: KIỂM ĐỊNH TỶ LỆ (Z-TEST OF PROPORTIONS)
# ==============================================================================

def run_z_test_proportions(
    df: pd.DataFrame,
    iv_col: str,
    dv_col: Optional[str] = None,
    p0: float = 0.5,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Z-test tỷ lệ (1 mẫu hoặc 2 mẫu độc lập) - Panel A (UR.F002.01).
    - Nếu chỉ có 1 biến nhị phân hoặc 1 nhóm: Kiểm định Z tỷ lệ 1 mẫu so với p0.
    - Nếu có biến độc lập 2 mức và biến phụ thuộc nhị phân: Kiểm định Z tỷ lệ 2 mẫu.
    """
    if dv_col is None or dv_col == iv_col or df[iv_col].dropna().nunique() == 1:
        target_col = dv_col if (dv_col and dv_col in df.columns) else iv_col
        s = df[target_col].dropna()
        vals = s.unique()
        if len(vals) == 0:
            raise ValueError("Không có dữ liệu hợp lệ để kiểm định tỷ lệ.")
        # Chọn giá trị sự kiện dương tính (ưu tiên 1, '1', 'Có', 'Thành công', hoặc giá trị đầu tiên)
        preferred = [1, 1.0, "1", "Có", "Co", "Yes", "Thành công", "Positive", True]
        pos_val = next((v for v in preferred if v in vals), vals[0])
        k = int((s == pos_val).sum())
        n = int(len(s))
        p_hat = k / n
        se = np.sqrt(p0 * (1.0 - p0) / n)
        z_stat = (p_hat - p0) / se if se > 0 else 0.0
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        z_crit = stats.norm.ppf(1.0 - alpha / 2.0)
        se_ci = np.sqrt(p_hat * (1.0 - p_hat) / n)
        ci_low = max(0.0, p_hat - z_crit * se_ci)
        ci_high = min(1.0, p_hat + z_crit * se_ci)

        sig = p_val < alpha
        interp = (
            f"Kiểm định Z tỷ lệ một mẫu trên biến '{target_col}' (biến cố '{pos_val}': {k}/{n} = {p_hat*100:.2f}%) "
            f"so với tỷ lệ kiểm định p₀ = {p0*100:.2f}% cho thấy {'CÓ' if sig else 'KHÔNG CÓ'} sự khác biệt "
            f"có ý nghĩa thống kê ở mức α = {alpha} (Z = {z_stat:.4f}, p = {_fmt_p(p_val)}, "
            f"KTC {int((1-alpha)*100)}%: [{ci_low*100:.2f}%, {ci_high*100:.2f}%])."
        )
        apa_headers = ["Biến số", "Biến cố", "n", "Số ca (k)", "Tỷ lệ (%)", f"KTC {int((1-alpha)*100)}%", "Z", "p"]
        apa_rows = [[
            str(target_col), str(pos_val), str(n), str(k), f"{p_hat*100:.2f}%",
            f"[{ci_low*100:.2f}%, {ci_high*100:.2f}%]", f"{z_stat:.4f}", _fmt_p(p_val)
        ]]
        chart_data = {
            "type": "bar",
            "title": f"Tỷ lệ biến cố '{pos_val}' ({target_col})",
            "x_label": str(target_col),
            "y_label": "Tỷ lệ (%)",
            "categories": [f"Quan sát ({pos_val})", "Giả thuyết (p₀)"],
            "values": [round(p_hat * 100, 2), round(p0 * 100, 2)]
        }
        return {
            "test_id": "z_test_proportion_1sample",
            "test_name_vi": "Kiểm định Z tỷ lệ (1 mẫu)",
            "test_name_en": "One-Proportion Z-Test",
            "panel": "Panel A",
            "statistic_name": "Z",
            "statistic": round(float(z_stat), 4),
            "df": None,
            "p_value": round(p_val, 6),
            "ci": [round(float(ci_low), 4), round(float(ci_high), 4)],
            "significant": bool(sig),
            "alpha": alpha,
            "interpretation_vi": interp,
            "apa_table": {"headers": apa_headers, "rows": apa_rows},
            "chart": chart_data,
        }
    else:
        # 2 mẫu tỷ lệ độc lập
        sub = df[[iv_col, dv_col]].dropna()
        groups = list(sub[iv_col].unique())
        if len(groups) != 2:
            raise ValueError(f"Z-test tỷ lệ 2 mẫu yêu cầu biến độc lập có 2 mức (hiện có {len(groups)} mức).")
        outcomes = list(sub[dv_col].unique())
        preferred = [1, 1.0, "1", "Có", "Co", "Yes", "Thành công", "Positive", True]
        pos_val = next((v for v in preferred if v in outcomes), outcomes[0])

        g1 = sub[sub[iv_col] == groups[0]][dv_col]
        g2 = sub[sub[iv_col] == groups[1]][dv_col]
        n1, n2 = len(g1), len(g2)
        k1, k2 = int((g1 == pos_val).sum()), int((g2 == pos_val).sum())
        p1, p2 = k1 / n1, k2 / n2
        p_pool = (k1 + k2) / (n1 + n2)
        se_pool = np.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n1 + 1.0 / n2))
        z_stat = (p1 - p2) / se_pool if se_pool > 0 else 0.0
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))

        se_unpool = np.sqrt(p1 * (1.0 - p1) / n1 + p2 * (1.0 - p2) / n2)
        z_crit = stats.norm.ppf(1.0 - alpha / 2.0)
        diff = p1 - p2
        ci_low = diff - z_crit * se_unpool
        ci_high = diff + z_crit * se_unpool

        sig = p_val < alpha
        interp = (
            f"Kiểm định Z hai tỷ lệ độc lập về biến cố '{dv_col} = {pos_val}' giữa nhóm '{groups[0]}' "
            f"({k1}/{n1} = {p1*100:.2f}%) và nhóm '{groups[1]}' ({k2}/{n2} = {p2*100:.2f}%) cho thấy "
            f"sự khác biệt tỷ lệ ({diff*100:+.2f}%) {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
            f"(Z = {z_stat:.4f}, p = {_fmt_p(p_val)}, KTC {int((1-alpha)*100)}% hiệu tỷ lệ: [{ci_low*100:.2f}%, {ci_high*100:.2f}%])."
        )
        apa_headers = ["Nhóm", "n", f"Số ca ({pos_val})", "Tỷ lệ (%)", "Hiệu tỷ lệ (%)", "Z", "p"]
        apa_rows = [
            [str(groups[0]), str(n1), str(k1), f"{p1*100:.2f}%", f"{diff*100:+.2f}%", f"{z_stat:.4f}", _fmt_p(p_val)],
            [str(groups[1]), str(n2), str(k2), f"{p2*100:.2f}%", "", "", ""]
        ]
        chart_data = {
            "type": "bar",
            "title": f"So sánh tỷ lệ '{pos_val}' của {dv_col} theo {iv_col}",
            "x_label": str(iv_col),
            "y_label": "Tỷ lệ (%)",
            "categories": [str(groups[0]), str(groups[1])],
            "values": [round(p1 * 100, 2), round(p2 * 100, 2)]
        }
        return {
            "test_id": "z_test_proportion_2sample",
            "test_name_vi": "Kiểm định Z tỷ lệ (2 mẫu độc lập)",
            "test_name_en": "Two-Proportion Z-Test",
            "panel": "Panel A",
            "statistic_name": "Z",
            "statistic": round(float(z_stat), 4),
            "df": None,
            "p_value": round(p_val, 6),
            "ci": [round(float(ci_low), 4), round(float(ci_high), 4)],
            "significant": bool(sig),
            "alpha": alpha,
            "interpretation_vi": interp,
            "apa_table": {"headers": apa_headers, "rows": apa_rows},
            "chart": chart_data,
        }


# ==============================================================================
# PANEL B: BIẾN ĐỘC LẬP RỜI RẠC - BIẾN PHỤ THUỘC LIÊN TỤC
# ==============================================================================

def run_one_sample_t_test(
    arr: np.ndarray,
    var_name: str,
    mu0: float = 0.0,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Kiểm định t một mẫu (One-Sample t-test & Confidence Interval) - Panel B (UR.F002.02)."""
    arr = pd.to_numeric(pd.Series(arr), errors="coerce").dropna().to_numpy(dtype=float)
    n = len(arr)
    if n < 2:
        raise ValueError("Cỡ mẫu phải >= 2 để thực hiện kiểm định t một mẫu.")
    desc = _summary_desc_continuous(arr)
    res = stats.ttest_1samp(arr, popmean=mu0)
    t_stat = float(res.statistic)
    p_val = float(res.pvalue)
    df_val = n - 1
    se = desc["sd"] / np.sqrt(n)
    t_crit = stats.t.ppf(1.0 - alpha / 2.0, df=df_val)
    ci_low = desc["mean"] - t_crit * se
    ci_high = desc["mean"] + t_crit * se

    sig = p_val < alpha
    interp = (
        f"Kiểm định t một mẫu trên biến '{var_name}' (Trung bình = {desc['mean']:.4f}, SD = {desc['sd']:.4f}, n = {n}) "
        f"so với giá trị kiểm định μ₀ = {mu0:.4f} cho thấy sự khác biệt {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê "
        f"ở mức α = {alpha} (t({df_val}) = {t_stat:.4f}, p = {_fmt_p(p_val)}, "
        f"KTC {int((1-alpha)*100)}% của trung bình: [{ci_low:.4f}, {ci_high:.4f}])."
    )
    apa_headers = ["Biến số", "n", "Trung bình (M)", "Độ lệch chuẩn (SD)", f"KTC {int((1-alpha)*100)}%", "Giá trị μ₀", "t", "df", "p"]
    apa_rows = [[
        str(var_name), str(n), f"{desc['mean']:.4f}", f"{desc['sd']:.4f}",
        f"[{ci_low:.4f}, {ci_high:.4f}]", f"{mu0:.4f}", f"{t_stat:.4f}", str(df_val), _fmt_p(p_val)
    ]]
    chart_data = {
        "type": "boxplot",
        "title": f"Phân bố của {var_name} (μ₀ = {mu0})",
        "x_label": "Mẫu nghiên cứu",
        "y_label": str(var_name),
        "groups": {str(var_name): arr.tolist()}
    }
    return {
        "test_id": "one_sample_t_test",
        "test_name_vi": "Kiểm định t một mẫu (One-Sample t-test)",
        "test_name_en": "One-Sample t-Test",
        "panel": "Panel B",
        "statistic_name": "t",
        "statistic": round(t_stat, 4),
        "df": df_val,
        "p_value": round(p_val, 6),
        "ci": [round(float(ci_low), 4), round(float(ci_high), 4)],
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_z_test_known_variance(
    groups: Dict[str, np.ndarray],
    dv_name: str,
    iv_name: str,
    sigma1: float,
    sigma2: Optional[float] = None,
    mu0: float = 0.0,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Kiểm định Z khi đã biết phương sai quần thể (Z-test with Known Variance) - Panel B."""
    g_names = list(groups.keys())
    if len(g_names) == 1:
        arr = groups[g_names[0]]
        n = len(arr)
        mean = float(np.mean(arr))
        se = sigma1 / np.sqrt(n)
        z_stat = (mean - mu0) / se
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        z_crit = stats.norm.ppf(1.0 - alpha / 2.0)
        ci_low, ci_high = mean - z_crit * se, mean + z_crit * se
        sig = p_val < alpha
        interp = (
            f"Kiểm định Z một mẫu (đã biết độ lệch chuẩn quần thể σ = {sigma1:.4f}) trên '{dv_name}' "
            f"(M = {mean:.4f}, n = {n}) so với μ₀ = {mu0:.4f} cho kết quả {'CÓ' if sig else 'KHÔNG CÓ'} "
            f"ý nghĩa thống kê (Z = {z_stat:.4f}, p = {_fmt_p(p_val)}, KTC {int((1-alpha)*100)}%: [{ci_low:.4f}, {ci_high:.4f}])."
        )
        apa_headers = ["Biến số", "n", "Trung bình (M)", "σ quần thể", f"KTC {int((1-alpha)*100)}%", "Z", "p"]
        apa_rows = [[str(dv_name), str(n), f"{mean:.4f}", f"{sigma1:.4f}", f"[{ci_low:.4f}, {ci_high:.4f}]", f"{z_stat:.4f}", _fmt_p(p_val)]]
    else:
        g1, g2 = groups[g_names[0]], groups[g_names[1]]
        s2 = sigma2 if (sigma2 is not None and sigma2 > 0) else sigma1
        n1, n2 = len(g1), len(g2)
        m1, m2 = float(np.mean(g1)), float(np.mean(g2))
        diff = m1 - m2
        se = np.sqrt((sigma1 ** 2) / n1 + (s2 ** 2) / n2)
        z_stat = diff / se
        p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        z_crit = stats.norm.ppf(1.0 - alpha / 2.0)
        ci_low, ci_high = diff - z_crit * se, diff + z_crit * se
        sig = p_val < alpha
        interp = (
            f"Kiểm định Z hai mẫu độc lập (đã biết phương sai quần thể: σ₁ = {sigma1:.4f}, σ₂ = {s2:.4f}) "
            f"so sánh '{dv_name}' giữa nhóm '{g_names[0]}' (M = {m1:.4f}, n = {n1}) và nhóm '{g_names[1]}' "
            f"(M = {m2:.4f}, n = {n2}) cho thấy sự khác biệt {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê "
            f"ở mức α = {alpha} (Z = {z_stat:.4f}, p = {_fmt_p(p_val)}, KTC {int((1-alpha)*100)}% hiệu trung bình: [{ci_low:.4f}, {ci_high:.4f}])."
        )
        apa_headers = ["Nhóm", "n", "Trung bình (M)", "σ quần thể", "Hiệu số (ΔM)", f"KTC {int((1-alpha)*100)}%", "Z", "p"]
        apa_rows = [
            [str(g_names[0]), str(n1), f"{m1:.4f}", f"{sigma1:.4f}", f"{diff:.4f}", f"[{ci_low:.4f}, {ci_high:.4f}]", f"{z_stat:.4f}", _fmt_p(p_val)],
            [str(g_names[1]), str(n2), f"{m2:.4f}", f"{s2:.4f}", "", "", "", ""]
        ]
    chart_data = {
        "type": "boxplot",
        "title": f"Phân bố {dv_name} theo {iv_name} (Z-test)",
        "x_label": str(iv_name),
        "y_label": str(dv_name),
        "groups": {str(k): v.tolist() for k, v in groups.items()}
    }
    return {
        "test_id": "z_test",
        "test_name_vi": "Kiểm định Z (Đã biết phương sai quần thể)",
        "test_name_en": "Z-Test (Population Variance Known)",
        "panel": "Panel B",
        "statistic_name": "Z",
        "statistic": round(float(z_stat), 4),
        "df": None,
        "p_value": round(p_val, 6),
        "ci": [round(float(ci_low), 4), round(float(ci_high), 4)],
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_two_sample_t_test(
    groups: Dict[str, np.ndarray],
    dv_name: str,
    iv_name: str,
    equal_var: bool = True,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Kiểm định t hai mẫu độc lập (Two-Sample Independent t-Test) - Panel B (UR.F002.02)."""
    g_names = list(groups.keys())
    g1, g2 = groups[g_names[0]], groups[g_names[1]]
    d1, d2 = _summary_desc_continuous(g1), _summary_desc_continuous(g2)
    n1, n2 = d1["n"], d2["n"]

    res = stats.ttest_ind(g1, g2, equal_var=equal_var)
    t_stat = float(res.statistic)
    p_val = float(res.pvalue)
    df_val = int(n1 + n2 - 2) if equal_var else float(res.df)

    diff = d1["mean"] - d2["mean"]
    if equal_var:
        sp2 = (((n1 - 1) * (d1["sd"] ** 2)) + ((n2 - 1) * (d2["sd"] ** 2))) / (n1 + n2 - 2)
        se = np.sqrt(sp2 * (1.0 / n1 + 1.0 / n2))
        cohen_d = diff / np.sqrt(sp2) if sp2 > 0 else 0.0
    else:
        se = np.sqrt((d1["sd"] ** 2) / n1 + (d2["sd"] ** 2) / n2)
        sp = np.sqrt(((d1["sd"] ** 2) + (d2["sd"] ** 2)) / 2.0)
        cohen_d = diff / sp if sp > 0 else 0.0

    t_crit = stats.t.ppf(1.0 - alpha / 2.0, df=df_val)
    ci_low, ci_high = diff - t_crit * se, diff + t_crit * se

    sig = p_val < alpha
    interp = (
        f"Kiểm định t hai mẫu độc lập so sánh '{dv_name}' giữa nhóm '{g_names[0]}' "
        f"(M = {d1['mean']:.4f}, SD = {d1['sd']:.4f}, n = {n1}) và nhóm '{g_names[1]}' "
        f"(M = {d2['mean']:.4f}, SD = {d2['sd']:.4f}, n = {n2}) cho thấy sự khác biệt trung bình "
        f"(ΔM = {diff:.4f}) {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(t({df_val if isinstance(df_val, int) else f'{df_val:.2f}'}) = {t_stat:.4f}, p = {_fmt_p(p_val)}, "
        f"KTC {int((1-alpha)*100)}%: [{ci_low:.4f}, {ci_high:.4f}], Cohen's d = {cohen_d:.4f})."
    )
    apa_headers = ["Nhóm", "n", "Trung bình (M)", "Độ lệch chuẩn (SD)", "Hiệu số (ΔM)", f"KTC {int((1-alpha)*100)}%", "t", "df", "p", "Cohen's d"]
    apa_rows = [
        [str(g_names[0]), str(n1), f"{d1['mean']:.4f}", f"{d1['sd']:.4f}", f"{diff:.4f}", f"[{ci_low:.4f}, {ci_high:.4f}]", f"{t_stat:.4f}", f"{df_val}", _fmt_p(p_val), f"{cohen_d:.4f}"],
        [str(g_names[1]), str(n2), f"{d2['mean']:.4f}", f"{d2['sd']:.4f}", "", "", "", "", "", ""]
    ]
    chart_data = {
        "type": "boxplot",
        "title": f"So sánh {dv_name} giữa 2 nhóm ({iv_name})",
        "x_label": str(iv_name),
        "y_label": str(dv_name),
        "groups": {str(k): v.tolist() for k, v in groups.items()}
    }
    return {
        "test_id": "two_sample_t_test",
        "test_name_vi": "Kiểm định t hai mẫu độc lập (Two-Sample t-test)",
        "test_name_en": "Two-Sample Independent t-Test",
        "panel": "Panel B",
        "statistic_name": "t",
        "statistic": round(t_stat, 4),
        "df": round(df_val, 4) if isinstance(df_val, float) else df_val,
        "p_value": round(p_val, 6),
        "ci": [round(float(ci_low), 4), round(float(ci_high), 4)],
        "effect_size": {"name": "Cohen's d", "value": round(float(cohen_d), 4)},
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_mann_whitney_and_median_test(
    groups: Dict[str, np.ndarray],
    dv_name: str,
    iv_name: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Kiểm định Mann-Whitney U và Kiểm định Trung vị (Mood's Median Test) - Panel B (UR.F002.02).
    Được kích hoạt khi 2 mẫu độc lập vi phạm giả định ND/H.
    """
    g_names = list(groups.keys())
    g1, g2 = groups[g_names[0]], groups[g_names[1]]
    d1, d2 = _summary_desc_continuous(g1), _summary_desc_continuous(g2)

    u_stat, p_val_mw = stats.mannwhitneyu(g1, g2, alternative="two-sided")
    u_stat = float(u_stat)
    p_val_mw = float(p_val_mw)

    # Mood's Median Test
    try:
        med_stat, p_val_med, grand_med, _ = stats.median_test(g1, g2)
        med_stat = float(med_stat)
        p_val_med = float(p_val_med)
        grand_med = float(grand_med)
    except Exception:
        med_stat, p_val_med, grand_med = np.nan, np.nan, float(np.median(np.concatenate([g1, g2])))

    sig = p_val_mw < alpha
    interp = (
        f"Do dữ liệu vi phạm giả định phân phối chuẩn hoặc đồng nhất phương sai (ND/H), hệ thống thực hiện "
        f"Kiểm định phi tham số Mann-Whitney U (kèm Kiểm định Trung vị Mood) so sánh '{dv_name}' giữa nhóm "
        f"'{g_names[0]}' (Trung vị = {d1['median']:.4f}, IQR = {d1['iqr']:.4f}, n = {d1['n']}) và nhóm "
        f"'{g_names[1]}' (Trung vị = {d2['median']:.4f}, IQR = {d2['iqr']:.4f}, n = {d2['n']}). "
        f"Kết quả cho thấy sự khác biệt giữa hai nhóm {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(Mann-Whitney U = {u_stat:.4f}, p = {_fmt_p(p_val_mw)}; "
        f"Kiểm định Trung vị χ² = {_fmt_num(med_stat)}, p = {_fmt_p(p_val_med)})."
    )
    apa_headers = ["Nhóm", "n", "Trung vị (Median)", "Khoảng tứ phân vị (IQR)", "Mann-Whitney U", "p (Mann-Whitney)", "χ² (Median Test)", "p (Median Test)"]
    apa_rows = [
        [str(g_names[0]), str(d1["n"]), f"{d1['median']:.4f}", f"{d1['iqr']:.4f} ({d1['q25']:.2f} - {d1['q75']:.2f})", f"{u_stat:.4f}", _fmt_p(p_val_mw), _fmt_num(med_stat), _fmt_p(p_val_med)],
        [str(g_names[1]), str(d2["n"]), f"{d2['median']:.4f}", f"{d2['iqr']:.4f} ({d2['q25']:.2f} - {d2['q75']:.2f})", "", "", "", ""]
    ]
    chart_data = {
        "type": "boxplot",
        "title": f"Phân bố trung vị & tứ phân vị {dv_name} theo {iv_name}",
        "x_label": str(iv_name),
        "y_label": str(dv_name),
        "groups": {str(k): v.tolist() for k, v in groups.items()}
    }
    return {
        "test_id": "mann_whitney_u_test",
        "test_name_vi": "Kiểm định Mann-Whitney U / Kiểm định Trung vị (Median Test)",
        "test_name_en": "Mann-Whitney U Test / Mood's Median Test",
        "panel": "Panel B",
        "statistic_name": "U",
        "statistic": round(u_stat, 4),
        "df": None,
        "p_value": round(p_val_mw, 6),
        "secondary_test": {
            "name": "Kiểm định Trung vị (Mood's Median Test)",
            "statistic_name": "χ²",
            "statistic": round(med_stat, 4) if not np.isnan(med_stat) else None,
            "p_value": round(p_val_med, 6) if not np.isnan(p_val_med) else None,
            "grand_median": round(grand_med, 4),
        },
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_paired_t_test(
    arr1: np.ndarray,
    arr2: np.ndarray,
    name1: str,
    name2: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Kiểm định t bắt cặp (Paired t-Test) - Panel B (UR.F002.02)."""
    n = len(arr1)
    if n < 2:
        raise ValueError("Cỡ mẫu bắt cặp phải >= 2.")
    diffs = arr1 - arr2
    d1, d2, dd = _summary_desc_continuous(arr1), _summary_desc_continuous(arr2), _summary_desc_continuous(diffs)

    res = stats.ttest_rel(arr1, arr2)
    t_stat = float(res.statistic)
    p_val = float(res.pvalue)
    df_val = n - 1
    se_d = dd["sd"] / np.sqrt(n)
    t_crit = stats.t.ppf(1.0 - alpha / 2.0, df=df_val)
    ci_low, ci_high = dd["mean"] - t_crit * se_d, dd["mean"] + t_crit * se_d

    sig = p_val < alpha
    interp = (
        f"Kiểm định t bắt cặp giữa '{name1}' (M = {d1['mean']:.4f}, SD = {d1['sd']:.4f}) và '{name2}' "
        f"(M = {d2['mean']:.4f}, SD = {d2['sd']:.4f}) trên n = {n} cặp quan sát cho thấy hiệu số trung bình "
        f"(ΔM = {dd['mean']:.4f}, SD_d = {dd['sd']:.4f}) {'CÓ' if sig else 'KHÔNG CÓ'} sự thay đổi có ý nghĩa thống kê "
        f"ở mức α = {alpha} (t({df_val}) = {t_stat:.4f}, p = {_fmt_p(p_val)}, "
        f"KTC {int((1-alpha)*100)}%: [{ci_low:.4f}, {ci_high:.4f}])."
    )
    apa_headers = ["Thời điểm / Nhóm", "n (cặp)", "Trung bình (M)", "Độ lệch chuẩn (SD)", "Hiệu trung bình (ΔM ± SD)", f"KTC {int((1-alpha)*100)}%", "t", "df", "p"]
    apa_rows = [
        [str(name1), str(n), f"{d1['mean']:.4f}", f"{d1['sd']:.4f}", f"{dd['mean']:.4f} ± {dd['sd']:.4f}", f"[{ci_low:.4f}, {ci_high:.4f}]", f"{t_stat:.4f}", str(df_val), _fmt_p(p_val)],
        [str(name2), str(n), f"{d2['mean']:.4f}", f"{d2['sd']:.4f}", "", "", "", "", ""]
    ]
    chart_data = {
        "type": "boxplot",
        "title": f"So sánh bắt cặp: {name1} vs {name2}",
        "x_label": "Thời điểm / Điều kiện",
        "y_label": "Giá trị đo lường",
        "groups": {str(name1): arr1.tolist(), str(name2): arr2.tolist()}
    }
    return {
        "test_id": "paired_t_test",
        "test_name_vi": "Kiểm định t bắt cặp (Paired t-test)",
        "test_name_en": "Paired Samples t-Test",
        "panel": "Panel B",
        "statistic_name": "t",
        "statistic": round(t_stat, 4),
        "df": df_val,
        "p_value": round(p_val, 6),
        "ci": [round(float(ci_low), 4), round(float(ci_high), 4)],
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_wilcoxon_and_sign_test(
    arr1: np.ndarray,
    arr2: np.ndarray,
    name1: str,
    name2: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Kiểm định dấu hạng Wilcoxon (Wilcoxon Signed-Rank Test) & Kiểm định dấu (Sign Test) - Panel B (UR.F002.02).
    """
    n = len(arr1)
    diffs = arr1 - arr2
    d1, d2, dd = _summary_desc_continuous(arr1), _summary_desc_continuous(arr2), _summary_desc_continuous(diffs)

    non_zero = diffs[diffs != 0]
    if len(non_zero) == 0:
        w_stat, p_val_w = 0.0, 1.0
        n_pos, n_neg, p_val_sign = 0, 0, 1.0
    else:
        res_w = stats.wilcoxon(arr1, arr2)
        w_stat = float(res_w.statistic)
        p_val_w = float(res_w.pvalue)
        n_pos = int(np.sum(diffs > 0))
        n_neg = int(np.sum(diffs < 0))
        n_eff = n_pos + n_neg
        p_val_sign = float(stats.binomtest(n_pos, n=n_eff, p=0.5, alternative="two-sided").pvalue) if n_eff > 0 else 1.0

    sig = p_val_w < alpha
    interp = (
        f"Do hiệu số bắt cặp vi phạm phân phối chuẩn (ND), hệ thống thực hiện Kiểm định dấu hạng Wilcoxon "
        f"(kèm Kiểm định dấu Sign Test) giữa '{name1}' (Trung vị = {d1['median']:.4f}, IQR = {d1['iqr']:.4f}) và "
        f"'{name2}' (Trung vị = {d2['median']:.4f}, IQR = {d2['iqr']:.4f}) trên n = {n} cặp. "
        f"Kết quả cho thấy sự thay đổi {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(Wilcoxon W = {w_stat:.4f}, p = {_fmt_p(p_val_w)}; "
        f"Sign Test: {n_pos} dương / {n_neg} âm, p = {_fmt_p(p_val_sign)})."
    )
    apa_headers = ["Thời điểm / Nhóm", "n (cặp)", "Trung vị (Median)", "IQR", " Trung vị hiệu số", "Wilcoxon W", "p (Wilcoxon)", "Sign Test (+ / -)", "p (Sign Test)"]
    apa_rows = [
        [str(name1), str(n), f"{d1['median']:.4f}", f"{d1['iqr']:.4f}", f"{dd['median']:.4f}", f"{w_stat:.4f}", _fmt_p(p_val_w), f"{n_pos} / {n_neg}", _fmt_p(p_val_sign)],
        [str(name2), str(n), f"{d2['median']:.4f}", f"{d2['iqr']:.4f}", "", "", "", "", ""]
    ]
    chart_data = {
        "type": "boxplot",
        "title": f"So sánh bắt cặp phi tham số: {name1} vs {name2}",
        "x_label": "Thời điểm / Điều kiện",
        "y_label": "Giá trị đo lường",
        "groups": {str(name1): arr1.tolist(), str(name2): arr2.tolist()}
    }
    return {
        "test_id": "wilcoxon_signed_rank_test",
        "test_name_vi": "Kiểm định dấu hạng Wilcoxon (Wilcoxon's Signed Rank Test) / Kiểm định dấu (Sign Test)",
        "test_name_en": "Wilcoxon Signed-Rank Test / Sign Test",
        "panel": "Panel B",
        "statistic_name": "W",
        "statistic": round(w_stat, 4),
        "df": None,
        "p_value": round(p_val_w, 6),
        "secondary_test": {
            "name": "Kiểm định dấu (Sign Test)",
            "statistic_name": "Số dấu dương (+)",
            "statistic": n_pos,
            "n_negative": n_neg,
            "p_value": round(p_val_sign, 6)
        },
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_one_way_anova(
    groups: Dict[str, np.ndarray],
    dv_name: str,
    iv_name: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Phân tích phương sai một yếu tố (One-Way ANOVA) - Panel B (UR.F002.02)."""
    g_names = list(groups.keys())
    g_arrays = [groups[k] for k in g_names]
    k = len(g_arrays)
    N = sum(len(a) for a in g_arrays)

    f_stat, p_val = stats.f_oneway(*g_arrays)
    f_stat = float(f_stat)
    p_val = float(p_val)

    all_vals = np.concatenate(g_arrays)
    grand_mean = float(np.mean(all_vals))
    ss_between = float(sum(len(a) * ((np.mean(a) - grand_mean) ** 2) for a in g_arrays))
    ss_within = float(sum(np.sum((a - np.mean(a)) ** 2) for a in g_arrays))
    ss_total = ss_between + ss_within
    df_between = k - 1
    df_within = N - k
    ms_between = ss_between / df_between if df_between > 0 else 0.0
    ms_within = ss_within / df_within if df_within > 0 else 0.0
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0

    sig = p_val < alpha
    desc_strs = []
    apa_rows = []
    for idx, g_name in enumerate(g_names):
        d = _summary_desc_continuous(groups[g_name])
        desc_strs.append(f"'{g_name}' (M = {d['mean']:.4f}, SD = {d['sd']:.4f}, n = {d['n']})")
        apa_rows.append([
            str(g_name), str(d["n"]), f"{d['mean']:.4f}", f"{d['sd']:.4f}",
            f"{f_stat:.4f}" if idx == 0 else "",
            f"({df_between}, {df_within})" if idx == 0 else "",
            _fmt_p(p_val) if idx == 0 else "",
            f"{eta_sq:.4f}" if idx == 0 else ""
        ])

    interp = (
        f"Phân tích phương sai một yếu tố (One-way ANOVA) so sánh '{dv_name}' giữa {k} nhóm của '{iv_name}' "
        f"[{'; '.join(desc_strs)}] cho thấy sự khác biệt trung bình giữa các nhóm "
        f"{'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(F({df_between}, {df_within}) = {f_stat:.4f}, p = {_fmt_p(p_val)}, η² = {eta_sq:.4f})."
    )
    apa_headers = ["Nhóm", "n", "Trung bình (M)", "Độ lệch chuẩn (SD)", "F", "df (giữa, trong)", "p", "η²"]
    chart_data = {
        "type": "boxplot",
        "title": f"So sánh {dv_name} giữa các nhóm {iv_name} (One-way ANOVA)",
        "x_label": str(iv_name),
        "y_label": str(dv_name),
        "groups": {str(k_name): v.tolist() for k_name, v in groups.items()}
    }
    return {
        "test_id": "one_way_anova",
        "test_name_vi": "Phân tích phương sai một yếu tố (One-way ANOVA)",
        "test_name_en": "One-Way ANOVA",
        "panel": "Panel B",
        "statistic_name": "F",
        "statistic": round(f_stat, 4),
        "df": [df_between, df_within],
        "p_value": round(p_val, 6),
        "anova_details": {
            "ss_between": round(ss_between, 4),
            "ss_within": round(ss_within, 4),
            "ms_between": round(ms_between, 4),
            "ms_within": round(ms_within, 4),
            "eta_squared": round(eta_sq, 4),
        },
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_kruskal_wallis(
    groups: Dict[str, np.ndarray],
    dv_name: str,
    iv_name: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Kiểm định Kruskal-Wallis (Kruskal-Wallis Test) - Panel B (UR.F002.02)."""
    g_names = list(groups.keys())
    g_arrays = [groups[k] for k in g_names]
    k = len(g_arrays)
    N = sum(len(a) for a in g_arrays)

    h_stat, p_val = stats.kruskal(*g_arrays)
    h_stat = float(h_stat)
    p_val = float(p_val)
    df_val = k - 1
    eps_sq = h_stat / ((N ** 2 - 1) / (N + 1)) if N > 1 else 0.0

    sig = p_val < alpha
    desc_strs = []
    apa_rows = []
    for idx, g_name in enumerate(g_names):
        d = _summary_desc_continuous(groups[g_name])
        desc_strs.append(f"'{g_name}' (Trung vị = {d['median']:.4f}, IQR = {d['iqr']:.4f}, n = {d['n']})")
        apa_rows.append([
            str(g_name), str(d["n"]), f"{d['median']:.4f}", f"{d['iqr']:.4f} ({d['q25']:.2f} - {d['q75']:.2f})",
            f"{h_stat:.4f}" if idx == 0 else "",
            str(df_val) if idx == 0 else "",
            _fmt_p(p_val) if idx == 0 else ""
        ])

    interp = (
        f"Do dữ liệu vi phạm giả định phân phối chuẩn hoặc đồng nhất phương sai (ND/H), hệ thống thực hiện "
        f"Kiểm định phi tham số Kruskal-Wallis so sánh '{dv_name}' giữa {k} nhóm của '{iv_name}' "
        f"[{'; '.join(desc_strs)}]. Kết quả cho thấy sự khác biệt giữa các nhóm "
        f"{'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(H({df_val}) = {h_stat:.4f}, p = {_fmt_p(p_val)}, ε² = {eps_sq:.4f})."
    )
    apa_headers = ["Nhóm", "n", "Trung vị (Median)", "Khoảng tứ phân vị (IQR)", "H (Kruskal-Wallis)", "df", "p"]
    chart_data = {
        "type": "boxplot",
        "title": f"Phân bố {dv_name} giữa các nhóm {iv_name} (Kruskal-Wallis)",
        "x_label": str(iv_name),
        "y_label": str(dv_name),
        "groups": {str(k_name): v.tolist() for k_name, v in groups.items()}
    }
    return {
        "test_id": "kruskal_wallis",
        "test_name_vi": "Kiểm định Kruskal-Wallis",
        "test_name_en": "Kruskal-Wallis H Test",
        "panel": "Panel B",
        "statistic_name": "H",
        "statistic": round(h_stat, 4),
        "df": df_val,
        "p_value": round(p_val, 6),
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_rcbd_anova(
    matrix_df: pd.DataFrame,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Thiết kế khối ngẫu nhiên hoàn chỉnh (Randomized Complete Block Design - RCBD / Repeated Measures ANOVA)
    cho >= 3 nhóm dữ liệu bắt cặp (Panel B - UR.F002.02).
    matrix_df: DataFrame với mỗi hàng là 1 khối (Subject/Block) và mỗi cột là 1 mức điều trị (Treatment/Time).
    """
    clean_df = matrix_df.apply(pd.to_numeric, errors="coerce").dropna()
    b, k = clean_df.shape  # b blocks (rows), k treatments (cols)
    if b < 2 or k < 3:
        raise ValueError(f"Thiết kế khối ngẫu nhiên hoàn chỉnh (RCBD) yêu cầu ít nhất 2 khối và >= 3 nhóm bắt cặp (hiện có {b} khối, {k} nhóm).")

    Y = clean_df.to_numpy(dtype=float)
    grand_mean = float(np.mean(Y))
    treat_means = np.mean(Y, axis=0)
    block_means = np.mean(Y, axis=1)

    ss_total = float(np.sum((Y - grand_mean) ** 2))
    ss_treat = float(b * np.sum((treat_means - grand_mean) ** 2))
    ss_block = float(k * np.sum((block_means - grand_mean) ** 2))
    ss_error = max(0.0, ss_total - ss_treat - ss_block)

    df_treat = k - 1
    df_block = b - 1
    df_error = (k - 1) * (b - 1)

    ms_treat = ss_treat / df_treat
    ms_block = ss_block / df_block
    ms_error = ss_error / df_error if df_error > 0 else 1e-12

    f_treat = ms_treat / ms_error if ms_error > 0 else 0.0
    p_treat = float(1.0 - stats.f.cdf(f_treat, df_treat, df_error))
    f_block = ms_block / ms_error if ms_error > 0 else 0.0
    p_block = float(1.0 - stats.f.cdf(f_block, df_block, df_error))

    sig = p_treat < alpha
    col_names = [str(c) for c in clean_df.columns]
    desc_strs = []
    for c in clean_df.columns:
        d = _summary_desc_continuous(clean_df[c].to_numpy())
        desc_strs.append(f"'{c}' (M = {d['mean']:.4f}, SD = {d['sd']:.4f})")

    interp = (
        f"Phân tích phương sai theo Thiết kế khối ngẫu nhiên hoàn chỉnh (Randomized Complete Block Design - RCBD) "
        f"trên {b} khối (đối tượng) qua {k} mức điều trị bắt cặp [{'; '.join(desc_strs)}] cho thấy sự khác biệt "
        f"giữa các mức điều trị {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(F({df_treat}, {df_error}) = {f_treat:.4f}, p = {_fmt_p(p_treat)}; "
        f"Hiệu ứng khối: F({df_block}, {df_error}) = {f_block:.4f}, p = {_fmt_p(p_block)})."
    )
    apa_headers = ["Nguồn biến thiên", "Tổng bình phương (SS)", "df", "Trung bình bình phương (MS)", "F", "p"]
    apa_rows = [
        ["Phương pháp / Điều trị (Treatment)", f"{ss_treat:.4f}", str(df_treat), f"{ms_treat:.4f}", f"{f_treat:.4f}", _fmt_p(p_treat)],
        ["Khối / Đối tượng (Block)", f"{ss_block:.4f}", str(df_block), f"{ms_block:.4f}", f"{f_block:.4f}", _fmt_p(p_block)],
        ["Sai số (Error)", f"{ss_error:.4f}", str(df_error), f"{ms_error:.4f}", "", ""],
        ["Tổng cộng (Total)", f"{ss_total:.4f}", str(b * k - 1), "", "", ""]
    ]
    chart_data = {
        "type": "boxplot",
        "title": "So sánh các nhóm theo Thiết kế khối ngẫu nhiên hoàn chỉnh (RCBD)",
        "x_label": "Nhóm điều trị / Thời điểm",
        "y_label": "Giá trị đo lường",
        "groups": {str(c): clean_df[c].to_numpy().tolist() for c in clean_df.columns}
    }
    return {
        "test_id": "randomized_complete_block_design",
        "test_name_vi": "Thiết kế khối ngẫu nhiên hoàn chỉnh (Randomized Complete Block Design)",
        "test_name_en": "Randomized Complete Block Design (RCBD ANOVA)",
        "panel": "Panel B",
        "statistic_name": "F",
        "statistic": round(float(f_treat), 4),
        "df": [df_treat, df_error],
        "p_value": round(p_treat, 6),
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_two_way_anova(
    df: pd.DataFrame,
    iv1_col: str,
    iv2_col: str,
    dv_col: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Phân tích phương sai hai yếu tố (Two-Way ANOVA) - Panel B (UR.F002.02).
    Tính hiệu ứng chính của Yếu tố A, Yếu tố B và Tương tác A × B bằng OLS (chuẩn Minitab).
    """
    sub = df[[iv1_col, iv2_col, dv_col]].copy()
    sub[dv_col] = pd.to_numeric(sub[dv_col], errors="coerce")
    sub = sub.dropna()
    if len(sub) < 4:
        raise ValueError("Cỡ mẫu quá nhỏ để thực hiện Phân tích phương sai hai yếu tố (Two-way ANOVA).")

    y = sub[dv_col].to_numpy(dtype=float)
    n = len(y)
    grand_mean = float(np.mean(y))
    ss_total = float(np.sum((y - grand_mean) ** 2))

    levels_a = list(sub[iv1_col].unique())
    levels_b = list(sub[iv2_col].unique())
    a_cnt, b_cnt = len(levels_a), len(levels_b)

    # Tạo ma trận thiết kế hiệu ứng sum-to-zero (chuẩn Type III / Balanced ANOVA)
    def _helmert_or_sum_coding(series: pd.Series, levels: list) -> np.ndarray:
        k = len(levels)
        if k <= 1:
            return np.zeros((len(series), 0))
        mat = np.zeros((len(series), k - 1))
        vals = series.to_numpy()
        for j in range(k - 1):
            mat[vals == levels[j], j] = 1.0
            mat[vals == levels[-1], j] = -1.0
        return mat

    Xa = _helmert_or_sum_coding(sub[iv1_col], levels_a)
    Xb = _helmert_or_sum_coding(sub[iv2_col], levels_b)
    Xab_list = []
    for i in range(Xa.shape[1]):
        for j in range(Xb.shape[1]):
            Xab_list.append(Xa[:, i] * Xb[:, j])
    Xab = np.column_stack(Xab_list) if Xab_list else np.zeros((n, 0))

    ones = np.ones((n, 1))
    X_full = np.hstack([ones, Xa, Xb, Xab])

    def _rss(X_mat: np.ndarray) -> float:
        beta, _, _, _ = np.linalg.lstsq(X_mat, y, rcond=None)
        resid = y - X_mat @ beta
        return float(np.sum(resid ** 2))

    rss_full = _rss(X_full)
    df_error = n - X_full.shape[1]

    # Nếu không đủ bậc tự do cho tương tác (ví dụ mỗi ô chỉ có 1 quan sát), gộp vào sai số
    has_interaction = df_error > 0 and Xab.shape[1] > 0
    if not has_interaction:
        X_no_ab = np.hstack([ones, Xa, Xb])
        rss_full = _rss(X_no_ab)
        df_error = n - X_no_ab.shape[1]
        rss_no_a = _rss(np.hstack([ones, Xb]))
        rss_no_b = _rss(np.hstack([ones, Xa]))
        ss_a = max(0.0, rss_no_a - rss_full)
        ss_b = max(0.0, rss_no_b - rss_full)
        ss_ab = 0.0
        df_ab = 0
    else:
        rss_no_a = _rss(np.hstack([ones, Xb, Xab]))
        rss_no_b = _rss(np.hstack([ones, Xa, Xab]))
        rss_no_ab = _rss(np.hstack([ones, Xa, Xb]))
        ss_a = max(0.0, rss_no_a - rss_full)
        ss_b = max(0.0, rss_no_b - rss_full)
        ss_ab = max(0.0, rss_no_ab - rss_full)
        df_ab = (a_cnt - 1) * (b_cnt - 1)

    ss_error = max(0.0, rss_full)
    df_a = a_cnt - 1
    df_b = b_cnt - 1
    ms_a = ss_a / df_a if df_a > 0 else 0.0
    ms_b = ss_b / df_b if df_b > 0 else 0.0
    ms_ab = ss_ab / df_ab if df_ab > 0 else 0.0
    ms_error = ss_error / df_error if df_error > 0 else 1e-12

    f_a = ms_a / ms_error if ms_error > 0 else 0.0
    p_a = float(1.0 - stats.f.cdf(f_a, df_a, df_error)) if df_error > 0 else 1.0
    f_b = ms_b / ms_error if ms_error > 0 else 0.0
    p_b = float(1.0 - stats.f.cdf(f_b, df_b, df_error)) if df_error > 0 else 1.0
    f_ab = ms_ab / ms_error if (has_interaction and ms_error > 0) else 0.0
    p_ab = float(1.0 - stats.f.cdf(f_ab, df_ab, df_error)) if (has_interaction and df_error > 0) else np.nan

    sig_a = p_a < alpha
    sig_b = p_b < alpha
    sig_ab = bool(has_interaction and p_ab < alpha)

    interp_parts = [
        f"Phân tích phương sai hai yếu tố (Two-way ANOVA) đánh giá ảnh hưởng của '{iv1_col}' và '{iv2_col}' lên '{dv_col}' (n = {n}):",
        f"- Hiệu ứng chính của '{iv1_col}': F({df_a}, {df_error}) = {f_a:.4f}, p = {_fmt_p(p_a)} ({'Có' if sig_a else 'Không có'} ý nghĩa thống kê).",
        f"- Hiệu ứng chính của '{iv2_col}': F({df_b}, {df_error}) = {f_b:.4f}, p = {_fmt_p(p_b)} ({'Có' if sig_b else 'Không có'} ý nghĩa thống kê)."
    ]
    if has_interaction:
        interp_parts.append(
            f"- Hiệu ứng tương tác '{iv1_col} × {iv2_col}': F({df_ab}, {df_error}) = {f_ab:.4f}, p = {_fmt_p(p_ab)} "
            f"({'Có' if sig_ab else 'Không có'} tương tác có ý nghĩa thống kê)."
        )
    interp = " ".join(interp_parts)

    apa_headers = ["Nguồn biến thiên", "SS", "df", "MS", "F", "p"]
    apa_rows = [
        [f"Yếu tố {iv1_col}", f"{ss_a:.4f}", str(df_a), f"{ms_a:.4f}", f"{f_a:.4f}", _fmt_p(p_a)],
        [f"Yếu tố {iv2_col}", f"{ss_b:.4f}", str(df_b), f"{ms_b:.4f}", f"{f_b:.4f}", _fmt_p(p_b)],
    ]
    if has_interaction:
        apa_rows.append([f"Tương tác {iv1_col} × {iv2_col}", f"{ss_ab:.4f}", str(df_ab), f"{ms_ab:.4f}", f"{f_ab:.4f}", _fmt_p(p_ab)])
    apa_rows.extend([
        ["Sai số (Error)", f"{ss_error:.4f}", str(df_error), f"{ms_error:.4f}", "", ""],
        ["Tổng cộng (Total)", f"{ss_total:.4f}", str(n - 1), "", "", ""]
    ])

    groups_dict = {}
    for (g1, g2), g_df in sub.groupby([iv1_col, iv2_col]):
        groups_dict[f"{g1} | {g2}"] = g_df[dv_col].to_numpy().tolist()

    chart_data = {
        "type": "boxplot",
        "title": f"Phân bố {dv_col} theo {iv1_col} và {iv2_col} (Two-way ANOVA)",
        "x_label": f"{iv1_col} | {iv2_col}",
        "y_label": str(dv_col),
        "groups": groups_dict
    }
    return {
        "test_id": "two_way_anova",
        "test_name_vi": "Phân tích phương sai hai yếu tố (Two-way ANOVA)",
        "test_name_en": "Two-Way ANOVA",
        "panel": "Panel B",
        "statistic_name": "F",
        "statistic": round(float(f_a), 4),
        "df": [df_a, df_error],
        "p_value": round(p_a, 6),
        "effects": {
            str(iv1_col): {"F": round(f_a, 4), "df": [df_a, df_error], "p_value": round(p_a, 6)},
            str(iv2_col): {"F": round(f_b, 4), "df": [df_b, df_error], "p_value": round(p_b, 6)},
            "interaction": {"F": round(f_ab, 4), "df": [df_ab, df_error], "p_value": round(p_ab, 6)} if has_interaction else None
        },
        "significant": bool(sig_a or sig_b or sig_ab),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_friedman_two_way_anova(
    matrix_df: pd.DataFrame,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Phân tích phương sai hai yếu tố Friedman (Friedman Two-way ANOVA by Ranks) - Panel B (UR.F002.02).
    """
    clean_df = matrix_df.apply(pd.to_numeric, errors="coerce").dropna()
    b, k = clean_df.shape
    if b < 2 or k < 2:
        raise ValueError("Kiểm định Friedman yêu cầu ít nhất 2 khối và >= 2 cột/mức điều trị.")

    if k >= 3:
        stat, p_val = stats.friedmanchisquare(*[clean_df[c].to_numpy() for c in clean_df.columns])
        stat = float(stat)
        p_val = float(p_val)
    else:
        # Với k = 2 khối bắt cặp theo hạng, Friedman chi-square tổng quát:
        ranks = np.apply_along_axis(stats.rankdata, 1, clean_df.to_numpy(dtype=float))
        R_j = np.sum(ranks, axis=0)
        stat = float((12.0 / (b * k * (k + 1))) * np.sum(R_j ** 2) - 3.0 * b * (k + 1))
        p_val = float(1.0 - stats.chi2.cdf(stat, df=k - 1))

    df_val = k - 1
    kendall_w = stat / (b * (k - 1)) if (b * (k - 1)) > 0 else 0.0
    ranks_mat = np.apply_along_axis(stats.rankdata, 1, clean_df.to_numpy(dtype=float))
    mean_ranks = np.mean(ranks_mat, axis=0)

    sig = p_val < alpha
    apa_rows = []
    desc_strs = []
    for idx, c in enumerate(clean_df.columns):
        d = _summary_desc_continuous(clean_df[c].to_numpy())
        desc_strs.append(f"'{c}' (Trung vị = {d['median']:.4f}, Hạng TB = {mean_ranks[idx]:.2f})")
        apa_rows.append([
            str(c), str(b), f"{d['median']:.4f}", f"{d['iqr']:.4f}", f"{mean_ranks[idx]:.2f}",
            f"{stat:.4f}" if idx == 0 else "",
            str(df_val) if idx == 0 else "",
            _fmt_p(p_val) if idx == 0 else ""
        ])

    interp = (
        f"Do dữ liệu vi phạm giả định phân phối chuẩn/đồng nhất phương sai (ND/H), hệ thống thực hiện "
        f"Phân tích phương sai hai yếu tố phi tham số Friedman trên {b} khối qua {k} nhóm [{'; '.join(desc_strs)}]. "
        f"Kết quả cho thấy sự khác biệt giữa các nhóm {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(χ²_F({df_val}) = {stat:.4f}, p = {_fmt_p(p_val)}, Kendall's W = {kendall_w:.4f})."
    )
    apa_headers = ["Nhóm / Điều kiện", "n (khối)", "Trung vị (Median)", "IQR", "Hạng trung bình", "χ² Friedman", "df", "p"]
    chart_data = {
        "type": "boxplot",
        "title": "Phân bố các nhóm trong Phân tích phương sai hai yếu tố Friedman",
        "x_label": "Nhóm / Điều kiện",
        "y_label": "Giá trị đo lường",
        "groups": {str(c): clean_df[c].to_numpy().tolist() for c in clean_df.columns}
    }
    return {
        "test_id": "friedman_two_way_anova",
        "test_name_vi": "Phân tích phương sai hai yếu tố Friedman (Friedman Two-way ANOVA)",
        "test_name_en": "Friedman Two-Way ANOVA by Ranks",
        "panel": "Panel B",
        "statistic_name": "χ²_F",
        "statistic": round(stat, 4),
        "df": df_val,
        "p_value": round(p_val, 6),
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


# ==============================================================================
# PANEL C: BIẾN RỜI RẠC - BẢNG TIẾP LIÊN (CONTINGENCY TABLES)
# ==============================================================================

def run_chi_square_or_yates_or_fisher(
    ct: pd.DataFrame,
    row_name: str,
    col_name: str,
    force_test: Optional[str] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Thực hiện kiểm định bảng chéo không bắt cặp theo đúng nhánh rẽ Panel C (UR.F002.03) và Panel A (UR.F002.01):
    - Kiểm tra ô trống (observed == 0) và tần số kỳ vọng <= 5.
    - Nếu có ô trống hoặc có E_ij <= 5 (hoặc force_test == 'fisher'): Kiểm định chính xác Fisher (Fisher's Exact Test).
    - Nếu không có ô trống và toàn bộ E_ij > 5:
        + Bảng 2x2: Kiểm định Chi bình phương hiệu chỉnh Yates (Yates' Chi Square).
        + Bảng > 2x2 (hoặc từ Panel A): Kiểm định Chi bình phương về tính độc lập (Chi Square Test of Independence).
    """
    obs = ct.to_numpy(dtype=float)
    r_cnt, c_cnt = obs.shape
    is_2x2 = (r_cnt == 2 and c_cnt == 2)

    chi2_no_corr, p_no_corr, dof, expected = stats.chi2_contingency(obs, correction=False)
    has_empty_cell = bool(np.any(obs == 0))
    min_expected = float(np.min(expected))
    pct_expected_le5 = float(np.mean(expected <= 5.0) * 100.0)
    assumption_ok = (not has_empty_cell) and (min_expected > 5.0)

    if force_test == "chi_square_independence":
        selected = "chi_square"
    elif force_test == "yates":
        selected = "yates"
    elif force_test == "fisher":
        selected = "fisher"
    else:
        if not assumption_ok:
            selected = "fisher"
        else:
            selected = "yates" if is_2x2 else "chi_square"

    N = int(np.sum(obs))

    if selected == "fisher":
        if is_2x2:
            odds_ratio, p_val = stats.fisher_exact(obs.astype(int), alternative="two-sided")
            stat_val = float(odds_ratio)
            stat_name = "OR"
        else:
            # Mở rộng Freeman-Halton cho bảng RxC bằng Monte Carlo chính xác của scipy
            try:
                res_mc = stats.chi2_contingency(obs, correction=False)
                stat_val = float(res_mc[0])
                # Tính p-value chính xác bằng mô phỏng Monte Carlo trên phân phối siêu bội đa biến (Patefield/r2dtable)
                rng = np.random.default_rng(42)
                row_sums = obs.sum(axis=1).astype(int)
                col_sums = obs.sum(axis=0).astype(int)
                n_sim = 10000
                # Sinh mẫu hoán vị biên cố định
                col_pool = np.repeat(np.arange(c_cnt), col_sums)
                ge_count = 0
                for _ in range(n_sim):
                    perm = rng.permutation(col_pool)
                    sim_table = np.zeros((r_cnt, c_cnt), dtype=float)
                    idx_start = 0
                    for i_r, r_s in enumerate(row_sums):
                        seg = perm[idx_start:idx_start + r_s]
                        idx_start += r_s
                        for c_idx in range(c_cnt):
                            sim_table[i_r, c_idx] = np.sum(seg == c_idx)
                    sim_chi2 = np.sum(((sim_table - expected) ** 2) / np.maximum(expected, 1e-12))
                    if sim_chi2 >= stat_val - 1e-12:
                        ge_count += 1
                p_val = float((ge_count + 1) / (n_sim + 1))
                stat_name = "χ² (Fisher-Freeman-Halton)"
            except Exception:
                stat_val = float(chi2_no_corr)
                p_val = float(p_no_corr)
                stat_name = "χ²"

        test_id = "fisher_exact_test"
        test_name_vi = "Kiểm định chính xác Fisher (Fisher's Exact Test)"
        test_name_en = "Fisher's Exact Test"
        df_out = None
        reason_str = (
            f"Do bảng tiếp liên có ô trống (tần số = 0: {has_empty_cell}) hoặc có tần số kỳ vọng ≤ 5 "
            f"(nhỏ nhất = {min_expected:.2f}), hệ thống tự động chọn Kiểm định chính xác Fisher."
        )
    elif selected == "yates":
        chi2_yates, p_yates, dof_y, _ = stats.chi2_contingency(obs, correction=True)
        stat_val = float(chi2_yates)
        p_val = float(p_yates)
        stat_name = "χ² (Yates)"
        df_out = int(dof_y)
        test_id = "yates_chi_square"
        test_name_vi = "Kiểm định Chi bình phương hiệu chỉnh Yates (Yates' Chi Square)"
        test_name_en = "Yates' Continuity Corrected Chi-Square Test"
        reason_str = (
            f"Bảng 2×2 không có ô trống và toàn bộ tần số kỳ vọng > 5 (nhỏ nhất = {min_expected:.2f}), "
            f"hệ thống thực hiện Kiểm định Chi bình phương hiệu chỉnh Yates."
        )
    else:
        stat_val = float(chi2_no_corr)
        p_val = float(p_no_corr)
        stat_name = "χ²"
        df_out = int(dof)
        test_id = "chi_square_test_of_independence"
        test_name_vi = "Kiểm định Chi bình phương về tính độc lập (Chi Square Test of Independence)"
        test_name_en = "Chi-Square Test of Independence"
        reason_str = (
            f"Bảng tiếp liên ({r_cnt}×{c_cnt}) thỏa mãn điều kiện kỳ vọng (tần số kỳ vọng nhỏ nhất = {min_expected:.2f}), "
            f"hệ thống thực hiện Kiểm định Chi bình phương về tính độc lập."
        )

    sig = p_val < alpha
    interp = (
        f"{reason_str} Phân tích mối liên quan giữa '{row_name}' và '{col_name}' (N = {N}) cho thấy "
        f"{'CÓ' if sig else 'KHÔNG CÓ'} mối liên quan có ý nghĩa thống kê ở mức α = {alpha} "
        f"({stat_name} = {_fmt_num(stat_val)}, p = {_fmt_p(p_val)})."
    )

    apa_headers = [f"{row_name} \\ {col_name}"] + [f"{c} - n (%)" for c in ct.columns] + ["Tổng hàng", stat_name, "p"]
    apa_rows = []
    for idx, r_label in enumerate(ct.index):
        row_total = int(np.sum(obs[idx, :]))
        cells = [
            f"{int(obs[idx, j])} ({(obs[idx, j]/row_total*100 if row_total > 0 else 0):.1f}%)"
            for j in range(c_cnt)
        ]
        apa_rows.append(
            [str(r_label)] + cells + [
                str(row_total),
                _fmt_num(stat_val) if idx == 0 else "",
                _fmt_p(p_val) if idx == 0 else ""
            ]
        )

    chart_data = {
        "type": "bar",
        "title": f"Phân bố tần số giữa {row_name} và {col_name}",
        "x_label": f"{row_name} | {col_name}",
        "y_label": "Số lượng (n)",
        "categories": [f"{r} - {c}" for r in ct.index for c in ct.columns],
        "values": [int(obs[i, j]) for i in range(r_cnt) for j in range(c_cnt)]
    }
    return {
        "test_id": test_id,
        "test_name_vi": test_name_vi,
        "test_name_en": test_name_en,
        "panel": "Panel C" if force_test != "chi_square_independence" else "Panel A / Panel C",
        "statistic_name": stat_name,
        "statistic": round(stat_val, 4) if not np.isnan(stat_val) else None,
        "df": df_out,
        "p_value": round(p_val, 6),
        "contingency_info": {
            "shape": [r_cnt, c_cnt],
            "has_empty_cell": has_empty_cell,
            "min_expected": round(min_expected, 4),
            "pct_expected_le5": round(pct_expected_le5, 2),
        },
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_mcnemar_test(
    ct_2x2: pd.DataFrame,
    name1: str,
    name2: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Kiểm định McNemar cho bảng chéo 2x2 dữ liệu bắt cặp - Panel C (UR.F002.03)."""
    obs = ct_2x2.to_numpy(dtype=float)
    if obs.shape != (2, 2):
        raise ValueError("Kiểm định McNemar yêu cầu bảng chéo kích thước 2×2.")
    b = float(obs[0, 1])
    c = float(obs[1, 0])
    N = int(np.sum(obs))

    if (b + c) == 0:
        stat_val = 0.0
        p_val = 1.0
    else:
        # McNemar chi-square (kèm exact binomial khi b + c < 25)
        stat_val = float(((abs(b - c) - 1.0) ** 2) / (b + c)) if (b + c) > 0 else 0.0
        stat_uncorr = float(((b - c) ** 2) / (b + c))
        if (b + c) < 25:
            p_val = float(stats.binomtest(int(min(b, c)), n=int(b + c), p=0.5, alternative="two-sided").pvalue)
        else:
            p_val = float(1.0 - stats.chi2.cdf(stat_val, df=1))
        stat_val = stat_uncorr if stat_val == 0 and b != c else stat_val

    sig = p_val < alpha
    interp = (
        f"Kiểm định McNemar trên dữ liệu định tính bắt cặp (bảng 2×2) giữa '{name1}' và '{name2}' (N = {N} cặp, "
        f"số cặp bất đồng b = {int(b)}, c = {int(c)}) cho thấy sự thay đổi tỷ lệ trước-sau "
        f"{'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(χ² McNemar = {stat_val:.4f}, df = 1, p = {_fmt_p(p_val)})."
    )
    apa_headers = [f"{name1} \\ {name2}"] + [str(col) for col in ct_2x2.columns] + ["χ² McNemar", "df", "p"]
    apa_rows = []
    for idx, r_label in enumerate(ct_2x2.index):
        apa_rows.append(
            [str(r_label), str(int(obs[idx, 0])), str(int(obs[idx, 1])),
             f"{stat_val:.4f}" if idx == 0 else "",
             "1" if idx == 0 else "",
             _fmt_p(p_val) if idx == 0 else ""]
        )
    chart_data = {
        "type": "bar",
        "title": f"Biểu đồ bảng chéo bắt cặp McNemar ({name1} vs {name2})",
        "x_label": "Ô bảng chéo 2×2",
        "y_label": "Số cặp (n)",
        "categories": [f"{r} → {c}" for r in ct_2x2.index for c in ct_2x2.columns],
        "values": [int(obs[i, j]) for i in range(2) for j in range(2)]
    }
    return {
        "test_id": "mcnemar_test",
        "test_name_vi": "Kiểm định McNemar (McNemar Test)",
        "test_name_en": "McNemar's Test",
        "panel": "Panel C",
        "statistic_name": "χ²",
        "statistic": round(stat_val, 4),
        "df": 1,
        "p_value": round(p_val, 6),
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_cochran_q_test(
    df_cols: pd.DataFrame,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Kiểm định Cochran's Q cho dữ liệu định tính bắt cặp lớn hơn 2x2 (nhiều thời điểm/điều kiện hoặc bảng chéo > 2x2)
    - Panel C (UR.F002.03).
    """
    clean_df = df_cols.dropna().copy()
    k = clean_df.shape[1]
    n = clean_df.shape[0]
    if n < 2 or k < 2:
        raise ValueError("Kiểm định Cochran's Q yêu cầu ít nhất 2 hàng và >= 2 cột dữ liệu.")

    # Chuyển đổi sang ma trận nhị phân (0/1) nếu có nhiều giá trị
    bin_mat = np.zeros((n, k), dtype=float)
    all_vals = pd.unique(clean_df.values.ravel())
    preferred = [1, 1.0, "1", "Có", "Co", "Yes", "Dương tính", "Positive", True]
    pos_val = next((v for v in preferred if v in all_vals), all_vals[-1])
    for j, col in enumerate(clean_df.columns):
        bin_mat[:, j] = (clean_df[col] == pos_val).astype(float)

    col_totals = np.sum(bin_mat, axis=0)  # C_j
    row_totals = np.sum(bin_mat, axis=1)  # L_i
    denom = float(k * np.sum(row_totals) - np.sum(row_totals ** 2))
    if denom <= 0:
        q_stat = 0.0
        p_val = 1.0
    else:
        mean_c = np.mean(col_totals)
        numer = float(k * (k - 1) * np.sum((col_totals - mean_c) ** 2))
        q_stat = numer / denom
        p_val = float(1.0 - stats.chi2.cdf(q_stat, df=k - 1))

    df_val = k - 1
    sig = p_val < alpha
    apa_headers = ["Thời điểm / Điều kiện", "n", f"Số ca ({pos_val})", "Tỷ lệ (%)", "Cochran's Q", "df", "p"]
    apa_rows = []
    for idx, col in enumerate(clean_df.columns):
        cnt = int(col_totals[idx])
        pct = cnt / n * 100.0
        apa_rows.append([
            str(col), str(n), str(cnt), f"{pct:.2f}%",
            f"{q_stat:.4f}" if idx == 0 else "",
            str(df_val) if idx == 0 else "",
            _fmt_p(p_val) if idx == 0 else ""
        ])

    interp = (
        f"Kiểm định Cochran's Q đánh giá sự thay đổi tỷ lệ biến cố '{pos_val}' trên {n} đối tượng bắt cặp "
        f"qua {k} điều kiện/nhóm cho thấy sự khác biệt {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(Q({df_val}) = {q_stat:.4f}, p = {_fmt_p(p_val)})."
    )
    chart_data = {
        "type": "bar",
        "title": f"Tỷ lệ biến cố '{pos_val}' qua các nhóm (Cochran's Q)",
        "x_label": "Nhóm / Thời điểm",
        "y_label": "Tỷ lệ (%)",
        "categories": [str(c) for c in clean_df.columns],
        "values": [round(float(col_totals[j] / n * 100.0), 2) for j in range(k)]
    }
    return {
        "test_id": "cochran_q_test",
        "test_name_vi": "Kiểm định Cochran's Q (Cochran's Q Test)",
        "test_name_en": "Cochran's Q Test",
        "panel": "Panel C",
        "statistic_name": "Q",
        "statistic": round(float(q_stat), 4),
        "df": df_val,
        "p_value": round(p_val, 6),
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_mantel_haenszel_test(
    df: pd.DataFrame,
    iv_col: str,
    dv_col: str,
    strata_col: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Kiểm định Cochran-Mantel-Haenszel Chi Square khi có biến rời rạc thứ 3 (biến phân tầng)
    - Panel C (UR.F002.03).
    """
    sub = df[[iv_col, dv_col, strata_col]].dropna()
    iv_levels = list(sub[iv_col].unique())
    dv_levels = list(sub[dv_col].unique())
    strata_levels = list(sub[strata_col].unique())

    if len(iv_levels) < 2 or len(dv_levels) < 2:
        raise ValueError("Kiểm định Mantel-Haenszel yêu cầu biến độc lập và biến phụ thuộc có ít nhất 2 mức.")

    # Chuẩn hóa về 2 mức chính (mức 0 vs các mức còn lại nếu > 2) để tính CMH 2x2xK chuẩn
    r0, c0 = iv_levels[0], dv_levels[0]
    numer_sum = 0.0
    var_sum = 0.0
    or_num = 0.0
    or_den = 0.0
    apa_rows = []
    strata_counts = []

    for s_val in strata_levels:
        s_df = sub[sub[strata_col] == s_val]
        n_k = len(s_df)
        if n_k < 2:
            continue
        a = float(np.sum((s_df[iv_col] == r0) & (s_df[dv_col] == c0)))
        b = float(np.sum((s_df[iv_col] == r0) & (s_df[dv_col] != c0)))
        c = float(np.sum((s_df[iv_col] != r0) & (s_df[dv_col] == c0)))
        d = float(np.sum((s_df[iv_col] != r0) & (s_df[dv_col] != c0)))

        r1 = a + b
        r2 = c + d
        c1 = a + c
        c2 = b + d

        e_a = (r1 * c1) / n_k
        v_a = (r1 * r2 * c1 * c2) / ((n_k ** 2) * (n_k - 1.0)) if n_k > 1 else 0.0

        numer_sum += (a - e_a)
        var_sum += v_a
        or_num += (a * d) / n_k
        or_den += (b * c) / n_k
        or_k = (a * d) / (b * c) if (b * c) > 0 else np.nan
        strata_counts.append((str(s_val), int(n_k), int(a), int(b), int(c), int(d), or_k))

    if var_sum <= 0:
        chi2_mh = 0.0
        p_val = 1.0
    else:
        # Cochran-Mantel-Haenszel statistic
        chi2_mh = float(((abs(numer_sum) - 0.5) ** 2) / var_sum) if abs(numer_sum) > 0.5 else float((numer_sum ** 2) / var_sum)
        p_val = float(1.0 - stats.chi2.cdf(chi2_mh, df=1))

    or_mh = float(or_num / or_den) if or_den > 0 else np.nan
    sig = p_val < alpha

    apa_headers = [f"Tầng ({strata_col})", "n", "a", "b", "c", "d", "OR tầng", "OR chung (MH)", "χ²_MH", "p"]
    for idx, (s_name, nk, a_i, b_i, c_i, d_i, ork) in enumerate(strata_counts):
        apa_rows.append([
            s_name, str(nk), str(a_i), str(b_i), str(c_i), str(d_i),
            _fmt_num(ork, 3),
            _fmt_num(or_mh, 3) if idx == 0 else "",
            f"{chi2_mh:.4f}" if idx == 0 else "",
            _fmt_p(p_val) if idx == 0 else ""
        ])

    interp = (
        f"Kiểm định Mantel-Haenszel Chi-Square đánh giá mối liên quan giữa '{iv_col}' và '{dv_col}' "
        f"khi kiểm soát biến phân tầng thứ 3 '{strata_col}' ({len(strata_counts)} tầng, tổng N = {len(sub)}) cho thấy "
        f"mối liên quan sau hiệu chỉnh phân tầng {'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(χ²_MH(1) = {chi2_mh:.4f}, p = {_fmt_p(p_val)}, OR_MH = {_fmt_num(or_mh, 3)})."
    )
    chart_data = {
        "type": "bar",
        "title": f"Cỡ mẫu theo từng tầng của {strata_col} (Mantel-Haenszel)",
        "x_label": str(strata_col),
        "y_label": "Số quan sát (n)",
        "categories": [x[0] for x in strata_counts],
        "values": [x[1] for x in strata_counts]
    }
    return {
        "test_id": "mantel_haenszel_chi_square",
        "test_name_vi": "Kiểm định Mantel-Haenszel Chi Square",
        "test_name_en": "Cochran-Mantel-Haenszel Chi-Square Test",
        "panel": "Panel C",
        "statistic_name": "χ²_MH",
        "statistic": round(chi2_mh, 4),
        "df": 1,
        "p_value": round(p_val, 6),
        "common_odds_ratio": round(or_mh, 4) if not np.isnan(or_mh) else None,
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


# ==============================================================================
# PANEL D: TƯƠNG QUAN VÀ HỒI QUY (CORRELATION & REGRESSION)
# ==============================================================================

def run_pearson_correlation(
    df: pd.DataFrame,
    col1: str,
    col2: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Phân tích tương quan tuyến tính Pearson (Pearson Correlation) - Panel D (UR.F002.04)."""
    sub = df[[col1, col2]].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(sub)
    if n < 3:
        raise ValueError("Phân tích tương quan Pearson yêu cầu ít nhất 3 cặp quan sát hợp lệ.")
    x = sub[col1].to_numpy(dtype=float)
    y = sub[col2].to_numpy(dtype=float)
    r_val, p_val = stats.pearsonr(x, y)
    r_val = float(r_val)
    p_val = float(p_val)
    df_val = n - 2
    t_stat = r_val * np.sqrt(df_val / max(1e-12, 1.0 - r_val ** 2))

    # Khoảng tin cậy Fisher's z
    if abs(r_val) < 0.999999 and n > 3:
        z = np.arctanh(r_val)
        se_z = 1.0 / np.sqrt(n - 3)
        z_crit = stats.norm.ppf(1.0 - alpha / 2.0)
        ci_low, ci_high = float(np.tanh(z - z_crit * se_z)), float(np.tanh(z + z_crit * se_z))
    else:
        ci_low, ci_high = r_val, r_val

    sig = p_val < alpha
    direction = "thuận" if r_val > 0 else "nghịch"
    abs_r = abs(r_val)
    strength = "rất mạnh" if abs_r >= 0.7 else ("trung bình - khá" if abs_r >= 0.4 else ("yếu" if abs_r >= 0.2 else "rất yếu"))
    interp = (
        f"Phân tích tương quan Pearson giữa '{col1}' và '{col2}' (n = {n}) cho thấy hai biến "
        f"{'CÓ' if sig else 'KHÔNG CÓ'} mối tương quan tuyến tính {direction} mức độ {strength} có ý nghĩa thống kê "
        f"ở mức α = {alpha} (r = {r_val:.4f}, t({df_val}) = {t_stat:.4f}, p = {_fmt_p(p_val)}, "
        f"KTC {int((1-alpha)*100)}%: [{ci_low:.4f}, {ci_high:.4f}])."
    )
    apa_headers = ["Cặp biến số", "n", "Hệ số Pearson (r)", f"KTC {int((1-alpha)*100)}%", "t", "df", "p"]
    apa_rows = [[f"{col1} × {col2}", str(n), f"{r_val:.4f}", f"[{ci_low:.4f}, {ci_high:.4f}]", f"{t_stat:.4f}", str(df_val), _fmt_p(p_val)]]
    chart_data = {
        "type": "scatter",
        "title": f"Biểu đồ phân tán: {col1} vs {col2} (r = {r_val:.3f})",
        "x_label": str(col1),
        "y_label": str(col2),
        "x": x.tolist(),
        "y": y.tolist()
    }
    return {
        "test_id": "pearson_correlation",
        "test_name_vi": "Phân tích tương quan Pearson (Pearson Correlation)",
        "test_name_en": "Pearson Correlation Analysis",
        "panel": "Panel D",
        "statistic_name": "r",
        "statistic": round(r_val, 4),
        "df": df_val,
        "p_value": round(p_val, 6),
        "ci": [round(ci_low, 4), round(ci_high, 4)],
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_partial_correlation(
    df: pd.DataFrame,
    cols: List[str],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Phân tích tương quan từng phần (Partial Correlation) giữa 2 biến đầu tiên khi kiểm soát các biến liên tục còn lại
    - Panel D (UR.F002.04).
    """
    sub = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(sub)
    k_ctrl = len(cols) - 2
    if n <= len(cols) + 1 or k_ctrl < 1:
        raise ValueError("Phân tích tương quan từng phần yêu cầu >= 3 biến liên tục và cỡ mẫu đủ lớn.")

    x_col, y_col = cols[0], cols[1]
    ctrl_cols = cols[2:]

    Z = np.column_stack([np.ones(n), sub[ctrl_cols].to_numpy(dtype=float)])
    x_vec = sub[x_col].to_numpy(dtype=float)
    y_vec = sub[y_col].to_numpy(dtype=float)

    bx, _, _, _ = np.linalg.lstsq(Z, x_vec, rcond=None)
    by, _, _, _ = np.linalg.lstsq(Z, y_vec, rcond=None)
    rx = x_vec - Z @ bx
    ry = y_vec - Z @ by

    r_part, _ = stats.pearsonr(rx, ry)
    r_part = float(r_part)
    df_val = n - 2 - k_ctrl
    t_stat = float(r_part * np.sqrt(df_val / max(1e-12, 1.0 - r_part ** 2)))
    p_val = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=df_val)))

    sig = p_val < alpha
    ctrl_str = ", ".join(ctrl_cols)
    interp = (
        f"Phân tích tương quan từng phần (Partial Correlation) giữa '{x_col}' và '{y_col}' sau khi kiểm soát "
        f"ảnh hưởng của [{ctrl_str}] (n = {n}) cho thấy mối tương quan riêng phần "
        f"{'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(r_partial = {r_part:.4f}, t({df_val}) = {t_stat:.4f}, p = {_fmt_p(p_val)})."
    )
    apa_headers = ["Cặp biến chính", "Biến kiểm soát", "n", "r từng phần", "t", "df", "p"]
    apa_rows = [[f"{x_col} × {y_col}", ctrl_str, str(n), f"{r_part:.4f}", f"{t_stat:.4f}", str(df_val), _fmt_p(p_val)]]
    chart_data = {
        "type": "scatter",
        "title": f"Phần dư từng phần: {x_col} vs {y_col} (Kiểm soát: {ctrl_str})",
        "x_label": f"Phần dư {x_col}",
        "y_label": f"Phần dư {y_col}",
        "x": rx.tolist(),
        "y": ry.tolist()
    }
    return {
        "test_id": "partial_correlation",
        "test_name_vi": "Phân tích tương quan từng phần (Partial Correlation)",
        "test_name_en": "Partial Correlation Analysis",
        "panel": "Panel D",
        "statistic_name": "r_partial",
        "statistic": round(r_part, 4),
        "df": df_val,
        "p_value": round(p_val, 6),
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_spearman_correlation(
    df: pd.DataFrame,
    cols: List[str],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Hệ số tương quan hạng Spearman (Spearman's Rho) - Panel D (UR.F002.04)."""
    sub = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(sub)
    if n < 3 or len(cols) < 2:
        raise ValueError("Phân tích tương quan hạng Spearman yêu cầu ít nhất 2 biến và >= 3 quan sát.")

    col1, col2 = cols[0], cols[1]
    x = sub[col1].to_numpy(dtype=float)
    y = sub[col2].to_numpy(dtype=float)
    rho, p_val = stats.spearmanr(x, y)
    rho = float(rho)
    p_val = float(p_val)
    df_val = n - 2

    sig = p_val < alpha
    direction = "thuận" if rho > 0 else "nghịch"
    interp = (
        f"Do dữ liệu vi phạm giả định phân phối chuẩn, hệ thống thực hiện Phân tích tương quan hạng Spearman "
        f"giữa '{col1}' và '{col2}' (n = {n}). Kết quả cho thấy hai biến {'CÓ' if sig else 'KHÔNG CÓ'} "
        f"mối tương quan hạng {direction} có ý nghĩa thống kê ở mức α = {alpha} "
        f"(Spearman's ρ = {rho:.4f}, df = {df_val}, p = {_fmt_p(p_val)})."
    )
    apa_headers = ["Cặp biến số", "n", "Hệ số Spearman (ρ)", "df", "p"]
    apa_rows = []
    # Nếu có > 2 biến, liệt kê tất cả các cặp vào bảng APA
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r_ij, p_ij = stats.spearmanr(sub[cols[i]].to_numpy(), sub[cols[j]].to_numpy())
            apa_rows.append([f"{cols[i]} × {cols[j]}", str(n), f"{float(r_ij):.4f}", str(n - 2), _fmt_p(float(p_ij))])

    chart_data = {
        "type": "scatter",
        "title": f"Biểu đồ phân tán (Spearman ρ = {rho:.3f}): {col1} vs {col2}",
        "x_label": str(col1),
        "y_label": str(col2),
        "x": x.tolist(),
        "y": y.tolist()
    }
    return {
        "test_id": "spearman_rho",
        "test_name_vi": "Hệ số tương quan hạng Spearman (Spearman Rho)",
        "test_name_en": "Spearman's Rank Correlation (Rho)",
        "panel": "Panel D",
        "statistic_name": "ρ",
        "statistic": round(rho, 4),
        "df": df_val,
        "p_value": round(p_val, 6),
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }


def run_regression_analysis(
    df: pd.DataFrame,
    iv_cols: List[str],
    dv_col: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Phân tích hồi quy đơn biến (Simple Linear Regression - 1 IV) và
    Phân tích hồi quy đa biến (Multiple Linear Regression - >= 2 IVs) - Panel D (UR.F002.04).
    """
    all_cols = list(iv_cols) + [dv_col]
    sub = df[all_cols].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(sub)
    p = len(iv_cols)
    if n <= p + 1:
        raise ValueError(f"Cỡ mẫu (n = {n}) phải lớn hơn số biến độc lập + 1 ({p + 1}) để chạy hồi quy.")

    X_raw = sub[iv_cols].to_numpy(dtype=float)
    y = sub[dv_col].to_numpy(dtype=float)
    X = np.column_stack([np.ones(n), X_raw])

    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ beta
    resid = y - y_hat

    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    ss_reg = max(0.0, ss_tot - ss_res)

    df_reg = p
    df_res = n - p - 1
    ms_reg = ss_reg / df_reg if df_reg > 0 else 0.0
    ms_res = ss_res / df_res if df_res > 0 else 1e-12

    f_stat = ms_reg / ms_res if ms_res > 0 else 0.0
    p_model = float(1.0 - stats.f.cdf(f_stat, df_reg, df_res))
    r_sq = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    adj_r_sq = 1.0 - (1.0 - r_sq) * (n - 1) / df_res if df_res > 0 else r_sq

    cov_beta = ms_res * np.linalg.pinv(X.T @ X)
    se_beta = np.sqrt(np.maximum(0.0, np.diag(cov_beta)))
    t_vals = np.divide(beta, se_beta, out=np.zeros_like(beta), where=se_beta > 0)
    p_vals = 2.0 * (1.0 - stats.t.cdf(np.abs(t_vals), df=df_res))
    t_crit = stats.t.ppf(1.0 - alpha / 2.0, df=df_res)
    ci_lows = beta - t_crit * se_beta
    ci_highs = beta + t_crit * se_beta

    is_multiple = p > 1
    test_id = "multiple_regression" if is_multiple else "regression_analysis"
    test_name_vi = (
        "Phân tích hồi quy đa biến (Multiple Regression)"
        if is_multiple else "Phân tích hồi quy đơn biến (Regression Analysis)"
    )
    test_name_en = "Multiple Linear Regression" if is_multiple else "Simple Linear Regression"

    eq_terms = [f"{beta[0]:.4f}"]
    for idx, col in enumerate(iv_cols):
        b_val = beta[idx + 1]
        sign_str = "+" if b_val >= 0 else "-"
        eq_terms.append(f"{sign_str} {abs(b_val):.4f}×[{col}]")
    equation_str = f"{dv_col} = " + " ".join(eq_terms)

    sig = p_model < alpha
    interp = (
        f"{test_name_vi} dự báo '{dv_col}' từ {', '.join(iv_cols)} (n = {n}) cho thấy mô hình hồi quy "
        f"{'CÓ' if sig else 'KHÔNG CÓ'} ý nghĩa thống kê ở mức α = {alpha} "
        f"(F({df_reg}, {df_res}) = {f_stat:.4f}, p = {_fmt_p(p_model)}, R² = {r_sq:.4f}, R² hiệu chỉnh = {adj_r_sq:.4f}). "
        f"Phương trình hồi quy: {equation_str}."
    )

    apa_headers = ["Biến dự báo", "Hệ số B", "SE", "t", "p", f"KTC {int((1-alpha)*100)}% cho B"]
    apa_rows = [[
        "(Hằng số / Intercept)", f"{beta[0]:.4f}", f"{se_beta[0]:.4f}",
        f"{t_vals[0]:.4f}", _fmt_p(float(p_vals[0])), f"[{ci_lows[0]:.4f}, {ci_highs[0]:.4f}]"
    ]]
    for idx, col in enumerate(iv_cols):
        i = idx + 1
        apa_rows.append([
            str(col), f"{beta[i]:.4f}", f"{se_beta[i]:.4f}",
            f"{t_vals[i]:.4f}", _fmt_p(float(p_vals[i])), f"[{ci_lows[i]:.4f}, {ci_highs[i]:.4f}]"
        ])
    apa_rows.append([
        "Mô hình tổng thể", f"R² = {r_sq:.4f}", f"Adj R² = {adj_r_sq:.4f}",
        f"F({df_reg},{df_res}) = {f_stat:.4f}", _fmt_p(p_model), equation_str
    ])

    chart_data = {
        "type": "scatter",
        "title": f"Biểu đồ hồi quy: {iv_cols[0]} → {dv_col} (R² = {r_sq:.3f})",
        "x_label": str(iv_cols[0]) if not is_multiple else "Giá trị dự báo (Ŷ)",
        "y_label": str(dv_col),
        "x": sub[iv_cols[0]].to_numpy().tolist() if not is_multiple else y_hat.tolist(),
        "y": y.tolist(),
        "reg_line": {
            "intercept": float(beta[0]) if not is_multiple else 0.0,
            "slope": float(beta[1]) if not is_multiple else 1.0,
        }
    }
    return {
        "test_id": test_id,
        "test_name_vi": test_name_vi,
        "test_name_en": test_name_en,
        "panel": "Panel D",
        "statistic_name": "F",
        "statistic": round(float(f_stat), 4),
        "df": [df_reg, df_res],
        "p_value": round(p_model, 6),
        "r_squared": round(float(r_sq), 4),
        "adj_r_squared": round(float(adj_r_sq), 4),
        "equation": equation_str,
        "significant": bool(sig),
        "alpha": alpha,
        "interpretation_vi": interp,
        "apa_table": {"headers": apa_headers, "rows": apa_rows},
        "chart": chart_data,
    }
