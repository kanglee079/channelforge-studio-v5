# ChannelForge Studio V5 — Master Execution Plan

## 1. Mục tiêu của V5

V5 là bước nâng cấp từ desktop-first studio hiện tại thành một **Channel Operating System** thực thụ cho mô hình multi-channel YouTube. Mục tiêu không chỉ là tạo video, mà là tạo ra một hệ thống có thể:

- vận hành nhiều kênh với **niche cố định theo từng channel**;
- giữ **môi trường làm việc riêng** cho từng channel/workspace;
- tạo pipeline media bám sát nội dung hơn;
- liên tục quan sát xu hướng, thu thập dữ liệu và biến dữ liệu thành idea/content có kiểm soát;
- có lớp review, analytics và cost routing để tối ưu chi phí và giảm lỗi;
- chạy như một **desktop super app** với Python engine sidecar, không phụ thuộc web app rời rạc.

V5 được chia thành 5 module chiến lược:

- **V5.1 — Visual Match Engine**
- **V5.2 — Channel Workspace Engine**
- **V5.3 — Desktop Packaging + Sidecar Orchestration**
- **V5.4 — Research/Trend Assistant 2.0**
- **V5.5 — Review + Analytics + Cost Router**

## 2. Nguyên tắc kiến trúc

### 2.1 Desktop-first, local-first
- App chạy như desktop app chính thức.
- UI shell: **Tauri 2 + React/TypeScript**.
- Engine: **Python sidecar** giữ pipeline hiện có.
- Dữ liệu local ưu tiên SQLite, file-system, cache local, vector index local.
- Không phụ thuộc frontend web + backend server chạy riêng nếu không cần.

### 2.2 Channel-first
Mỗi channel là một đơn vị độc lập có:
- niche cố định;
- tone/content policy riêng;
- upload cadence riêng;
- media style riêng;
- browser workspace riêng;
- source whitelist/blacklist riêng;
- ngân sách API riêng;
- analytics dashboard riêng.

### 2.3 Human-in-the-loop but automation-first
- Mọi phần có thể auto thì auto.
- Mọi phần có rủi ro cao phải có review gate.
- Các quyết định có confidence thấp phải được đưa vào review queue.

### 2.4 Provider abstraction
Tất cả provider phải qua adapter layer:
- LLM providers
- TTS providers
- STT providers
- Footage/image providers
- Trend/news providers
- Browser/profile providers
- Upload providers

Không được gắn logic trực tiếp vào UI.

### 2.5 Auditability
Mọi thứ phải log được:
- prompt version
- source URLs
- asset origins
- model/provider used
- cost estimate
- retry state
- failure reason
- upload metadata

## 3. Kiến trúc tổng thể

```text
Tauri Desktop Shell
  ├─ React UI
  ├─ Local event bus
  ├─ Native commands
  └─ Python sidecar supervisor

Python Engine
  ├─ Job Queue
  ├─ Visual Match Engine
  ├─ Research/Trend Assistant
  ├─ Content Pipeline
  ├─ Review / Policy / Moderation
  ├─ Analytics / Cost Router
  ├─ Browser Workspace Manager
  └─ Upload Orchestrator

Data Layer
  ├─ SQLite main DB
  ├─ Vector index (FAISS)
  ├─ Asset cache
  ├─ Workspace folders
  ├─ Logs / traces
  └─ Generated outputs
```

## 4. Core entities

### 4.1 Channel
- id
- name
- platform = youtube
- niche_slug
- language
- content_style
- upload_policy
- thumbnail_style
- status
- daily_quota_soft_limit
- budget_profile_id
- workspace_id
- review_policy_id
- created_at
- updated_at

### 4.2 Workspace
- id
- channel_id
- browser_engine
- user_data_dir
- downloads_dir
- cookies_state_path
- storage_state_path
- proxy_profile_id
- timezone
- locale
- safe_mode_enabled
- notes

### 4.3 Content Idea
- id
- channel_id
- source_type
- source_ref
- title_candidate
- hook_candidate
- angle
- trend_score
- novelty_score
- competition_score
- risk_score
- status

### 4.4 Research Document
- id
- channel_id
- url
- source_name
- fetched_at
- cleaned_text
- entities_json
- summary_json
- quality_score
- license_notes
- hash

### 4.5 Script Project
- id
- channel_id
- idea_id
- structure_json
- scenes_json
- prompt_version
- model_used
- total_words
- est_duration_sec
- status

### 4.6 Media Asset
- id
- asset_type
- source_provider
- source_url
- local_path
- width
- height
- duration_sec
- aspect_ratio
- language_hint
- tags_json
- embedding_status
- license_notes
- quality_score
- phash
- sha256

### 4.7 Render Job
- id
- channel_id
- script_project_id
- render_preset
- subtitle_mode
- thumbnail_mode
- output_video_path
- output_thumbnail_path
- output_srt_path
- status
- started_at
- finished_at

### 4.8 Upload Job
- id
- channel_id
- render_job_id
- youtube_video_id
- title
- description
- tags_json
- privacy_status
- publish_at
- disclose_synthetic_media
- status
- error_message

### 4.9 Cost Event
- id
- provider
- provider_model
- channel_id
- job_id
- event_type
- unit_count
- unit_cost_estimate
- currency
- metadata_json
- created_at

## 5. Desktop app sections

### 5.1 Dashboard
- health of all channels
- render queue summary
- upload queue summary
- cost today/week/month
- trends discovered today
- review queue count
- failures/retries summary

### 5.2 Channel Portfolio
- list channels
- each channel card shows niche, status, budget, schedule, last upload, workspace health
- channel detail with tabs: Overview / Policy / Workspace / Content / Uploads / Analytics / Costs / Logs

### 5.3 Content Studio
- ideas inbox
- research documents
- script editor
- scene planner
- media matching panel
- render preset selector
- compare variations

### 5.4 Trend Radar
- trending topics board
- source cards
- trend confidence and freshness
- convert trend → idea → script
- watchlists

### 5.5 Operations
- queue monitor
- worker health
- sidecar status
- cache browser
- vector index browser
- provider settings
- proxy/network settings

### 5.6 Review Center
- low confidence script
- low confidence media matches
- moderation flags
- policy conflicts
- cost anomaly alerts
- upload approval queue

## 6. Cross-cutting systems

### 6.1 Event bus topics
- `job.created`
- `job.started`
- `job.progress`
- `job.failed`
- `job.completed`
- `script.generated`
- `scene.match.completed`
- `workspace.health.changed`
- `trend.ingested`
- `upload.scheduled`
- `upload.completed`
- `cost.recorded`

### 6.2 Error policy
- retry transient errors with exponential backoff
- hard fail on policy violations
- degrade gracefully when premium provider unavailable
- auto fallback to local providers when allowed by channel budget policy

### 6.3 Security & privacy
- secrets encrypted locally if possible
- no hardcoded secrets
- per-channel workspace isolation
- source tracking for every scraped document
- license notes for assets

## 7. V5 roadmap theo thứ tự build

### Phase A — nền tảng
1. chuẩn hóa DB migration cho V5 entities
2. event bus + job orchestration upgrades
3. provider abstraction cleanup
4. Tauri shell + sidecar supervisor cleanup

### Phase B — V5.2 trước V5.1
Build **Workspace Engine** trước vì đây là xương sống cho multi-channel desktop app.

### Phase C — V5.1
Build Visual Match Engine để giải quyết pain point lớn nhất: footage lệch content.

### Phase D — V5.4
Build Research/Trend Assistant 2.0 để feed idea pipeline chất lượng hơn.

### Phase E — V5.5
Build Review + Analytics + Cost Router để vận hành ổn định.

### Phase F — V5.3 hoàn thiện packaging
Finalize desktop packaging, updater, logging, diagnostics.

## 8. Definition of done cho V5

Một V5 đủ chuẩn phải đạt các điều kiện:
- tạo được video có media bám nội dung tốt hơn rõ rệt;
- quản lý được nhiều channel với workspace riêng;
- desktop app chạy ổn định với sidecar engine;
- quét trend/research liên tục và biến thành idea có kiểm soát;
- có review queue cho các điểm confidence thấp;
- có analytics/cost tracking theo channel;
- có log/audit đủ để debug;
- không phụ thuộc thủ công CLI cho quy trình chính.

## 9. File map gợi ý để AI code

```text
src/
  features/
    dashboard/
    channels/
    workspace/
    content-studio/
    trend-radar/
    review-center/
    analytics/
    settings/
  shared/
    api/
    store/
    ui/
    types/
    utils/

src-tauri/
  src/
    commands/
    sidecar/
    ipc/
    diagnostics/

engine/
  app/
    core/
    queue/
    db/
    providers/
    workspace/
    visual_match/
    research/
    scripts/
    render/
    review/
    analytics/
    uploads/
    cost/
    api/
```

## 10. AI coding rules cho toàn bộ V5

- không rewrite toàn bộ project một lúc;
- đi theo module và migration nhỏ;
- mỗi PR phải chạy được độc lập;
- thêm tests cho domain logic quan trọng;
- UI phải hiển thị fallback state, loading, error, empty state;
- mọi bảng đều hỗ trợ filter/sort/search;
- mọi long-running task đều phải có progress;
- mọi background task phải resume được;
- không triển khai fingerprint spoofing hoặc anti-detect bypass.
