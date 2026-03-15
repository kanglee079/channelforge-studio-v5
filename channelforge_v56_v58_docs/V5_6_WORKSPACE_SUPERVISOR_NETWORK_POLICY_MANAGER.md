# V5.6 — Workspace Supervisor + Network Policy Manager (AI-Ready)

## 1. Mục tiêu

Biến subsystem workspace hiện tại từ mức:
- CRUD + launch browser + proxy string + healthcheck sơ khai

thành:
- **Workspace Supervisor**: quản lý lifecycle thật của từng channel workspace
- **Network Policy Manager**: điều tiết egress/network route theo workspace và theo loại job

Đây là phase quyết định việc app có thật sự là một công cụ **quản lý nhiều kênh dài hạn** hay chưa.

---

## 2. Bài toán hiện tại trong repo

### 2.1 Repo đang làm được gì
`engine/app/routers/workspaces.py` hiện có:
- list/create/get/delete workspace
- launch browser
- healthcheck 3 mức
- archive/restore
- clear temp
- health events
- proxy profiles
- bind proxy

`engine/app/services/workspace_manager.py` hiện có:
- tạo thư mục workspace
- launch Playwright persistent context
- check health đơn giản

### 2.2 Điểm yếu hiện tại
1. Không có **browser/session registry**
2. Không có **workspace state machine**
3. Không có **session verification thật** với YouTube Studio
4. Không có **start/stop/reconnect/relaunch policies**
5. Không có **policy tách route theo job type**
6. Không có **audit trail đầy đủ**
7. Không có **network diagnostics** ngoài một proxy reachability check đơn giản
8. Không có **upload-only route policy**
9. Không có **per-workspace browser locks**
10. Không có **resource cleanup policy** khi app đóng/mở lại

---

## 3. Kết quả cuối phase

Sau V5.6, app phải hỗ trợ:

### 3.1 Workspace lifecycle
- tạo workspace
- bind channel
- bind route profile
- launch workspace browser
- attach/reconnect nếu browser đã sống
- graceful close
- force kill
- relaunch
- session verify
- mark degraded / login_required / blocked
- archive / restore

### 3.2 Network policies
Mỗi job chạy qua engine phải có trường `network_policy`:

- `DIRECT`  
  Dùng egress local/direct. Áp cho:
  - crawl công khai
  - trend fetch
  - render
  - embedding/indexing
  - subtitle
  - thumbnail generation local
  - analytics aggregation local

- `WORKSPACE_ROUTE`  
  Dùng route của workspace. Áp cho:
  - mở YouTube Studio
  - login
  - upload
  - edit metadata trên Studio
  - channel checks yêu cầu account context

- `BLOCK`
  Nếu action nhạy cảm mà chưa có workspace route hợp lệ thì chặn.

### 3.3 Quan sát và debug
- xem trạng thái workspace theo thời gian thực gần-thời-gian-thực
- xem network policy đang áp cho job
- xem route verification log
- xem health history
- xem screenshots/logs cuối cùng
- xem lần verify thành công cuối

---

## 4. Non-goals

Không được xây:
- anti-detect
- fingerprint spoofing
- giả thiết bị
- giả user-agent để né phát hiện
- tự động lách policy nền tảng

Được phép xây:
- profile isolation hợp lệ
- persistent context per workspace
- stable proxy/VPN route per workspace nếu người dùng sở hữu hợp lệ
- route verification và audit

---

## 5. Kiến trúc mục tiêu

## 5.1 Backend services mới/cần nâng cấp

### 5.1.1 `engine/app/services/workspace_supervisor.py` (mới)
Chịu trách nhiệm:
- registry tất cả workspace runtime đang sống
- mở/đóng browser contexts
- process ownership
- reconnect logic
- workspace locks
- snapshot runtime state
- expose control methods cho router

State lưu trong memory runtime + DB snapshot.

### 5.1.2 `engine/app/services/network_policy_manager.py` (mới)
Chịu trách nhiệm:
- resolve policy theo job type
- resolve route profile theo workspace
- verify outbound IP
- verify route liveness
- verify DNS/basic leak checks ở mức app policy
- log policy decisions

### 5.1.3 `engine/app/services/workspace_verifier.py` (mới)
Chịu trách nhiệm:
- xác minh session thật sự usable
- xác minh trang Studio load được
- xác minh login state
- xác minh upload entrypoint reachable
- chụp screenshot khi verify fail

### 5.1.4 `engine/app/services/workspace_manager.py` (sửa)
Giảm scope:
- chỉ giữ file-system ops cơ bản
- browser launch low-level
- không giữ orchestration logic nữa

---

## 6. Data model mới

## 6.1 Bảng `workspace_runtime_state`
Mục đích: snapshot runtime hiện tại

```sql
CREATE TABLE IF NOT EXISTS workspace_runtime_state (
  workspace_id INTEGER PRIMARY KEY,
  runtime_status TEXT NOT NULL,
  browser_pid INTEGER,
  browser_type TEXT DEFAULT 'chromium',
  context_attached INTEGER DEFAULT 0,
  last_launch_at TEXT,
  last_seen_alive_at TEXT,
  last_close_at TEXT,
  last_error_code TEXT,
  last_error_message TEXT,
  current_route_mode TEXT DEFAULT 'DIRECT',
  current_outbound_ip TEXT DEFAULT '',
  updated_at TEXT NOT NULL
);
```

`runtime_status`:
- `stopped`
- `launching`
- `running`
- `verifying`
- `login_required`
- `upload_ready`
- `degraded`
- `blocked`
- `closing`
- `crashed`

## 6.2 Bảng `workspace_route_bindings`
```sql
CREATE TABLE IF NOT EXISTS workspace_route_bindings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER NOT NULL,
  route_profile_id INTEGER NOT NULL,
  bind_mode TEXT NOT NULL DEFAULT 'studio_only',
  active INTEGER NOT NULL DEFAULT 1,
  notes TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

`bind_mode`:
- `studio_only`
- `all_browser_actions`

## 6.3 Bảng `network_policy_events`
```sql
CREATE TABLE IF NOT EXISTS network_policy_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER DEFAULT 0,
  job_id INTEGER DEFAULT 0,
  job_type TEXT NOT NULL,
  policy_mode TEXT NOT NULL,
  route_profile_id INTEGER DEFAULT 0,
  decision TEXT NOT NULL,
  outbound_ip TEXT DEFAULT '',
  evidence_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);
```

## 6.4 Bảng `workspace_session_checks`
```sql
CREATE TABLE IF NOT EXISTS workspace_session_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER NOT NULL,
  check_type TEXT NOT NULL,
  status TEXT NOT NULL,
  details_json TEXT DEFAULT '{}',
  screenshot_path TEXT DEFAULT '',
  created_at TEXT NOT NULL
);
```

---

## 7. Router/API thay đổi

## 7.1 File cần sửa
- `engine/app/routers/workspaces.py`
- `engine/app/main.py`
- `engine/app/db.py` hoặc migration helper thích hợp
- `engine/app/db_v5.py`

## 7.2 Endpoints mới

### Runtime control
- `POST /api/v2/workspaces/{id}/open`
- `POST /api/v2/workspaces/{id}/close`
- `POST /api/v2/workspaces/{id}/force-kill`
- `POST /api/v2/workspaces/{id}/relaunch`
- `GET  /api/v2/workspaces/{id}/runtime`
- `GET  /api/v2/workspaces/runtime/all`

### Verification
- `POST /api/v2/workspaces/{id}/verify-session`
- `GET  /api/v2/workspaces/{id}/session-checks`

### Route/network
- `GET  /api/v2/workspaces/{id}/route-binding`
- `POST /api/v2/workspaces/{id}/bind-route`
- `POST /api/v2/workspaces/{id}/unbind-route`
- `POST /api/v2/workspaces/{id}/verify-route`
- `GET  /api/v2/workspaces/{id}/network-events`

### Screenshot/log helpers
- `GET /api/v2/workspaces/{id}/artifacts`
- `POST /api/v2/workspaces/{id}/capture-screenshot`

---

## 8. UI/UX cần thêm

## 8.1 Sửa `src/pages/WorkspacesPage.tsx`
Chia trang thành 4 panel:

### A. Workspace Grid
Hiển thị:
- tên workspace
- channel
- session status
- runtime status
- route mode
- current outbound IP
- last verified
- last error

Buttons:
- Open
- Verify
- Close
- Relaunch
- Logs
- Artifacts
- Archive

### B. Workspace Detail Drawer
Tabs:
- Overview
- Runtime
- Session
- Route
- Health
- Artifacts

### C. Route Profiles
Hiển thị:
- protocol
- server
- port
- bind status
- last reachable
- notes
- test result

### D. Policy Event Stream
Table:
- time
- workspace
- job type
- chosen policy
- outbound IP
- decision
- evidence summary

## 8.2 Component mới đề xuất
- `src/components/workspaces/WorkspaceRuntimeCard.tsx`
- `src/components/workspaces/RouteBindingPanel.tsx`
- `src/components/workspaces/SessionCheckTable.tsx`
- `src/components/workspaces/PolicyEventTable.tsx`
- `src/components/workspaces/ArtifactList.tsx`

---

## 9. Runtime state machine

```text
new
  ↓
open_requested
  ↓
launching
  ↓
running
  ↓
verifying
  ├─> upload_ready
  ├─> login_required
  ├─> degraded
  └─> blocked
```

Transitions:

- `running -> closing -> stopped`
- `degraded -> relaunch -> launching`
- `login_required -> verify-session after user login -> upload_ready`
- `upload_ready -> route fail -> degraded`
- `running -> browser crash -> crashed`

---

## 10. Network Policy Manager — decision rules

## 10.1 Policy resolver input
```python
{
  "job_type": "youtube_upload",
  "workspace_id": 12,
  "channel_name": "History Shorts EN",
  "requires_account_context": True,
  "requires_upload_surface": True
}
```

## 10.2 Resolver output
```python
{
  "policy_mode": "WORKSPACE_ROUTE",
  "route_profile_id": 3,
  "decision": "allow",
  "outbound_ip": "x.x.x.x",
  "reason": "upload job bound to workspace route"
}
```

## 10.3 Policy table

| Job Type | Policy |
|---|---|
| trend_ingest | DIRECT |
| generic_scrape_public | DIRECT |
| render_video | DIRECT |
| embed_asset | DIRECT |
| transcribe_audio | DIRECT |
| open_studio | WORKSPACE_ROUTE |
| verify_session | WORKSPACE_ROUTE |
| youtube_upload | WORKSPACE_ROUTE |
| youtube_metadata_edit | WORKSPACE_ROUTE |
| delete_video_from_channel | WORKSPACE_ROUTE |
| unknown_sensitive | BLOCK |

---

## 11. Backend implementation plan

## 11.1 `workspace_supervisor.py`
Public methods:
- `open_workspace(workspace_id: int) -> dict`
- `close_workspace(workspace_id: int) -> dict`
- `force_kill_workspace(workspace_id: int) -> dict`
- `relaunch_workspace(workspace_id: int) -> dict`
- `get_runtime_state(workspace_id: int) -> dict`
- `list_runtime_states() -> list[dict]`
- `capture_artifacts(workspace_id: int) -> dict`

Internal concerns:
- `asyncio.Lock` per workspace
- registry: `{workspace_id: RuntimeHandle}`
- remember `playwright`, `context`, `page`, `launched_at`
- cleanup on app shutdown
- heartbeat timestamp updates

## 11.2 `network_policy_manager.py`
Public methods:
- `resolve_policy(job_type, workspace_id=None, job_id=0) -> dict`
- `verify_route(workspace_id: int) -> dict`
- `get_outbound_ip_via_route(proxy_url: str) -> str`
- `record_policy_event(...)`

Important:
- route verify phải có timeout
- route verify fail không được treo whole app
- phải ghi `network_policy_events`

## 11.3 `workspace_verifier.py`
Public methods:
- `verify_youtube_studio(context, workspace_id) -> dict`
- `capture_failure_artifacts(context, workspace_id) -> dict`

Checks:
- page title/url
- presence của một số selectors ổn định
- login redirect detection
- upload button / studio shell availability
- screenshot on failure
- update `workspace_session_checks`

---

## 12. Tích hợp với Tauri shell

## 12.1 `src-tauri/src/lib.rs`
Cần thêm:
- graceful shutdown gọi backend endpoint close/flush trước khi kill child
- diagnostics command cho workspace runtime summary
- auto-restart sidecar phải tránh restart loop nếu migration fail
- expose command:
  - `get_sidecar_health`
  - `restart_sidecar`
  - `get_diagnostics`
  - `get_workspace_runtime_snapshot`

## 12.2 Không làm ở phase này
- chưa đóng gói self-contained hoàn toàn
- chưa làm updater sâu
- đó là V5.8

---

## 13. Acceptance criteria

### 13.1 Functional
- Có thể tạo 5 workspace và mở độc lập.
- Mỗi workspace dùng `userDataDir` riêng.
- Mỗi workspace có runtime status rõ ràng.
- Có thể verify session từng workspace.
- Có thể bind route profile vào workspace.
- Upload job mô phỏng phải resolve sang `WORKSPACE_ROUTE`.
- Render job mô phỏng phải resolve sang `DIRECT`.
- Khi route fail, workspace status phải thành `degraded` hoặc `blocked`.
- Có thể close và relaunch workspace không crash app.

### 13.2 Observability
- Có log event cho policy decisions.
- Có session checks table.
- Có screenshot khi verify fail.
- Có UI xem runtime state và route state.

### 13.3 Safety
- Không có code spoof fingerprint.
- Không có code fake device identity.
- Không ép mọi job đi qua route workspace.

---

## 14. Test plan

### Unit tests
- policy resolver cho 10 job types
- workspace state transitions
- DB write/read runtime snapshot
- bind/unbind route
- event logging

### Integration tests
- create workspace -> open -> verify -> close
- verify route profile success/fail
- launch workspace without route
- open 3 workspaces concurrently
- sidecar restart preserves DB state

### Manual tests
- tạo workspace từ UI
- bind proxy/route
- mở browser
- đăng nhập thủ công
- verify session
- xem logs + screenshots

---

## 15. File change map

### Files to create
- `engine/app/services/workspace_supervisor.py`
- `engine/app/services/network_policy_manager.py`
- `engine/app/services/workspace_verifier.py`
- `engine/app/tests/test_workspace_supervisor.py`
- `engine/app/tests/test_network_policy_manager.py`
- `src/components/workspaces/WorkspaceRuntimeCard.tsx`
- `src/components/workspaces/RouteBindingPanel.tsx`
- `src/components/workspaces/SessionCheckTable.tsx`
- `src/components/workspaces/PolicyEventTable.tsx`

### Files to modify
- `engine/app/routers/workspaces.py`
- `engine/app/services/workspace_manager.py`
- `engine/app/db.py` or migration path in existing schema init
- `engine/app/db_v5.py`
- `engine/app/main.py`
- `src/pages/WorkspacesPage.tsx`
- `src-tauri/src/lib.rs`

---

## 16. Migration notes

- Không xóa bảng cũ.
- `workspaces.proxy_config` vẫn giữ để backward compatibility.
- Route profile binding mới chỉ bổ sung.
- Nếu workspace cũ đã có `proxy_config`, migration script có thể sinh record binding mặc định nếu người dùng chọn “upgrade existing”.

---

## 17. Anti-regression constraints cho AI coder

- Không rewrite toàn bộ `workspaces.py`.
- Tách logic orchestration khỏi router.
- Không xóa API cũ đang dùng bởi UI hiện tại nếu chưa có migration frontend.
- Không buộc Playwright import ở module import time; chỉ import khi cần.
- Không làm browser open ở startup.
- Không giữ process handles trong global không khóa.

---

## 18. Handoff note

Khi hoàn tất phase này, AI phải xuất:
- danh sách endpoint mới
- migration summary
- ảnh chụp UI mới
- cách manual test 1 workspace end-to-end
