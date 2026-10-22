from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog,QDialog
from PySide6.QtCore import QTimer
from GiaoDien_ui import Ui_MainWindow
from DoYouWantToSaveDialog_ui import Ui_Dialog
import sys
import pandas as pd
import pickle

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.tableWidget.setColumnCount(50)
        self.ui.tableWidget.setRowCount(50)
        
        self.df = None  # Biến cốt lõi để lưu dữ liệu Pandas (RẤT QUAN TRỌNG: Dùng self.df thay vì df)
        self.current_file_path = None  # Biến để lưu đường dẫn file hiện tại (nếu có)
        self.last_state = None  # Biến để lưu trạng thái trước khi undo (nếu có)
        self.undo_stack = []  # Ngăn xếp để lưu các trạng thái trước khi undo
        self.is_updating = False  # Biến cờ để kiểm tra xem đang khôi phục giao diện hay không
        self.setup_action_triggers() #
        self.redo_stack = []  # Ngăn xếp để lưu các trạng thái trước khi redo (nếu có)

        self.ui.actionImport.triggered.connect(self.import_file_window)
        self.ui.actionSaveProjectAs.triggered.connect(self.save_file_window)
        self.ui.actionSaveProject.triggered.connect(self.save_current_project)
        self.ui.actionOpenProject.triggered.connect(self.load_file_window)
        self.ui.actionNewProject.triggered.connect(self.new_project_window)
        self.ui.actionUndo.triggered.connect(self.undo_action)
        self.ui.actionRedo.triggered.connect(self.redo_action)

        self.set_baseline_state()  # Thiết lập trạng thái cơ bản ban đầu khi khởi động phần mềm
    def kiem_tra_bang_trong(self):
        """Quét toàn bộ bảng, nếu có bất kỳ 1 ô nào có chữ thì trả về False, ngược lại là True"""
        so_dong = self.ui.tableWidget.rowCount()
        so_cot = self.ui.tableWidget.columnCount()
        
        for row in range(so_dong):
            for col in range(so_cot):
                item = self.ui.tableWidget.item(row, col)
                if item is not None and item.text().strip() != "":
                    return False  # Bảng có chứa dữ liệu
        return True  # Bảng hoàn toàn trắng
    
    def set_baseline_state(self):   
        """Hàm này được gọi khi phần mềm khởi động hoặc khi mở một dự án mới, để thiết lập trạng thái cơ bản ban đầu."""
        self.last_state = self.get_ui_state()  # Lấy trạng thái hiện tại của giao diện và lưu vào last_state
        self.undo_stack.clear()  # Xóa ngăn xếp undo khi bắt đầu một dự án mới
        self.redo_stack.clear()  # Xóa ngăn xếp redo khi bắt đầu một dự án mới
    def closeEvent(self, event):   
        """Hàm kích hoạt khi người dùng bấm dấu X tắt phần mềm"""
        self.ui.tableWidget.clearFocus() 
        
        # CHẶN: Nếu bảng trắng trơn -> Cho tắt luôn không cần hỏi
        if self.kiem_tra_bang_trong():
            event.accept()
            return
            
        dialog = self.DoYouWantToSaveDialog(self)
        user_choice = dialog.exec()
        
        if user_choice == QDialog.Accepted:
            is_saved = self.save_current_project()
            if is_saved:
                event.accept()
            else:
                event.ignore()
        elif user_choice == 3:
            event.accept()  
        elif user_choice == QDialog.Rejected:
            event.ignore()
############################################################################################
###Import CSV    
    def import_file_window(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import File", "", "CSV (*.csv);;All Files (*)")
        if file_name:
            print(f"Selected file: {file_name}")
            self.df = pd.read_csv(file_name)
            self.show_data(self.df)

    def show_data(self, df): # để hiện thị dữ liệu lên tableWidget
        self.is_updating = True  # Bật cờ để tránh tự động lưu khi đang cập nhật giao diện
        self.ui.tableWidget.setRowCount(df.shape[0])
        self.ui.tableWidget.setColumnCount(df.shape[1])
        self.ui.tableWidget.setHorizontalHeaderLabels(df.columns)
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.ui.tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(str(df.iat[i, j])))

        self.is_updating = False  # Tắt cờ sau khi cập nhật xong
        self.set_baseline_state()  # Cập nhật trạng thái cơ bản sau khi import dữ liệu  

##################################################################################################
#save project as
    def save_file_window(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Pharta Files (*.pf);;All Files (*)")
        if file_name:
            self.current_file_path = file_name  # Cập nhật đường dẫn file hiện tại
            with open(file_name, 'wb') as f:
                pickle.dump(self.get_ui_state(), f)
            return True
        return False

    def get_ui_state(self): #hàm tự động quét giao diện và lấy trạng thái của các widget
        state = {}
        so_dong = self.ui.tableWidget.rowCount()
        so_cot = self.ui.tableWidget.columnCount()
        
        # 1. Lấy lại dòng tiêu đề (Headers)
        headers = []
        for col in range(so_cot):
            header_item = self.ui.tableWidget.horizontalHeaderItem(col)
            if header_item:
                headers.append(header_item.text())
            else:
                headers.append(f"Cot_{col}")
                    
        # 2. Lấy dữ liệu từng ô trên bảng
        data = []
        for row in range(so_dong):
            row_data = []
            for col in range(so_cot):
                item = self.ui.tableWidget.item(row, col)
                # Nếu ô có chữ thì lấy chữ, nếu ô trống thì để rỗng
                row_data.append(item.text() if item is not None else "")
            data.append(row_data)
            
        # 3. Ép bảng dữ liệu này đè lên self.df cũ
        self.df = pd.DataFrame(data, columns=headers)
    # ========================================================

        # Lưu cục dữ liệu Pandas (Lúc này ĐÃ LÀ BẢN MỚI NHẤT do người dùng vừa sửa)
        state['dataframe'] = self.df 
        
        # Quét tự động các Widget khác (Giữ nguyên như cũ)
        for widget in self.findChildren(QtWidgets.QWidget):
            ten_widget = widget.objectName()
            if not ten_widget: 
                continue
                
            if isinstance(widget, QtWidgets.QLineEdit):
                state[ten_widget] = widget.text()
            elif isinstance(widget, QtWidgets.QComboBox):
                state[ten_widget] = widget.currentIndex()
            elif isinstance(widget, QtWidgets.QCheckBox) or isinstance(widget, QtWidgets.QRadioButton):
                state[ten_widget] = widget.isChecked()
                
        return state
##################################################################################    
#Save project
    def save_current_project(self):
        if self.current_file_path:
            with open(self.current_file_path, 'wb') as f:
                pickle.dump(self.get_ui_state(), f)
            return True
        else:
            self.save_file_window()  # Nếu chưa có đường dẫn file, gọi save_as
#Open project    
    def restore_ui_state(self, state): #hàm tự động khôi phục giao diện từ Dictionary
        self.is_updating = True
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

        self.is_updating = False

    def load_file_window(self):
        # CHẶN: Kiểm tra nếu bảng có dữ liệu mới hiện Dialog
        if not self.kiem_tra_bang_trong():  
            dialog = self.DoYouWantToSaveDialog(self)
            user_choice = dialog.exec()
            if user_choice == QDialog.Accepted:
                self.save_current_project()
            elif user_choice == QDialog.Rejected:
                return 
            elif user_choice == 3:
                pass 
                
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Pharta Files (*.pf);;All Files (*)")
        if file_name:
            with open(file_name, 'rb') as f:
                state = pickle.load(f)
            self.restore_ui_state(state)
            self.current_file_path = file_name 
            self.set_baseline_state()
###################################################################################
#New project
    class DoYouWantToSaveDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.ui = Ui_Dialog()
            self.ui.setupUi(self)

            self.ui.CancelButton.clicked.connect(self.reject)
            self.ui.SaveButton.clicked.connect(self.accept)
            self.ui.DontSaveButton.clicked.connect(lambda: self.done(3))  # Nếu người dùng chọn "Don't Save", cũng coi như hủy bỏ

    def new_project_window(self):
        # CHẶN: Nếu bảng đang trắng -> Reset luôn không cần hỏi
        if self.kiem_tra_bang_trong():
            self.df = None
            self.current_file_path = None
            self.reset_table()
            self.set_baseline_state()
            return

        dialog = self.DoYouWantToSaveDialog(self)
        user_choice = dialog.exec()
        if user_choice == QDialog.Accepted:
            self.save_current_project()
            self.df = None
            self.current_file_path = None
            self.reset_table()
            self.set_baseline_state() 
        elif user_choice == QDialog.Rejected:
            pass 
        elif user_choice == 3:
            self.df = None
            self.current_file_path = None   
            self.reset_table()
            self.set_baseline_state()

    def reset_table(self):
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setRowCount(50)
        self.ui.tableWidget.setColumnCount(50)
        self.ui.tableWidget.setHorizontalHeaderLabels([f"Cot_{i}" for i in range(50)])           
###################################################################################################
### Triggers, Undo & Auto-save
    def setup_action_triggers(self):
        self.ui.tableWidget.itemChanged.connect(self.on_user_action)
        for widget in self.findChildren(QtWidgets.QWidget):
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.textChanged.connect(self.on_user_action) 
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.connect(self.on_user_action) 
            elif isinstance(widget, QtWidgets.QCheckBox) or isinstance(widget, QtWidgets.QRadioButton):
                widget.toggled.connect(self.on_user_action) 

    def on_user_action(self, *args):
        """1. HÀM TRỌNG TÀI: Chỉ làm nhiệm vụ kiểm tra xem có thay đổi thật không"""
        if self.is_updating:
            return
            
        current_state = self.get_ui_state() 
        current_bytes = pickle.dumps(current_state) 
        
        if self.last_state is not None:
            last_bytes = pickle.dumps(self.last_state) 
            
            if current_bytes != last_bytes:
                # Khi phát hiện thay đổi, phân chia nhiệm vụ rõ ràng:
                self.update_undo_history()        # Gọi hàm quản lý Undo
                # self.auto_save_project(current_state) # Gọi hàm quản lý Auto-save
                
                # Cập nhật mốc mới
                self.last_state = current_state
        else:
            self.last_state = current_state

    def update_undo_history(self):
        """2. HÀM UNDO: Chỉ làm nhiệm vụ đẩy trạng thái cũ vào ngăn xếp RAM"""
        if len(self.undo_stack) >= 20:  
            self.undo_stack.pop(0)  
        self.undo_stack.append(self.last_state) 
        self.redo_stack.clear()  # Xóa ngăn xếp redo khi có thao tác mới

    # def auto_save_project(self, state_to_save):
    #     """3. HÀM AUTO-SAVE: Chỉ làm nhiệm vụ ghi đè file xuống ổ cứng"""
    #     if self.current_file_path:
    #         with open(self.current_file_path, 'wb') as f:
    #             pickle.dump(state_to_save, f)
    #         print("Đã Auto-save âm thầm!")

    def undo_action(self):
        if self.undo_stack:
            self.redo_stack.append(self.last_state)  # Lưu trạng thái hiện tại vào ngăn xếp Redo trước khi Undo
            last_state = self.undo_stack.pop()
            self.restore_ui_state(last_state)  
            self.last_state = last_state  
            print("Đã Undo thành công!")
            
        else:
            print("Không có thao tác nào để Undo.")

    def redo_action(self):
        if self.redo_stack:
            self.undo_stack.append(self.last_state)  # Lưu trạng thái hiện tại vào ngăn xếp Undo trước khi Redo
            redo_state = self.redo_stack.pop()
            self.restore_ui_state(redo_state)  
            self.last_state = redo_state  
            print("Đã Redo thành công!")
        else:
            print("Không có thao tác nào để Redo.")
app = QApplication(sys.argv)
window = MainWindow()
window.showMaximized()
sys.exit(app.exec())