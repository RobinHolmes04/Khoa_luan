import pandas as pd
import numpy as np

# Cố định seed để kết quả đồng nhất qua các lần chạy
np.random.seed(42)

# Mô phỏng 100 bệnh nhân với tỷ lệ thành công thực tế khoảng 65%
# 1: Thành công (Ví dụ: Sống/Khỏi bệnh), 0: Thất bại (Ví dụ: Chết/Không khỏi)
ket_qua = np.random.choice([1, 0], size=100, p=[0.65, 0.35])

# Đóng gói dữ liệu
df = pd.DataFrame({
    'ID_BenhNhan': range(1, 101),
    'KetQua_DieuTri': ket_qua
})

# Xuất file CSV để nạp vào giao diện phần mềm
df.to_csv('ztest_1_mau_data.csv', index=False)