# GLOBAL RULES AND GUARDRAILS FOR ANTIGRAVITY

Dán nguyên file này vào Antigravity trước mọi phase.

---

Bạn đang làm việc trên repo `channelforge-studio-v5`, một desktop-first YouTube channel operating system dùng:

- Frontend: React + TypeScript + Vite
- Desktop shell: Tauri 2
- Backend engine: Python + FastAPI + SQLite
- Media pipeline: FFmpeg, local cache, AI providers, stock media providers

## Cách làm việc bắt buộc

1. **Planning mode only** cho các phase lớn.
2. Luôn tạo artifacts trước khi code:
   - implementation plan
   - file impact map
   - migration plan (nếu có)
   - validation plan
3. Chỉ sửa các file nằm trong phạm vi phase hiện tại.
4. Không refactor lan rộng nếu không cần để hoàn thành phase.
5. Mọi thay đổi phải có:
   - typed interfaces/schemas
   - structured logging
   - graceful error handling
   - backward-compatible defaults khi có thể
6. Không phá API cũ nếu chưa có migration path.
7. Không hardcode secrets, machine-specific paths, credentials.
8. Nếu thêm dependencies mới, phải cập nhật:
   - `engine/requirements*.txt`
   - diagnostics/setup wizard
   - docs / release notes / README liên quan
9. Nếu thêm DB tables/cột/index mới, phải dùng migration có version rõ ràng.
10. Mọi phase phải kết thúc bằng một **validation report**.

## Guardrails an toàn

- Không build anti-detect browser.
- Không build fingerprint spoofing.
- Không build captcha bypass.
- Không build account farming, evasion, stealth scraping trái phép.
- Không build logic dùng nhiều tài khoản để lách quota/dịch vụ.
- Được phép build:
  - workspace isolation hợp lệ
  - persistent profile per workspace
  - network route policy per workspace
  - proxy/VPN binding hợp lệ do người dùng tự cấu hình
  - diagnostics / healthcheck / audit trail

## Mục tiêu kiến trúc xuyên suốt

Tách hệ thống thành 3 planes:

### 1) Local Processing Plane
Chạy bằng local/default network:
- trend ingestion
- research normalization
- script generation
- scene decomposition
- media indexing
- reranking
- subtitle generation
- rendering
- local QC

### 2) Channel Workspace Plane
Mỗi channel có workspace riêng:
- storage riêng
- browser profile riêng
- downloads riêng
- logs riêng
- policy riêng
- upload queue riêng
- health riêng

### 3) Publish Plane
Chỉ các job chạm YouTube Studio mới dùng route/network của workspace:
- open studio
- verify login
- upload assets
- fill metadata
- publish / schedule publish
- analytics pull (nếu sau này qua browser workflow)

## Format phản hồi bắt buộc sau mỗi phase

Phản hồi cuối phase phải theo đúng cấu trúc:

1. Scope completed
2. Files changed
3. Migrations added/updated
4. Dependencies added/updated
5. API changes
6. UI changes
7. Validation commands run
8. Validation results
9. Known limitations
10. Suggested next phase handoff

## Quy ước chất lượng

- Python: type hints, services tách khỏi routers
- TS/React: component rõ ràng, state hợp lý, không để logic backend trong UI
- SQLite: có index cho bảng chạy thường xuyên
- Tauri: sidecar handling phải có timeout/restart/health
- Logs: machine-readable khi có thể
- Background jobs: retry/backoff/idempotent càng nhiều càng tốt
