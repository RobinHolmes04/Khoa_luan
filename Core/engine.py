# -*- coding: utf-8 -*-
"""
Lõi xử lý trung tâm Pharta (Core Processing Engine) - UR.F001.02, UR.F002.01-04, UR.F003.01-03.
Độc lập 100% với giao diện người dùng (GUI). Có thể gọi qua API Python, JSON payload hoặc CLI.
"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd

from Core.assumptions import (
    clean_series,
    detect_variable_type,
    test_normality,
    test_homogeneity,
    check_nd_h_groups,
)
from Core.stats_tests import (
    run_z_test_proportions,
    run_one_sample_t_test,
    run_z_test_known_variance,
    run_two_sample_t_test,
    run_mann_whitney_and_median_test,
    run_paired_t_test,
    run_wilcoxon_and_sign_test,
    run_one_way_anova,
    run_kruskal_wallis,
    run_rcbd_anova,
    run_two_way_anova,
    run_friedman_two_way_anova,
    run_chi_square_or_yates_or_fisher,
    run_mcnemar_test,
    run_cochran_q_test,
    run_mantel_haenszel_test,
    run_pearson_correlation,
    run_partial_correlation,
    run_spearman_correlation,
    run_regression_analysis,
)


class PhartaCoreEngine:
    """
    Bộ máy suy luận Cây quyết định thống kê Y Dược theo Phụ lục A (Panel A, B, C, D).
    """

    @staticmethod
    def load_file(file_path: str) -> pd.DataFrame:
        """Đọc dữ liệu từ tệp CSV hoặc Excel (.xlsx, .xls) - UR.F001.02."""
        lower = file_path.lower()
        if lower.endswith(".xlsx") or lower.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin1")
        return PhartaCoreEngine.preprocess_dataframe(df)

    @staticmethod
    def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Tiền xử lý bảng dữ liệu thô: loại bỏ các hàng và cột hoàn toàn trống."""
        if df is None or df.empty:
            return pd.DataFrame()
        cleaned = df.copy()
        # Chuyển các ô chuỗi chỉ chứa khoảng trắng thành NaN
        for col in cleaned.columns:
            if cleaned[col].dtype == object or pd.api.types.is_string_dtype(cleaned[col]):
                s = cleaned[col].astype(str).str.strip()
                cleaned[col] = s.replace({"": np.nan, "nan": np.nan, "NaN": np.nan, "None": np.nan})
                # Tự động ép sang kiểu số nếu toàn bộ giá trị không rỗng là số
                non_na = cleaned[col].dropna()
                if len(non_na) > 0:
                    num_conv = pd.to_numeric(non_na, errors="coerce")
                    if num_conv.notna().all():
                        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
        cleaned = cleaned.dropna(how="all").dropna(axis=1, how="all")
        return cleaned

    @staticmethod
    def inspect_variables(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Tự động quét và phân loại toàn bộ các cột trong DataFrame."""
        clean_df = PhartaCoreEngine.preprocess_dataframe(df)
        info = {}
        for col in clean_df.columns:
            v_type, n_unique, reason = detect_variable_type(clean_df, str(col))
            info[str(col)] = {
                "type": v_type,
                "n_unique": n_unique,
                "reason": reason,
                "n_valid": int(clean_df[col].dropna().shape[0])
            }
        return info

    @classmethod
    def analyze(cls, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hàm thực thi chính của Lõi xử lý (nhận Request Payload và trả về Response JSON chuẩn).
        Tham số trong `request`:
        - dataframe: pd.DataFrame hoặc list/dict records
        - independent_vars: list[str] (Biến độc lập / phân nhóm, có thể rỗng)
        - dependent_vars: list[str] (Biến phụ thuộc / các biến chính cần phân tích)
        - third_var: Optional[str] (Biến rời rạc thứ 3 / phân tầng cho Mantel-Haenszel)
        - var_types: Dict[str, str] (Thiết lập kiểu biến thủ công: {'col': 'discrete'|'continuous'}; nếu để trống sẽ tự động phát hiện kèm cảnh báo)
        - alpha: float (Mức ý nghĩa thống kê, mặc định 0.05)
        - paired: bool (Dữ liệu bắt cặp / lặp lại, mặc định False)
        - is_proportion_outcome: bool (Dữ liệu báo cáo dạng tỷ lệ phần trăm ở Panel A, mặc định False)
        - pop_variance_known: bool (Đã biết phương sai quần thể ở Panel B, mặc định False)
        - pop_sigma1: float (Độ lệch chuẩn quần thể 1 khi biết phương sai, mặc định 1.0)
        - pop_sigma2: Optional[float] (Độ lệch chuẩn quần thể 2)
        - mu0: float (Giá trị kiểm định lý thuyết cho One-sample t-test / Z-test, mặc định 0.0)
        - p0: float (Tỷ lệ lý thuyết cho Z-test tỷ lệ 1 mẫu, mặc định 0.5)
        - format_mode: str ('auto' | 'preselected' | 'free' cho Panel D: Hồi quy vs Tương quan)
        - data_is_contingency_table: bool (Nếu bảng đầu vào đã là bảng tần số chéo tổng hợp sẵn)
        """
        t_start = time.perf_counter()
        warnings: List[str] = []
        decision_path: List[Dict[str, str]] = []

        raw_df = request.get("dataframe")
        if isinstance(raw_df, pd.DataFrame):
            df = cls.preprocess_dataframe(raw_df)
        elif isinstance(raw_df, (list, dict)):
            df = cls.preprocess_dataframe(pd.DataFrame(raw_df))
        else:
            raise ValueError("Request payload thiếu dữ liệu 'dataframe' hợp lệ.")

        if df.empty:
            raise ValueError("Bảng dữ liệu trống. Vui lòng nạp dữ liệu hoặc nhập số liệu trước khi phân tích.")

        alpha = float(request.get("alpha", 0.05))
        paired = bool(request.get("paired", False))
        is_prop = bool(request.get("is_proportion_outcome", False))
        pop_var_known = bool(request.get("pop_variance_known", False))
        pop_sigma1 = float(request.get("pop_sigma1", 1.0))
        pop_sigma2 = request.get("pop_sigma2")
        pop_sigma2 = float(pop_sigma2) if pop_sigma2 is not None else None
        mu0 = float(request.get("mu0", 0.0))
        p0 = float(request.get("p0", 0.5))
        format_mode = str(request.get("format_mode", "auto")).lower()
        is_contingency_matrix = bool(request.get("data_is_contingency_table", False))

        iv_cols: List[str] = [c for c in request.get("independent_vars", []) if c in df.columns]
        dv_cols: List[str] = [c for c in request.get("dependent_vars", []) if c in df.columns]
        third_var: Optional[str] = request.get("third_var")
        if third_var not in df.columns:
            third_var = None

        # Nếu người dùng chưa chọn biến nào, tự động lấy các cột không phải cột ID/STT
        if not iv_cols and not dv_cols:
            candidate_cols = [
                c for c in df.columns
                if str(c).strip().lower() not in ("id", "stt", "id_benhnhan", "ma_bn", "index")
            ]
            if not candidate_cols:
                candidate_cols = list(df.columns)
            dv_cols = candidate_cols
            warnings.append(
                "CẢNH BÁO: Bạn chưa chọn biến phân tích. Hệ thống tự động chọn các cột dữ liệu: "
                + ", ".join(map(str, dv_cols)) + "."
            )

        # Kiểm tra thiết lập kiểu biến (UR.F001.02 NOTE)
        user_var_types: Dict[str, str] = request.get("var_types") or {}
        resolved_types: Dict[str, str] = {}
        auto_detected_cols: List[str] = []

        all_selected_cols = list(dict.fromkeys(iv_cols + dv_cols + ([third_var] if third_var else [])))
        for col in all_selected_cols:
            u_type = user_var_types.get(col, "auto")
            if u_type in ("discrete", "continuous"):
                resolved_types[col] = u_type
            else:
                det_type, _, _ = detect_variable_type(df, col)
                resolved_types[col] = det_type
                auto_detected_cols.append(f"{col} → {'Rời rạc (Định tính)' if det_type == 'discrete' else 'Liên tục (Định lượng)'}")

        if auto_detected_cols:
            warnings.append(
                "CẢNH BÁO (UR.F001.02): Bạn chưa thiết lập thủ công kiểu biến cho một số cột. "
                "Hệ thống đã tự động phân loại và có thể có sai sót: "
                + "; ".join(auto_detected_cols) + "."
            )

        def add_step(panel: str, node: str, branch: str, detail: str = "") -> None:
            decision_path.append({
                "panel": panel,
                "node": node,
                "branch": branch,
                "detail": detail
            })

        # ======================================================================
        # PANEL A: PHÂN LOẠI BIẾN VÀ ĐIỀU HƯỚNG TỔNG QUAN (UR.F002.01)
        # ======================================================================
        has_iv = len(iv_cols) > 0
        add_step(
            "Panel A",
            "Có biến độc lập (Independent Variable) không?",
            "Có" if has_iv else "Không",
            f"Biến độc lập: {iv_cols if has_iv else 'Không chỉ định'}; Biến phụ thuộc/chính: {dv_cols}"
        )

        target_panel = ""
        assumptions_report: Dict[str, Any] = {}

        if not has_iv:
            # Không có biến độc lập -> Xem xét kiểu của các biến chính (dv_cols)
            primary_types = [resolved_types[c] for c in dv_cols]
            if all(t == "discrete" for t in primary_types) or is_contingency_matrix:
                if is_prop and len(dv_cols) == 1:
                    add_step("Panel A", "Dữ liệu tỷ lệ phần trăm (1 biến rời rạc)", "Z-test tỷ lệ", f"Cột: {dv_cols[0]}")
                    result = run_z_test_proportions(df, iv_col=dv_cols[0], dv_col=None, p0=p0, alpha=alpha)
                    return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

                target_panel = "Panel C"
                add_step("Panel A", "Phân loại biến chính (Primary Variables)", "Rời rạc (Discrete) → Chuyển sang Panel C")
            elif all(t == "continuous" for t in primary_types):
                # Chú ý (UR.F001.01 NOTE): Người dùng có thể chọn 1, 2 hoặc nhiều cột liên tục để kiểm định
                # (ví dụ: 1 mẫu t-test/Z-test, hoặc 2 cột bắt cặp Trước-Sau ở Panel B, hoặc tương quan ở Panel D)
                if len(dv_cols) == 1 or paired or pop_var_known:
                    target_panel = "Panel B"
                    add_step(
                        "Panel A",
                        "Biến liên tục phân tích so sánh mẫu/bắt cặp",
                        "Chuyển sang Panel B",
                        "Hỗ trợ phân tích theo cặp (Wide format) hoặc kiểm định 1 mẫu không cần tách cột biến độc lập."
                    )
                elif format_mode == "compare_groups":
                    target_panel = "Panel B"
                    add_step("Panel A", "So sánh các cột định lượng độc lập (Wide format)", "Chuyển sang Panel B")
                else:
                    target_panel = "Panel D"
                    add_step("Panel A", "Phân loại biến chính (Primary Variables)", "Liên tục (Continuous) → Chuyển sang Panel D")
            else:
                # Hỗn hợp rời rạc + liên tục nhưng người dùng để chung trong dv_cols
                disc_cols = [c for c in dv_cols if resolved_types[c] == "discrete"]
                cont_cols = [c for c in dv_cols if resolved_types[c] == "continuous"]
                iv_cols = disc_cols
                dv_cols = cont_cols
                has_iv = True
                target_panel = "Panel B"
                add_step(
                    "Panel A",
                    "Tự động tách biến Rời rạc làm biến phân nhóm & Liên tục làm biến phụ thuộc",
                    f"IV={iv_cols}, DV={dv_cols} → Chuyển sang Panel B"
                )
        else:
            # Có biến độc lập
            iv_types = [resolved_types[c] for c in iv_cols]
            if all(t == "continuous" for t in iv_types):
                target_panel = "Panel D"
                add_step("Panel A", "Bản chất biến độc lập", "Liên tục (Continuous) → Chuyển sang Panel D")
            else:
                add_step("Panel A", "Bản chất biến độc lập", "Rời rạc (Discrete)")
                if is_prop:
                    n_levels = int(df[iv_cols[0]].dropna().nunique())
                    add_step("Panel A", "Dữ liệu báo cáo dạng tỷ lệ phần trăm?", f"Có (Số mức biến độc lập = {n_levels})")
                    if n_levels in (1, 2):
                        add_step("Panel A", "Số mức của biến độc lập rời rạc", f"{n_levels} mức → Z-test tỷ lệ")
                        dv_target = dv_cols[0] if dv_cols else None
                        result = run_z_test_proportions(df, iv_col=iv_cols[0], dv_col=dv_target, p0=p0, alpha=alpha)
                        return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)
                    else:
                        add_step("Panel A", "Số mức của biến độc lập rời rạc", f"{n_levels} (> 2 mức) → Chi Square Test of Independence")
                        if not dv_cols:
                            raise ValueError("Cần chọn biến phụ thuộc rời rạc để lập bảng chéo Chi-square.")
                        ct = pd.crosstab(df[iv_cols[0]], df[dv_cols[0]])
                        result = run_chi_square_or_yates_or_fisher(
                            ct, row_name=iv_cols[0], col_name=dv_cols[0],
                            force_test="chi_square_independence", alpha=alpha
                        )
                        return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)
                else:
                    add_step("Panel A", "Dữ liệu báo cáo dạng tỷ lệ phần trăm?", "Không")
                    if not dv_cols:
                        # Nếu chỉ đưa 1 biến vào IV mà chưa chọn DV
                        if resolved_types[iv_cols[0]] == "discrete":
                            dv_cols = iv_cols
                            iv_cols = []
                            target_panel = "Panel C"
                        else:
                            dv_cols = iv_cols
                            iv_cols = []
                            target_panel = "Panel B"
                    else:
                        dv_type = resolved_types[dv_cols[0]]
                        if dv_type == "continuous":
                            target_panel = "Panel B"
                            add_step("Panel A", "Bản chất biến phụ thuộc", "Liên tục (Continuous) → Chuyển sang Panel B")
                        else:
                            target_panel = "Panel C"
                            add_step("Panel A", "Bản chất biến phụ thuộc", "Rời rạc (Discrete) → Chuyển sang Panel C")

        # ======================================================================
        # PANEL B: BIẾN ĐỘC LẬP RỜI RẠC & BIẾN PHỤ THUỘC LIÊN TỤC (UR.F002.02)
        # ======================================================================
        if target_panel == "Panel B":
            disc_ivs = [c for c in iv_cols if resolved_types.get(c) == "discrete"]

            # Trường hợp 1: Có 2 biến độc lập rời rạc (Two-way ANOVA vs Friedman Two-way ANOVA)
            if len(disc_ivs) >= 2:
                iv1, iv2 = disc_ivs[0], disc_ivs[1]
                dv = dv_cols[0]
                add_step("Panel B", "Số lượng biến độc lập rời rạc", f"2 biến ({iv1}, {iv2})")

                sub = df[[iv1, iv2, dv]].copy()
                sub[dv] = pd.to_numeric(sub[dv], errors="coerce")
                sub = sub.dropna()
                cell_groups = {}
                for (g1, g2), g_df in sub.groupby([iv1, iv2]):
                    arr = g_df[dv].to_numpy(dtype=float)
                    if len(arr) > 0:
                        cell_groups[f"{g1}_{g2}"] = arr

                nd_h_info = check_nd_h_groups(cell_groups, alpha=alpha, require_homogeneity=True)
                assumptions_report = nd_h_info

                if nd_h_info["nd_h_passed"]:
                    add_step("Panel B", "Kiểm tra phân phối chuẩn & đồng nhất phương sai (ND/H)", "Thỏa mãn ND/H → Two-way ANOVA", nd_h_info["summary"])
                    result = run_two_way_anova(df, iv1, iv2, dv, alpha=alpha)
                else:
                    add_step("Panel B", "Kiểm tra phân phối chuẩn & đồng nhất phương sai (ND/H)", "Vi phạm ND/H → Friedman Two-way ANOVA", nd_h_info["summary"])
                    # Pivot hoặc dùng các mức của iv2 làm cột theo từng khối iv1
                    piv = sub.pivot_table(index=iv1, columns=iv2, values=dv, aggfunc="mean")
                    if piv.shape[0] < 2 or piv.shape[1] < 2:
                        # Nếu nhiều quan sát lặp lại trong mỗi ô, đánh số khối trong từng mức iv1
                        sub = sub.copy()
                        sub["_block_id"] = sub.groupby(iv2).cumcount()
                        piv = sub.pivot_table(index="_block_id", columns=iv2, values=dv, aggfunc="mean").dropna()
                    result = run_friedman_two_way_anova(piv, alpha=alpha)

                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

            # Trường hợp 2: Dữ liệu dạng Wide format (không cần cột IV, các nhóm nằm ở nhiều cột DV liên tục)
            if len(disc_ivs) == 0:
                k_cols = len(dv_cols)
                add_step("Panel B", "Số lượng biến độc lập rời rạc", f"1 yếu tố phân nhóm ngầm định ({k_cols} cột dữ liệu)")
                if k_cols == 1:
                    col = dv_cols[0]
                    arr = pd.to_numeric(df[col], errors="coerce").dropna().to_numpy(dtype=float)
                    if pop_var_known:
                        add_step("Panel B", "1 nhóm (Đã biết phương sai quần thể)", "Z-test")
                        result = run_z_test_known_variance({col: arr}, dv_name=col, iv_name="Mẫu", sigma1=pop_sigma1, mu0=mu0, alpha=alpha)
                    else:
                        add_step("Panel B", "Số mức trong biến độc lập", "1 nhóm (One level) → Kiểm định t một mẫu (One Sample t-test)")
                        result = run_one_sample_t_test(arr, var_name=col, mu0=mu0, alpha=alpha)
                    return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

                elif k_cols == 2:
                    c1, c2 = dv_cols[0], dv_cols[1]
                    add_step("Panel B", "Số mức trong biến độc lập", f"2 nhóm ({c1}, {c2})")
                    if paired:
                        add_step("Panel B", "Dữ liệu bắt cặp (Paired data)?", "Có (Paired)")
                        sub = df[[c1, c2]].apply(pd.to_numeric, errors="coerce").dropna()
                        a1 = sub[c1].to_numpy(dtype=float)
                        a2 = sub[c2].to_numpy(dtype=float)
                        diffs = a1 - a2
                        norm_diff = test_normality(diffs, alpha=alpha)
                        assumptions_report = {
                            "nd_h_passed": norm_diff["is_normal"],
                            "normality_of_differences": norm_diff,
                            "summary": f"Hiệu số ({c1} - {c2}): {norm_diff['message']}"
                        }
                        if norm_diff["is_normal"]:
                            add_step("Panel B", "Kiểm định phân phối chuẩn của hiệu số (ND/H)", "Thỏa mãn ND/H → Kiểm định t bắt cặp (Paired t-test)", norm_diff["message"])
                            result = run_paired_t_test(a1, a2, c1, c2, alpha=alpha)
                        else:
                            add_step("Panel B", "Kiểm định phân phối chuẩn của hiệu số (ND/H)", "Vi phạm ND/H → Kiểm định dấu hạng Wilcoxon / Sign Test", norm_diff["message"])
                            result = run_wilcoxon_and_sign_test(a1, a2, c1, c2, alpha=alpha)
                        return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)
                    else:
                        add_step("Panel B", "Dữ liệu bắt cặp (Paired data)?", "Không (Độc lập)")
                        groups = {
                            c1: pd.to_numeric(df[c1], errors="coerce").dropna().to_numpy(dtype=float),
                            c2: pd.to_numeric(df[c2], errors="coerce").dropna().to_numpy(dtype=float),
                        }
                        if pop_var_known:
                            add_step("Panel B", "Đã biết phương sai quần thể?", "Có → Z-test")
                            result = run_z_test_known_variance(groups, dv_name="Giá trị", iv_name="Nhóm", sigma1=pop_sigma1, sigma2=pop_sigma2, alpha=alpha)
                        else:
                            add_step("Panel B", "Đã biết phương sai quần thể?", "Không")
                            nd_h_info = check_nd_h_groups(groups, alpha=alpha, require_homogeneity=True)
                            assumptions_report = nd_h_info
                            if nd_h_info["nd_h_passed"]:
                                add_step("Panel B", "Kiểm tra phân phối chuẩn & đồng nhất phương sai (ND/H)", "Thỏa mãn ND/H → Kiểm định t hai mẫu độc lập", nd_h_info["summary"])
                                result = run_two_sample_t_test(groups, dv_name="Giá trị", iv_name="Nhóm", equal_var=True, alpha=alpha)
                            else:
                                add_step("Panel B", "Kiểm tra phân phối chuẩn & đồng nhất phương sai (ND/H)", "Vi phạm ND/H → Kiểm định Mann-Whitney U / Median Test", nd_h_info["summary"])
                                result = run_mann_whitney_and_median_test(groups, dv_name="Giá trị", iv_name="Nhóm", alpha=alpha)
                        return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

                else:  # k_cols >= 3
                    add_step("Panel B", "Số mức trong biến độc lập", f"{k_cols} nhóm (>= 3 mức)")
                    if paired:
                        if format_mode == "friedman":
                            add_step("Panel B", "Dữ liệu khối bắt cặp phi tham số", "Friedman Two-way ANOVA")
                            result = run_friedman_two_way_anova(df[dv_cols], alpha=alpha)
                        else:
                            add_step("Panel B", "Dữ liệu bắt cặp (Paired data)?", "Có → Thiết kế khối ngẫu nhiên hoàn chỉnh (RCBD)")
                            result = run_rcbd_anova(df[dv_cols], alpha=alpha)
                        return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)
                    else:
                        add_step("Panel B", "Dữ liệu bắt cặp (Paired data)?", "Không (Độc lập)")
                        groups = {
                            c: pd.to_numeric(df[c], errors="coerce").dropna().to_numpy(dtype=float)
                            for c in dv_cols
                        }
                        nd_h_info = check_nd_h_groups(groups, alpha=alpha, require_homogeneity=True)
                        assumptions_report = nd_h_info
                        if nd_h_info["nd_h_passed"]:
                            add_step("Panel B", "Kiểm tra ND/H", "Thỏa mãn ND/H → Phân tích phương sai một yếu tố (One-way ANOVA)", nd_h_info["summary"])
                            result = run_one_way_anova(groups, dv_name="Giá trị", iv_name="Nhóm", alpha=alpha)
                        else:
                            add_step("Panel B", "Kiểm tra ND/H", "Vi phạm ND/H → Kiểm định Kruskal-Wallis", nd_h_info["summary"])
                            result = run_kruskal_wallis(groups, dv_name="Giá trị", iv_name="Nhóm", alpha=alpha)
                        return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

            # Trường hợp 3: Dữ liệu dạng Long format (1 biến độc lập rời rạc + 1 biến phụ thuộc liên tục)
            iv = disc_ivs[0]
            dv = dv_cols[0]
            sub = df[[iv, dv]].copy()
            sub[dv] = pd.to_numeric(sub[dv], errors="coerce")
            sub = sub.dropna()
            levels = list(sub[iv].unique())
            n_levels = len(levels)

            add_step("Panel B", "Số lượng biến độc lập rời rạc", f"1 biến ({iv})")
            add_step("Panel B", "Số nhóm (Levels) của biến độc lập", f"{n_levels} nhóm: {levels}")

            if n_levels == 1:
                arr = sub[dv].to_numpy(dtype=float)
                if pop_var_known:
                    add_step("Panel B", "1 nhóm (Biết phương sai quần thể)", "Z-test")
                    result = run_z_test_known_variance({str(levels[0]): arr}, dv_name=dv, iv_name=iv, sigma1=pop_sigma1, mu0=mu0, alpha=alpha)
                else:
                    add_step("Panel B", "1 nhóm (One level)", "Kiểm định t một mẫu (One Sample t-test)")
                    result = run_one_sample_t_test(arr, var_name=dv, mu0=mu0, alpha=alpha)
                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

            groups = {str(lv): sub[sub[iv] == lv][dv].to_numpy(dtype=float) for lv in levels}

            if n_levels == 2:
                if paired:
                    add_step("Panel B", "Dữ liệu bắt cặp (Paired data)?", "Có")
                    g1, g2 = groups[str(levels[0])], groups[str(levels[1])]
                    min_len = min(len(g1), len(g2))
                    g1, g2 = g1[:min_len], g2[:min_len]
                    norm_diff = test_normality(g1 - g2, alpha=alpha)
                    assumptions_report = {
                        "nd_h_passed": norm_diff["is_normal"],
                        "normality_of_differences": norm_diff,
                        "summary": norm_diff["message"]
                    }
                    if norm_diff["is_normal"]:
                        add_step("Panel B", "Kiểm tra phân phối chuẩn của hiệu số (ND/H)", "Thỏa mãn ND/H → Kiểm định t bắt cặp (Paired t-test)", norm_diff["message"])
                        result = run_paired_t_test(g1, g2, str(levels[0]), str(levels[1]), alpha=alpha)
                    else:
                        add_step("Panel B", "Kiểm tra phân phối chuẩn của hiệu số (ND/H)", "Vi phạm ND/H → Kiểm định dấu hạng Wilcoxon / Sign Test", norm_diff["message"])
                        result = run_wilcoxon_and_sign_test(g1, g2, str(levels[0]), str(levels[1]), alpha=alpha)
                else:
                    add_step("Panel B", "Dữ liệu bắt cặp (Paired data)?", "Không")
                    if pop_var_known:
                        add_step("Panel B", "Đã biết phương sai quần thể?", "Có → Z-test")
                        result = run_z_test_known_variance(groups, dv_name=dv, iv_name=iv, sigma1=pop_sigma1, sigma2=pop_sigma2, alpha=alpha)
                    else:
                        add_step("Panel B", "Đã biết phương sai quần thể?", "Không")
                        nd_h_info = check_nd_h_groups(groups, alpha=alpha, require_homogeneity=True)
                        assumptions_report = nd_h_info
                        if nd_h_info["nd_h_passed"]:
                            add_step("Panel B", "Kiểm tra ND/H", "Thỏa mãn ND/H → Kiểm định t hai mẫu độc lập (Two-sample t-test)", nd_h_info["summary"])
                            result = run_two_sample_t_test(groups, dv_name=dv, iv_name=iv, equal_var=True, alpha=alpha)
                        else:
                            add_step("Panel B", "Kiểm tra ND/H", "Vi phạm ND/H → Kiểm định Mann-Whitney U / Median Test", nd_h_info["summary"])
                            result = run_mann_whitney_and_median_test(groups, dv_name=dv, iv_name=iv, alpha=alpha)
                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

            else:  # n_levels >= 3
                if paired:
                    add_step("Panel B", "Dữ liệu bắt cặp (Paired data)?", "Có → Thiết kế khối ngẫu nhiên hoàn chỉnh (RCBD)")
                    min_len = min(len(v) for v in groups.values())
                    mat_df = pd.DataFrame({k: v[:min_len] for k, v in groups.items()})
                    result = run_rcbd_anova(mat_df, alpha=alpha)
                else:
                    add_step("Panel B", "Dữ liệu bắt cặp (Paired data)?", "Không")
                    nd_h_info = check_nd_h_groups(groups, alpha=alpha, require_homogeneity=True)
                    assumptions_report = nd_h_info
                    if nd_h_info["nd_h_passed"]:
                        add_step("Panel B", "Kiểm tra ND/H", "Thỏa mãn ND/H → Phân tích phương sai một yếu tố (One-way ANOVA)", nd_h_info["summary"])
                        result = run_one_way_anova(groups, dv_name=dv, iv_name=iv, alpha=alpha)
                    else:
                        add_step("Panel B", "Kiểm tra ND/H", "Vi phạm ND/H → Kiểm định Kruskal-Wallis", nd_h_info["summary"])
                        result = run_kruskal_wallis(groups, dv_name=dv, iv_name=iv, alpha=alpha)
                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

        # ======================================================================
        # PANEL C: BIẾN RỜI RẠC - BẢNG CHÉO (UR.F002.03)
        # ======================================================================
        if target_panel == "Panel C":
            all_disc = list(dict.fromkeys(iv_cols + dv_cols))
            if third_var is None and len(all_disc) >= 3 and not paired and not is_contingency_matrix:
                third_var = all_disc[2]

            if third_var is not None and len(all_disc) >= 2:
                add_step("Panel C", "Có biến rời rạc thứ 3 (Third Discrete Variable)?", f"Có ({third_var}) → Kiểm định Mantel-Haenszel Chi Square")
                result = run_mantel_haenszel_test(df, iv_col=all_disc[0], dv_col=all_disc[1], strata_col=third_var, alpha=alpha)
                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

            add_step("Panel C", "Có biến rời rạc thứ 3 (Third Discrete Variable)?", "Không")

            if paired:
                add_step("Panel C", "Dữ liệu bắt cặp (Paired data)?", "Có")
                if is_contingency_matrix:
                    ct = df[all_disc].apply(pd.to_numeric, errors="coerce").dropna()
                    if ct.shape == (2, 2):
                        add_step("Panel C", "Kích thước bảng chéo", "Bảng 2×2 → Kiểm định McNemar")
                        result = run_mcnemar_test(ct, name1="Hàng", name2="Cột", alpha=alpha)
                    else:
                        add_step("Panel C", "Kích thước bảng chéo", "Lớn hơn 2×2 → Kiểm định Cochran's Q")
                        result = run_cochran_q_test(ct, alpha=alpha)
                    return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

                if len(all_disc) == 2:
                    c1, c2 = all_disc[0], all_disc[1]
                    ct = pd.crosstab(df[c1], df[c2])
                    if ct.shape == (2, 2):
                        add_step("Panel C", "Kích thước bảng chéo", "Ma trận 2×2 → Kiểm định McNemar (McNemar Test)")
                        result = run_mcnemar_test(ct, name1=c1, name2=c2, alpha=alpha)
                    else:
                        add_step("Panel C", "Kích thước bảng chéo", f"Lớn hơn 2×2 ({ct.shape[0]}×{ct.shape[1]}) → Kiểm định Cochran's Q")
                        result = run_cochran_q_test(df[all_disc], alpha=alpha)
                elif len(all_disc) >= 3:
                    add_step("Panel C", "Kích thước bảng chéo / Số nhóm bắt cặp", f"{len(all_disc)} biến rời rạc bắt cặp (> 2×2) → Kiểm định Cochran's Q")
                    result = run_cochran_q_test(df[all_disc], alpha=alpha)
                else:
                    raise ValueError("Kiểm định dữ liệu rời rạc bắt cặp (McNemar / Cochran's Q) cần ít nhất 2 cột biến rời rạc.")
                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

            else:
                add_step("Panel C", "Dữ liệu bắt cặp (Paired data)?", "Không")
                if is_contingency_matrix:
                    ct = df[all_disc].apply(pd.to_numeric, errors="coerce").dropna()
                    row_name, col_name = "Nhóm hàng", "Nhóm cột"
                elif len(all_disc) >= 2:
                    row_name, col_name = all_disc[0], all_disc[1]
                    ct = pd.crosstab(df[row_name], df[col_name])
                elif len(all_disc) == 1:
                    # Nếu chỉ có 1 biến rời rạc không bắt cặp -> Kiểm định Z tỷ lệ 1 mẫu
                    add_step("Panel C", "Chỉ có 1 biến rời rạc đơn lẻ", "Z-test tỷ lệ 1 mẫu")
                    result = run_z_test_proportions(df, iv_col=all_disc[0], dv_col=None, p0=p0, alpha=alpha)
                    return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)
                else:
                    raise ValueError("Không đủ biến rời rạc để lập bảng tiếp liên.")

                result = run_chi_square_or_yates_or_fisher(ct, row_name=str(row_name), col_name=str(col_name), alpha=alpha)
                c_info = result.get("contingency_info", {})
                assumptions_report = {
                    "contingency_check": c_info,
                    "summary": (
                        f"Kích thước bảng: {c_info.get('shape')}, Có ô trống: {c_info.get('has_empty_cell')}, "
                        f"Tần số kỳ vọng nhỏ nhất: {c_info.get('min_expected')}"
                    )
                }
                if result["test_id"] == "fisher_exact_test":
                    add_step("Panel C", "Kiểm tra ô trống và tần số kỳ vọng > 5", "Vi phạm (Có ô trống hoặc kỳ vọng ≤ 5) → Kiểm định chính xác Fisher", assumptions_report["summary"])
                elif result["test_id"] == "yates_chi_square":
                    add_step("Panel C", "Kiểm tra ô trống và tần số kỳ vọng > 5", "Thỏa mãn & Bảng 2×2 → Kiểm định Chi bình phương hiệu chỉnh Yates", assumptions_report["summary"])
                else:
                    add_step("Panel C", "Kiểm tra ô trống và tần số kỳ vọng > 5", "Thỏa mãn & Bảng > 2×2 → Kiểm định Chi bình phương về tính độc lập", assumptions_report["summary"])

                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

        # ======================================================================
        # PANEL D: BIẾN LIÊN TỤC - TƯƠNG QUAN & HỒI QUY (UR.F002.04)
        # ======================================================================
        if target_panel == "Panel D":
            cont_ivs = [c for c in iv_cols if resolved_types.get(c) == "continuous"]
            cont_dvs = [c for c in dv_cols if resolved_types.get(c) == "continuous"]
            all_cont = list(dict.fromkeys(cont_ivs + cont_dvs))

            if len(all_cont) < 2:
                raise ValueError("Panel D (Tương quan & Hồi quy) yêu cầu ít nhất 2 biến định lượng liên tục.")

            # Xác định Preselected levels (Hồi quy) hay Free format / Không có IV (Tương quan)
            is_regression = (
                format_mode == "preselected"
                or (format_mode == "auto" and len(cont_ivs) >= 1 and len(cont_dvs) >= 1)
            )
            if format_mode == "free":
                is_regression = False

            if is_regression:
                if not cont_ivs:
                    cont_ivs = all_cont[:-1]
                    cont_dvs = [all_cont[-1]]
                dv_target = cont_dvs[0]
                iv_targets = [c for c in cont_ivs if c != dv_target]
                add_step("Panel D", "Định dạng phân tích", "Có biến độc lập & phụ thuộc (Preselected levels / Hồi quy)")
                if len(iv_targets) == 1:
                    add_step("Panel D", "Số lượng biến độc lập liên tục", f"1 biến ({iv_targets[0]}) → Phân tích hồi quy đơn biến (Regression Analysis)")
                else:
                    add_step("Panel D", "Số lượng biến độc lập liên tục", f"{len(iv_targets)} biến ({', '.join(iv_targets)}) → Phân tích hồi quy đa biến (Multiple Regression)")
                result = run_regression_analysis(df, iv_cols=iv_targets, dv_col=dv_target, alpha=alpha)
                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)
            else:
                add_step("Panel D", "Định dạng phân tích", "Định dạng tự do (Free format) / Không phân định biến độc lập")
                groups_cont = {
                    c: pd.to_numeric(df[c], errors="coerce").dropna().to_numpy(dtype=float)
                    for c in all_cont
                }
                nd_info = check_nd_h_groups(groups_cont, alpha=alpha, require_homogeneity=False)
                assumptions_report = nd_info

                if nd_info["all_normal"]:
                    add_step("Panel D", "Kiểm tra phân phối chuẩn (Normal distribution)", "Đạt phân phối chuẩn", nd_info["summary"])
                    if len(all_cont) == 2:
                        add_step("Panel D", "Số lượng biến liên tục", "2 biến → Phân tích tương quan Pearson (Pearson Correlation)")
                        result = run_pearson_correlation(df, all_cont[0], all_cont[1], alpha=alpha)
                    else:
                        add_step("Panel D", "Số lượng biến liên tục", f"{len(all_cont)} biến (> 2 biến) → Phân tích tương quan từng phần (Partial Correlation)")
                        result = run_partial_correlation(df, all_cont, alpha=alpha)
                else:
                    add_step("Panel D", "Kiểm tra phân phối chuẩn (Normal distribution)", "Vi phạm phân phối chuẩn → Hệ số tương quan hạng Spearman (Spearman Rho)", nd_info["summary"])
                    result = run_spearman_correlation(df, all_cont, alpha=alpha)

                return cls._finalize(result, decision_path, assumptions_report, warnings, resolved_types, t_start)

        raise RuntimeError(f"Không thể điều hướng cây quyết định cho cấu hình hiện tại (target={target_panel}).")

    @staticmethod
    def _finalize(
        result: Dict[str, Any],
        decision_path: List[Dict[str, str]],
        assumptions_report: Dict[str, Any],
        warnings: List[str],
        resolved_types: Dict[str, str],
        t_start: float
    ) -> Dict[str, Any]:
        chart = result.get("chart")
        if isinstance(chart, dict) and chart.get("type") == "boxplot" and "box_stats" not in chart:
            from Core.stats_tests import _summary_desc_continuous
            box_stats = {}
            for g_name, vals in chart.get("groups", {}).items():
                box_stats[str(g_name)] = _summary_desc_continuous(np.asarray(vals, dtype=float))
            chart["box_stats"] = box_stats

        elapsed_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        response = {
            "status": "success",
            "execution_time_ms": elapsed_ms,
            "warnings": warnings,
            "variable_types": resolved_types,
            "decision_path": decision_path,
            "assumptions": assumptions_report,
            "result": result,
        }
        return response

    @classmethod
    def to_json(cls, response: Dict[str, Any], indent: int = 2) -> str:
        """Tuần tự hóa kết quả sang chuỗi JSON chuẩn UTF-8."""
        return json.dumps(response, ensure_ascii=False, indent=indent)
