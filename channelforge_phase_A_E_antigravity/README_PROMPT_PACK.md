# ChannelForge Studio V5.8 — Antigravity Prompt Pack (Phase A → E)

Bộ này được viết để bạn **copy/paste trực tiếp vào Antigravity** theo từng phase, giúp agent code dần dần mà không phá repo.

## Cách dùng khuyến nghị trong Antigravity

1. Mở repo `channelforge-studio-v5`.
2. Chuyển agent sang **Planning mode**.
3. Dán `GLOBAL_RULES_AND_GUARDRAILS.md` trước.
4. Dán `MASTER_ORCHESTRATION_PROMPT.md` để agent hiểu toàn cảnh.
5. Chỉ chạy **một phase tại một thời điểm**:
   - `PHASE_A_FOUNDATION_BOOTSTRAP.md`
   - `PHASE_B_WORKSPACE_NETWORK.md`
   - `PHASE_C_MEDIA_INTELLIGENCE.md`
   - `PHASE_D_AUTOMATION_CONTROLLER.md`
   - `PHASE_E_PACKAGING_RELEASE.md`
6. Sau mỗi phase, bắt agent xuất ra:
   - change plan
   - changed files summary
   - migrations created
   - validation output
   - known limitations
   - next-phase handoff

## Mục tiêu tổng thể

Biến repo hiện tại thành một **desktop-first YouTube channel operating system** có thể:

- quản lý nhiều channel theo workspace riêng
- chạy pipeline nội bộ chủ yếu bằng local resources
- chỉ route browser/network riêng khi mở YouTube Studio hoặc upload/publish
- render video bám nội dung hơn bằng media intelligence
- có automation controller chạy end-to-end
- có packaging/installer/release flow ổn định

## Quy ước bắt buộc

- Không đổi stack nền tảng nếu không thật sự cần thiết.
- Không đụng toàn repo cùng lúc.
- Mỗi phase chỉ làm đúng scope phase đó.
- Ưu tiên thay đổi **tương thích ngược** với cấu trúc đang có.
- Không thêm anti-detect, fingerprint spoofing, automation lách phát hiện, hoặc logic dùng để né policy.
- Cho phép **workspace isolation hợp lệ** + **network policy per workspace**.
- Nếu cần dependency mới, phải cập nhật tài liệu, diagnostics, setup wizard, release checklist.

## Thứ tự thực hiện đề xuất

1. Phase A — Foundation / Bootstrap / Dependency & Readiness
2. Phase B — Workspace Supervisor + Network Policy
3. Phase C — Media Intelligence Layer
4. Phase D — Automation Controller
5. Phase E — Packaging, Installer, Release Hardening

## Kết quả mong đợi sau khi xong cả 5 phase

- app desktop có thể khởi động ổn định
- backend đủ dependency để chạy các module đã khai báo
- workspace per channel sống như runtime riêng có state rõ ràng
- policy mạng phân tách local processing và publish plane
- visual matching đủ tốt để phần lớn scene không lệch nội dung
- scheduler/controller có thể chạy từ idea đến publish queue
- first-run wizard + diagnostics + release build đi được
