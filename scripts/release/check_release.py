"""Pre-release checks — Verify build artifacts and configuration before release."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def check_versions():
    """Ensure package.json and tauri.conf.json versions match."""
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
    result = subprocess.run("npx tsc --noEmit", cwd=str(ROOT), capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print("✅ TypeScript: 0 errors")
        return True
    print(f"❌ TypeScript errors:\n{result.stdout}")
    return False


def check_migrations():
    """Check migration files exist."""
    migrations = sorted((ROOT / "engine" / "app" / "migrations").glob("*.sql"))
    print(f"✅ Migrations: {len(migrations)} files found")
    for m in migrations:
        print(f"   {m.name}")
    return len(migrations) > 0


def check_sidecar():
    """Check if sidecar binaries exist."""
    bin_dir = ROOT / "src-tauri" / "binaries"
    if not bin_dir.exists():
        print("⚠️  Sidecar binaries not found (run scripts/build_engine_sidecar.py first)")
        return False
    bins = list(bin_dir.iterdir())
    print(f"✅ Sidecar binaries: {len(bins)} found")
    return True


def main():
    print("=" * 50)
    print("ChannelForge Studio — Pre-Release Checks")
    print("=" * 50)
    
    results = {
        "versions": check_versions(),
        "typescript": check_typescript(),
        "migrations": check_migrations(),
        "sidecar": check_sidecar(),
    }
    
    print("\n" + "=" * 50)
    passed = sum(results.values())
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    
    if all(results.values()):
        print("✅ All checks passed — ready for release!")
    else:
        print("⚠️  Some checks failed — review before release")
        sys.exit(1)


if __name__ == "__main__":
    main()
