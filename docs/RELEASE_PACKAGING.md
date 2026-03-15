# ChannelForge Studio — Release & Packaging Guide

## Tóm tắt

Tài liệu này mô tả quy trình đóng gói và phát hành ChannelForge Studio desktop app.

---

## 1. Kiến trúc đóng gói

```
ChannelForge Studio
├── Frontend (Vite + React + TypeScript)
│   └── Build → dist/
├── Backend (Python + FastAPI + SQLite)
│   └── Build → engine sidecar binary
└── Desktop Shell (Tauri v2)
    └── Bundle → .msi (Win) / .dmg (Mac) / .AppImage (Linux)
```

### Chiến lược sidecar (Option A — Khuyến nghị)

- Python engine được đóng gói thành executable riêng bằng PyInstaller
- Tauri bundle sidecar qua `externalBin` config
- User cuối **không cần** cài Python

---

## 2. Build Flow

### 2.1 Development Mode

```bash
# Terminal 1: Backend
cd engine && .venv/Scripts/python -m uvicorn app.main:app --reload

# Terminal 2: Frontend + Tauri
npm run tauri dev
```

### 2.2 Production Build

```bash
# Step 1: Build engine sidecar
python scripts/build_engine_sidecar.py --target windows

# Step 2: Build frontend + Tauri package
npm run tauri build
```

### 2.3 Pre-release check

```bash
python scripts/release/check_release.py
```

---

## 3. Migration Strategy

- Mọi thay đổi DB phải tạo file SQL mới trong `engine/app/migrations/`
- Đặt tên: `VVV_description.sql` (VVV = version number)
- Migration tự chạy khi app khởi động thông qua `_run_migrations()` trong `db.py`
- Không bao giờ xóa hoặc sửa migration cũ

### Current migrations:
| Version | File | Nội dung |
|---------|------|-------|
| 001 | 001_workspaces.sql | Core workspace tables |
| 002 | 002_proxy_profiles.sql | Proxy profile management |
| 003 | 003_audit_logs.sql | Audit logging |
| 004 | 004_v5_entities.sql | V5 entity tables |
| 005 | 005_v56_workspace_supervisor.sql | V5.6 runtime + policy tables |
| 006 | 006_v57_media_intel.sql | V5.7 media intelligence tables |
| 007 | 007_v58_packaging.sql | V5.8 config + crash logs |

---

## 4. FFmpeg Strategy

- **Dev mode**: System FFmpeg (phải có trong PATH)
- **Production Windows**: Bundle FFmpeg hoặc first-run wizard hướng dẫn cài
- **Đường dẫn**: Lưu resolved path trong `app_config` table

---

## 5. First-Run Wizard

Wizard tự động chạy khi app mở lần đầu, kiểm tra:
1. ✅ Engine (Python backend) responsive
2. ✅ Database writable
3. ✅ FFmpeg reachable
4. ✅ Browser automation (Playwright)
5. ✅ Media cache directory
6. ✅ API keys configuration
7. ✅ Workspace base directory

---

## 6. Support Bundle

Export từ UI hoặc API:
```
POST /api/v5/system/diagnostics/support-bundle
```

Bundle bao gồm (đã sanitize):
- ✅ App version, OS info
- ✅ Diagnostics JSON
- ✅ Migration status
- ✅ Recent crash logs
- ✅ Health events
- ✅ Masked config values

**Không bao gồm**: API keys, cookies, credentials, browser profiles

---

## 7. Smoke Test Checklist

| # | Test | Endpoint/Action |
|---|------|----------------|
| 1 | App launch | Desktop app opens |
| 2 | Backend health | `GET /api/health` → 200 |
| 3 | Dashboard loads | UI renders without error |
| 4 | Diagnostics pass | `GET /api/v5/system/diagnostics/full` |
| 5 | Create workspace | `POST /api/v2/workspaces` |
| 6 | Trend fetch | `GET /api/v2/trends/*` |
| 7 | Render sample | Pipeline test |
| 8 | Support bundle | `POST /api/v5/system/diagnostics/support-bundle` |

---

## 8. Platform Notes

### Windows
- Target: `.msi` installer
- WebView2 required (auto-installed by Tauri)
- FFmpeg: bundle hoặc wizard

### macOS
- Target: `.dmg`
- Notarization: requires Apple Developer cert (placeholder)
- Sidecar: `aarch64-apple-darwin`

### Linux
- Target: `.AppImage` hoặc `.deb`
- Permissions: sidecar cần `chmod +x`
- Sidecar: `x86_64-unknown-linux-gnu`
