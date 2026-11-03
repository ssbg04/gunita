"""
Local build script to package Scanner Background Remover into a lightweight,
standalone portable Windows .exe using PyInstaller.
"""

import subprocess
import sys
from pathlib import Path


EXCLUDE_MODULES = [
    # Heavy Qt modules not used by the app
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQml",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.QtBluetooth",
    "PySide6.QtSensors",
    "PySide6.QtSql",
    "PySide6.QtPositioning",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtSpatialAudio",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtTest",
    "PySide6.QtNfc",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtStateMachine",
    "PySide6.QtVirtualKeyboard",
    # Unused standard/third-party modules
    "tkinter",
    "matplotlib",
    "scipy",
]


def build():
    workspace = Path(__file__).resolve().parent
    entry_point = workspace / "app.py"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--clean",
        "--name",
        "Gunita",
    ]

    for mod in EXCLUDE_MODULES:
        cmd.extend(["--exclude-module", mod])

    cmd.append(str(entry_point))

    print("Building lightweight portable Gunita executable...")
    print(f"Executing: {' '.join(cmd)}\n")
    ret = subprocess.run(cmd, cwd=str(workspace))

    if ret.returncode == 0:
        exe_path = workspace / "dist" / "Gunita.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nBuild Succeeded!")
            print(f"Portable Executable: {exe_path}")
            print(f"Size: {size_mb:.2f} MB")
    else:
        print("\nBuild Failed. Check errors above.")
        sys.exit(ret.returncode)


if __name__ == "__main__":
    build()

