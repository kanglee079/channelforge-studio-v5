# V5.8 — Packaging & Installer Hardening (AI-Ready)

## 1. Mục tiêu

Biến desktop app từ trạng thái:
- Tauri shell + Python sidecar khởi chạy từ `.venv` hoặc system Python

thành:
- bản desktop package cài đặt được ổn định hơn
- có runtime self-check
- có installer flow
- có diagnostics rõ ràng
- có migration/upgrade path

---

## 2. Hiện trạng repo

### 2.1 Đã có
- `src-tauri/src/lib.rs` khởi động Python sidecar bằng `uvicorn`
- `src-tauri/tauri.conf.json` đã bật bundle
- UI có thể nói chuyện với backend local

### 2.2 Chưa đủ
- chưa bundle backend sidecar chuẩn theo external binary flow
- còn phụ thuộc `.venv` hoặc Python system
- chưa có installer prerequisites strategy
- chưa có first-run wizard
- chưa có upgrade/migration checklist
- chưa có diagnostics page đủ sâu
- chưa có release packaging policy cho Windows/macOS/Linux

---

## 3. Kết quả cuối phase

Sau V5.8, app phải có:

1. **Packaged desktop build** đáng tin cậy hơn
2. **Engine bootstrap strategy** rõ ràng
3. **First-run diagnostics wizard**
4. **Installer/prerequisite handling**
5. **Versioned migrations**
6. **Crash-safe logs & support bundle**
7. **Release checklist**

---

## 4. Định hướng triển khai

## 4.1 Packaging strategy
Chọn một trong hai hướng, nhưng phải cố định trong code/docs:

### Option A — Bundled Python engine binary (khuyến nghị)
- Python engine được build thành executable/onedir artifact riêng
- Tauri bundle sidecar qua `externalBin`
- User cuối không cần tự có Python

### Option B — Managed embedded runtime
- ship Python runtime + venv-like environment
- app bootstrap script dùng runtime nội bộ
- phức tạp hơn khi update

**Khuyến nghị cho repo này:**  
Bám **Option A** để tránh phụ thuộc system Python.

---

## 5. Những gì phải thay đổi

## 5.1 `src-tauri/tauri.conf.json`
Thêm cấu hình sidecar/binary packaging:
- `bundle.externalBin`
- per-platform paths
- signing/notarization placeholders nếu cần
- updater placeholders (chưa cần full implementation)

## 5.2 `src-tauri/src/lib.rs`
Thay `Command::new("python" or venv_python)` bằng logic:
- detect packaged sidecar binary trước
- fallback dev mode chỉ khi chạy local dev
- startup timeout + health wait
- structured errors nếu engine không lên
- support bundle generation command

## 5.3 Backend
Thêm:
- `/api/diagnostics/full`
- `/api/diagnostics/dependencies`
- `/api/diagnostics/support-bundle`
- `/api/system/migrations/status`
- `/api/system/migrations/run`

---

## 6. First-run wizard

## 6.1 Wizard steps
1. Welcome
2. Engine check
3. FFmpeg check
4. Optional AI deps check
5. Browser automation deps check
6. Workspace base directory selection
7. API keys setup
8. Sample smoke test
9. Finish

## 6.2 Điều kiện pass
- backend responsive
- DB writable
- media cache dir writable
- workspace base dir writable
- FFmpeg reachable
- Playwright/browser dependency reachable (nếu bật workspace browser)
- one sample health test thành công

---

## 7. Diagnostics & Support Bundle

## 7.1 Support bundle contents
- app version
- OS / arch
- engine version
- migration status
- diagnostics summary JSON
- recent logs
- sidecar health snapshot
- workspace runtime summary
- masked config values
- installed optional deps matrix

Không include:
- raw API keys
- raw cookies
- raw credentials
- full browser profile data

## 7.2 UI page
Tạo `src/pages/DiagnosticsPage.tsx` nâng cấp hoặc mở rộng trang đang có:
- app health
- engine health
- dependency matrix
- FFmpeg
- browser automation
- vector index status
- last crash info
- “Export Support Bundle”

---

## 8. Installer hardening

## 8.1 Windows
- tạo installer target mặc định của Tauri
- cộng thêm optional script/check cho:
  - WebView2 presence
  - FFmpeg presence or bundled ffmpeg
  - sidecar binary presence
  - writable app data dir

## 8.2 macOS
- path handling
- app bundle paths
- sidecar location
- sandbox/notarization placeholders trong docs

## 8.3 Linux
- AppImage/deb path sanity
- executable permissions
- bundled binary paths

---

## 9. FFmpeg strategy

App hiện phụ thuộc render pipeline.

Bắt buộc chọn một trong ba hướng:
1. system ffmpeg required
2. bundled ffmpeg per platform
3. user-configurable ffmpeg path

**Khuyến nghị:**
- dev mode: system ffmpeg
- production Windows build: bundle ffmpeg or first-run setup path
- store resolved ffmpeg path in config

---

## 10. Versioning & migrations

## 10.1 App version
- app semantic version trong package.json và tauri config phải đồng bộ

## 10.2 DB migration
Tạo migration ledger:
- `schema_version`
- applied_at
- migration_name

Nếu migration fail:
- app phải hiển thị lỗi rõ
- không loop restart sidecar vô tận

---

## 11. File structure changes

### Create
- `engine/app/routers/diagnostics.py`
- `engine/app/services/diagnostics_service.py`
- `engine/app/services/support_bundle.py`
- `engine/app/services/dependency_probe.py`
- `engine/app/services/migration_runner.py`
- `src/pages/DiagnosticsPage.tsx` (nâng cấp hoặc mới)
- `src/components/diagnostics/*`
- `scripts/build_engine_sidecar.*`
- `scripts/release/check_release.py`
- `docs/RELEASE_PACKAGING.md`

### Modify
- `src-tauri/src/lib.rs`
- `src-tauri/tauri.conf.json`
- `package.json`
- `engine/app/main.py`

---

## 12. Build matrix

## 12.1 Development
- `npm run tauri dev`
- backend chạy từ source/dev Python
- dev diagnostics hiển thị “source mode”

## 12.2 Release
- build engine sidecar
- copy/bundle sidecar binary
- build frontend
- build Tauri package
- run smoke tests on packaged artifact

---

## 13. Release smoke tests

1. app launch được
2. sidecar lên trong timeout
3. dashboard load được
4. diagnostics pass cơ bản
5. create workspace được
6. trend fetch sample được
7. render sample job được
8. support bundle export được
9. sidecar restart command hoạt động

---

## 14. Acceptance criteria

- Không cần system Python để chạy release build (mục tiêu khuyến nghị).
- App phát hiện thiếu dependency và chỉ rõ cách sửa.
- First-run wizard hoạt động.
- Support bundle export được.
- Diagnostics page đầy đủ.
- Sidecar restart loop được chặn nếu engine fail repeated.
- Migration failure không làm app treo im lặng.

---

## 15. Anti-regression constraints

- Không phá `npm run tauri dev`.
- Không hardcode absolute paths.
- Không assume `.venv` tồn tại trong release.
- Không log secrets.
- Không bundle raw credentials.

---

## 16. Manual test checklist

### Fresh machine test
- cài app
- mở lần đầu
- chạy wizard
- cấu hình folder
- chạy smoke test
- mở diagnostics

### Upgrade test
- có DB cũ
- app mới mở lên
- migration chạy
- data cũ còn
- workspace cũ còn

### Failure test
- xóa ffmpeg
- xóa sidecar
- corrupt env
- route sidecar port occupied

---

## 17. Handoff note

AI coder phải xuất:
- release flow docs
- screenshot first-run wizard
- diagnostics sample JSON
- smoke test checklist passed
