"""
crop_white_background.py
Crops white (or near-white) backgrounds from scanned photos.

Usage:
    python crop_white_background.py input.jpg
    python crop_white_background.py input.jpg -o output.jpg
    python crop_white_background.py input.jpg --threshold 225 --padding 15
    python crop_white_background.py --folder photos/
    python crop_white_background.py *.jpg       (batch mode)

Requirements:
    pip install Pillow numpy
"""

import argparse
import sys
from pathlib import Path
import glob
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

    top    = max(real_rows[0]  - padding, 0)
    bottom = min(real_rows[-1] + padding + 1, arr.shape[0])
    left   = max(real_cols[0]  - padding, 0)
    right  = min(real_cols[-1] + padding + 1, arr.shape[1])

    return image.crop((left, top, right, bottom))


def process_file(
    input_path: Path,
    output_path,
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

    if output_path is None:
        stem = input_path.stem
        suffix = input_path.suffix or ".png"
        output_path = input_path.parent / f"{stem}_cropped{suffix}"

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
    print(f"  Saved to      : {output_path}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Crop white scanner backgrounds from photos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crop_white_background.py scan.jpg
  python crop_white_background.py scan.jpg -o result.jpg
  python crop_white_background.py scan.jpg --threshold 220 --padding 20
  python crop_white_background.py --folder photos/
  python crop_white_background.py *.jpg

Tuning tips:
  --threshold   Lower (e.g. 200) keeps less; raise (e.g. 240) for very light photos.
  --min-density Lower (e.g. 10) to keep faint/thin content; raise to ignore more noise.
  --padding     Increase if the photo edges feel too tight.
        """,
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
        "-o", "--output",
        metavar="FILE",
        help="Output file path (only valid for a single input image).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=225,
        help="Brightness threshold (0-255). Pixels below this are treated as content. Default: 225.",
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
        dest="min_density",
        help="Min content pixels per row/col to count as real content (filters dust). Default: 50.",
    )

    args = parser.parse_args()

    if args.output and (len(args.inputs) > 1 or args.folder):
        print("Error: --output can only be used with a single input file.", file=sys.stderr)
        sys.exit(1)

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

    output_path = Path(args.output) if args.output else None

    for input_path in image_paths:
        if not input_path.exists():
            print(f"Warning: '{input_path}' not found - skipping.", file=sys.stderr)
            continue
        process_file(input_path, output_path, args.threshold, args.padding, args.min_density)


if __name__ == "__main__":
    main()