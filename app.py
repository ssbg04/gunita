"""
Main entry point for Scanner Background Remover.
Launches the PySide6 Windows desktop GUI by default,
or runs headless batch mode if command-line arguments are provided.
"""

import sys
import argparse
from pathlib import Path

from core import CropConfig, process_single_image, run_batch


def run_gui():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from ui import MainWindow

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Scanner Background Remover")
    app.setOrganizationName("BgRmBr")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def run_cli(args):
    config = CropConfig(
        threshold=args.threshold,
        padding=args.padding,
        min_density=args.min_density,
        output_format=args.format,
    )

    image_paths = []
    if args.folder:
        folder = Path(args.folder)
        if not folder.is_dir():
            print(f"Error: '{folder}' is not a valid folder.", file=sys.stderr)
            sys.exit(1)
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp", "*.tif", "*.tiff"):
            image_paths.extend(folder.glob(ext))
            image_paths.extend(folder.glob(ext.upper()))

    for pattern in args.inputs:
        matched = list(Path(pattern).parent.glob(Path(pattern).name))
        if not matched and Path(pattern).exists():
            matched = [Path(pattern)]
        image_paths.extend(matched)

    if not image_paths:
        print("No image files found to process.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output) if args.output else Path("cropped")
    print(f"Processing {len(image_paths)} image(s) -> '{output_dir}'")

    def on_progress(idx, total, res):
        status = "OK" if res.success else f"FAILED: {res.error_message}"
        if res.is_fallback:
            status = "FALLBACK (No edge detected)"
        print(f"[{idx}/{total}] {res.input_path.name} -> {status}")

    results = run_batch(image_paths, output_dir, config, on_progress=on_progress)
    success_count = sum(1 for r in results if r.success)
    print(f"\nDone: {success_count}/{len(results)} images processed successfully.")


def main():
    # If no arguments or explicitly requesting GUI, run GUI
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "--gui"):
        run_gui()
        return

    parser = argparse.ArgumentParser(
        description="Crop white scanner backgrounds from photos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--gui", action="store_true", help="Launch the desktop GUI.")
    parser.add_argument("inputs", nargs="*", metavar="IMAGE", help="Input image file(s) or glob patterns.")
    parser.add_argument("--folder", metavar="FOLDER", help="Process all images in the specified folder.")
    parser.add_argument("-o", "--output", metavar="DIR", help="Output directory (default: 'cropped').")
    parser.add_argument("--threshold", type=int, default=225, help="Brightness threshold (0-255). Default: 225.")
    parser.add_argument("--padding", type=int, default=15, help="Extra pixels around content boundary. Default: 15.")
    parser.add_argument("--min-density", type=int, default=50, help="Min pixels per row/col to count as content. Default: 50.")
    parser.add_argument("--format", choices=["PNG", "JPEG"], default=None, help="Force export format (default: match input).")

    args = parser.parse_args()

    if args.gui:
        run_gui()
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
