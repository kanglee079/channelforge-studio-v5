# ChannelForge Studio V5.6–V5.8 Addendum (AI-Ready)

## 1. Mục đích

Bộ tài liệu này là phần nối tiếp **đúng theo repo hiện tại** `kanglee079/channelforge-studio-v5`, nhằm nâng app từ mức desktop alpha có UI + sidecar + workspace/proxy/visual-match cơ bản thành một **desktop operating system cho nhiều kênh YouTube** với 3 năng lực còn thiếu lớn nhất:

- **V5.6 — Workspace Supervisor + Network Policy Manager**
- **V5.7 — Media Intelligence Layer**
- **V5.8 — Packaging & Installer Hardening**

Mục tiêu là để **Antigravity / Cursor / Claude Code** có thể code tiếp **theo từng phase**, tránh phá repo, tránh đụng toàn bộ codebase một lúc, nhưng vẫn đủ chi tiết để triển khai thật.

---

## 2. Repo hiện tại đang có gì (baseline bắt buộc phải bám)

Các file và subsystem đang tồn tại trong repo hiện tại:

- `engine/app/routers/workspaces.py`
- `engine/app/services/workspace_manager.py`
- `engine/app/db_v5.py`
- `engine/app/visual_match/schema.py`
- `engine/app/visual_match/scene_decomposer.py`
- `engine/app/visual_match/scorer.py`
- `src/pages/WorkspacesPage.tsx`
- `src-tauri/src/lib.rs`
- `src-tauri/tauri.conf.json`
- `engine/requirements.txt`
- `engine/requirements-optional.txt`

### 2.1 Những gì đang tốt
- Đã có **desktop shell** bằng Tauri.
- Đã có **Python sidecar** khởi động backend local.
- Đã có **workspace CRUD** và **proxy profiles** ở mức cơ bản.
- Đã có **health event log** sơ khai.
- Đã có **scene decomposition** và **candidate scoring** mức heuristic.
- Đã có UI trang quản lý workspace/proxy.
- Đã có nền review/cost/trend ở `db_v5.py`.

### 2.2 Những gì đang thiếu
- Chưa có **Workspace Supervisor** thực sự (session lifecycle, state machine, browser registry, reconnect/restart policies).
- Chưa có **Network Policy Manager** đúng nghĩa (per-job egress policy, upload-only route, route verification, leak tests, audit).
- Chưa có **semantic media intelligence** (CLIP embeddings, vector index, scene-level retrieval, frame-based scoring, shot planner).
- Chưa có **production packaging** cho desktop app (self-contained sidecar, dependency bootstrap, installer flows, upgrade/migration, diagnostics hardening).

---

## 3. Kiến trúc mục tiêu sau V5.8

```text
┌───────────────────────────────────────────────────────────────┐
│                    ChannelForge Desktop App                   │
│                     (Tauri 2 + React UI)                     │
├───────────────────────────────────────────────────────────────┤
│ Workspace UI │ Content UI │ Review UI │ Trend UI │ Diagnostics│
├───────────────────────────────────────────────────────────────┤
│                 Rust App Shell / Sidecar Orchestrator        │
│  - health checks  - restart policies  - updater  - telemetry│
├───────────────────────────────────────────────────────────────┤
│                  Python Engine (FastAPI + Workers)           │
│                                                               │
│  V5.6 Workspace Supervisor + Network Policy Manager           │
│  V5.7 Media Intelligence Layer                                │
│  Existing pipeline: research / script / TTS / render / upload│
│  Existing DB + new DB tables                                  │
├───────────────────────────────────────────────────────────────┤
│         Local Data Plane / Asset Cache / Vector Index         │
│    workspaces/   media-cache/   vector-index/   logs/         │
└───────────────────────────────────────────────────────────────┘
```

---

## 4. Nguyên tắc thiết kế bắt buộc

1. **Desktop-first, local-first**
   - Crawl/research/script/subtitle/render/indexing chạy local tối đa.
   - Chỉ workflow cần account/channel mới đi qua workspace browser.

2. **One channel = one isolated workspace**
   - Mỗi channel có browser profile riêng, storage riêng, logs riêng, downloads riêng, temp riêng, screenshots riêng, upload queue riêng.
   - Không dùng chung profile Chrome mặc định.

3. **Network policy theo loại job**
   - `research/render/index/indexing = DIRECT`
   - `studio/login/upload = WORKSPACE_ROUTE`
   - `sensitive action without route = BLOCK`
   - Không build anti-detect, không spoof fingerprint, không giả thiết bị/người dùng.

4. **Media bám content bằng semantic retrieval**
   - Không chỉ keyword search.
   - Bắt buộc có embedding + index + rerank + fallback plan.

5. **Không phá repo**
   - Phải tận dụng các file hiện có trước khi tạo subsystem mới.
   - Chỉ thêm file mới khi thật sự cần.

---

## 5. Phase order bắt buộc

### Phase A — V5.6
Làm **Workspace Supervisor + Network Policy Manager** trước.

Lý do:
- Đây là nền cho multi-channel.
- Đây là nền cho channel isolation.
- Đây là nền cho upload route policies.
- Nếu chưa làm phần này, app chưa thể gọi là “quản lý kênh” đúng nghĩa.

### Phase B — V5.7
Làm **Media Intelligence Layer** sau khi workspace plane đã ổn.

Lý do:
- Visual quality ảnh hưởng trực tiếp tới độ usable của tool.
- Đây là subsystem độc lập với packaging nhưng phụ thuộc vào local asset/data plane.

### Phase C — V5.8
Làm **Packaging & Installer Hardening** cuối cùng.

Lý do:
- Chỉ harden package khi engine đã ổn.
- Tránh đóng gói một runtime còn thay đổi mạnh.

---

## 6. Deliverables bắt buộc sau mỗi phase

Mỗi phase phải tạo ra:

1. **Code chạy được**
2. **DB migration**
3. **API docs ngắn**
4. **UI hoàn chỉnh cho phase đó**
5. **Integration tests tối thiểu**
6. **Release notes**
7. **Rollback notes**

Không được merge phase mới nếu phase cũ chưa có:
- health path
- manual test checklist
- idempotent migration
- error states có UI

---

## 7. Definition of Done toàn gói

Bộ V5.6–V5.8 được coi là hoàn tất khi:

- Có thể tạo nhiều workspace, mở/đóng/khôi phục/giám sát từng workspace thật.
- Có thể áp network policy theo workspace và theo job type.
- Có thể chứng minh local processing không chạy qua route workspace.
- Có thể chọn media bám scene bằng semantic search + rerank + fallback.
- Có desktop package chạy được mà không phụ thuộc “tình cờ” vào môi trường dev.
- Có installer + diagnostics đủ cho người dùng cuối cài đặt và self-check.
- Có rollback/migration path cho người dùng đang ở repo hiện tại.

---

## 8. Danh sách tài liệu con

- `V5_6_WORKSPACE_SUPERVISOR_NETWORK_POLICY_MANAGER.md`
- `V5_7_MEDIA_INTELLIGENCE_LAYER.md`
- `V5_8_PACKAGING_INSTALLER_HARDENING.md`
- `V5_6_TO_V5_8_ISSUE_BREAKDOWN.md`
- `V5_6_TO_V5_8_AI_EXECUTION_BRIEF.md`
- `REFERENCES.md`
