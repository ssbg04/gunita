"""
Main application window assembling file management, live preview, and controls.
Optimized for zero-lag live tuning and non-blocking background batches.
"""

from pathlib import Path
from typing import Optional, List, Tuple
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QPixmap, QImage, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFileDialog,
    QMessageBox,
)
from PIL import Image, ImageOps

from core.models import CropConfig, BoundingBox, ProcessResult
from core.cropper import find_content_bbox
from .styles import DARK_THEME
from .components import FileTableWidget, ComparisonPreviewWidget, ControlsPanel
from .workers import BatchWorkerThread

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
MAX_PREVIEW_DIMENSION = 1280


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """Fast zero-copy / buffer conversion from PIL Image to QPixmap without PNG encode overhead."""
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    data = pil_img.tobytes("raw", "RGB")
    qimg = QImage(data, pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gunita — Scanner Background Remover & Auto-Crop")
        self.resize(1180, 740)
        self.setStyleSheet(DARK_THEME)

        self.workspace_dir = Path(__file__).resolve().parent.parent
        self.default_output = self.workspace_dir / "cropped"

        self.active_worker: Optional[BatchWorkerThread] = None
        self.current_preview_path: Optional[Path] = None

        # Image caching for instant preview response
        self._cached_pil_orig: Optional[Image.Image] = None
        self._cached_proxy_img: Optional[Image.Image] = None
        self._proxy_scale_factor: float = 1.0
        self._cached_orig_pixmap: Optional[QPixmap] = None
        self._cached_orig_size: Tuple[int, int] = (0, 0)

        # Debounce timer for smooth slider responsiveness (50ms)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(50)
        self._debounce_timer.timeout.connect(self._recalculate_preview)

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # Main Splitter: Left (Files + Controls) vs Right (Preview)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Container
        left_container = QWidget()
        left_container.setMinimumWidth(320)
        left_container.setMaximumWidth(480)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.file_table = FileTableWidget(self)
        self.controls = ControlsPanel(default_output_folder=self.default_output, parent=self)

        left_layout.addWidget(self.file_table, stretch=3)
        left_layout.addWidget(self.controls, stretch=2)

        # Right Container (Preview area)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.preview = ComparisonPreviewWidget(self)
        right_layout.addWidget(self.preview)

        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 0)  # Left panel stays compact
        splitter.setStretchFactor(1, 1)  # Preview panel expands to fill window
        splitter.setSizes([380, 800])

        root_layout.addWidget(splitter)

        # Wire Signals
        self.file_table.file_selected.connect(self._on_file_selected)
        self.file_table.files_dropped.connect(self._on_files_dropped)

        self.controls.add_files_requested.connect(self._on_add_files)
        self.controls.add_folder_requested.connect(self._on_add_folder)
        self.controls.clear_files_requested.connect(self._on_clear_files)
        self.controls.params_changed.connect(self._on_params_changed)
        self.controls.start_batch_requested.connect(self._start_batch)
        self.controls.cancel_batch_requested.connect(self._cancel_batch)

    def _on_add_files(self):
        filter_str = "Images (*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff);;All Files (*.*)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select Image Files", str(self.workspace_dir), filter_str)
        if files:
            paths = [Path(f) for f in files]
            self.file_table.add_files(paths)
            if not self.current_preview_path and paths:
                self._select_and_preview(paths[0])

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing Scans", str(self.workspace_dir))
        if folder:
            fpath = Path(folder)
            found: List[Path] = []
            for ext in IMAGE_EXTENSIONS:
                found.extend(fpath.glob(f"*{ext}"))
                found.extend(fpath.glob(f"*{ext.upper()}"))
            if found:
                self.file_table.add_files(found)
                if not self.current_preview_path:
                    self._select_and_preview(found[0])

    def _on_files_dropped(self, paths: List[Path]):
        self.file_table.add_files(paths)
        if not self.current_preview_path and paths:
            self._select_and_preview(paths[0])

    def _on_clear_files(self):
        self.file_table.clear_all()
        self.preview.clear()
        self.current_preview_path = None
        self._cached_pil_orig = None
        self._cached_proxy_img = None
        self._cached_orig_pixmap = None
        self.controls.progress_bar.setValue(0)
        self.controls.status_label.setText("Ready")

    def _select_and_preview(self, path: Path):
        self.current_preview_path = path
        self._load_and_cache_image(path)
        self._recalculate_preview()

    def _on_file_selected(self, path: Path):
        self._select_and_preview(path)

    def _load_and_cache_image(self, path: Path):
        """Load image once into memory and generate a downsampled proxy for instantaneous slider feedback."""
        try:
            with Image.open(path) as img:
                img_normalized = ImageOps.exif_transpose(img) or img
                self._cached_pil_orig = img_normalized.convert("RGB")
                self._cached_orig_size = (self._cached_pil_orig.width, self._cached_pil_orig.height)

                # Downsample proxy if image exceeds MAX_PREVIEW_DIMENSION
                max_dim = max(self._cached_orig_size)
                if max_dim > MAX_PREVIEW_DIMENSION:
                    scale = MAX_PREVIEW_DIMENSION / max_dim
                    new_w = max(1, int(self._cached_orig_size[0] * scale))
                    new_h = max(1, int(self._cached_orig_size[1] * scale))
                    self._cached_proxy_img = self._cached_pil_orig.resize((new_w, new_h), Image.Resampling.BILINEAR)
                    self._proxy_scale_factor = scale
                else:
                    self._cached_proxy_img = self._cached_pil_orig
                    self._proxy_scale_factor = 1.0

                self._cached_orig_pixmap = pil_to_qpixmap(self._cached_proxy_img)
        except Exception:
            self._cached_pil_orig = None
            self._cached_proxy_img = None
            self._cached_orig_pixmap = None
            self._cached_orig_size = (0, 0)

    def _on_params_changed(self):
        """Debounce slider changes to maintain 60 FPS UI without blocking on every mouse move."""
        if self.current_preview_path and not self.active_worker:
            self._debounce_timer.start()

    def _recalculate_preview(self):
        if not self.current_preview_path or not self._cached_proxy_img:
            return

        cfg = self.controls.get_config()
        result = self.file_table.get_result(self.current_preview_path)

        # If already processed and saved on disk, display the real saved file
        if result and result.output_path and result.output_path.exists():
            crop_pix = QPixmap(str(result.output_path))
            self.preview.show_preview(
                orig_pixmap=self._cached_orig_pixmap,
                crop_pixmap=crop_pix,
                orig_size=self._cached_orig_size,
                crop_size=result.cropped_size,
                bbox=result.bbox,
                filename=self.current_preview_path.name,
            )
            return

        # Fast calculation using the downsampled proxy image (takes ~2ms instead of 300ms)
        proxy_cfg = CropConfig(
            threshold=cfg.threshold,
            padding=max(0, int(cfg.padding * self._proxy_scale_factor)),
            min_density=max(1, int(cfg.min_density * self._proxy_scale_factor)),
        )

        proxy_bbox = find_content_bbox(self._cached_proxy_img, proxy_cfg)

        if proxy_bbox:
            # Map proxy coordinates back to original image size
            inv_scale = 1.0 / self._proxy_scale_factor
            orig_bbox = BoundingBox(
                left=int(proxy_bbox.left * inv_scale),
                top=int(proxy_bbox.top * inv_scale),
                right=min(int(proxy_bbox.right * inv_scale), self._cached_orig_size[0]),
                bottom=min(int(proxy_bbox.bottom * inv_scale), self._cached_orig_size[1]),
            )
            # Crop fast from proxy for instantaneous preview
            cropped_proxy = self._cached_proxy_img.crop(proxy_bbox.as_tuple())
            crop_pix = pil_to_qpixmap(cropped_proxy)
            crop_size = (orig_bbox.width, orig_bbox.height)
            display_bbox = orig_bbox
        else:
            display_bbox = None
            crop_size = self._cached_orig_size
            crop_pix = self._cached_orig_pixmap

        self.preview.show_preview(
            orig_pixmap=self._cached_orig_pixmap,
            crop_pixmap=crop_pix,
            orig_size=self._cached_orig_size,
            crop_size=crop_size,
            bbox=display_bbox,
            filename=self.current_preview_path.name,
        )

    def _start_batch(self):
        files = self.file_table.get_all_files()
        if not files:
            QMessageBox.information(self, "No Files", "Please add image files before starting processing.")
            return

        out_folder = self.controls.get_output_folder()
        cfg = self.controls.get_config()

        self.controls.set_processing_state(True)
        self.controls.progress_bar.setMaximum(len(files))
        self.controls.progress_bar.setValue(0)
        self.controls.status_label.setText(f"Processing 0 / {len(files)}...")

        self.active_worker = BatchWorkerThread(files, out_folder, cfg, self)
        self.active_worker.progress.connect(self._on_worker_progress)
        self.active_worker.finished_batch.connect(self._on_worker_finished)
        self.active_worker.error.connect(self._on_worker_error)
        self.active_worker.start()

    def _cancel_batch(self):
        if self.active_worker:
            self.active_worker.cancel()
            self.controls.status_label.setText("Cancelling...")

    def _on_worker_progress(self, current: int, total: int, res: ProcessResult):
        self.file_table.update_result(res)
        self.controls.progress_bar.setValue(current)
        self.controls.status_label.setText(f"Processed {current} / {total} files")

        if self.current_preview_path == res.input_path:
            self._recalculate_preview()

    def _on_worker_finished(self, results: List[ProcessResult]):
        self.controls.set_processing_state(False)
        self.active_worker = None
        success_count = sum(1 for r in results if r.success)
        self.controls.status_label.setText(f"Completed: {success_count} / {len(results)} saved successfully.")

        if self.current_preview_path:
            self._recalculate_preview()

        out_folder = self.controls.get_output_folder()
        reply = QMessageBox.question(
            self,
            "Batch Complete",
            f"Finished processing {len(results)} images.\n\nOpen output folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes and out_folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(out_folder)))

    def _on_worker_error(self, err_msg: str):
        self.controls.set_processing_state(False)
        self.active_worker = None
        QMessageBox.critical(self, "Processing Error", f"An error occurred during batch execution:\n{err_msg}")
