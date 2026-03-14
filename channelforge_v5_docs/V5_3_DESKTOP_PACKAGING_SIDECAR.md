# V5.3 — Desktop Packaging + Sidecar Orchestration

## 1. Mục tiêu

Biến project từ app lai/web-centric thành **desktop app chuẩn** có thể cài đặt, update, chạy nền sidecar engine, log chẩn đoán, và vận hành ổn định trên máy người dùng.

## 2. Kết quả mong muốn

- app đóng gói thành installer desktop;
- backend Python không phải chạy thủ công;
- desktop shell quản sidecar lifecycle;
- có diagnostics, logs, restart sidecar, health view;
- có môi trường setup rõ ràng cho dev và production.

## 3. Stack đề xuất

### Shell
- Tauri 2
- React + TypeScript frontend
- Rust commands cho native operations tối thiểu

### Sidecar
- Python engine packaged as executable hoặc embedded runtime
- supervisor do Tauri side quản lý

### IPC
- HTTP local loopback hoặc IPC command bridge
- event streaming qua WebSocket local hoặc Tauri events

## 4. Packaging modes

### Mode A — Dev
- frontend dev server
- python engine chạy venv
- Tauri dev connects to both

### Mode B — Local release
- frontend bundled static
- python engine packaged as sidecar executable
- SQLite local DB

### Mode C — Pro install
- signed app
- updater enabled
- diagnostics bundle
- sidecar logs rotation

## 5. Internal architecture

```text
Tauri app
  ├─ app lifecycle manager
  ├─ sidecar supervisor
  ├─ config manager
  ├─ local paths manager
  ├─ diagnostics manager
  ├─ updater manager
  └─ event bridge
```

## 6. Sidecar supervisor responsibilities

- find packaged sidecar path
- spawn sidecar
- ensure ports/IPC ready
- restart sidecar on crash under policy
- expose health to UI
- kill sidecar on app exit if needed
- collect logs/stdout/stderr
- write diagnostics bundle

## 7. Project structure target

```text
root/
  src/
  src-tauri/
    src/
      commands/
      sidecar/
      diagnostics/
      state/
    capabilities/
    icons/
    tauri.conf.json
  engine/
  scripts/
```

## 8. Packaging strategy options

### Option 1 — Bundle Python executable
Pros:
- simple for end user
- predictable runtime
Cons:
- larger build size
- cross-platform packaging more complex

### Option 2 — Embedded Python runtime
Pros:
- flexible
Cons:
- more packaging complexity

### Recommended for current project
Start with **sidecar executable** generated per platform.

## 9. Desktop-specific features

### 9.1 App settings
- root data directory
- cache limits
- logs retention
- provider paths
- ffmpeg path override
- local models path

### 9.2 Diagnostics center
- sidecar status
- DB status
- cache size
- workspace count
- last errors
- export diagnostics zip

### 9.3 Operations console
- view worker queue
- restart sidecar
- open engine logs
- run system checks
- open data directory

## 10. Native commands needed

### Rust commands
- get_app_paths
- open_path_in_explorer
- spawn_sidecar
- stop_sidecar
- tail_log
- read_system_info
- export_diagnostics
- check_ffmpeg

## 11. IPC contract

### Frontend -> Tauri
- request paths
- request sidecar state
- restart sidecar
- export diagnostics

### Frontend -> Python engine
- app domain APIs via HTTP/IPC
- job queue commands
- workspace commands
- render/upload/research commands

### Python -> Frontend
- progress events
- job state changes
- warnings
- cost alerts
- low confidence review alerts

## 12. Installer and updater

### Installer requirements
- create app data dirs
- verify sidecar binary exists
- verify ffmpeg availability or bundled path
- first-run wizard

### Updater requirements
- version channel: stable/beta/dev
- DB migration checks before app fully opens
- rollback-safe if migration fails

## 13. First-run setup wizard

Wizard pages:
1. choose data directory
2. provider keys
3. check ffmpeg
4. check optional Playwright/browser deps
5. import existing V4 data if available
6. create first channel

## 14. Migration from V4

### Existing assets to migrate
- SQLite DB
- generated outputs
- provider settings
- channel list
- queue jobs
- trend cache

### Migration strategy
- create `schema_version`
- run idempotent migrations
- generate migration report
- keep backup before migration

## 15. Logging strategy

Logs split thành:
- desktop shell logs
- sidecar supervisor logs
- engine domain logs
- workspace logs
- upload logs

Rotation:
- daily or size-based
- keep last N files

## 16. Acceptance criteria

### Must-have
- app bundles and opens as desktop app
- sidecar auto starts
- UI can see sidecar health
- diagnostics export works
- first-run wizard exists

### Nice-to-have
- auto updater
- signed builds
- crash recovery screen

## 17. Tests

### E2E
- open app -> sidecar healthy -> create channel -> queue job -> restart app -> state restored

### Packaging tests
- Windows build
- macOS build later if needed

## 18. Implementation order

1. Tauri app lifecycle
2. sidecar spawn/health/restart
3. local paths manager
4. diagnostics center
5. first-run wizard
6. migration support
7. release packaging

## 19. Risks

- platform-specific path issues
- Python packaging bloat
- FFmpeg path problems
- firewall/AV false positives on first run

## 20. Mitigations

- explicit diagnostics screen
- command-line fallback for engine debug
- bundled ffmpeg or guided path selection
- logs export in one click
