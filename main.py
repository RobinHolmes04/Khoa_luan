<<<<<<< Updated upstream
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog,QDialog
from PySide6.QtCore import QTimer
from GiaoDien_ui import Ui_MainWindow
from DoYouWantToSaveDialog_ui import Ui_Dialog
import sys
import pandas as pd
import pickle
=======
# -*- coding: utf-8 -*-
"""
Khối Giao diện Người dùng (Presentation Layer / Thin UI) của phần mềm Pharta.
Tuân thủ tuyệt đối UR.F001.01, UR.NF003, UR.NF005 và AC-01:
- Chỉ tiếp nhận thao tác người dùng, đóng gói Request Payload gửi xuống Core Engine (`PhartaCoreEngine.analyze`),
  và hiển thị kết quả trả về (Bảng chuẩn APA, câu diễn giải tiếng Việt lâm sàng, Cây quyết định, Biểu đồ).
- Tuyệt đối KHÔNG chứa bất kỳ mã tính toán thống kê hay rẽ nhánh cây quyết định nào.
"""

import os
import sys
import json
import pickle
from collections import deque
from contextlib import contextmanager
from typing import Dict, Any, Optional

# Tự động nạp site-packages nếu VS Code gọi nhầm shim python3.15.exe trong .local\bin
_FALLBACK_SITE_PACKAGES = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Python", "pythoncore-3.15-64", "Lib", "site-packages"
)
if os.path.isdir(_FALLBACK_SITE_PACKAGES) and _FALLBACK_SITE_PACKAGES not in sys.path:
    sys.path.append(_FALLBACK_SITE_PACKAGES)

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QFont, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QDialog, QWidget,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QCheckBox, QRadioButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QTabWidget,
    QTextBrowser, QSplitter, QGroupBox, QHeaderView, QMessageBox, QInputDialog,
    QDoubleSpinBox, QFrame
)

from GiaoDien_ui import Ui_MainWindow
from DoYouWantToSaveDialog_ui import Ui_Dialog
from Core.engine import PhartaCoreEngine
from Core.sample_datasets import get_sample_datasets
from giao_dien.chart_widget import PhartaChartWidget

DEFAULT_SIZE = 30
DEFAULT_COLS = 8
MAX_UNDO = 20
DONT_SAVE = 3
PF_FILTER = "Pharta Project (*.pf);;All Files (*)"
DATA_FILTER = "Dữ liệu Y Dược (*.csv *.xlsx *.xls);;CSV (*.csv);;Excel (*.xlsx *.xls);;All Files (*)"

WIDGET_HANDLERS = [
    (QLineEdit, "text", "setText", "textChanged"),
    (QComboBox, "currentIndex", "setCurrentIndex", "currentIndexChanged"),
    ((QCheckBox, QRadioButton), "isChecked", "setChecked", "toggled"),
]

ROLE_OPTIONS = [
    ("none", "Bỏ qua / Không chọn"),
    ("dv", "Biến phụ thuộc / Biến chính (DV)"),
    ("iv", "Biến độc lập / Phân nhóm (IV)"),
    ("third", "Biến rời rạc thứ 3 (Phân tầng MH)"),
]

TYPE_OPTIONS = [
    ("auto", "Tự động phát hiện (Cảnh báo)"),
    ("continuous", "Liên tục / Định lượng (Continuous)"),
    ("discrete", "Rời rạc / Định tính (Discrete)"),
]


class SaveDialog(QDialog):
    """Hộp thoại xác nhận lưu dự án trước khi đóng hoặc tạo mới."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Lưu dự án Pharta")
        self.ui.SaveButton.clicked.connect(self.accept)
        self.ui.CancelButton.clicked.connect(self.reject)
        self.ui.DontSaveButton.clicked.connect(lambda: self.done(DONT_SAVE))

>>>>>>> Stashed changes

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
<<<<<<< Updated upstream
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
=======
        self.setWindowTitle("PHARTA - Phần mềm Tự động hóa Phân tích Thống kê Y Dược (Chuẩn GAMP 5 / Phụ lục A)")
        self.resize(1380, 860)

        self.df: Optional[pd.DataFrame] = None
        self.last_response: Optional[Dict[str, Any]] = None
        self.current_file_path: Optional[str] = None
        self.last_state: Optional[Dict[str, Any]] = None
        self.undo_stack = deque(maxlen=MAX_UNDO)
        self.redo_stack = []
        self.is_updating = False
        self.sample_datasets = get_sample_datasets()

        self._build_modern_medical_ui()
        self._connect_actions()
        self.reset_table()
        self.set_baseline_state()

    # ===================== Xây dựng Giao diện Y khoa Tiếng Việt =====================
    def _build_modern_medical_ui(self) -> None:
        """Tổ chức bố cục giao diện trực quan bằng tiếng Việt thân thiện với nhân viên y tế (UR.NF005)."""
        self.setStyleSheet("""
            QMainWindow { background-color: #f1f5f9; }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: #ffffff;
                color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton#btnRunAnalysis {
                background-color: #0284c7;
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 14px;
                border-radius: 6px;
            }
            QPushButton#btnRunAnalysis:hover { background-color: #0369a1; }
            QPushButton#btnExportReport {
                background-color: #0d9488;
                color: white;
                font-weight: bold;
                padding: 7px 12px;
                border-radius: 5px;
            }
            QPushButton#btnExportReport:hover { background-color: #0f766e; }
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                background: #ffffff;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #e2e8f0;
                color: #334155;
                padding: 8px 16px;
                font-weight: bold;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0284c7;
            }
        """)

        # Tái cấu trúc centralwidget sử dụng QSplitter giữa bảng điều khiển trái và vùng làm việc phải
        old_table = self.ui.tableWidget
        old_table.setParent(None)
        self.table = old_table

        # Xóa các frame mặc định trong gridLayout của GiaoDien_ui để đặt Splitter chuẩn
        while self.ui.gridLayout.count():
            item = self.ui.gridLayout.takeAt(0)
            if item.widget():
                item.widget().hide()

        splitter = QSplitter(Qt.Horizontal, self.ui.centralwidget)
        self.ui.gridLayout.addWidget(splitter, 0, 0, 1, 1)

        # ---------------- PANEL TRÁI: THIẾT LẬP NGHIỆP VỤ ----------------
        left_panel = QFrame()
        left_panel.setMinimumWidth(420)
        left_panel.setMaximumWidth(520)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(8)

        # Header thương hiệu Pharta
        header_lbl = QLabel("🩺 PHARTA - TRỢ LÝ THỐNG KÊ Y DƯỢC")
        header_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_lbl.setStyleSheet("color: #0369a1; padding: 4px;")
        left_layout.addWidget(header_lbl)

        # 1. Nhóm Nạp dữ liệu & Bộ dữ liệu mẫu
        grp_data = QGroupBox("1. Nguồn Dữ Liệu (Excel / CSV / Mẫu Y Khoa)")
        data_layout = QVBoxLayout(grp_data)
        btn_row = QHBoxLayout()
        self.btn_import = QPushButton("📂 Nạp tệp Excel / CSV")
        self.btn_paste = QPushButton("📋 Dán từ Clipboard")
        self.btn_clear = QPushButton("🧹 Làm mới bảng")
        btn_row.addWidget(self.btn_import)
        btn_row.addWidget(self.btn_paste)
        btn_row.addWidget(self.btn_clear)
        data_layout.addLayout(btn_row)

        sample_row = QHBoxLayout()
        sample_row.addWidget(QLabel("Dữ liệu mẫu:"))
        self.cmb_samples = QComboBox()
        self.cmb_samples.setObjectName("cmb_samples")
        self.cmb_samples.addItem("-- Chọn kịch bản dữ liệu mẫu Phụ lục A (23 ca chuẩn) --")
        for s_name in self.sample_datasets.keys():
            self.cmb_samples.addItem(s_name)
        sample_row.addWidget(self.cmb_samples, 1)
        data_layout.addLayout(sample_row)
        left_layout.addWidget(grp_data)

        # 2. Nhóm Thiết lập Biến số & Kiểu biến
        grp_vars = QGroupBox("2. Thiết Lập Vai Trò Biến & Kiểu Dữ Liệu")
        vars_layout = QVBoxLayout(grp_vars)
        note_lbl = QLabel(
            "💡 Mẹo: Phân tích theo cặp hoặc tương quan không bắt buộc chọn biến độc lập (đặt tất cả là DV). "
            "Nếu để kiểu biến 'Tự động', hệ thống sẽ cảnh báo và tự phân loại."
        )
        note_lbl.setWordWrap(True)
        note_lbl.setStyleSheet("color: #475569; font-size: 11px;")
        vars_layout.addWidget(note_lbl)

        self.var_config_table = QTableWidget(0, 3)
        self.var_config_table.setHorizontalHeaderLabels(["Tên cột biến", "Vai trò trong mô hình", "Kiểu biến (Định tính/Định lượng)"])
        self.var_config_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.var_config_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.var_config_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.var_config_table.verticalHeader().setVisible(False)
        vars_layout.addWidget(self.var_config_table)

        var_btn_row = QHBoxLayout()
        self.btn_sync_cols = QPushButton("🔄 Cập nhật danh sách cột từ bảng")
        self.btn_auto_fill_types = QPushButton("✨ Gợi ý kiểu biến tự động")
        var_btn_row.addWidget(self.btn_sync_cols)
        var_btn_row.addWidget(self.btn_auto_fill_types)
        vars_layout.addLayout(var_btn_row)
        left_layout.addWidget(grp_vars, 1)

        # 3. Nhóm Tham số Kiểm định & Cây quyết định
        grp_params = QGroupBox("3. Tham Số Thống Kê & Tuỳ Chọn Cây Quyết Định")
        params_grid = QGridLayout(grp_params)

        params_grid.addWidget(QLabel("Mức ý nghĩa α:"), 0, 0)
        self.cmb_alpha = QComboBox()
        self.cmb_alpha.setObjectName("cmb_alpha")
        self.cmb_alpha.addItems(["0.05 (Độ tin cậy 95%)", "0.01 (Độ tin cậy 99%)", "0.10 (Độ tin cậy 90%)"])
        params_grid.addWidget(self.cmb_alpha, 0, 1)

        params_grid.addWidget(QLabel("Chế độ Panel D:"), 1, 0)
        self.cmb_format_mode = QComboBox()
        self.cmb_format_mode.setObjectName("cmb_format_mode")
        self.cmb_format_mode.addItems([
            "Tự động (Có IV → Hồi quy, Không IV → Tương quan)",
            "Tương quan tự do (Free format - Pearson / Spearman / Partial)",
            "Hồi quy tuyến tính (Preselected levels - Đơn biến / Đa biến)",
            "So sánh các cột định lượng độc lập (Wide format - Panel B)"
        ])
        params_grid.addWidget(self.cmb_format_mode, 1, 1)

        self.chk_paired = QCheckBox("Dữ liệu bắt cặp / Đo lặp lại trên cùng đối tượng (Paired data)")
        self.chk_paired.setObjectName("chk_paired")
        params_grid.addWidget(self.chk_paired, 2, 0, 1, 2)

        self.chk_proportion = QCheckBox("Dữ liệu báo cáo dạng tỷ lệ phần trăm (Percent/Proportions - Panel A)")
        self.chk_proportion.setObjectName("chk_proportion")
        params_grid.addWidget(self.chk_proportion, 3, 0, 1, 2)

        self.chk_pop_var = QCheckBox("Đã biết phương sai/độ lệch chuẩn quần thể (Kích hoạt Z-test - Panel B)")
        self.chk_pop_var.setObjectName("chk_pop_var")
        params_grid.addWidget(self.chk_pop_var, 4, 0, 1, 2)

        sigma_row = QHBoxLayout()
        sigma_row.addWidget(QLabel("σ₁ quần thể:"))
        self.spn_sigma1 = QDoubleSpinBox()
        self.spn_sigma1.setRange(0.0001, 1e6)
        self.spn_sigma1.setDecimals(4)
        self.spn_sigma1.setValue(10.0)
        sigma_row.addWidget(self.spn_sigma1)

        sigma_row.addWidget(QLabel("Giá trị kiểm định μ₀ (1 mẫu):"))
        self.spn_mu0 = QDoubleSpinBox()
        self.spn_mu0.setRange(-1e6, 1e6)
        self.spn_mu0.setDecimals(4)
        self.spn_mu0.setValue(0.0)
        sigma_row.addWidget(self.spn_mu0)
        params_grid.addLayout(sigma_row, 5, 0, 1, 2)

        left_layout.addWidget(grp_params)

        # Nút Chạy Phân Tích Tự Động
        self.btn_run = QPushButton("▶ CHẠY PHÂN TÍCH TỰ ĐỘNG (PHARTA ENGINE)")
        self.btn_run.setObjectName("btnRunAnalysis")
        left_layout.addWidget(self.btn_run)

        splitter.addWidget(left_panel)

        # ---------------- PANEL PHẢI: VÙNG LÀM VIỆC ĐA TAB ----------------
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)

        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)

        # TAB 1: Bảng dữ liệu
        tab_data = QWidget()
        tab_data_layout = QVBoxLayout(tab_data)
        data_toolbar = QHBoxLayout()
        lbl_data_hint = QLabel("📌 Nháy đúp vào tiêu đề cột để đổi tên biến. Có thể nhập trực tiếp hoặc dán (Ctrl+V) từ Excel.")
        lbl_data_hint.setStyleSheet("color: #334155;")
        self.btn_rename_col = QPushButton("✏️ Đổi tên cột đang chọn")
        data_toolbar.addWidget(lbl_data_hint, 1)
        data_toolbar.addWidget(self.btn_rename_col)
        tab_data_layout.addLayout(data_toolbar)
        tab_data_layout.addWidget(self.table, 1)
        self.tabs.addTab(tab_data, "📋 1. Bảng Dữ Liệu")

        # TAB 2: Kết quả Lâm sàng & Bảng chuẩn APA
        tab_report = QWidget()
        tab_report_layout = QVBoxLayout(tab_report)

        report_top_bar = QHBoxLayout()
        self.lbl_summary_badge = QLabel("Chưa có kết quả phân tích. Hãy nạp dữ liệu và nhấn 'Chạy Phân Tích Tự Động'.")
        self.lbl_summary_badge.setStyleSheet(
            "background-color: #e0f2fe; color: #0369a1; font-weight: bold; padding: 8px 12px; border-radius: 6px;"
        )
        self.btn_copy_apa = QPushButton("📋 Sao chép báo cáo")
        self.btn_export_html = QPushButton("📄 Xuất Báo Cáo Chuẩn APA (.html)")
        self.btn_export_html.setObjectName("btnExportReport")
        report_top_bar.addWidget(self.lbl_summary_badge, 1)
        report_top_bar.addWidget(self.btn_copy_apa)
        report_top_bar.addWidget(self.btn_export_html)
        tab_report_layout.addLayout(report_top_bar)

        self.txt_clinical_report = QTextBrowser()
        self.txt_clinical_report.setOpenExternalLinks(True)
        tab_report_layout.addWidget(self.txt_clinical_report, 3)

        apa_lbl = QLabel("BẢNG KẾT QUẢ ĐỊNH DẠNG CHUẨN QUỐC TẾ APA (UR.F003.02):")
        apa_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        tab_report_layout.addWidget(apa_lbl)

        self.apa_table_widget = QTableWidget(0, 0)
        self.apa_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.apa_table_widget.setAlternatingRowColors(True)
        self.apa_table_widget.setMinimumHeight(190)
        tab_report_layout.addWidget(self.apa_table_widget, 2)

        self.tabs.addTab(tab_report, "🩺 2. Diễn Giải Lâm Sàng & Bảng APA")

        # TAB 3: Lưu đồ Cây quyết định & JSON Payload
        tab_tree = QWidget()
        tab_tree_layout = QVBoxLayout(tab_tree)
        self.txt_tree_and_json = QTextBrowser()
        tab_tree_layout.addWidget(self.txt_tree_and_json)
        self.tabs.addTab(tab_tree, "🌳 3. Cây Quyết Định & Giao Thức JSON")

        # TAB 4: Biểu đồ trực quan
        tab_chart = QWidget()
        tab_chart_layout = QVBoxLayout(tab_chart)
        chart_bar = QHBoxLayout()
        chart_bar.addWidget(QLabel("📊 Biểu đồ trực quan được dựng từ thông số của Lõi xử lý (UR.F003.03):"), 1)
        self.btn_save_chart = QPushButton("💾 Lưu ảnh Biểu đồ (.png)")
        chart_bar.addWidget(self.btn_save_chart)
        tab_chart_layout.addLayout(chart_bar)

        self.chart_widget = PhartaChartWidget()
        tab_chart_layout.addWidget(self.chart_widget, 1)
        self.tabs.addTab(tab_chart, "📊 4. Biểu Đồ Trực Quan")

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Việt hóa thanh Menu
        self.ui.menuFile.setTitle("Tệp (File)")
        self.ui.menuEdit.setTitle("Chỉnh sửa (Edit)")
        self.ui.actionNewProject.setText("Dự án mới (New Project)")
        self.ui.actionOpenProject.setText("Mở dự án (.pf)")
        self.ui.actionSaveProject.setText("Lưu dự án (Save)")
        self.ui.actionSaveProjectAs.setText("Lưu dự án thành (Save As...)")
        self.ui.actionImport.setText("Nạp dữ liệu CSV / Excel...")
        self.ui.actionUndo.setText("Hoàn tác (Undo)")
        self.ui.actionRedo.setText("Làm lại (Redo)")

    def _connect_actions(self) -> None:
        for action, slot in [
            (self.ui.actionImport, self.import_file_window),
            (self.ui.actionSaveProjectAs, self.save_file_window),
            (self.ui.actionSaveProject, self.save_current_project),
            (self.ui.actionOpenProject, self.load_file_window),
            (self.ui.actionNewProject, self.new_project_window),
            (self.ui.actionUndo, self.undo_action),
            (self.ui.actionRedo, self.redo_action),
        ]:
            action.triggered.connect(slot)

        self.btn_import.clicked.connect(self.import_file_window)
        self.btn_paste.clicked.connect(self.paste_from_clipboard)
        self.btn_clear.clicked.connect(self.new_project_window)
        self.cmb_samples.currentIndexChanged.connect(self.on_sample_selected)
        self.btn_sync_cols.clicked.connect(self.sync_variable_config_from_table)
        self.btn_auto_fill_types.clicked.connect(self.auto_fill_variable_types)
        self.btn_run.clicked.connect(self.run_statistical_analysis)
        self.btn_rename_col.clicked.connect(self.rename_selected_column)
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.rename_column_by_index)
        self.btn_export_html.clicked.connect(self.export_apa_report_html)
        self.btn_copy_apa.clicked.connect(self.copy_report_to_clipboard)
        self.btn_save_chart.clicked.connect(self.save_chart_image)

        # Phím tắt Ctrl+V để dán dữ liệu vào bảng
        paste_shortcut = QAction(self)
        paste_shortcut.setShortcut(QKeySequence.Paste)
        paste_shortcut.triggered.connect(self.paste_from_clipboard)
        self.addAction(paste_shortcut)

        self.table.itemChanged.connect(self.on_user_action)
        for w, _, _, signal in self._widgets():
            getattr(w, signal).connect(self.on_user_action)

    # ===================== Tiện ích quản lý trạng thái =====================
    def _widgets(self):
        for w in self.findChildren(QWidget):
            for types, getter, setter, signal in WIDGET_HANDLERS:
                if isinstance(w, types) and w.objectName():
                    yield w, getter, setter, signal
                    break

    @contextmanager
    def updating(self):
        old, self.is_updating = self.is_updating, True
        try:
            yield
        finally:
            self.is_updating = old

    def kiem_tra_bang_trong(self) -> bool:
        t = self.table
        return not any(
            (it := t.item(r, c)) and it.text().strip()
            for r in range(t.rowCount()) for c in range(t.columnCount())
        )

    def hoi_luu_truoc(self) -> bool:
        if self.kiem_tra_bang_trong():
            return True
        choice = SaveDialog(self).exec()
        if choice == QDialog.Accepted:
            return self.save_current_project()
        return choice == DONT_SAVE

    def set_baseline_state(self) -> None:
        self.last_state = self.get_ui_state()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def closeEvent(self, event) -> None:
        self.table.clearFocus()
        if self.hoi_luu_truoc():
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
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
=======

    # ===================== Xử lý Bảng dữ liệu & Thiết lập Biến =====================
    def show_data(self, df: pd.DataFrame, default_config: Optional[Dict[str, Any]] = None) -> None:
        with self.updating():
            rows = max(df.shape[0], 15)
            cols = max(df.shape[1], 1)
            self.table.clear()
            self.table.setRowCount(rows)
            self.table.setColumnCount(cols)
            headers = [str(c) for c in df.columns]
            self.table.setHorizontalHeaderLabels(headers)
            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    val = df.iloc[i, j]
                    text = "" if pd.isna(val) else str(val)
                    self.table.setItem(i, j, QTableWidgetItem(text))
            self.sync_variable_config_from_table(default_config=default_config)

    def reset_table(self) -> None:
        with self.updating():
            self.table.clear()
            self.table.setRowCount(DEFAULT_SIZE)
            self.table.setColumnCount(DEFAULT_COLS)
            self.table.setHorizontalHeaderLabels([f"Bien_{i+1}" for i in range(DEFAULT_COLS)])
            self.var_config_table.setRowCount(0)

    def extract_dataframe_from_table(self) -> pd.DataFrame:
        t = self.table
        cols = range(t.columnCount())
        headers = [h.text().strip() if (h := t.horizontalHeaderItem(c)) and h.text().strip() else f"Bien_{c+1}" for c in cols]
        data = [
            [it.text().strip() if (it := t.item(r, c)) else "" for c in cols]
            for r in range(t.rowCount())
        ]
        raw_df = pd.DataFrame(data, columns=headers)
        # Ủy quyền tiền xử lý dữ liệu cho Lõi xử lý (UR.F001.02)
        return PhartaCoreEngine.preprocess_dataframe(raw_df)

    def sync_variable_config_from_table(self, default_config: Optional[Dict[str, Any]] = None) -> None:
        """Đồng bộ danh sách cột có dữ liệu vào bảng thiết lập vai trò biến."""
        df_clean = self.extract_dataframe_from_table()
        cols = list(df_clean.columns)
        cfg = default_config or {}
        iv_set = set(cfg.get("independent_vars", []))
        dv_set = set(cfg.get("dependent_vars", []))
        third_var = cfg.get("third_var")
        var_types_cfg = cfg.get("var_types", {})

        self.var_config_table.setRowCount(len(cols))
        for idx, col_name in enumerate(cols):
            item_name = QTableWidgetItem(str(col_name))
            item_name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.var_config_table.setItem(idx, 0, item_name)

            cmb_role = QComboBox()
            for r_code, r_label in ROLE_OPTIONS:
                cmb_role.addItem(r_label, userData=r_code)

            # Thiết lập vai trò mặc định thông minh
            low_name = str(col_name).strip().lower()
            if col_name in iv_set:
                cmb_role.setCurrentIndex(2)
            elif col_name == third_var:
                cmb_role.setCurrentIndex(3)
            elif col_name in dv_set:
                cmb_role.setCurrentIndex(1)
            elif not iv_set and not dv_set:
                if low_name in ("id", "stt", "id_benhnhan", "ma_bn"):
                    cmb_role.setCurrentIndex(0)
                else:
                    cmb_role.setCurrentIndex(1)
            else:
                cmb_role.setCurrentIndex(0)
            self.var_config_table.setCellWidget(idx, 1, cmb_role)

            cmb_type = QComboBox()
            for t_code, t_label in TYPE_OPTIONS:
                cmb_type.addItem(t_label, userData=t_code)

            preset_t = var_types_cfg.get(col_name, "auto")
            if preset_t == "continuous":
                cmb_type.setCurrentIndex(1)
            elif preset_t == "discrete":
                cmb_type.setCurrentIndex(2)
            else:
                cmb_type.setCurrentIndex(0)
            self.var_config_table.setCellWidget(idx, 2, cmb_type)

    def auto_fill_variable_types(self) -> None:
        """Gọi Lõi xử lý để quét kiểu biến và điền sẵn vào bảng cấu hình."""
        df_clean = self.extract_dataframe_from_table()
        if df_clean.empty:
            QMessageBox.information(self, "Thông báo", "Bảng dữ liệu đang trống.")
            return
        inspected = PhartaCoreEngine.inspect_variables(df_clean)
        for r in range(self.var_config_table.rowCount()):
            col_name = self.var_config_table.item(r, 0).text()
            cmb_type: QComboBox = self.var_config_table.cellWidget(r, 2)
            if col_name in inspected and cmb_type:
                v_type = inspected[col_name]["type"]
                cmb_type.setCurrentIndex(1 if v_type == "continuous" else 2)
        self.statusBar().showMessage("Đã tự động điền kiểu biến gợi ý từ Lõi xử lý Pharta.", 5000)

    def rename_selected_column(self) -> None:
        col = self.table.currentColumn()
        if col >= 0:
            self.rename_column_by_index(col)

    def rename_column_by_index(self, col_idx: int) -> None:
        curr_item = self.table.horizontalHeaderItem(col_idx)
        curr_name = curr_item.text() if curr_item else f"Bien_{col_idx+1}"
        new_name, ok = QInputDialog.getText(self, "Đổi tên cột biến", "Nhập tên biến mới:", text=curr_name)
        if ok and new_name.strip():
            self.table.setHorizontalHeaderItem(col_idx, QTableWidgetItem(new_name.strip()))
            self.sync_variable_config_from_table()

    def paste_from_clipboard(self) -> None:
        text = QGuiApplication.clipboard().text()
        if not text or not text.strip():
            return
        lines = [line.split("\t") for line in text.strip().splitlines()]
        if not lines:
            return
        with self.updating():
            start_r = max(0, self.table.currentRow())
            start_c = max(0, self.table.currentColumn())
            # Nếu người dùng dán từ dòng 0 và dòng đầu tiên có vẻ là tiêu đề cột
            first_row = lines[0]
            has_header = any(not cell.replace(".", "", 1).replace("-", "", 1).isdigit() for cell in first_row if cell.strip())
            if start_r == 0 and has_header and len(lines) > 1:
                self.table.setColumnCount(max(self.table.columnCount(), start_c + len(first_row)))
                for c_idx, h_text in enumerate(first_row):
                    if h_text.strip():
                        self.table.setHorizontalHeaderItem(start_c + c_idx, QTableWidgetItem(h_text.strip()))
                lines = lines[1:]

            needed_rows = start_r + len(lines)
            needed_cols = start_c + max(len(r) for r in lines)
            if needed_rows > self.table.rowCount():
                self.table.setRowCount(needed_rows)
            if needed_cols > self.table.columnCount():
                self.table.setColumnCount(needed_cols)

            for r_offset, row_vals in enumerate(lines):
                for c_offset, val in enumerate(row_vals):
                    self.table.setItem(start_r + r_offset, start_c + c_offset, QTableWidgetItem(val.strip()))

        self.sync_variable_config_from_table()
        self.on_user_action()
        self.statusBar().showMessage("Đã dán dữ liệu từ Clipboard thành công.", 4000)

    def on_sample_selected(self, idx: int) -> None:
        if self.is_updating or idx <= 0:
            return
        sample_name = self.cmb_samples.currentText()
        sample = self.sample_datasets.get(sample_name)
        if not sample:
            return
        df_sample = sample["df"]
        cfg = sample.get("config", {})
        self.df = df_sample.copy()
        self.show_data(self.df, default_config=cfg)

        with self.updating():
            self.chk_paired.setChecked(bool(cfg.get("paired", False)))
            self.chk_proportion.setChecked(bool(cfg.get("is_proportion_outcome", False)))
            self.chk_pop_var.setChecked(bool(cfg.get("pop_variance_known", False)))
            if "pop_sigma1" in cfg:
                self.spn_sigma1.setValue(float(cfg["pop_sigma1"]))
            if "mu0" in cfg:
                self.spn_mu0.setValue(float(cfg["mu0"]))
            f_mode = cfg.get("format_mode", "auto")
            mode_map = {"auto": 0, "free": 1, "preselected": 2, "compare_groups": 3}
            self.cmb_format_mode.setCurrentIndex(mode_map.get(f_mode, 0))

        self.set_baseline_state()
        self.statusBar().showMessage(f"Đã nạp bộ dữ liệu mẫu: {sample_name}. Nhấn 'Chạy Phân Tích Tự Động' để xem kết quả!", 6000)

    # ===================== Giao tiếp với Lõi xử lý (Core Engine) =====================
    def build_request_payload(self) -> Dict[str, Any]:
        """Đóng gói Request Payload từ các thiết lập trên GUI để gửi xuống Core Engine (UR.F001.01)."""
        df_clean = self.extract_dataframe_from_table()
        if self.var_config_table.rowCount() == 0 and not df_clean.empty:
            self.sync_variable_config_from_table()

        iv_cols = []
        dv_cols = []
        third_var = None
        var_types = {}

        for r in range(self.var_config_table.rowCount()):
            col_item = self.var_config_table.item(r, 0)
            if not col_item:
                continue
            col_name = col_item.text()
            if col_name not in df_clean.columns:
                continue
            cmb_role: QComboBox = self.var_config_table.cellWidget(r, 1)
            cmb_type: QComboBox = self.var_config_table.cellWidget(r, 2)
            role = cmb_role.currentData() if cmb_role else "dv"
            v_type = cmb_type.currentData() if cmb_type else "auto"

            if role == "iv":
                iv_cols.append(col_name)
            elif role == "dv":
                dv_cols.append(col_name)
            elif role == "third":
                third_var = col_name

            if v_type in ("discrete", "continuous"):
                var_types[col_name] = v_type

        alpha_map = {0: 0.05, 1: 0.01, 2: 0.10}
        alpha = alpha_map.get(self.cmb_alpha.currentIndex(), 0.05)

        mode_map = {0: "auto", 1: "free", 2: "preselected", 3: "compare_groups"}
        format_mode = mode_map.get(self.cmb_format_mode.currentIndex(), "auto")

        return {
            "dataframe": df_clean,
            "independent_vars": iv_cols,
            "dependent_vars": dv_cols,
            "third_var": third_var,
            "var_types": var_types,
            "alpha": alpha,
            "paired": self.chk_paired.isChecked(),
            "is_proportion_outcome": self.chk_proportion.isChecked(),
            "pop_variance_known": self.chk_pop_var.isChecked(),
            "pop_sigma1": self.spn_sigma1.value(),
            "pop_sigma2": self.spn_sigma1.value(),
            "mu0": self.spn_mu0.value(),
            "p0": 0.5,
            "format_mode": format_mode,
        }

    def run_statistical_analysis(self) -> None:
        """Gửi Request xuống Lõi xử lý Pharta và hiển thị kết quả trả về (UR.F001.01)."""
        try:
            request = self.build_request_payload()
            response = PhartaCoreEngine.analyze(request)
            self.last_response = response
            self._render_analysis_response(response)
            self.tabs.setCurrentIndex(1)
            self.statusBar().showMessage(
                f"Phân tích hoàn tất trong {response.get('execution_time_ms', 0)} ms - "
                f"Phép kiểm: {response['result']['test_name_vi']}",
                7000
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Không thể thực hiện phân tích",
                f"Hệ thống phát hiện vấn đề trong dữ liệu hoặc cấu hình biến:\n\n{exc}"
            )

    def _render_analysis_response(self, response: Dict[str, Any]) -> None:
        """Hiển thị kết quả từ JSON/Dict của Lõi xử lý lên các Tab giao diện."""
        res = response["result"]
        warnings = response.get("warnings", [])
        assumptions = response.get("assumptions", {})
        path = response.get("decision_path", [])
        exec_ms = response.get("execution_time_ms", 0)

        sig = res.get("significant", False)
        p_val = res.get("p_value")
        p_str = "< 0.001" if (p_val is not None and p_val < 0.001) else (f"{p_val:.4f}" if p_val is not None else "N/A")

        # Cập nhật thanh huy hiệu tóm tắt
        badge_bg = "#dcfce7" if sig else "#fef3c7"
        badge_fg = "#166534" if sig else "#92400e"
        sig_label = "CÓ Ý NGHĨA THỐNG KÊ" if sig else "KHÔNG CÓ Ý NGHĨA THỐNG KÊ"
        self.lbl_summary_badge.setStyleSheet(
            f"background-color: {badge_bg}; color: {badge_fg}; font-weight: bold; padding: 8px 12px; border-radius: 6px;"
        )
        self.lbl_summary_badge.setText(
            f"✅ {res['test_name_vi']} ({res['panel']})  |  "
            f"{res['statistic_name']} = {res['statistic']}  |  p = {p_str}  →  {sig_label} (Thời gian: {exec_ms} ms)"
        )

        # Xây dựng HTML Báo cáo Lâm sàng Tiếng Việt
        html_parts = [
            "<div style='font-family: Segoe UI, sans-serif; color: #0f172a; line-height: 1.55;'>"
        ]

        if warnings:
            html_parts.append(
                "<div style='background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 10px 14px; margin-bottom: 12px;'>"
                "<b style='color: #b45309;'>⚠️ Cảnh báo từ Hệ thống (UR.F001.02):</b><ul style='margin: 4px 0 0 18px;'>"
            )
            for w in warnings:
                html_parts.append(f"<li>{w}</li>")
            html_parts.append("</ul></div>")

        html_parts.append(
            f"<div style='background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;'>"
            f"<h3 style='margin: 0 0 6px 0; color: #0369a1;'>1. Phép kiểm định được lựa chọn tự động: {res['test_name_vi']}</h3>"
            f"<p style='margin: 2px 0;'><b>Tên quốc tế:</b> {res.get('test_name_en', '')} &nbsp;|&nbsp; "
            f"<b>Nhánh Phụ lục A:</b> {res.get('panel', '')} &nbsp;|&nbsp; "
            f"<b>Mức ý nghĩa α:</b> {res.get('alpha', 0.05)}</p>"
            f"<p style='margin: 2px 0;'><b>Trị số thống kê ({res['statistic_name']}):</b> {res['statistic']} &nbsp;|&nbsp; "
            f"<b>Bậc tự do (df):</b> {res.get('df') if res.get('df') is not None else 'Không áp dụng'} &nbsp;|&nbsp; "
            f"<b>Giá trị p (p-value):</b> <span style='color: #dc2626; font-weight: bold;'>{p_str}</span></p>"
            f"</div>"
        )

        if assumptions and assumptions.get("summary"):
            html_parts.append(
                f"<div style='background-color: #f0f9ff; border-left: 4px solid #0284c7; padding: 10px 14px; margin-bottom: 12px;'>"
                f"<b>🔍 Kết quả kiểm tra giả định thống kê (ND/H & Điều kiện kỳ vọng):</b><br/>"
                f"{assumptions.get('summary')}"
                f"</div>"
            )

        html_parts.append(
            f"<div style='background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px 16px;'>"
            f"<h3 style='margin: 0 0 6px 0; color: #15803d;'>2. Diễn giải Ý nghĩa Lâm sàng (Tiếng Việt - UR.F003.01):</h3>"
            f"<p style='margin: 0; font-size: 14px;'>{res.get('interpretation_vi', '')}</p>"
            f"</div></div>"
        )
        self.txt_clinical_report.setHtml("".join(html_parts))

        # Hiển thị Bảng chuẩn APA
        apa = res.get("apa_table", {})
        headers = apa.get("headers", [])
        rows = apa.get("rows", [])
        self.apa_table_widget.clear()
        self.apa_table_widget.setColumnCount(len(headers))
        self.apa_table_widget.setRowCount(len(rows))
        self.apa_table_widget.setHorizontalHeaderLabels(headers)
        for r_idx, r_vals in enumerate(rows):
            for c_idx, val in enumerate(r_vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter if c_idx > 0 else (Qt.AlignLeft | Qt.AlignVCenter))
                self.apa_table_widget.setItem(r_idx, c_idx, item)

        # Hiển thị Tab 3: Lưu đồ Cây quyết định & JSON Payload
        tree_html = [
            "<div style='font-family: Segoe UI, sans-serif; color: #0f172a;'>",
            "<h3 style='color: #0369a1;'>🌳 Lưu Đồ Rẽ Nhánh Cây Quyết Định (Theo Phụ Lục A)</h3>",
            "<ol style='line-height: 1.7;'>"
        ]
        for step in path:
            detail_html = f"<br/><span style='color: #64748b; font-size: 12px;'>↳ Chi tiết: {step['detail']}</span>" if step.get("detail") else ""
            tree_html.append(
                f"<li><b>[{step['panel']}] {step['node']}</b> → "
                f"<span style='color: #0d9488; font-weight: bold;'>{step['branch']}</span>{detail_html}</li>"
            )
        tree_html.append("</ol>")
        tree_html.append(
            "<hr/><h3 style='color: #0369a1;'>📦 Cấu Trúc Dữ Liệu Giao Tiếp Giữa Lõi Xử Lý & Giao Diện (JSON Payload)</h3>"
            "<p style='color: #475569; font-size: 12px;'>"
            "Giải đáp kỹ thuật (UR.F001.01): Cấu trúc JSON phân tách hoàn toàn Lõi xử lý và Giao diện, biểu diễn "
            "tường minh đường đi trên Cây quyết định (`decision_path`), kiểm tra giả định (`assumptions`), "
            "bảng chuẩn APA (`apa_table`) và thông số biểu đồ (`chart`).</p>"
            f"<pre style='background-color: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 6px; font-family: Consolas, monospace; font-size: 12px;'>"
            f"{PhartaCoreEngine.to_json(response, indent=2)}</pre></div>"
        )
        self.txt_tree_and_json.setHtml("".join(tree_html))

        # Hiển thị Tab 4: Biểu đồ trực quan
        self.chart_widget.set_chart_spec(res.get("chart"))

    # ===================== Xuất Báo cáo APA & Biểu đồ =====================
    def export_apa_report_html(self) -> None:
        if not self.last_response:
            QMessageBox.information(self, "Thông báo", "Chưa có kết quả phân tích để xuất báo cáo.")
            return
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Xuất Báo Cáo Chuẩn APA", "BaoCao_ThongKe_Pharta_APA.html", "HTML Report (*.html);;CSV Table (*.csv)"
        )
        if not file_name:
            return
        res = self.last_response["result"]
        apa = res.get("apa_table", {})
        headers = apa.get("headers", [])
        rows = apa.get("rows", [])

        if file_name.lower().endswith(".csv"):
            out_df = pd.DataFrame(rows, columns=headers)
            out_df.to_csv(file_name, index=False, encoding="utf-8-sig")
        else:
            th_html = "".join(f"<th style='border-top: 2px solid #000; border-bottom: 1px solid #000; padding: 8px; text-align: center;'>{h}</th>" for h in headers)
            tr_html = []
            for idx, r in enumerate(rows):
                b_style = "border-bottom: 2px solid #000;" if idx == len(rows) - 1 else ""
                tds = "".join(f"<td style='{b_style} padding: 7px 10px; text-align: {'left' if i == 0 else 'center'};'>{c}</td>" for i, c in enumerate(r))
                tr_html.append(f"<tr>{tds}</tr>")
            doc_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8"/>
<title>Báo cáo Phân tích Thống kê Y Dược Pharta (Chuẩn APA)</title>
<style>
body {{ font-family: 'Times New Roman', Times, serif; margin: 40px; color: #000; line-height: 1.6; }}
h1, h2 {{ font-family: 'Segoe UI', Arial, sans-serif; color: #0f172a; }}
table.apa {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 12pt; }}
.interp {{ background: #f8fafc; border-left: 4px solid #0284c7; padding: 12px 16px; margin: 16px 0; }}
</style>
</head>
<body>
<h1>BÁO CÁO KẾT QUẢ PHÂN TÍCH THỐNG KÊ Y DƯỢC (PHARTA)</h1>
<p><b>Phép kiểm định:</b> {res['test_name_vi']} ({res.get('test_name_en', '')})</p>
<p><b>Nhánh Cây quyết định:</b> {res.get('panel', '')} &nbsp;|&nbsp; <b>Mức ý nghĩa α:</b> {res.get('alpha', 0.05)}</p>
<h2>1. Diễn giải Lâm sàng</h2>
<div class="interp">{res.get('interpretation_vi', '')}</div>
<h2>2. Bảng Kết quả Chuẩn Quốc tế APA</h2>
<p><i>Bảng 1. Kết quả phân tích {res['test_name_vi']}</i></p>
<table class="apa">
<thead><tr>{th_html}</tr></thead>
<tbody>{''.join(tr_html)}</tbody>
</table>
<p><i>Ghi chú:</i> Báo cáo được trích xuất tự động từ phần mềm Pharta ở mức ý nghĩa thống kê α = {res.get('alpha', 0.05)}.</p>
</body>
</html>"""
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(doc_html)
        QMessageBox.information(self, "Xuất báo cáo thành công", f"Đã lưu báo cáo chuẩn APA tại:\n{file_name}")

    def copy_report_to_clipboard(self) -> None:
        if not self.last_response:
            return
        res = self.last_response["result"]
        apa = res.get("apa_table", {})
        lines = [
            f"PHÉP KIỂM ĐỊNH: {res['test_name_vi']}",
            f"DIỄN GIẢI LÂM SÀNG: {res.get('interpretation_vi', '')}",
            "",
            "\t".join(apa.get("headers", [])),
        ]
        for r in apa.get("rows", []):
            lines.append("\t".join(map(str, r)))
        QGuiApplication.clipboard().setText("\n".join(lines))
        self.statusBar().showMessage("Đã sao chép Diễn giải lâm sàng và Bảng APA vào Clipboard!", 4000)

    def save_chart_image(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(self, "Lưu ảnh Biểu đồ", "BieuDo_Pharta.png", "PNG Image (*.png)")
        if file_name:
            pixmap = self.chart_widget.grab()
            pixmap.save(file_name, "PNG")
            self.statusBar().showMessage(f"Đã lưu biểu đồ tại: {file_name}", 4000)

    # ===================== Quản lý Tệp Dự Án & Undo/Redo =====================
    def get_ui_state(self) -> Dict[str, Any]:
        t = self.table
        cols = range(t.columnCount())
        headers = [h.text() if (h := t.horizontalHeaderItem(c)) else f"Bien_{c+1}" for c in cols]
        data = [[it.text() if (it := t.item(r, c)) else "" for c in cols] for r in range(t.rowCount())]
        self.df = pd.DataFrame(data, columns=headers)

        state = {"dataframe": self.df}
        state.update({
            w.objectName(): getattr(w, getter)()
            for w, getter, _, _ in self._widgets() if w.objectName()
        })
        return state

    def restore_ui_state(self, state: Dict[str, Any]) -> None:
        with self.updating():
            self.df = state.get("dataframe")
            if self.df is not None:
                self.show_data(self.df)
            for w, _, setter, _ in self._widgets():
                if w.objectName() in state:
                    getattr(w, setter)(state[w.objectName()])

    def import_file_window(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, "Nạp tệp dữ liệu Y Dược", "", DATA_FILTER)
        if file_name:
            try:
                self.df = PhartaCoreEngine.load_file(file_name)
                self.show_data(self.df)
                self.set_baseline_state()
                self.tabs.setCurrentIndex(0)
                self.statusBar().showMessage(f"Đã nạp tệp: {file_name} ({len(self.df)} dòng).", 5000)
            except Exception as exc:
                QMessageBox.critical(self, "Lỗi nạp tệp", f"Không thể đọc tệp dữ liệu:\n{exc}")

    def _write_project(self, path: str) -> bool:
        with open(path, "wb") as f:
            pickle.dump(self.get_ui_state(), f)
        self.current_file_path = path
        return True

    def save_file_window(self) -> bool:
        file_name, _ = QFileDialog.getSaveFileName(self, "Lưu dự án Pharta", "", PF_FILTER)
        return bool(file_name) and self._write_project(file_name)

    def save_current_project(self) -> bool:
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
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
=======
    def load_file_window(self) -> None:
        if not self.hoi_luu_truoc():
            return
        file_name, _ = QFileDialog.getOpenFileName(self, "Mở dự án Pharta", "", PF_FILTER)
        if file_name:
            with open(file_name, "rb") as f:
                self.restore_ui_state(pickle.load(f))
            self.current_file_path = file_name
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
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
=======
    def new_project_window(self) -> None:
        if self.hoi_luu_truoc():
            self.df = None
            self.current_file_path = None
            self.last_response = None
            self.reset_table()
            self.set_baseline_state()

    def on_user_action(self, *args) -> None:
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
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
=======
    def _step(self, src, dst, name: str) -> None:
        if not src:
            self.statusBar().showMessage(f"Không có thao tác nào để {name}.", 3000)
            return
        dst.append(self.last_state)
        self.last_state = src.pop()
        self.restore_ui_state(self.last_state)
        self.statusBar().showMessage(f"Đã {name} thành công!", 3000)

    def undo_action(self) -> None:
        self._step(self.undo_stack, self.redo_stack, "Hoàn tác (Undo)")

    def redo_action(self) -> None:
        self._step(self.redo_stack, self.undo_stack, "Làm lại (Redo)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
>>>>>>> Stashed changes
