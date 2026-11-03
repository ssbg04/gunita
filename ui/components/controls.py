"""
Control panels for parameters, directory selection, and action buttons.
"""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QSlider,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFileDialog,
    QProgressBar,
)

from core.models import CropConfig

DEFAULT_THRESHOLD = 225
DEFAULT_PADDING = 15
DEFAULT_MIN_DENSITY = 50
DEFAULT_FORMAT_INDEX = 0


class ControlsPanel(QWidget):
    params_changed = Signal()
    start_batch_requested = Signal()
    cancel_batch_requested = Signal()
    add_files_requested = Signal()
    add_folder_requested = Signal()
    clear_files_requested = Signal()

    def __init__(self, default_output_folder: Path, parent=None):
        super().__init__(parent)
        self.default_output_folder = default_output_folder

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(12)

        # 1. File Actions Box
        file_box = QGroupBox("File Input")
        file_lay = QHBoxLayout(file_box)
        self.btn_add_files = QPushButton("Add Files...")
        self.btn_add_folder = QPushButton("Add Folder...")
        self.btn_clear = QPushButton("Clear")

        self.btn_add_files.clicked.connect(self.add_files_requested.emit)
        self.btn_add_folder.clicked.connect(self.add_folder_requested.emit)
        self.btn_clear.clicked.connect(self.clear_files_requested.emit)

        file_lay.addWidget(self.btn_add_files)
        file_lay.addWidget(self.btn_add_folder)
        file_lay.addWidget(self.btn_clear)
        main_layout.addWidget(file_box)

        # 2. Parameters Box
        param_box = QGroupBox("Tuning Parameters")
        param_grid = QGridLayout(param_box)
        param_grid.setSpacing(8)

        # Threshold
        lbl_thresh = QLabel("Threshold (0-255):")
        self.slider_thresh = QSlider(Qt.Orientation.Horizontal)
        self.slider_thresh.setRange(100, 255)
        self.slider_thresh.setValue(DEFAULT_THRESHOLD)
        self.spin_thresh = QSpinBox()
        self.spin_thresh.setRange(100, 255)
        self.spin_thresh.setValue(DEFAULT_THRESHOLD)
        self.slider_thresh.valueChanged.connect(self.spin_thresh.setValue)
        self.spin_thresh.valueChanged.connect(self.slider_thresh.setValue)
        self.slider_thresh.valueChanged.connect(lambda _: self.params_changed.emit())

        param_grid.addWidget(lbl_thresh, 0, 0)
        param_grid.addWidget(self.slider_thresh, 0, 1)
        param_grid.addWidget(self.spin_thresh, 0, 2)

        # Padding
        lbl_pad = QLabel("Padding (px):")
        self.slider_pad = QSlider(Qt.Orientation.Horizontal)
        self.slider_pad.setRange(0, 100)
        self.slider_pad.setValue(DEFAULT_PADDING)
        self.spin_pad = QSpinBox()
        self.spin_pad.setRange(0, 100)
        self.spin_pad.setValue(DEFAULT_PADDING)
        self.slider_pad.valueChanged.connect(self.spin_pad.setValue)
        self.spin_pad.valueChanged.connect(self.slider_pad.setValue)
        self.slider_pad.valueChanged.connect(lambda _: self.params_changed.emit())

        param_grid.addWidget(lbl_pad, 1, 0)
        param_grid.addWidget(self.slider_pad, 1, 1)
        param_grid.addWidget(self.spin_pad, 1, 2)

        # Min Density
        lbl_density = QLabel("Min Density:")
        self.slider_density = QSlider(Qt.Orientation.Horizontal)
        self.slider_density.setRange(0, 300)
        self.slider_density.setValue(DEFAULT_MIN_DENSITY)
        self.spin_density = QSpinBox()
        self.spin_density.setRange(0, 300)
        self.spin_density.setValue(DEFAULT_MIN_DENSITY)
        self.slider_density.valueChanged.connect(self.spin_density.setValue)
        self.spin_density.valueChanged.connect(self.slider_density.setValue)
        self.slider_density.valueChanged.connect(lambda _: self.params_changed.emit())

        param_grid.addWidget(lbl_density, 2, 0)
        param_grid.addWidget(self.slider_density, 2, 1)
        param_grid.addWidget(self.spin_density, 2, 2)

        # Format combo
        lbl_fmt = QLabel("Format:")
        self.combo_format = QComboBox()
        self.combo_format.addItems(["Auto (Match Input)", "PNG", "JPEG"])
        param_grid.addWidget(lbl_fmt, 3, 0)
        param_grid.addWidget(self.combo_format, 3, 1, 1, 2)

        # Reset to Defaults button
        self.btn_reset_defaults = QPushButton("Reset to Defaults")
        self.btn_reset_defaults.setToolTip("Restore default parameter values (Threshold: 225, Padding: 15, Min Density: 50)")
        self.btn_reset_defaults.clicked.connect(self.reset_to_defaults)
        param_grid.addWidget(self.btn_reset_defaults, 4, 0, 1, 3)

        main_layout.addWidget(param_box)

        # 3. Output Folder Box
        out_box = QGroupBox("Destination Folder")
        out_lay = QHBoxLayout(out_box)
        self.line_out = QLineEdit(str(self.default_output_folder))
        self.btn_browse_out = QPushButton("Browse...")
        self.btn_browse_out.clicked.connect(self._browse_output_dir)
        out_lay.addWidget(self.line_out)
        out_lay.addWidget(self.btn_browse_out)
        main_layout.addWidget(out_box)

        # 4. Action & Progress Box
        action_box = QGroupBox("Execution")
        action_lay = QVBoxLayout(action_box)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Start Batch Processing")
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("DangerButton")
        self.btn_cancel.setEnabled(False)

        self.btn_start.clicked.connect(self.start_batch_requested.emit)
        self.btn_cancel.clicked.connect(self.cancel_batch_requested.emit)

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_cancel)
        action_lay.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        action_lay.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #7aa2f7;")
        action_lay.addWidget(self.status_label)

        main_layout.addWidget(action_box)
        main_layout.addStretch()

    def reset_to_defaults(self):
        """Restore all tuning parameters to factory defaults."""
        self.slider_thresh.setValue(DEFAULT_THRESHOLD)
        self.slider_pad.setValue(DEFAULT_PADDING)
        self.slider_density.setValue(DEFAULT_MIN_DENSITY)
        self.combo_format.setCurrentIndex(DEFAULT_FORMAT_INDEX)
        self.params_changed.emit()

    def _browse_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.line_out.text())
        if folder:
            self.line_out.setText(folder)

    def get_output_folder(self) -> Path:
        return Path(self.line_out.text().strip())

    def get_config(self) -> CropConfig:
        fmt_text = self.combo_format.currentText()
        out_fmt = None
        if "PNG" in fmt_text:
            out_fmt = "PNG"
        elif "JPEG" in fmt_text:
            out_fmt = "JPEG"

        return CropConfig(
            threshold=self.spin_thresh.value(),
            padding=self.spin_pad.value(),
            min_density=self.spin_density.value(),
            output_format=out_fmt,
        )

    def set_processing_state(self, is_processing: bool):
        self.btn_start.setEnabled(not is_processing)
        self.btn_add_files.setEnabled(not is_processing)
        self.btn_add_folder.setEnabled(not is_processing)
        self.btn_clear.setEnabled(not is_processing)
        self.btn_reset_defaults.setEnabled(not is_processing)
        self.btn_cancel.setEnabled(is_processing)
