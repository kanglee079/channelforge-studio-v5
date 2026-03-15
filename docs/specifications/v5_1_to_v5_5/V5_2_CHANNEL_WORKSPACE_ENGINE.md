# V5.2 — Channel Workspace Engine

## 1. Mục tiêu

Channel Workspace Engine biến mỗi channel thành một **workspace độc lập** về nội dung, lịch vận hành, session browser, downloads, storage, logs và network configuration hợp lệ.

Đây không phải anti-detect hay fingerprint spoofing. Đây là **profile isolation + workspace lifecycle management** để vận hành nhiều channel ổn định, rõ ràng và ít rủi ro.

## 2. Kết quả mong muốn

- mỗi channel có một workspace riêng;
- session/cookies không chồng chéo giữa các channel;
- downloads và logs tách biệt;
- có thể gắn network profile/proxy hợp lệ riêng cho từng workspace;
- có health check và recovery;
- có giao diện quản lý workspace như tài nguyên hạng nhất.

## 3. Functional requirements

### 3.1 Workspace per channel
Mỗi channel phải map 1-1 hoặc 1-n với workspace tùy mode.

Schema workspace:
- workspace id
- channel id
- browser engine
- browser binary path
- user_data_dir
- storage_state_path
- downloads_dir
- temp_dir
- screenshots_dir
- proxy_profile_id
- locale
- timezone
- status
- last_health_check_at
- last_login_at

### 3.2 Persistent browser context
Engine phải hỗ trợ persistent browser context để giữ session bền vững theo workspace.

### 3.3 Workspace lifecycle
Các hành động:
- create workspace
- clone workspace template
- open workspace
- lock workspace
- rotate credentials manually
- clear temp only
- archive workspace
- restore workspace
- rebind proxy profile

### 3.4 Workspace health
Health signals:
- browser executable available?
- profile dir accessible?
- storage state valid?
- proxy reachable?
- disk space okay?
- last upload success?
- last login too old?
- suspicious repeated failures?

### 3.5 Network profile
Network profile là cấu hình kết nối hợp lệ cho workspace:
- profile name
- proxy server
- proxy type
- username/password optional
- bypass domains
- notes
- active/inactive
- test status

### 3.6 Policy per channel
Mỗi channel có policy pack:
- niche fixed
- language
- publish cadence
- upload limits
- allowed providers
- source whitelist
- forbidden topics
- sensitive keywords
- human review requirements

### 3.7 Safe browser operations
Engine phải hỗ trợ:
- open channel dashboard
- open upload page
- attach screenshot/log on failure
- controlled file selection for upload
- optional manual intervention mode

## 4. Không làm gì

Không triển khai:
- fingerprint spoofing
- anti-detect browser
- account farming bypass
- stealth bypass systems
- tự động lách platform protections

## 5. Internal architecture

```text
engine/app/workspace/
  service.py
  browser_manager.py
  profile_store.py
  network_profiles.py
  healthcheck.py
  recovery.py
  uploader_bridge.py
  schema.py
```

## 6. Folder structure on disk

```text
/workspaces/
  /channel_<slug>/
    /profile/
    /downloads/
    /screenshots/
    /storage/
    /logs/
    /temp/
    workspace.json
```

## 7. Database changes

### 7.1 workspaces
- id
- channel_id
- name
- browser_engine
- browser_channel
- user_data_dir
- storage_state_path
- downloads_dir
- screenshots_dir
- temp_dir
- proxy_profile_id
- timezone
- locale
- status
- notes
- created_at
- updated_at

### 7.2 proxy_profiles
- id
- name
- protocol
- server
- port
- username
- password_encrypted
- bypass
- status
- last_tested_at
- last_test_status
- notes

### 7.3 workspace_health_events
- id
- workspace_id
- event_type
- severity
- message
- payload_json
- created_at

## 8. API design

### 8.1 Create workspace
`POST /api/v5/workspaces`

### 8.2 Get workspace detail
`GET /api/v5/workspaces/{workspace_id}`

### 8.3 Run health check
`POST /api/v5/workspaces/{workspace_id}/healthcheck`

### 8.4 Open browser session
`POST /api/v5/workspaces/{workspace_id}/open-browser`

### 8.5 Bind network profile
`POST /api/v5/workspaces/{workspace_id}/bind-proxy`

### 8.6 Archive workspace
`POST /api/v5/workspaces/{workspace_id}/archive`

### 8.7 Upload through workspace
`POST /api/v5/workspaces/{workspace_id}/upload`

## 9. Desktop UI specification

### 9.1 Workspace Manager page
Table columns:
- channel
- workspace name
- browser
- proxy profile
- last login
- last upload
- health status
- disk size
- actions

### 9.2 Workspace detail tabs
- Overview
- Session
- Network
- Files
- Upload History
- Health Logs
- Recovery

### 9.3 Actions
- open local folder
- open browser
- export diagnostics bundle
- clear temp files
- test network
- verify storage state
- take screenshot

## 10. Browser automation design

### 10.1 Preferred engine
Use Playwright with persistent context support.

### 10.2 Launch config
For each workspace:
- choose browser binary or bundled browser
- set userDataDir to workspace profile dir
- set downloads path
- set locale/timezone if supported
- set proxy if proxy profile bound

### 10.3 Upload flow abstraction
Upload subsystem không được hardcode vào UI. Nó phải là service có step logs:
- open upload page
- verify auth state
- upload file
- fill title/description/tags
- schedule if needed
- attach thumbnail if enabled
- finalize / record result

## 11. Health check logic

### Health checks cấp 1
- profile dir exists
- storage files exist
- disk writable
- browser executable reachable

### Health checks cấp 2
- proxy connectivity
- can open simple site
- can open YouTube Studio page

### Health checks cấp 3
- authenticated state still valid
- upload permissions okay
- no repeated blocking or captcha loops

## 12. Recovery playbooks

### 12.1 Broken profile
- back up current state
- mark degraded
- open manual intervention mode
- allow restore from checkpoint

### 12.2 Proxy down
- mark network degraded
- switch to no proxy or fallback profile only if policy allows
- pause uploads for affected workspace

### 12.3 Upload repeated failures
- attach screenshots/logs
- move to review queue
- do not retry infinitely

## 13. Acceptance criteria

### Must-have
- create and store workspace
- open persistent browser session per workspace
- bind proxy profile and test it
- upload flow can reference a specific workspace
- workspace detail UI exists

### Nice-to-have
- diagnostics bundle export
- workspace clone from template
- workspace archive/restore

## 14. Tests

### Unit
- path generation
- proxy config validation
- workspace health classification

### Integration
- create workspace -> launch context -> save state -> reopen context

### Manual QA
- 3 channels, 3 workspaces, different folders, no leakage of downloads/cookies

## 15. Implementation order

1. DB schema
2. file-system layout service
3. proxy profile schema and validation
4. Playwright persistent context wrapper
5. workspace CRUD UI
6. health checks
7. upload flow binding
8. recovery tools

## 16. Future extensions
- per-workspace encrypted secrets vault
- upload automation templates per channel
- diagnostics compression and sharing
