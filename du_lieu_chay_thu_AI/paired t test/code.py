import pandas as pd
import numpy as np

# Cố định seed để kết quả tái lập đồng nhất
np.random.seed(42)

# Tạo 100 dòng dữ liệu huyết áp trước can thiệp (phân phối chuẩn)
truoc_can_thiep = np.random.normal(loc=140, scale=10, size=100)

# Tạo dữ liệu sau can thiệp dựa trên sự phụ thuộc (bắt cặp)
# Giả định can thiệp làm giảm trung bình 8 mmHg
sau_can_thiep = truoc_can_thiep - np.random.normal(loc=8, scale=3, size=100)

# Đóng gói và xuất dữ liệu
df = pd.DataFrame({
    'ID_BenhNhan': range(1, 101),
    'Truoc_Can_Thiep': np.round(truoc_can_thiep, 1),
    'Sau_Can_Thiep': np.round(sau_can_thiep, 1)
})

df.to_csv('paired_ttest_100_rows.csv', index=False)
print(df.head())