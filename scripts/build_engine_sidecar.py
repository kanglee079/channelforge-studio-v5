"""Build Engine Sidecar — Package Python backend as standalone binary.

Usage:
    python scripts/build_engine_sidecar.py [--target windows|macos|linux]

Sử dụng PyInstaller hoặc Nuitka để tạo executable.
Kết quả output vào src-tauri/binaries/ để Tauri bundle.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "engine"
TAURI_BIN_DIR = ROOT / "src-tauri" / "binaries"

# Target triple cho Tauri externalBin
PLATFORM_TRIPLES = {
    "windows": "x86_64-pc-windows-msvc",
    "macos": "aarch64-apple-darwin",
    "linux": "x86_64-unknown-linux-gnu",
}


def build_with_pyinstaller(target: str):
    """Build engine sidecar using PyInstaller."""
    print(f"🔨 Building engine sidecar for {target}...")

    dist_dir = ENGINE_DIR / "dist"
    build_dir = ENGINE_DIR / "build"

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--name", "channelforge-engine",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--clean",
        "--noconfirm",
        # Include data files
        "--add-data", f"{ENGINE_DIR / 'app' / 'migrations'}{os.pathsep}app/migrations",
        # Main entry point
        str(ENGINE_DIR / "run_engine.py"),
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ENGINE_DIR))

    if result.returncode != 0:
        print("❌ PyInstaller build failed!")
        sys.exit(1)

    # Copy to Tauri binaries dir
    triple = PLATFORM_TRIPLES.get(target, PLATFORM_TRIPLES["windows"])
    TAURI_BIN_DIR.mkdir(parents=True, exist_ok=True)

    sidecar_name = f"channelforge-engine-{triple}"
    if target == "windows":
        sidecar_name += ".exe"

    # Copy the dist folder contents
    src = dist_dir / "channelforge-engine"
    dst = TAURI_BIN_DIR / sidecar_name

    if src.is_dir():
        # For onedir mode, zip or copy the directory
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        shutil.copytree(src, dst)
        print(f"✅ Sidecar built: {dst}")
    elif src.is_file():
        shutil.copy2(src, dst)
        print(f"✅ Sidecar binary: {dst}")

    return str(dst)


def create_run_engine():
    """Create the run_engine.py entry point if not exists."""
    entry = ENGINE_DIR / "run_engine.py"
    if not entry.exists():
        entry.write_text(
            '"""Engine entry point for sidecar binary."""\n'
            'import uvicorn\n'
            'from app.main import app\n\n'
            'if __name__ == "__main__":\n'
            '    uvicorn.run(app, host="127.0.0.1", port=8000)\n',
            encoding="utf-8",
        )
        print(f"Created {entry}")


def main():
    parser = argparse.ArgumentParser(description="Build ChannelForge engine sidecar binary")
    parser.add_argument("--target", choices=["windows", "macos", "linux"],
                        default="windows" if platform.system() == "Windows" else
                                "macos" if platform.system() == "Darwin" else "linux")
    args = parser.parse_args()

    create_run_engine()
    build_with_pyinstaller(args.target)


if __name__ == "__main__":
    main()
