# -*- coding: utf-8 -*-
"""
Bộ dữ liệu y khoa giả lập chuẩn hóa (Standardized Clinical Datasets) cho toàn bộ các nhánh
của Cây quyết định Phụ lục A (Panel A, B, C, D) - Phục vụ thử nghiệm và thẩm định PQ (AC-02, AC-03).
"""

from typing import Dict, Any
import numpy as np
import pandas as pd


def get_sample_datasets() -> Dict[str, Dict[str, Any]]:
    """
    Trả về từ điển chứa các bộ dữ liệu mẫu y dược đại diện cho mọi nhánh trong Phụ lục A,
    kèm cấu hình gợi ý để người dùng hoặc bộ kiểm thử tự động chạy thử ngay.
    """
    rng = np.random.default_rng(42)
    samples: Dict[str, Dict[str, Any]] = {}

    # 1. Panel A - Z-test tỷ lệ (2 nhóm điều trị)
    n_a1 = 120
    nhom_a1 = ["Thuốc_Mới"] * 60 + ["Giả_Dược"] * 60
    kq_a1 = ([1] * 45 + [0] * 15) + ([1] * 28 + [0] * 32)
    samples["Panel A: Z-test tỷ lệ (Tỷ lệ khỏi bệnh 2 phác đồ)"] = {
        "df": pd.DataFrame({"Phac_Do": nhom_a1, "Khoi_Benh": kq_a1}),
        "config": {
            "independent_vars": ["Phac_Do"],
            "dependent_vars": ["Khoi_Benh"],
            "is_proportion_outcome": True,
            "paired": False,
        }
    }

    # 2. Panel B - One-sample t-test (Nồng độ Glucose máu so với ngưỡng 5.6 mmol/L)
    glucose = np.round(rng.normal(loc=6.15, scale=0.65, size=40), 2)
    samples["Panel B: Kiểm định t 1 mẫu (Glucose máu so với μ0 = 5.6)"] = {
        "df": pd.DataFrame({"Glucose_mmol_L": glucose}),
        "config": {
            "independent_vars": [],
            "dependent_vars": ["Glucose_mmol_L"],
            "mu0": 5.6,
            "paired": False,
        }
    }

    # 3. Panel B - Z-test biết phương sai quần thể
    ha_z1 = np.round(rng.normal(loc=132.0, scale=10.0, size=35), 1)
    ha_z2 = np.round(rng.normal(loc=124.0, scale=10.0, size=35), 1)
    samples["Panel B: Z-test 2 mẫu (Biết phương sai quần thể σ = 10)"] = {
        "df": pd.DataFrame({
            "Nhom_Thuoc": ["Amlodipin"] * 35 + ["Losartan"] * 35,
            "Huyet_Ap_Tam_Thu": np.concatenate([ha_z1, ha_z2])
        }),
        "config": {
            "independent_vars": ["Nhom_Thuoc"],
            "dependent_vars": ["Huyet_Ap_Tam_Thu"],
            "pop_variance_known": True,
            "pop_sigma1": 10.0,
            "pop_sigma2": 10.0,
        }
    }

    # 4. Panel B - Two-sample t-test (Đạt chuẩn ND/H)
    g1_norm = np.round(rng.normal(loc=125.0, scale=8.5, size=40), 2)
    g2_norm = np.round(rng.normal(loc=133.5, scale=8.2, size=40), 2)
    samples["Panel B: Kiểm định t 2 mẫu độc lập (Huyết áp - Đạt chuẩn ND/H)"] = {
        "df": pd.DataFrame({
            "Phac_Do": ["Phác đồ A"] * 40 + ["Phác đồ B"] * 40,
            "Huyet_Ap_mmHg": np.concatenate([g1_norm, g2_norm])
        }),
        "config": {
            "independent_vars": ["Phac_Do"],
            "dependent_vars": ["Huyet_Ap_mmHg"],
            "paired": False,
        }
    }

    # 5. Panel B - Mann-Whitney U / Median Test (Vi phạm phân phối chuẩn - Thời gian nằm viện lệch phải)
    g1_skew = np.round(rng.exponential(scale=4.0, size=45) + 2.0, 1)
    g2_skew = np.round(rng.exponential(scale=8.5, size=45) + 3.0, 1)
    samples["Panel B: Mann-Whitney U & Median Test (Ngày nằm viện - Không chuẩn)"] = {
        "df": pd.DataFrame({
            "Nhom_Phau_Thuat": ["Nội soi"] * 45 + ["Mổ hở"] * 45,
            "Ngay_Nam_Vien": np.concatenate([g1_skew, g2_skew])
        }),
        "config": {
            "independent_vars": ["Nhom_Phau_Thuat"],
            "dependent_vars": ["Ngay_Nam_Vien"],
            "paired": False,
        }
    }

    # 6. Panel B - Paired t-test (Huyết áp Trước - Sau can thiệp, hiệu số chuẩn)
    truoc = np.round(rng.normal(loc=142.0, scale=9.0, size=50), 1)
    sau = np.round(truoc - rng.normal(loc=8.5, scale=3.2, size=50), 1)
    samples["Panel B: Kiểm định t bắt cặp (Huyết áp Trước & Sau điều trị)"] = {
        "df": pd.DataFrame({"HA_Truoc": truoc, "HA_Sau": sau}),
        "config": {
            "independent_vars": [],
            "dependent_vars": ["HA_Truoc", "HA_Sau"],
            "paired": True,
        }
    }

    # 7. Panel B - Wilcoxon Signed Rank & Sign Test (Nồng độ Triglyceride Trước - Sau, hiệu số lệch mạnh)
    trig_truoc = np.round(rng.exponential(scale=2.5, size=45) + 2.2, 2)
    giam_trig = np.round(rng.exponential(scale=1.2, size=45), 2)
    trig_sau = np.round(np.maximum(0.5, trig_truoc - giam_trig), 2)
    samples["Panel B: Wilcoxon & Sign Test (Điểm đau VAS Trước & Sau - Không chuẩn)"] = {
        "df": pd.DataFrame({"VAS_Truoc": trig_truoc, "VAS_Sau": trig_sau}),
        "config": {
            "independent_vars": [],
            "dependent_vars": ["VAS_Truoc", "VAS_Sau"],
            "paired": True,
        }
    }

    # 8. Panel B - One-way ANOVA (3 mức liều thuốc đạt chuẩn ND/H)
    lieu_thap = np.round(rng.normal(loc=45.0, scale=5.0, size=30), 2)
    lieu_tb = np.round(rng.normal(loc=54.0, scale=5.2, size=30), 2)
    lieu_cao = np.round(rng.normal(loc=63.0, scale=4.8, size=30), 2)
    samples["Panel B: One-way ANOVA (Hiệu quả giảm LDL-C theo 3 mức liều)"] = {
        "df": pd.DataFrame({
            "Muc_Lieu": ["Liều 10mg"] * 30 + ["Liều 20mg"] * 30 + ["Liều 40mg"] * 30,
            "Giam_LDL_mg_dL": np.concatenate([lieu_thap, lieu_tb, lieu_cao])
        }),
        "config": {
            "independent_vars": ["Muc_Lieu"],
            "dependent_vars": ["Giam_LDL_mg_dL"],
            "paired": False,
        }
    }

    # 9. Panel B - Kruskal-Wallis (3 nhóm CRP vi phạm phân phối chuẩn)
    crp_nhe = np.round(rng.exponential(scale=3.0, size=35) + 1.0, 2)
    crp_vua = np.round(rng.exponential(scale=12.0, size=35) + 5.0, 2)
    crp_nang = np.round(rng.exponential(scale=35.0, size=35) + 15.0, 2)
    samples["Panel B: Kruskal-Wallis (Nồng độ CRP ở 3 mức độ viêm phổi)"] = {
        "df": pd.DataFrame({
            "Muc_Do_Benh": ["Nhẹ"] * 35 + ["Trung bình"] * 35 + ["Nặng"] * 35,
            "CRP_mg_L": np.concatenate([crp_nhe, crp_vua, crp_nang])
        }),
        "config": {
            "independent_vars": ["Muc_Do_Benh"],
            "dependent_vars": ["CRP_mg_L"],
            "paired": False,
        }
    }

    # 10. Panel B - RCBD (Thiết kế khối ngẫu nhiên hoàn chỉnh - Nồng độ thuốc tại 3 thời điểm trên cùng bệnh nhân)
    subj_base = rng.normal(loc=100.0, scale=12.0, size=25)
    t_1h = np.round(subj_base + rng.normal(loc=25.0, scale=3.0, size=25), 2)
    t_3h = np.round(subj_base + rng.normal(loc=10.0, scale=3.0, size=25), 2)
    t_6h = np.round(subj_base - rng.normal(loc=15.0, scale=3.0, size=25), 2)
    samples["Panel B: Thiết kế khối ngẫu nhiên hoàn chỉnh RCBD (3 thời điểm bắt cặp)"] = {
        "df": pd.DataFrame({"NongDo_1h": t_1h, "NongDo_3h": t_3h, "NongDo_6h": t_6h}),
        "config": {
            "independent_vars": [],
            "dependent_vars": ["NongDo_1h", "NongDo_3h", "NongDo_6h"],
            "paired": True,
        }
    }

    # 11. Panel B - Two-way ANOVA (2 biến độc lập rời rạc: Phác đồ × Giới tính, đạt chuẩn ND/H)
    rows_2w = []
    for pd_name, base_val in [("Thuốc_X", 115.0), ("Thuốc_Y", 128.0)]:
        for gioi, offset in [("Nam", 6.0), ("Nữ", 0.0)]:
            vals = np.round(rng.normal(loc=base_val + offset, scale=4.5, size=20), 2)
            for v in vals:
                rows_2w.append({"Phac_Do": pd_name, "Gioi_Tinh": gioi, "Huyet_Ap": v})
    samples["Panel B: Two-way ANOVA (Phác đồ × Giới tính - Đạt chuẩn ND/H)"] = {
        "df": pd.DataFrame(rows_2w),
        "config": {
            "independent_vars": ["Phac_Do", "Gioi_Tinh"],
            "dependent_vars": ["Huyet_Ap"],
            "paired": False,
        }
    }

    # 12. Panel B - Friedman Two-way ANOVA (2 biến độc lập rời rạc vi phạm ND/H)
    rows_fr = []
    for khoi in range(1, 26):
        for idx_m, muc in enumerate(["Trước", "Sau_1_Tuan", "Sau_4_Tuan"]):
            val = float(rng.exponential(scale=(10.0 / (idx_m + 1))) + (3 - idx_m))
            rows_fr.append({"Benh_Nhan_Khoi": f"BN_{khoi:02d}", "Thoi_Diem": muc, "Diem_Trieu_Chung": round(val, 2)})
    samples["Panel B: Friedman Two-way ANOVA (2 yếu tố vi phạm ND/H)"] = {
        "df": pd.DataFrame(rows_fr),
        "config": {
            "independent_vars": ["Benh_Nhan_Khoi", "Thoi_Diem"],
            "dependent_vars": ["Diem_Trieu_Chung"],
            "paired": False,
        }
    }

    # 13. Panel C - Yates' Chi-Square (Bảng 2x2 không ô trống, mọi kỳ vọng > 5)
    rows_yates = (
        [{"Hut_Thuoc": "Có", "Benh_COPD": "Có"}] * 38 +
        [{"Hut_Thuoc": "Có", "Benh_COPD": "Không"}] * 22 +
        [{"Hut_Thuoc": "Không", "Benh_COPD": "Có"}] * 16 +
        [{"Hut_Thuoc": "Không", "Benh_COPD": "Không"}] * 44
    )
    samples["Panel C: Yates' Chi-Square (Bảng 2x2 Hút thuốc & COPD, E > 5)"] = {
        "df": pd.DataFrame(rows_yates),
        "config": {
            "independent_vars": ["Hut_Thuoc"],
            "dependent_vars": ["Benh_COPD"],
            "paired": False,
        }
    }

    # 14. Panel C - Fisher's Exact Test (Bảng 2x2 có tần số kỳ vọng <= 5)
    rows_fisher = (
        [{"Thuoc": "Thuốc_Mới", "Soc_Phan_Ve": "Có"}] * 1 +
        [{"Thuoc": "Thuốc_Mới", "Soc_Phan_Ve": "Không"}] * 18 +
        [{"Thuoc": "Thuốc_Cũ", "Soc_Phan_Ve": "Có"}] * 7 +
        [{"Thuoc": "Thuốc_Cũ", "Soc_Phan_Ve": "Không"}] * 11
    )
    samples["Panel C: Kiểm định chính xác Fisher (Bảng có kỳ vọng <= 5)"] = {
        "df": pd.DataFrame(rows_fisher),
        "config": {
            "independent_vars": ["Thuoc"],
            "dependent_vars": ["Soc_Phan_Ve"],
            "paired": False,
        }
    }

    # 15. Panel C - Chi-Square Test of Independence (Bảng 3x2, mọi E > 5)
    rows_chi = (
        [{"Nhom_Tuoi": "Trẻ", "Tuan_Thu_Thuoc": "Tốt"}] * 25 +
        [{"Nhom_Tuoi": "Trẻ", "Tuan_Thu_Thuoc": "Kém"}] * 20 +
        [{"Nhom_Tuoi": "Trung niên", "Tuan_Thu_Thuoc": "Tốt"}] * 35 +
        [{"Nhom_Tuoi": "Trung niên", "Tuan_Thu_Thuoc": "Kém"}] * 15 +
        [{"Nhom_Tuoi": "Cao tuổi", "Tuan_Thu_Thuoc": "Tốt"}] * 18 +
        [{"Nhom_Tuoi": "Cao tuổi", "Tuan_Thu_Thuoc": "Kém"}] * 28
    )
    samples["Panel C: Chi-Square độc lập (Bảng 3x2 Nhóm tuổi & Tuân thủ thuốc)"] = {
        "df": pd.DataFrame(rows_chi),
        "config": {
            "independent_vars": ["Nhom_Tuoi"],
            "dependent_vars": ["Tuan_Thu_Thuoc"],
            "paired": False,
        }
    }

    # 16. Panel C - McNemar Test (Bảng 2x2 bắt cặp Trước - Sau)
    rows_mcn = (
        [{"Truoc_DT": "Dương tính", "Sau_DT": "Dương tính"}] * 12 +
        [{"Truoc_DT": "Dương tính", "Sau_DT": "Âm tính"}] * 28 +
        [{"Truoc_DT": "Âm tính", "Sau_DT": "Dương tính"}] * 4 +
        [{"Truoc_DT": "Âm tính", "Sau_DT": "Âm tính"}] * 36
    )
    samples["Panel C: Kiểm định McNemar (Dữ liệu định tính 2x2 bắt cặp)"] = {
        "df": pd.DataFrame(rows_mcn),
        "config": {
            "independent_vars": ["Truoc_DT"],
            "dependent_vars": ["Sau_DT"],
            "paired": True,
        }
    }

    # 17. Panel C - Cochran's Q Test (3 thời điểm định tính bắt cặp)
    n_cq = 50
    t1_cq = rng.choice(["Có", "Không"], size=n_cq, p=[0.75, 0.25])
    t2_cq = rng.choice(["Có", "Không"], size=n_cq, p=[0.45, 0.55])
    t3_cq = rng.choice(["Có", "Không"], size=n_cq, p=[0.20, 0.80])
    samples["Panel C: Kiểm định Cochran's Q (Tỷ lệ triệu chứng qua 3 thời điểm bắt cặp)"] = {
        "df": pd.DataFrame({"Tuan_1": t1_cq, "Tuan_2": t2_cq, "Tuan_4": t3_cq}),
        "config": {
            "independent_vars": [],
            "dependent_vars": ["Tuan_1", "Tuan_2", "Tuan_4"],
            "paired": True,
        }
    }

    # 18. Panel C - Mantel-Haenszel Chi-Square (Có biến rời rạc thứ 3 phân tầng)
    rows_mh = (
        [{"Phac_Do": "Thuốc_A", "Ket_Qua": "Khỏi", "Benh_Vien": "BV_Tuyến_TW"}] * 35 +
        [{"Phac_Do": "Thuốc_A", "Ket_Qua": "Không", "Benh_Vien": "BV_Tuyến_TW"}] * 15 +
        [{"Phac_Do": "Thuốc_B", "Ket_Qua": "Khỏi", "Benh_Vien": "BV_Tuyến_TW"}] * 20 +
        [{"Phac_Do": "Thuốc_B", "Ket_Qua": "Không", "Benh_Vien": "BV_Tuyến_TW"}] * 30 +
        [{"Phac_Do": "Thuốc_A", "Ket_Qua": "Khỏi", "Benh_Vien": "BV_Tuyến_Tỉnh"}] * 28 +
        [{"Phac_Do": "Thuốc_A", "Ket_Qua": "Không", "Benh_Vien": "BV_Tuyến_Tỉnh"}] * 12 +
        [{"Phac_Do": "Thuốc_B", "Ket_Qua": "Khỏi", "Benh_Vien": "BV_Tuyến_Tỉnh"}] * 14 +
        [{"Phac_Do": "Thuốc_B", "Ket_Qua": "Không", "Benh_Vien": "BV_Tuyến_Tỉnh"}] * 26
    )
    samples["Panel C: Mantel-Haenszel Chi-Square (Kiểm soát biến thứ 3: Bệnh viện)"] = {
        "df": pd.DataFrame(rows_mh),
        "config": {
            "independent_vars": ["Phac_Do"],
            "dependent_vars": ["Ket_Qua"],
            "third_var": "Benh_Vien",
            "paired": False,
        }
    }

    # 19. Panel D - Pearson Correlation (2 biến liên tục phân phối chuẩn)
    tuoi = np.round(rng.normal(loc=55.0, scale=10.0, size=60), 1)
    huyet_ap = np.round(95.0 + 0.72 * tuoi + rng.normal(loc=0.0, scale=5.5, size=60), 1)
    samples["Panel D: Tương quan Pearson (Tuổi & Huyết áp - Đạt chuẩn)"] = {
        "df": pd.DataFrame({"Tuoi": tuoi, "Huyet_Ap": huyet_ap}),
        "config": {
            "independent_vars": [],
            "dependent_vars": ["Tuoi", "Huyet_Ap"],
            "format_mode": "free",
        }
    }

    # 20. Panel D - Partial Correlation (3 biến liên tục phân phối chuẩn)
    bmi = np.round(rng.normal(loc=24.5, scale=3.0, size=60), 2)
    cholesterol = np.round(130.0 + 1.1 * tuoi + 2.4 * bmi + rng.normal(loc=0.0, scale=8.0, size=60), 1)
    samples["Panel D: Tương quan từng phần Partial Correlation (Huyết áp, Cholesterol kiểm soát Tuổi)"] = {
        "df": pd.DataFrame({"Huyet_Ap": huyet_ap, "Cholesterol": cholesterol, "Tuoi": tuoi}),
        "config": {
            "independent_vars": [],
            "dependent_vars": ["Huyet_Ap", "Cholesterol", "Tuoi"],
            "format_mode": "free",
        }
    }

    # 21. Panel D - Spearman Rho (2 biến liên tục không phân phối chuẩn)
    nong_do_crp = np.round(rng.exponential(scale=15.0, size=60), 2)
    ngay_hoi_phuc = np.round(3.0 + 0.35 * nong_do_crp + rng.exponential(scale=2.0, size=60), 1)
    samples["Panel D: Tương quan hạng Spearman Rho (CRP & Ngày hồi phục - Không chuẩn)"] = {
        "df": pd.DataFrame({"Nong_Do_CRP": nong_do_crp, "Ngay_Hoi_Phuc": ngay_hoi_phuc}),
        "config": {
            "independent_vars": [],
            "dependent_vars": ["Nong_Do_CRP", "Ngay_Hoi_Phuc"],
            "format_mode": "free",
        }
    }

    # 22. Panel D - Hồi quy đơn biến (Simple Linear Regression)
    samples["Panel D: Hồi quy tuyến tính đơn biến (Dự báo Huyết áp từ Tuổi)"] = {
        "df": pd.DataFrame({"Tuoi": tuoi, "Huyet_Ap": huyet_ap}),
        "config": {
            "independent_vars": ["Tuoi"],
            "dependent_vars": ["Huyet_Ap"],
            "format_mode": "preselected",
        }
    }

    # 23. Panel D - Hồi quy đa biến (Multiple Linear Regression)
    samples["Panel D: Hồi quy tuyến tính đa biến (Dự báo Cholesterol từ Tuổi & BMI)"] = {
        "df": pd.DataFrame({"Tuoi": tuoi, "BMI": bmi, "Cholesterol": cholesterol}),
        "config": {
            "independent_vars": ["Tuoi", "BMI"],
            "dependent_vars": ["Cholesterol"],
            "format_mode": "preselected",
        }
    }

    return samples
