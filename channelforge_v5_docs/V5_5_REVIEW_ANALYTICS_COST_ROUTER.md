# V5.5 — Review + Analytics + Cost Router

## 1. Mục tiêu

Tạo lớp vận hành để hệ thống không chỉ “chạy được” mà còn **chạy có kiểm soát**:
- review các điểm rủi ro/confidence thấp;
- theo dõi hiệu quả content/video/channel;
- đo chi phí theo provider/channel/job;
- tự route tác vụ qua local hay premium provider theo policy.

## 2. Kết quả mong muốn

- pipeline tự động nhưng không mù;
- biết đang tốn tiền ở đâu;
- biết channel nào hiệu quả hơn;
- biết lúc nào nên dùng local model, lúc nào nên dùng cloud premium;
- có queue review thay vì fail âm thầm.

## 3. Review Center

## 3.1 Review queues
- low-confidence scenes
- source-risk research packs
- policy-conflict ideas
- upload approval queue
- repeated asset warnings
- budget anomaly alerts

### 3.2 Review actions
- approve
- reject
- retry with different provider
- escalate to human edit
- pin asset/angle/title
- blacklist source or asset

### 3.3 Review objects must show
- why flagged
- source references
- score breakdown
- suggested next actions
- prior history for this channel

## 4. Analytics subsystem

### 4.1 Operational analytics
- jobs created/completed/failed
- queue latency
- render time
- upload success rate
- cache hit rate
- workspace health trend

### 4.2 Content analytics
- video outputs by channel
- format split shorts/long
- topic clusters covered
- title variants used
- thumbnail variants used
- retention proxy metrics if imported later

### 4.3 Quality analytics
- average scene confidence
- manual replacement rate
- review rate by module
- policy conflict frequency

### 4.4 Cost analytics
- provider usage by day/week/month
- channel cost breakdown
- cost per video
- cost per minute rendered
- local vs cloud ratio

## 5. Cost Router

Cost Router là lớp quyết định provider nào được dùng cho một bước.

### 5.1 Inputs
- channel budget profile
- task type
- urgency
- current provider availability
- quality requirement
- user override
- cached asset/data availability

### 5.2 Outputs
- selected provider
- fallback chain
- cost estimate
- confidence estimate

### 5.3 Example policies
#### Budget mode
- script: local LLM first, OpenAI fallback
- TTS: Kokoro/Piper first, ElevenLabs only premium jobs
- STT: Faster-Whisper first
- trend sources: free sources first, SerpApi only when needed

#### Premium mode
- script: OpenAI / Claude
- TTS: ElevenLabs / OpenAI TTS
- subtitle: WhisperX enhanced

## 6. Database changes

### 6.1 review_items
- id
- review_type
- object_type
- object_id
- channel_id
- priority
- reason_code
- score
- payload_json
- status
- created_at
- resolved_at

### 6.2 analytics_daily
- id
- channel_id
- day
- jobs_completed
- jobs_failed
- videos_rendered
- uploads_completed
- avg_scene_confidence
- manual_replacements
- total_cost_estimate

### 6.3 provider_usage_events
- id
- provider
- model
- task_type
- channel_id
- job_id
- request_count
- token_count
- duration_sec
- cost_estimate
- cache_hit
- created_at

### 6.4 budget_profiles
- id
- name
- monthly_limit
- preferred_quality_mode
- rules_json

## 7. API design

### 7.1 Review queue
`GET /api/v5/review/items`

### 7.2 Resolve review item
`POST /api/v5/review/items/{id}/resolve`

### 7.3 Analytics dashboard
`GET /api/v5/analytics/dashboard?channel_id=...`

### 7.4 Cost summary
`GET /api/v5/cost/summary?channel_id=...&range=30d`

### 7.5 Simulate routing
`POST /api/v5/cost/router/simulate`

## 8. UI specification

### 8.1 Review Center
- tabs by review type
- batch actions
- side panel with detailed context
- quick open related scene/script/channel

### 8.2 Analytics page
Sections:
- overview KPIs
- operational chart
- content performance table
- quality chart
- cost chart
- provider usage chart

### 8.3 Cost Router settings
- global defaults
- per-channel overrides
- provider priorities
- hard/soft budget caps
- cache first toggles

## 9. Review rules

### Auto-create review item when
- scene match score below threshold
- research pack source confidence low
- policy conflict found
- provider cost estimate above budget rule
- repeated upload failure
- workspace degraded but upload requested

## 10. Cost estimate methodology

### Track as early as possible
- before request: estimated cost
- after request: actual or refined estimate
- if local provider: record compute time + local cost proxy optional

## 11. Acceptance criteria

### Must-have
- review queue populated from other modules
- analytics dashboard with basic KPIs
- provider usage logging
- cost router can choose providers by policy

### Nice-to-have
- cost anomaly detection
- monthly budget forecasting
- channel ROI overlays later

## 12. Tests

### Unit
- routing policy evaluation
- budget threshold checks
- review item creation rules

### Integration
- low score scene -> review item -> resolve -> rerun
- provider event -> cost summary dashboard

## 13. Implementation order

1. provider usage logging
2. review item schema and service
3. cost router policy engine
4. analytics aggregations
5. UI dashboards
6. alerts/anomaly detection

## 14. Key success metrics

- giảm cost/video mà không làm quality sụt mạnh
- giảm số lỗi âm thầm
- tăng khả năng debug và ra quyết định
