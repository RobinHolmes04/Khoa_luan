# -*- coding: utf-8 -*-
"""
Widget hiển thị biểu đồ trực quan (Boxplot, Bar chart, Scatter plot) thuộc Khối Giao diện (Thin UI).
Tuân thủ tuyệt đối UR.F001.01, UR.F003.03, AC-01:
- Không chứa bất kỳ thuật toán tính toán thống kê nào.
- Chỉ đọc dữ liệu tọa độ/thông số đã được Lõi xử lý (Core Engine) kết xuất sẵn trong `chart_spec` để vẽ lên màn hình.
"""

from typing import Dict, Any, Optional
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


PALETTE = [
    QColor("#0284c7"),
    QColor("#0d9488"),
    QColor("#7c3aed"),
    QColor("#ea580c"),
    QColor("#e11d48"),
    QColor("#2563eb"),
    QColor("#16a34a"),
]


class PhartaChartWidget(QWidget):
    """Widget vẽ biểu đồ trực tiếp từ thông số JSON của Core Engine."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.chart_spec: Optional[Dict[str, Any]] = None
        self.setMinimumHeight(340)

    def set_chart_spec(self, spec: Optional[Dict[str, Any]]) -> None:
        self.chart_spec = spec
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor("#ffffff"))

        if not self.chart_spec:
            painter.setPen(QColor("#64748b"))
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, "Chưa có dữ liệu biểu đồ. Hãy nhấn 'Chạy Phân Tích Tự Động' để hiển thị.")
            return

        c_type = self.chart_spec.get("type", "bar")
        title = self.chart_spec.get("title", "Biểu đồ thống kê")
        x_label = self.chart_spec.get("x_label", "")
        y_label = self.chart_spec.get("y_label", "")

        # Vẽ tiêu đề
        painter.setPen(QColor("#0f172a"))
        title_font = QFont("Segoe UI", 12, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(QRectF(20, 10, rect.width() - 40, 32), Qt.AlignCenter, title)

        margin_left = 75
        margin_right = 35
        margin_top = 52
        margin_bottom = 65
        plot_rect = QRectF(
            margin_left,
            margin_top,
            max(100, rect.width() - margin_left - margin_right),
            max(100, rect.height() - margin_top - margin_bottom)
        )

        # Khung nền biểu đồ
        painter.fillRect(plot_rect, QColor("#f8fafc"))
        painter.setPen(QPen(QColor("#cbd5e1"), 1))
        painter.drawRect(plot_rect)

        # Nhãn trục X
        label_font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(label_font)
        painter.setPen(QColor("#334155"))
        painter.drawText(
            QRectF(margin_left, rect.height() - 28, plot_rect.width(), 22),
            Qt.AlignCenter,
            f"{x_label}   (Trục tung: {y_label})"
        )

        if c_type == "boxplot":
            self._draw_boxplot(painter, plot_rect)
        elif c_type == "scatter":
            self._draw_scatter(painter, plot_rect)
        else:
            self._draw_bar(painter, plot_rect)

    def _draw_y_grid(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        if y_max <= y_min:
            y_max = y_min + 1.0
        steps = 5
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        for i in range(steps + 1):
            frac = i / steps
            val = y_min + frac * (y_max - y_min)
            py = plot_rect.bottom() - frac * plot_rect.height()
            painter.setPen(QPen(QColor("#e2e8f0"), 1, Qt.DashLine))
            painter.drawLine(QPointF(plot_rect.left(), py), QPointF(plot_rect.right(), py))
            painter.setPen(QColor("#475569"))
            painter.drawText(QRectF(5, py - 10, plot_rect.left() - 12, 20), Qt.AlignRight | Qt.AlignVCenter, f"{val:.2f}")

    def _draw_boxplot(self, painter: QPainter, plot_rect: QRectF) -> None:
        box_stats: Dict[str, Dict[str, float]] = self.chart_spec.get("box_stats", {})
        if not box_stats:
            return
        names = list(box_stats.keys())
        all_mins = [b["min"] for b in box_stats.values() if b.get("n", 0) > 0]
        all_maxs = [b["max"] for b in box_stats.values() if b.get("n", 0) > 0]
        if not all_mins or not all_maxs:
            return

        raw_min, raw_max = min(all_mins), max(all_maxs)
        pad = (raw_max - raw_min) * 0.12 if raw_max > raw_min else 1.0
        y_min, y_max = raw_min - pad, raw_max + pad
        self._draw_y_grid(painter, plot_rect, y_min, y_max)

        def to_py(v: float) -> float:
            return plot_rect.bottom() - ((v - y_min) / (y_max - y_min)) * plot_rect.height()

        k = len(names)
        slot_w = plot_rect.width() / max(1, k)
        box_w = min(64.0, slot_w * 0.45)

        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        for idx, g_name in enumerate(names):
            st = box_stats[g_name]
            if st.get("n", 0) == 0:
                continue
            cx = plot_rect.left() + (idx + 0.5) * slot_w
            py_min = to_py(st["min"])
            py_q25 = to_py(st["q25"])
            py_med = to_py(st["median"])
            py_q75 = to_py(st["q75"])
            py_max = to_py(st["max"])
            py_mean = to_py(st["mean"])

            color = PALETTE[idx % len(PALETTE)]
            fill_color = QColor(color)
            fill_color.setAlpha(75)

            # Đường râu (Whiskers)
            painter.setPen(QPen(color.darker(120), 1.8))
            painter.drawLine(QPointF(cx, py_min), QPointF(cx, py_q25))
            painter.drawLine(QPointF(cx, py_q75), QPointF(cx, py_max))
            painter.drawLine(QPointF(cx - box_w * 0.3, py_min), QPointF(cx + box_w * 0.3, py_min))
            painter.drawLine(QPointF(cx - box_w * 0.3, py_max), QPointF(cx + box_w * 0.3, py_max))

            # Hộp Q25 - Q75
            box_rect = QRectF(cx - box_w / 2.0, py_q75, box_w, max(2.0, py_q25 - py_q75))
            painter.setBrush(QBrush(fill_color))
            painter.drawRect(box_rect)

            # Đường trung vị (Median)
            painter.setPen(QPen(color.darker(150), 2.5))
            painter.drawLine(QPointF(cx - box_w / 2.0, py_med), QPointF(cx + box_w / 2.0, py_med))

            # Điểm trung bình (Mean) hình tròn nhỏ
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(cx, py_mean), 4.0, 4.0)

            # Nhãn nhóm trên trục X
            painter.setPen(QColor("#1e293b"))
            painter.drawText(
                QRectF(cx - slot_w / 2.0, plot_rect.bottom() + 6, slot_w, 26),
                Qt.AlignCenter,
                str(g_name)
            )

    def _draw_bar(self, painter: QPainter, plot_rect: QRectF) -> None:
        cats = self.chart_spec.get("categories", [])
        vals = self.chart_spec.get("values", [])
        if not cats or not vals:
            return
        y_min = 0.0
        y_max = max(vals) * 1.15 if max(vals) > 0 else 10.0
        self._draw_y_grid(painter, plot_rect, y_min, y_max)

        k = len(cats)
        slot_w = plot_rect.width() / max(1, k)
        bar_w = min(65.0, slot_w * 0.55)

        font = QFont("Segoe UI", 8)
        painter.setFont(font)

        for idx, (cat, val) in enumerate(zip(cats, vals)):
            cx = plot_rect.left() + (idx + 0.5) * slot_w
            bh = (float(val) / y_max) * plot_rect.height() if y_max > 0 else 0.0
            by = plot_rect.bottom() - bh
            color = PALETTE[idx % len(PALETTE)]
            bar_rect = QRectF(cx - bar_w / 2.0, by, bar_w, bh)

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            painter.drawRoundedRect(bar_rect, 3, 3)

            painter.setPen(QColor("#0f172a"))
            painter.drawText(QRectF(cx - slot_w / 2.0, by - 20, slot_w, 18), Qt.AlignCenter, f"{val}")
            painter.drawText(QRectF(cx - slot_w / 2.0, plot_rect.bottom() + 5, slot_w, 28), Qt.AlignCenter, str(cat))

    def _draw_scatter(self, painter: QPainter, plot_rect: QRectF) -> None:
        xs = self.chart_spec.get("x", [])
        ys = self.chart_spec.get("y", [])
        if not xs or not ys:
            return
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_pad = (x_max - x_min) * 0.08 if x_max > x_min else 1.0
        y_pad = (y_max - y_min) * 0.10 if y_max > y_min else 1.0
        x_min, x_max = x_min - x_pad, x_max + x_pad
        y_min, y_max = y_min - y_pad, y_max + y_pad

        self._draw_y_grid(painter, plot_rect, y_min, y_max)

        def to_px(vx: float) -> float:
            return plot_rect.left() + ((vx - x_min) / (x_max - x_min)) * plot_rect.width()

        def to_py(vy: float) -> float:
            return plot_rect.bottom() - ((vy - y_min) / (y_max - y_min)) * plot_rect.height()

        # Vẽ nhãn trục X
        steps = 4
        for i in range(steps + 1):
            frac = i / steps
            vx = x_min + frac * (x_max - x_min)
            px = plot_rect.left() + frac * plot_rect.width()
            painter.setPen(QColor("#475569"))
            painter.drawText(QRectF(px - 30, plot_rect.bottom() + 4, 60, 20), Qt.AlignCenter, f"{vx:.2f}")

        # Vẽ điểm dữ liệu
        color = PALETTE[0]
        fill_c = QColor(color)
        fill_c.setAlpha(160)
        painter.setBrush(QBrush(fill_c))
        painter.setPen(QPen(color.darker(130), 1.2))
        for vx, vy in zip(xs, ys):
            painter.drawEllipse(QPointF(to_px(vx), to_py(vy)), 4.2, 4.2)

        # Vẽ đường hồi quy nếu có thông số từ Core Engine
        reg = self.chart_spec.get("reg_line")
        if isinstance(reg, dict) and "intercept" in reg and "slope" in reg:
            b0 = float(reg["intercept"])
            b1 = float(reg["slope"])
            y1 = b0 + b1 * x_min
            y2 = b0 + b1 * x_max
            painter.setPen(QPen(QColor("#e11d48"), 2.2, Qt.SolidLine))
            painter.drawLine(QPointF(to_px(x_min), to_py(y1)), QPointF(to_px(x_max), to_py(y2)))
