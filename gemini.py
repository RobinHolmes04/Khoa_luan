from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
# Giả sử bạn đang dùng file giao diện này
from GiaoDien_ui import Ui_MainWindow 
import sys
from pandas import read_csv
import pickle

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Biến cốt lõi để lưu dữ liệu Pandas (RẤT QUAN TRỌNG: Dùng self.df thay vì df)
        self.df = None 

        self.ui.actionImport.triggered.connect(self.import_file_window)
        self.ui.actionSave.triggered.connect(self.save_file_window)
        
        # Giả sử bạn có thêm nút Open Project (Mở file .pf)
        # self.ui.actionOpenProject.triggered.connect(self.load_file_window)

    # ==========================================
    # CÁC HÀM TỰ ĐỘNG QUÉT VÀ PHỤC HỒI GIAO DIỆN
    # ==========================================
    def tu_dong_lay_trang_thai(self):
        """Hàm tự động quét toàn bộ giao diện và gom vào Dictionary"""
        state = {}
        
        # 1. Lưu cục dữ liệu Pandas to nhất
        state['dataframe'] = self.df 
        
        # 2. Quét tự động các Widget khác (không cần gõ tay từng cái)
        # Lấy tất cả widget con nằm trong giao diện chính
        for widget in self.findChildren(QtWidgets.QWidget):
            ten_widget = widget.objectName()
            if not ten_widget: 
                continue # Bỏ qua các widget không có tên
                
            # Tự động nhận diện loại widget và lấy giá trị tương ứng
            if isinstance(widget, QtWidgets.QLineEdit):
                state[ten_widget] = widget.text()
            elif isinstance(widget, QtWidgets.QComboBox):
                state[ten_widget] = widget.currentIndex()
            elif isinstance(widget, QtWidgets.QCheckBox):
                state[ten_widget] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QRadioButton):
                state[ten_widget] = widget.isChecked()
                
        return state

    def tu_dong_phuc_hoi_trang_thai(self, state):
        """Hàm tự động khôi phục giao diện từ Dictionary"""
        # 1. Khôi phục cục dữ liệu Pandas và vẽ lại bảng
        self.df = state.get('dataframe', None)
        if self.df is not None:
            self.show_data(self.df)
            
        # 2. Khôi phục tự động các Widget khác
        for widget in self.findChildren(QtWidgets.QWidget):
            ten_widget = widget.objectName()
            if ten_widget in state:
                gia_tri_cu = state[ten_widget]
                
                if isinstance(widget, QtWidgets.QLineEdit):
                    widget.setText(gia_tri_cu)
                elif isinstance(widget, QtWidgets.QComboBox):
                    widget.setCurrentIndex(gia_tri_cu)
                elif isinstance(widget, QtWidgets.QCheckBox) or isinstance(widget, QtWidgets.QRadioButton):
                    widget.setChecked(gia_tri_cu)

    # ==========================================
    # CÁC HÀM XỬ LÝ FILE (OPEN / SAVE)
    # ==========================================
    def import_file_window(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import File", "", "CSV (*.csv);;All Files (*)")
        if file_name:
            print(f"Selected file: {file_name}")
            # LƯU Ý: Phải gắn vào self.df để biến này sống sót sang các hàm khác
            self.df = read_csv(file_name) 
            self.show_data(self.df)

    def show_data(self, df):
        self.ui.tableWidget.setRowCount(df.shape[0])
        self.ui.tableWidget.setColumnCount(df.shape[1])
        self.ui.tableWidget.setHorizontalHeaderLabels(df.columns.astype(str)) # Đảm bảo tên cột là chữ
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.ui.tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(str(df.iat[i, j])))

    def save_file_window(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Pharta Files (*.pf);;All Files (*)")
        if file_name:
            try:
                # 1. Gọi hàm tự động quét lấy dữ liệu
                trang_thai_hien_tai = self.tu_dong_lay_trang_thai()
                
                # 2. Dùng Pickle nén lại
                with open(file_name, 'wb') as file:
                    pickle.dump(trang_thai_hien_tai, file)
                    
                print(f"Project saved successfully: {file_name}")
            except Exception as e:
                print(f"Error saving file: {e}")

    # Hàm này tôi viết thêm để bạn thấy cách mở file .pf đã lưu
    def load_file_window(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Pharta Files (*.pf);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'rb') as file:
                    trang_thai_cu = pickle.load(file)
                
                # Gọi hàm tự động phục hồi
                self.tu_dong_phuc_hoi_trang_thai(trang_thai_cu)
                print(f"Project loaded successfully: {file_name}")
            except Exception as e:
                print(f"Error loading file: {e}")

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())