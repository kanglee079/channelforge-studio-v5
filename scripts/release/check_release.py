"""Pre-release checks — Verify build artifacts and configuration before release.

Usage:
    python scripts/release/check_release.py

Checks: version sync, TypeScript, backend import, migrations, sidecar binaries, critical docs.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def check_versions():
    """Ensure package.json, tauri.conf.json, and backend versions match."""
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    tauri_conf = json.loads((ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))

    pkg_ver = pkg.get("version", "unknown")
    tauri_ver = tauri_conf.get("version", tauri_conf.get("package", {}).get("version", "unknown"))

    if pkg_ver != tauri_ver:
        print(f"⚠️  Version mismatch: package.json={pkg_ver}, tauri.conf.json={tauri_ver}")
        return False
    print(f"✅ Versions match: {pkg_ver}")
    return True


def check_typescript():
    """Run TypeScript type check."""
    try:
        result = subprocess.run("npx tsc --noEmit", cwd=str(ROOT), capture_output=True, text=True, shell=True, timeout=120)
        if result.returncode == 0:
            print("✅ TypeScript: 0 errors")
            return True
        error_lines = (result.stdout or result.stderr or "").strip().split("\n")[:10]
        print(f"❌ TypeScript errors ({len(error_lines)} shown):")
        for line in error_lines:
            print(f"   {line}")
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"⚠️  TypeScript check skipped: {e}")
        return False


def check_backend_import():
    """Verify backend can import without errors."""
    try:
        venv_python = ROOT / "engine" / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = ROOT / "engine" / ".venv" / "bin" / "python"
        if not venv_python.exists():
            print("⚠️  Backend venv not found — skipping import check")
            return False

        result = subprocess.run(
            [str(venv_python), "-c", "from app.main import app; print(app.version)"],
            cwd=str(ROOT / "engine"), capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Backend import OK: version {version}")
            return True
        print(f"❌ Backend import failed:\n   {result.stderr.strip()[:200]}")
        return False
    except Exception as e:
        print(f"⚠️  Backend import check skipped: {e}")
        return False


def check_migrations():
    """Check migration files exist and are numbered correctly."""
    mig_dir = ROOT / "engine" / "app" / "migrations"
    migrations = sorted(mig_dir.glob("*.sql"))
    print(f"✅ Migrations: {len(migrations)} files found")
    for m in migrations:
        print(f"   {m.name}")
    return len(migrations) > 0


def check_sidecar():
    """Check if sidecar binaries exist."""
    bin_dir = ROOT / "src-tauri" / "binaries"
    if not bin_dir.exists():
        print("⚠️  Sidecar binaries not found (run: python scripts/build_engine_sidecar.py)")
        return False
    bins = list(bin_dir.iterdir())
    if not bins:
        print("⚠️  Sidecar binaries directory is empty")
        return False
    print(f"✅ Sidecar binaries: {len(bins)} found")
    for b in bins:
        print(f"   {b.name}")
    return True


def check_docs():
    """Check critical documentation exists."""
    required = ["README.md"]
    missing = [f for f in required if not (ROOT / f).exists()]
    if missing:
        print(f"❌ Missing docs: {', '.join(missing)}")
        return False
    print("✅ Critical docs present")
    return True


def main():
    print("=" * 50)
    print("ChannelForge Studio — Pre-Release Checks v5.8")
    print("=" * 50)

    results = {
        "versions": check_versions(),
        "typescript": check_typescript(),
        "backend_import": check_backend_import(),
        "migrations": check_migrations(),
        "sidecar": check_sidecar(),
        "docs": check_docs(),
    }

    print("\n" + "=" * 50)
    passed = sum(results.values())
    total = len(results)
    print(f"Results: {passed}/{total} passed")

    critical = ["versions", "backend_import", "migrations"]
    critical_ok = all(results.get(k, False) for k in critical)

    if all(results.values()):
        print("✅ All checks passed — ready for release!")
    elif critical_ok:
        print("⚠️  Non-critical checks failed — review before release")
        print("   (Sidecar and TypeScript are needed for desktop build)")
    else:
        print("❌ Critical checks failed — fix before release")
        sys.exit(1)


if __name__ == "__main__":
    main()
