"""
File list and drop zone table widget.
Handles drag-and-drop and selection events.
"""

from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)

from core.models import ProcessResult

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


class FileTableWidget(QTableWidget):
    file_selected = Signal(Path)       # emitted on row selection
    files_dropped = Signal(list)       # emitted when valid files/folders are dropped

    COL_INDEX = 0
    COL_NAME = 1
    COL_ORIG_SIZE = 2
    COL_CROP_SIZE = 3
    COL_STATUS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["#", "Filename", "Original Size", "Cropped Size", "Status"])
        self.horizontalHeader().setSectionResizeMode(self.COL_INDEX, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(self.COL_ORIG_SIZE, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(self.COL_CROP_SIZE, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAcceptDrops(True)
        self.verticalHeader().setVisible(False)

        self._file_paths: List[Path] = []
        self._results_map: dict[Path, ProcessResult] = {}

        self.itemSelectionChanged.connect(self._handle_selection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                local_path = Path(url.toLocalFile())
                if local_path.is_file() and local_path.suffix.lower() in IMAGE_EXTENSIONS:
                    paths.append(local_path)
                elif local_path.is_dir():
                    for ext in IMAGE_EXTENSIONS:
                        paths.extend(local_path.glob(f"*{ext}"))
                        paths.extend(local_path.glob(f"*{ext.upper()}"))
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def add_files(self, paths: List[Path]):
        existing_set = set(self._file_paths)
        for p in paths:
            if p not in existing_set:
                self._file_paths.append(p)
                row = self.rowCount()
                self.insertRow(row)

                item_idx = QTableWidgetItem(str(row + 1))
                item_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, self.COL_INDEX, item_idx)

                item_name = QTableWidgetItem(p.name)
                item_name.setToolTip(str(p))
                self.setItem(row, self.COL_NAME, item_name)

                item_orig = QTableWidgetItem("—")
                item_orig.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, self.COL_ORIG_SIZE, item_orig)

                item_crop = QTableWidgetItem("—")
                item_crop.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, self.COL_CROP_SIZE, item_crop)

                item_status = QTableWidgetItem("Pending")
                item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_status.setForeground(QColor("#7aa2f7"))
                self.setItem(row, self.COL_STATUS, item_status)

    def get_all_files(self) -> List[Path]:
        return list(self._file_paths)

    def clear_all(self):
        self.setRowCount(0)
        self._file_paths.clear()
        self._results_map.clear()

    def update_result(self, result: ProcessResult):
        self._results_map[result.input_path] = result
        try:
            row = self._file_paths.index(result.input_path)
        except ValueError:
            return

        # Original size
        if result.original_size != (0, 0):
            orig_txt = f"{result.original_size[0]} × {result.original_size[1]}"
            self.item(row, self.COL_ORIG_SIZE).setText(orig_txt)

        # Cropped size
        if result.cropped_size != (0, 0):
            crop_txt = f"{result.cropped_size[0]} × {result.cropped_size[1]}"
            self.item(row, self.COL_CROP_SIZE).setText(crop_txt)

        status_item = self.item(row, self.COL_STATUS)
        if not result.success:
            status_item.setText("Failed")
            status_item.setForeground(QColor("#f7768e"))
            status_item.setToolTip(result.error_message or "Unknown error")
        elif result.is_fallback:
            status_item.setText("No Edge (Original)")
            status_item.setForeground(QColor("#e0af68"))
        else:
            status_item.setText("Done")
            status_item.setForeground(QColor("#9ece6a"))

    def get_result(self, file_path: Path) -> Optional[ProcessResult]:
        return self._results_map.get(file_path)

    def _handle_selection(self):
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self._file_paths):
                self.file_selected.emit(self._file_paths[row])

