# Gunita

A fast, lightweight, and offline desktop application to preserve memories by auto-cropping white scanner margins from scanned photos, vintage prints, and documents.

> **Gunita** *(Tagalog)*: Memory, reminiscence, nostalgic recollection.

![Windows Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-green)
![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Key Features

- **Automatic Scanner Margin Detection**: Vectorized brightness thresholding and density analysis filter out scanner beds and dust specks.
- **Real-Time Interactive Preview**: Side-by-side comparison with a live bounding box overlay that updates dynamically as you tune parameters.
- **Fast & Responsive**: Utilizes cached proxy previews and direct memory buffer conversions for smooth 60 FPS slider responsiveness.
- **Non-Blocking Batch Processing**: Multi-threaded execution (`QThread`) processes hundreds of images without freezing the UI.
- **Drag-and-Drop Workflow**: Drop individual image files or entire folders directly into the application queue.
- **Parameter Controls**:
  - **Threshold**: Adjust sensitivity to white and off-white scanner backgrounds.
  - **Padding**: Add safety margins around cropped photo edges.
  - **Min Density**: Filter out dust specks, stray scanner lines, and noise artifacts.
  - **Reset to Defaults**: Quickly restore factory settings with one click.
- **Format Flexibility**: Auto-detects input formats or converts exports to high-quality JPEG or lossless PNG.
- **Headless CLI Support**: Run batch jobs from PowerShell, Command Prompt, or automated scripts without launching the GUI.
- **Privacy-First**: 100% local computation. No internet connection required, zero cloud uploads.

---

## Quick Start (Running from Source)

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone Repository & Install Dependencies
```bash
git clone https://github.com/your-username/bgrmbr.git
cd bgrmbr
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python app.py
```

---

## Headless CLI Usage

You can also run batch processing directly from the command line:

```bash
# Process a single scan
python app.py "photos/scan1.jpg" -o "output_folder"

# Process an entire folder of scans with custom tuning
python app.py --folder "C:/Users/User/ScannedPhotos" --threshold 230 --padding 20 --min-density 40

# Force output format to PNG
python app.py --folder "photos" --format PNG
```

### CLI Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--gui` | Force launch desktop GUI | `False` |
| `--folder <DIR>` | Process all images in directory | None |
| `-o, --output <DIR>` | Destination folder for cropped images | `cropped/` |
| `--threshold <INT>` | Brightness threshold (0–255) | `225` |
| `--padding <INT>` | Boundary margin in pixels | `15` |
| `--min-density <INT>` | Density filter for dust suppression | `50` |
| `--format [PNG\|JPEG]` | Force output file format | Match Input |

---

## Building Standalone Portable EXE

The project includes an optimized build script that strips over 150MB of unused Qt bloat modules (`QtWebEngine`, `QtQuick`, `Qt3D`, `QtQml`, etc.):

```bash
pip install pyinstaller
python build_exe.py
```

The resulting standalone executable is generated at:
```
dist/Gunita.exe
```

### GitHub Actions (Automated CI/CD)
Pushing to `main` or pushing a version tag (e.g. `v1.0.0`) automatically builds a compressed, lightweight portable package (`Gunita-Windows-x64-portable.zip`) via `.github/workflows/build.yml`.

---

## Project Structure

```
bgrmbr/
├── .github/workflows/       # GitHub Actions automated build CI/CD
│   └── build.yml
├── core/                    # Decoupled processing engine (Zero GUI imports)
│   ├── models.py            # CropConfig, BoundingBox, ProcessResult
│   ├── cropper.py           # Thresholding, density checks, crop logic
│   └── batch.py             # Batch coordinator with progress callbacks
├── ui/                      # PySide6 desktop interface
│   ├── components/
│   │   ├── controls.py      # Sliders, buttons, folder selection
│   │   ├── file_table.py    # Drag-and-drop table with status tracking
│   │   └── preview.py       # Side-by-side comparison with box overlay
│   ├── main_window.py       # Assembled main window & event wiring
│   ├── styles.py            # Modern dark theme stylesheet
│   └── workers.py           # Background QThread worker
├── tests/                   # Automated unit tests
│   └── test_cropper.py
├── app.py                   # Main entry point (GUI & CLI launcher)
├── build_exe.py             # Portable standalone executable builder
├── requirements.txt         # Project dependencies
└── README.md                # Documentation
```

---

## Running Automated Tests

Run the test suite using Python's standard `unittest` framework:

```bash
python -m unittest discover tests
```

---

## Roadmap

- [x] Windows Desktop GUI with PySide6
- [x] Real-time live bounding box preview with debounce optimization
- [x] Single-file portable `.exe` build with GitHub Actions CI
- [ ] AI Subject / Person segmentation mode (transparent PNG background removal)
- [ ] Mobile companion app (React Native Android)

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

