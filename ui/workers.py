"""
Background threading workers for batch processing without blocking GUI.
"""

from pathlib import Path
from typing import List
from PySide6.QtCore import QThread, Signal

from core.models import CropConfig, ProcessResult
from core.cropper import process_single_image


class BatchWorkerThread(QThread):
    progress = Signal(int, int, object)  # (current_index, total_count, ProcessResult)
    finished_batch = Signal(list)        # list of ProcessResult
    error = Signal(str)

    def __init__(
        self,
        files: List[Path],
        output_folder: Path,
        config: CropConfig,
        parent=None,
    ):
        super().__init__(parent)
        self.files = files
        self.output_folder = output_folder
        self.config = config
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            total = len(self.files)
            results: List[ProcessResult] = []

            for index, file_path in enumerate(self.files, start=1):
                if self._is_cancelled:
                    break

                res = process_single_image(file_path, self.output_folder, self.config)
                results.append(res)
                self.progress.emit(index, total, res)

            self.finished_batch.emit(results)
        except Exception as exc:
            self.error.emit(str(exc))

