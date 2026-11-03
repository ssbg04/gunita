"""
Image preview widgets with cached scaling, bounding box overlay, and maximized display area.
"""

from typing import Optional, Tuple
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPixmap, QPen, QColor, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSplitter,
    QSizePolicy,
)

from core.models import BoundingBox


class ImageCanvas(QWidget):
    """Canvas widget rendering a QPixmap with cached scaling and optional bounding box."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._pixmap: Optional[QPixmap] = None
        self._raw_image_size: Optional[Tuple[int, int]] = None
        self._bbox: Optional[BoundingBox] = None

        # Cached render properties
        self._cached_scaled_pixmap: Optional[QPixmap] = None
        self._cached_offset_x: float = 0.0
        self._cached_offset_y: float = 0.0

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(180, 180)
        self.setStyleSheet("background-color: #12131a; border: 1px solid #24283b; border-radius: 6px;")

    def set_image(
        self,
        pixmap: Optional[QPixmap],
        raw_size: Optional[Tuple[int, int]] = None,
        bbox: Optional[BoundingBox] = None,
    ):
        self._pixmap = pixmap
        self._raw_image_size = raw_size or ((pixmap.width(), pixmap.height()) if pixmap else None)
        self._bbox = bbox
        self._update_scaled_cache()
        self.update()

    def clear(self):
        self._pixmap = None
        self._raw_image_size = None
        self._bbox = None
        self._cached_scaled_pixmap = None
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_cache()

    def _update_scaled_cache(self):
        if not self._pixmap or self._pixmap.isNull():
            self._cached_scaled_pixmap = None
            return

        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        self._cached_scaled_pixmap = self._pixmap.scaled(
            w,
            h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._cached_offset_x = (w - self._cached_scaled_pixmap.width()) / 2.0
        self._cached_offset_y = (h - self._cached_scaled_pixmap.height()) / 2.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._cached_scaled_pixmap or self._cached_scaled_pixmap.isNull():
            painter.setPen(QColor("#565f89"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                f"No {self.title} Image",
            )
            return

        # Draw scaled image
        painter.drawPixmap(int(self._cached_offset_x), int(self._cached_offset_y), self._cached_scaled_pixmap)

        # Draw Bounding Box if present
        if self._bbox and self._raw_image_size:
            orig_w, orig_h = self._raw_image_size
            scaled_w = self._cached_scaled_pixmap.width()
            scaled_h = self._cached_scaled_pixmap.height()

            if orig_w > 0 and orig_h > 0:
                scale_x = scaled_w / orig_w
                scale_y = scaled_h / orig_h

                box_x = self._cached_offset_x + (self._bbox.left * scale_x)
                box_y = self._cached_offset_y + (self._bbox.top * scale_y)
                box_w = self._bbox.width * scale_x
                box_h = self._bbox.height * scale_y

                pen = QPen(QColor("#7dcfff"), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(125, 207, 255, 35)))
                painter.drawRect(QRectF(box_x, box_y, box_w, box_h))


class ComparisonPreviewWidget(QFrame):
    """Side-by-side comparison panel maximizing image preview area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Compact Header Bar
        self.header_bar = QFrame()
        self.header_bar.setStyleSheet("""
            QFrame {
                background-color: #1f2335;
                border: 1px solid #2f354a;
                border-radius: 6px;
                padding: 2px;
            }
        """)
        h_layout = QHBoxLayout(self.header_bar)
        h_layout.setContentsMargins(10, 4, 10, 4)
        h_layout.setSpacing(12)

        self.file_name_label = QLabel("No image selected")
        self.file_name_label.setStyleSheet("color: #7aa2f7; font-weight: bold; font-size: 13px;")

        self.dimensions_label = QLabel("")
        self.dimensions_label.setStyleSheet("color: #9aa5ce; font-size: 12px;")

        h_layout.addWidget(self.file_name_label, stretch=1)
        h_layout.addWidget(self.dimensions_label, stretch=0)
        main_layout.addWidget(self.header_bar, stretch=0)

        # Splitter for Canvases
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.setStyleSheet("QSplitter::handle { background-color: #24283b; width: 4px; }")

        # Before section
        before_container = QWidget()
        b_lay = QVBoxLayout(before_container)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setSpacing(4)
        self.lbl_b = QLabel("Original / Detection")
        self.lbl_b.setStyleSheet("color: #7aa2f7; font-weight: 600; font-size: 12px; padding: 2px;")
        self.before_canvas = ImageCanvas("Original")
        b_lay.addWidget(self.lbl_b, stretch=0)
        b_lay.addWidget(self.before_canvas, stretch=1)

        # After section
        after_container = QWidget()
        a_lay = QVBoxLayout(after_container)
        a_lay.setContentsMargins(0, 0, 0, 0)
        a_lay.setSpacing(4)
        self.lbl_a = QLabel("Cropped Result")
        self.lbl_a.setStyleSheet("color: #9ece6a; font-weight: 600; font-size: 12px; padding: 2px;")
        self.after_canvas = ImageCanvas("Cropped")
        a_lay.addWidget(self.lbl_a, stretch=0)
        a_lay.addWidget(self.after_canvas, stretch=1)

        splitter.addWidget(before_container)
        splitter.addWidget(after_container)
        splitter.setSizes([450, 450])

        main_layout.addWidget(splitter, stretch=1)

    def show_preview(
        self,
        orig_pixmap: Optional[QPixmap],
        crop_pixmap: Optional[QPixmap],
        orig_size: Optional[Tuple[int, int]] = None,
        crop_size: Optional[Tuple[int, int]] = None,
        bbox: Optional[BoundingBox] = None,
        filename: str = "",
    ):
        self.before_canvas.set_image(orig_pixmap, orig_size, bbox)
        self.after_canvas.set_image(crop_pixmap, crop_size)

        if orig_pixmap and filename:
            self.file_name_label.setText(f"📄 {filename}")
            orig_txt = f"{orig_size[0]}×{orig_size[1]} px" if orig_size else ""
            crop_txt = f"{crop_size[0]}×{crop_size[1]} px" if crop_size else "Pending"
            self.dimensions_label.setText(f"{orig_txt}  ➔  {crop_txt}")
            self.lbl_b.setText(f"Original / Detection ({orig_txt})")
            self.lbl_a.setText(f"Cropped Result ({crop_txt})")
        else:
            self.file_name_label.setText("No image selected")
            self.dimensions_label.setText("")
            self.lbl_b.setText("Original / Detection")
            self.lbl_a.setText("Cropped Result")

    def clear(self):
        self.before_canvas.clear()
        self.after_canvas.clear()
        self.file_name_label.setText("No image selected")
        self.dimensions_label.setText("")
        self.lbl_b.setText("Original / Detection")
        self.lbl_a.setText("Cropped Result")
