"""
crop_white_background.py
Crops white (or near-white) backgrounds from scanned photos and saves
results in a 'cropped' folder automatically.
"""

import argparse
import sys
from pathlib import Path
import numpy as np
from PIL import Image


def crop_white_background(
    image: Image.Image,
    threshold: int = 225,
    padding: int = 15,
    min_density: int = 50,
) -> Image.Image:
    rgb = image.convert("RGB")
    arr = np.array(rgb)
    gray = arr.mean(axis=2)
    is_content = gray < threshold

    row_counts = is_content.sum(axis=1)
    col_counts = is_content.sum(axis=0)

    real_rows = np.where(row_counts > min_density)[0]
    real_cols = np.where(col_counts > min_density)[0]

    if real_rows.size == 0 or real_cols.size == 0:
        print("  Warning: No substantial content found - returning original image.")
        return image

    top = max(real_rows[0] - padding, 0)
    bottom = min(real_rows[-1] + padding + 1, arr.shape[0])
    left = max(real_cols[0] - padding, 0)
    right = min(real_cols[-1] + padding + 1, arr.shape[1])

    return image.crop((left, top, right, bottom))


def process_file(
    input_path: Path,
    output_folder: Path,
    threshold: int,
    padding: int,
    min_density: int,
) -> None:
    print(f"Processing: {input_path}")

    image = Image.open(input_path)
    original_size = image.size

    cropped = crop_white_background(
        image,
        threshold=threshold,
        padding=padding,
        min_density=min_density,
    )

    # Create 'cropped' folder if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / f"{input_path.stem}_cropped{input_path.suffix}"

    fmt = image.format or "PNG"
    save_kwargs = {}
    if fmt.upper() in ("JPEG", "JPG"):
        save_kwargs["quality"] = 95
        save_kwargs["subsampling"] = 0
        cropped = cropped.convert("RGB")

    cropped.save(output_path, format=fmt, **save_kwargs)

    new_size = cropped.size
    print(f"  Original size : {original_size[0]} x {original_size[1]} px")
    print(f"  Cropped size  : {new_size[0]} x {new_size[1]} px")
    print(f"  Saved to      : {output_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Crop white scanner backgrounds from photos and save to 'cropped' folder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        metavar="IMAGE",
        help="Input image file(s) or glob patterns.",
    )
    parser.add_argument(
        "--folder",
        metavar="FOLDER",
        help="Process all images in the specified folder.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=225,
        help="Brightness threshold (0-255). Default: 225.",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=15,
        help="Extra pixels to keep around the content boundary. Default: 15.",
    )
    parser.add_argument(
        "--min-density",
        type=int,
        default=50,
        help="Min content pixels per row/col to count as real content (filters dust). Default: 50.",
    )

    args = parser.parse_args()

    image_paths = []

    # Folder support
    if args.folder:
        folder_path = Path(args.folder)
        if not folder_path.is_dir():
            print(f"Error: '{folder_path}' is not a valid folder.", file=sys.stderr)
            sys.exit(1)
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff"):
            image_paths.extend(folder_path.glob(ext))

    # Handle individual inputs or glob patterns
    for pattern in args.inputs:
        image_paths.extend(Path(p).parent.glob(Path(p).name))

    if not image_paths:
        print("No images found to process!", file=sys.stderr)
        sys.exit(1)

    for input_path in image_paths:
        if not input_path.exists():
            print(f"Warning: '{input_path}' not found - skipping.", file=sys.stderr)
            continue
        # Use a 'cropped' folder inside the image's parent folder
        output_folder = input_path.parent / "cropped"
        process_file(input_path, output_folder, args.threshold, args.padding, args.min_density)


if __name__ == "__main__":
    main()