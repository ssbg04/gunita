"""
Batch processing coordinator.
Pure Python - zero GUI dependencies.
"""

from pathlib import Path
from typing import Callable, Iterable, List, Optional
from .models import CropConfig, ProcessResult
from .cropper import process_single_image


ProgressCallback = Callable[[int, int, ProcessResult], None]


def run_batch(
    file_paths: Iterable[Path],
    output_folder: Path,
    config: Optional[CropConfig] = None,
    on_progress: Optional[ProgressCallback] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> List[ProcessResult]:
    """
    Sequentially process a list of files with progress reporting and cancellation support.
    """
    items = list(file_paths)
    total = len(items)
    results: List[ProcessResult] = []

    for index, path in enumerate(items, start=1):
        if is_cancelled and is_cancelled():
            break

        result = process_single_image(path, output_folder, config)
        results.append(result)

        if on_progress:
            on_progress(index, total, result)

    return results

