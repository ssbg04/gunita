"""
Core image cropping logic for detecting and removing scanner borders.
Pure Python - zero GUI dependencies.
"""

from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageOps

from .models import BoundingBox, CropConfig, ProcessResult


def find_content_bbox(image: Image.Image, config: CropConfig) -> Optional[BoundingBox]:
    """
    Analyze image array to find content boundary based on white background threshold
    and row/column density filters.
    """
    rgb = image.convert("RGB")
    arr = np.array(rgb)
    
    # Calculate average intensity across color channels
    gray = arr.mean(axis=2)
    is_content = gray < config.threshold

    row_counts = is_content.sum(axis=1)
    col_counts = is_content.sum(axis=0)

    real_rows = np.where(row_counts > config.min_density)[0]
    real_cols = np.where(col_counts > config.min_density)[0]

    if real_rows.size == 0 or real_cols.size == 0:
        return None

    top = max(int(real_rows[0]) - config.padding, 0)
    bottom = min(int(real_rows[-1]) + config.padding + 1, arr.shape[0])
    left = max(int(real_cols[0]) - config.padding, 0)
    right = min(int(real_cols[-1]) + config.padding + 1, arr.shape[1])

    return BoundingBox(top=top, bottom=bottom, left=left, right=right)


def crop_image(
    image: Image.Image,
    config: Optional[CropConfig] = None,
) -> Tuple[Image.Image, Optional[BoundingBox], bool]:
    """
    Crop scanner background from a PIL Image.
    Returns (cropped_image, bounding_box, is_fallback).
    If no content is detected, returns original image and is_fallback=True.
    """
    cfg = config or CropConfig()

    # Automatically adjust orientation based on EXIF
    normalized_img = ImageOps.exif_transpose(image) or image

    bbox = find_content_bbox(normalized_img, cfg)
    if bbox is None:
        return normalized_img, None, True

    cropped = normalized_img.crop(bbox.as_tuple())
    return cropped, bbox, False


def process_single_image(
    input_path: Path,
    output_folder: Path,
    config: Optional[CropConfig] = None,
) -> ProcessResult:
    """
    Read image from input_path, execute background cropping, save to output_folder,
    and return ProcessResult.
    """
    cfg = config or CropConfig()
    input_path = Path(input_path)
    output_folder = Path(output_folder)

    try:
        if not input_path.exists():
            return ProcessResult(
                input_path=input_path,
                success=False,
                error_message=f"File not found: {input_path}",
            )

        with Image.open(input_path) as img:
            original_size = img.size
            img_format = img.format or "PNG"
            cropped, bbox, is_fallback = crop_image(img, cfg)

        output_folder.mkdir(parents=True, exist_ok=True)
        suffix = input_path.suffix if not cfg.output_format else f".{cfg.output_format.lower()}"
        out_filename = f"{input_path.stem}_cropped{suffix}"
        output_path = output_folder / out_filename

        save_fmt = cfg.output_format or img_format
        save_kwargs = {}
        if str(save_fmt).upper() in ("JPEG", "JPG"):
            save_kwargs["quality"] = cfg.jpeg_quality
            save_kwargs["subsampling"] = 0
            if cropped.mode != "RGB":
                cropped = cropped.convert("RGB")

        cropped.save(output_path, format=save_fmt, **save_kwargs)
        cropped_size = cropped.size

        return ProcessResult(
            input_path=input_path,
            output_path=output_path,
            original_size=original_size,
            cropped_size=cropped_size,
            bbox=bbox,
            success=True,
            is_fallback=is_fallback,
        )

    except Exception as exc:
        return ProcessResult(
            input_path=input_path,
            success=False,
            error_message=str(exc),
        )

