"""ChannelForge Studio — Doctor / Bootstrap Validator.

Run: python scripts/doctor.py

Checks all prerequisites and reports pass/fail/fix per check.
Exit code 0 if bootable, 1 if blocked.
"""

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg: str):
    print(f"  {GREEN}✅ PASS{RESET}  {msg}")

def warn(msg: str, fix: str = ""):
    print(f"  {YELLOW}⚠️  WARN{RESET}  {msg}")
    if fix:
        print(f"          {YELLOW}Fix: {fix}{RESET}")

def fail(msg: str, fix: str = ""):
    print(f"  {RED}❌ FAIL{RESET}  {msg}")
    if fix:
        print(f"          {RED}Fix: {fix}{RESET}")


def check_python() -> bool:
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 11):
        fail(f"Python {v.major}.{v.minor} — cần >= 3.11", "Cài Python 3.11+ từ python.org")
        return False
    ok(f"Python {v.major}.{v.minor}.{v.micro}")
    return True


def check_node() -> bool:
    try:
        result = subprocess.run("node --version", capture_output=True, text=True, shell=True, timeout=5)
        if result.returncode == 0:
            ok(f"Node.js {result.stdout.strip()}")
            return True
    except Exception:
        pass
    warn("Node.js không tìm thấy", "Cài Node.js 18+ từ nodejs.org")
    return False


def check_ffmpeg() -> bool:
    path = shutil.which("ffmpeg")
    if path:
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            ver = result.stdout.split("\n")[0][:60] if result.stdout else ""
            ok(f"FFmpeg: {ver}")
            return True
        except Exception:
            pass
    warn("FFmpeg không tìm thấy", "Cài từ https://ffmpeg.org/download.html và thêm vào PATH")
    return False


def check_pip_packages() -> bool:
    base_req = ENGINE / "requirements" / "base.txt"
    if not base_req.exists():
        base_req = ENGINE / "requirements.txt"
    if not base_req.exists():
        fail("Không tìm thấy requirements file")
        return False

    # Critical packages (app won't boot without these)
    critical = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "pydantic": "pydantic",
        "httpx": "httpx",
        "python-dotenv": "dotenv",
        "aiohttp": "aiohttp",
    }
    # Optional but expected packages (features degrade without these)
    optional = {
        "openai": "openai",
        "moviepy": "moviepy",
        "elevenlabs": "elevenlabs",
        "sentence-transformers": "sentence_transformers",
        "faiss-cpu": "faiss",
        "Pillow": "PIL",
        "opencv-python-headless": "cv2",
    }

    missing_critical = []
    for pkg, mod_name in critical.items():
        try:
            importlib.import_module(mod_name)
        except ImportError:
            missing_critical.append(pkg)

    if missing_critical:
        fail(f"Thiếu core packages: {', '.join(missing_critical)}", f"pip install -r {base_req}")
        return False
    ok("Core pip packages đã cài")

    missing_opt = []
    for pkg, mod_name in optional.items():
        try:
            importlib.import_module(mod_name)
        except ImportError:
            missing_opt.append(pkg)

    if missing_opt:
        warn(f"Optional packages chưa cài: {', '.join(missing_opt)}",
             "pip install -r engine/requirements/all.txt")
    else:
        ok("All optional packages đã cài")

    return True


def check_database() -> bool:
    # Check writable
    data_dir = ENGINE / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    test_file = data_dir / ".write_test"
    try:
        test_file.write_text("ok")
        test_file.unlink()
        ok("Database directory writable")
        return True
    except Exception:
        fail(f"Không ghi được vào {data_dir}", f"Cấp quyền ghi cho {data_dir}")
        return False


def check_env_file() -> bool:
    env_file = ENGINE / ".env"
    if env_file.exists():
        content = env_file.read_text()
        keys_found = sum(1 for k in ["OPENAI_API_KEY", "PEXELS_API_KEY", "PIXABAY_API_KEY"]
                        if k in content and content.split(k)[1].strip().startswith("="))
        if keys_found > 0:
            ok(f"engine/.env found ({keys_found} API keys configured)")
            return True
        warn("engine/.env tồn tại nhưng chưa có API key", "Thêm API keys vào engine/.env")
        return False
    warn("engine/.env chưa tạo", "Copy engine/.env.example thành engine/.env và thêm API keys")
    return False


def check_playwright() -> bool:
    try:
        importlib.import_module("playwright")
        ok("Playwright installed")
        return True
    except ImportError:
        warn("Playwright chưa cài", "pip install playwright && python -m playwright install chromium")
        return False


def check_version_sync() -> bool:
    import json
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    pkg_ver = pkg.get("version", "?")

    tauri_conf = json.loads((ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    tauri_ver = tauri_conf.get("version", "?")

    if pkg_ver == tauri_ver:
        ok(f"Version sync: {pkg_ver}")
        return True
    fail(f"Version mismatch: package.json={pkg_ver}, tauri.conf.json={tauri_ver}")
    return False


def main():
    print(f"\n{BOLD}{'='*55}")
    print(f"  ChannelForge Studio — Doctor / Bootstrap Validator")
    print(f"{'='*55}{RESET}\n")

    results = {}

    sections = [
        ("Python Runtime", check_python),
        ("Node.js", check_node),
        ("FFmpeg", check_ffmpeg),
        ("Core Packages", check_pip_packages),
        ("Database Dir", check_database),
        ("Environment File", check_env_file),
        ("Playwright", check_playwright),
        ("Version Sync", check_version_sync),
    ]

    blockers = 0
    warnings = 0
    passed = 0

    for name, check_fn in sections:
        print(f"\n{BOLD}[{name}]{RESET}")
        result = check_fn()
        if result:
            passed += 1
        elif name in ("Python Runtime", "Core Packages", "Database Dir"):
            blockers += 1
        else:
            warnings += 1

    print(f"\n{BOLD}{'='*55}{RESET}")
    print(f"  {GREEN}Passed: {passed}{RESET}  |  {YELLOW}Warnings: {warnings}{RESET}  |  {RED}Blockers: {blockers}{RESET}")

    if blockers > 0:
        print(f"\n  {RED}{BOLD}❌ App BLOCKED — fix critical issues above{RESET}")
        sys.exit(1)
    elif warnings > 0:
        print(f"\n  {YELLOW}{BOLD}⚠️  App BOOTABLE but some features degraded{RESET}")
    else:
        print(f"\n  {GREEN}{BOLD}✅ All checks passed — ready to run!{RESET}")

    print(f"\n  Quick start:")
    print(f"    cd engine && python -m uvicorn app.main:app --reload")
    print(f"    npm run dev")
    print()


if __name__ == "__main__":
    main()
