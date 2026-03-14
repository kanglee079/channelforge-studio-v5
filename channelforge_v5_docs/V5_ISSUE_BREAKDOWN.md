# ChannelForge Studio V5 — Issue Breakdown cho AI Coder

## Cách dùng file này
AI coder phải tạo issue/task theo từng nhóm dưới đây. Mỗi task phải nhỏ, có acceptance criteria và không phá vỡ chạy hiện tại.

---

## Epic 1 — V5 foundation

### Task 1.1 — Add schema_version and migrations scaffold
**Done when:**
- DB có bảng schema_version
- migration runner idempotent
- backup trước migration

### Task 1.2 — Add event bus topics standardization
**Done when:**
- event names chuẩn hóa
- frontend có thể subscribe progress

### Task 1.3 — Provider adapter cleanup
**Done when:**
- mọi provider qua interface chung
- không còn gọi provider trực tiếp từ UI layer

---

## Epic 2 — Workspace Engine

### Task 2.1 — Create workspace DB tables
### Task 2.2 — Filesystem workspace layout service
### Task 2.3 — Proxy profile CRUD + validation
### Task 2.4 — Playwright persistent context wrapper
### Task 2.5 — Workspace CRUD API
### Task 2.6 — Workspace Manager UI list/detail
### Task 2.7 — Workspace health checks
### Task 2.8 — Upload flow bound to workspace
### Task 2.9 — Recovery actions and diagnostics

---

## Epic 3 — Visual Match Engine

### Task 3.1 — Scene decomposition service
### Task 3.2 — Candidate retrieval service
### Task 3.3 — Candidate preprocessing and metadata extraction
### Task 3.4 — Asset embedding generation cache
### Task 3.5 — Scoring engine
### Task 3.6 — Duplicate guard
### Task 3.7 — Shot planner
### Task 3.8 — Scene Planner API
### Task 3.9 — Scene Planner UI
### Task 3.10 — Manual replace / pin / blacklist actions
### Task 3.11 — Review queue integration

---

## Epic 4 — Research Assistant 2.0

### Task 4.1 — trend_items and topic_clusters schema
### Task 4.2 — multi-source ingestion pipeline
### Task 4.3 — cleaning/dedupe pipeline
### Task 4.4 — niche relevance scoring
### Task 4.5 — idea generation from trend item
### Task 4.6 — research pack generator
### Task 4.7 — Trend Radar UI
### Task 4.8 — Research Inbox UI
### Task 4.9 — watchlists

---

## Epic 5 — Review / Analytics / Cost Router

### Task 5.1 — review_items schema/service
### Task 5.2 — provider usage logging
### Task 5.3 — budget profiles schema/service
### Task 5.4 — cost router policy engine
### Task 5.5 — analytics_daily aggregation
### Task 5.6 — Review Center UI
### Task 5.7 — Analytics dashboard UI
### Task 5.8 — Cost settings UI

---

## Epic 6 — Desktop packaging

### Task 6.1 — sidecar supervisor in Tauri
### Task 6.2 — diagnostics bundle export
### Task 6.3 — first-run wizard
### Task 6.4 — migration assistant V4 -> V5
### Task 6.5 — production release build scripts

---

## QA gates cho mọi task
- có type definitions rõ ràng
- có empty/loading/error state
- có logs
- có test ít nhất ở mức unit nếu là domain logic
- không hardcode secrets or absolute paths
