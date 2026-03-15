# V5.6–V5.8 Issue Breakdown (AI-Ready)

## Epic 1 — Workspace Supervisor + Network Policy Manager

### WS-001
Tạo migration cho:
- workspace_runtime_state
- workspace_route_bindings
- network_policy_events
- workspace_session_checks

### WS-002
Tạo `workspace_supervisor.py`
- runtime registry
- locks
- open/close/relaunch
- graceful cleanup

### WS-003
Refactor `workspace_manager.py`
- tách launch low-level
- giữ file-system ops cơ bản

### WS-004
Tạo `workspace_verifier.py`
- verify studio session
- screenshot on fail

### WS-005
Tạo `network_policy_manager.py`
- policy resolution
- route verification
- outbound IP evidence
- event logging

### WS-006
Mở rộng router `workspaces.py`
- runtime endpoints
- verify endpoints
- route endpoints
- artifacts endpoints

### WS-007
Nâng UI `WorkspacesPage.tsx`
- runtime panel
- route tab
- session checks tab
- policy event stream

### WS-008
Thêm integration tests phase 1

---

## Epic 2 — Media Intelligence Layer

### MI-001
Tạo migration cho:
- media_assets
- asset_embeddings
- scene_match_runs
- scene_match_items

### MI-002
Tạo `scene_spec_builder.py`

### MI-003
Tạo `frame_extractor.py`

### MI-004
Tạo `embedder.py`

### MI-005
Tạo `index_store.py`

### MI-006
Tạo `retriever.py`

### MI-007
Tạo `reranker.py`

### MI-008
Tạo `shot_planner.py`

### MI-009
Tạo `review_gate.py`

### MI-010
Tạo router `media_intel.py`

### MI-011
Tạo UI `MediaIntelligencePage.tsx`

### MI-012
Tích hợp review_items hiện có

### MI-013
Benchmark script sample + cache warmup tests

---

## Epic 3 — Packaging & Installer Hardening

### PK-001
Thiết kế sidecar packaging strategy chính thức

### PK-002
Sửa `tauri.conf.json` để chuẩn bị externalBin/release paths

### PK-003
Sửa `src-tauri/src/lib.rs`
- dev mode vs release mode
- startup timeout
- structured error
- support bundle command

### PK-004
Tạo `diagnostics_service.py`

### PK-005
Tạo `dependency_probe.py`

### PK-006
Tạo `support_bundle.py`

### PK-007
Tạo migration runner / schema version ledger

### PK-008
Tạo/nâng `DiagnosticsPage.tsx`

### PK-009
Tạo scripts build/release checks

### PK-010
Viết `docs/RELEASE_PACKAGING.md`

### PK-011
First-run wizard

### PK-012
Smoke tests packaged build

---

## Merge gates

Không merge Epic 2 nếu Epic 1 chưa pass:
- 3 integration tests
- UI runtime states
- route policy logs

Không merge Epic 3 nếu Epic 2 chưa pass:
- sample match run
- review queue path
- asset index rebuild path
