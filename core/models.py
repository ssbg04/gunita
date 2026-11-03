"""
Data models and configuration definitions for background cropper.
Pure Python - zero GUI dependencies.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass(frozen=True)
class CropConfig:
    threshold: int = 225
    padding: int = 15
    min_density: int = 50
    output_format: Optional[str] = None
    jpeg_quality: int = 95


@dataclass(frozen=True)
class BoundingBox:
    top: int
    bottom: int
    left: int
    right: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    def as_tuple(self) -> Tuple[int, int, int, int]:
        """Return (left, top, right, bottom) for PIL.Image.crop."""
        return (self.left, self.top, self.right, self.bottom)


@dataclass
class ProcessResult:
    input_path: Path
    output_path: Optional[Path] = None
    original_size: Tuple[int, int] = (0, 0)
    cropped_size: Tuple[int, int] = (0, 0)
    bbox: Optional[BoundingBox] = None
    success: bool = True
    is_fallback: bool = False
    error_message: Optional[str] = None

