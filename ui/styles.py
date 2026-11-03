"""
Application styling and color palette for PySide6 UI.
Modern dark theme.
"""

DARK_THEME = """
QWidget {
    background-color: #1a1b26;
    color: #c0caf5;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #2f354a;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 16px;
    font-weight: bold;
    color: #7aa2f7;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
}

/* Push Buttons */
QPushButton {
    background-color: #24283b;
    border: 1px solid #414868;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    color: #c0caf5;
}
QPushButton:hover {
    background-color: #2f354a;
    border-color: #7aa2f7;
}
QPushButton:pressed {
    background-color: #1f2335;
}
QPushButton:disabled {
    background-color: #16161e;
    color: #565f89;
    border-color: #24283b;
}

QPushButton#PrimaryButton {
    background-color: #7aa2f7;
    color: #15161e;
    border: 1px solid #7aa2f7;
    font-weight: bold;
}
QPushButton#PrimaryButton:hover {
    background-color: #89b4fa;
    border-color: #89b4fa;
}
QPushButton#PrimaryButton:pressed {
    background-color: #6187db;
}

QPushButton#DangerButton {
    background-color: #f7768e;
    color: #15161e;
    border: 1px solid #f7768e;
}
QPushButton#DangerButton:hover {
    background-color: #ff9eaf;
}

/* Text & Spin Inputs */
QLineEdit, QSpinBox {
    background-color: #1f2335;
    border: 1px solid #414868;
    border-radius: 6px;
    padding: 6px 10px;
    color: #c0caf5;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #7aa2f7;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #24283b;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #7aa2f7;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #c0caf5;
    border: 2px solid #7aa2f7;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #ffffff;
}

/* Tables */
QTableWidget {
    background-color: #1f2335;
    border: 1px solid #2f354a;
    border-radius: 8px;
    gridline-color: #24283b;
    selection-background-color: #3b4261;
    selection-color: #c0caf5;
}
QHeaderView::section {
    background-color: #24283b;
    color: #7aa2f7;
    padding: 6px;
    border: none;
    border-right: 1px solid #1a1b26;
    border-bottom: 1px solid #2f354a;
    font-weight: bold;
}

/* Progress Bar */
QProgressBar {
    background-color: #1f2335;
    border: 1px solid #414868;
    border-radius: 6px;
    text-align: center;
    color: #c0caf5;
    font-weight: bold;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #7aa2f7;
    border-radius: 5px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #1a1b26;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #414868;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #7aa2f7;
}

/* Drop Zone Highlight */
QFrame#DropZone {
    border: 2px dashed #414868;
    border-radius: 10px;
    background-color: #1f2335;
}
QFrame#DropZone[dragActive="true"] {
    border-color: #7aa2f7;
    background-color: #292e42;
}
"""

