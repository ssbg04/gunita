# AGENT.md - Project Specification & Roadmap

## 1. Project Overview
A utility application designed to detect, crop, and remove scan backgrounds (white/near-white scanner margins) and isolate subject content from photos.

- **Phase 1**: Windows Desktop Application (native Python GUI).
- **Phase 2**: Mobile Application (React Native Android).

---

## 2. Tech Stack

### Phase 1: Windows Desktop App
- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt for Python)
  - Native Windows appearance and high-DPI scaling.
  - Multi-threading support (`QThread`, `QThreadPool`) to prevent UI freezes during batch processing.
- **Image Processing Core**:
  - `Pillow (PIL)`: Image I/O, format conversion, metadata preservation.
  - `numpy`: Fast vectorized array operations for thresholding and density analysis.
  - Optional future upgrade: `opencv-python` / `onnxruntime` for AI-based boundary segmentation.
- **Packaging & Distribution**:
  - `PyInstaller` or `Nuitka` to produce standalone `.exe` binaries.

### Phase 2: Android App (Planned)
- **Framework**: React Native (TypeScript)
- **Engine**: Expo / React Native CLI
- **Image Processing Engine**:
  - Client-side: OpenCV for React Native (`react-native-fast-opencv`) or ONNX Runtime Web/Mobile.
  - Camera integration: `react-native-vision-camera`.

---

## 3. Architecture & System Design

### Decoupled Core Design
The core processing engine must remain strictly decoupled from the UI layer to enable seamless reuse and straightforward porting to other platforms.

```
bgrmbr/
├── core/                   # Pure Python processing logic (zero GUI dependencies)
│   ├── __init__.py
│   ├── cropper.py          # Thresholding, density checks, bounding box logic
│   ├── batch.py            # Batch queue management, progress callbacks
│   └── models.py           # Dataclasses (CropConfig, ProcessResult, ImageMetadata)
├── ui/                     # Desktop GUI (PySide6)
│   ├── __init__.py
│   ├── main_window.py      # Main application window & layout
│   ├── components/         # Reusable widgets (ImagePreview, DropZone, SettingsPanel)
│   ├── workers.py          # Background worker threads
│   └── styles.py           # Themes and styling
├── tests/                  # Automated unit and integration tests
├── app.py                  # Desktop application entry point
├── requirements.txt        # Dependency definitions
└── AGENT.md                # Project specification & rules
```

### Processing Pipeline
1. **Input Stage**: Accept single files, multiple files, or directory paths (via file dialog or drag-and-drop).
2. **Analysis Stage**:
   - Convert image to RGB array.
   - Compute grayscale representation.
   - Apply intensity thresholding (`threshold`, default 225) to separate content from scanner margins.
   - Perform row/column density filtering (`min_density`) to discard noise/dust artifacts.
   - Compute crop boundaries with configurable safety `padding`.
3. **Execution Stage**:
   - Crop source image.
   - Fall back safely to original image if no content exceeds density thresholds.
4. **Export Stage**:
   - Save to designated output folder (default: `cropped/` subfolder).
   - Preserve or optimize format (PNG lossless, JPEG high quality).
   - Update processing log and preview widget.

---

## 4. UI/UX Specifications (Windows App)

### Layout
- **Left Panel**:
  - Drag-and-drop zone for files/folders.
  - File list / queue with status indicators (Pending, Processing, Done, Failed).
  - Batch action buttons (Start, Pause, Clear).
- **Center / Main Area**:
  - Side-by-side or before/after comparison preview.
  - Interactive bounding box preview with zoom/pan capability.
- **Right / Bottom Panel**:
  - Parameter controls:
    - Threshold slider (0–255).
    - Padding input (pixels).
    - Minimum density slider/input.
  - Output folder selector.
  - Real-time progress bar and log console.

### Performance Requirements
- Processing must never block the main GUI thread.
- Support cancellation and graceful shutdown of running batch tasks.
- Low memory footprint when handling large batches (stream files one at a time, release memory promptly).

---

## 5. Development & Engineering Rules

### Code Quality
1. **Strict Typing**: All core logic must use Python type hints (`typing` module).
2. **Zero UI Imports in Core**: `core/` modules must never import `PySide6`, `PyQt`, or UI widgets.
3. **Config-Driven**: All processing parameters must be passed via config objects/dataclasses, never hardcoded in function bodies.
4. **Robust Error Handling**:
   - Never crash on corrupted image files. Mark file as failed, log error, and continue batch.
   - Handle permission errors gracefully when reading or saving files.

### Testing & Verification
- Unit test coverage required for `core/cropper.py` with edge cases:
  - Completely white images.
  - Completely dark images.
  - Images with border noise / dust specks.
  - Different formats: JPEG, PNG, TIFF, WebP.
- Batch processing tests verifying output directory generation and file naming collisions.

