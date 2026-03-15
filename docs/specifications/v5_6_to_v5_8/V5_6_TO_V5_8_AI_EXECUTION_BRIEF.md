# V5.6–V5.8 AI Execution Brief for Antigravity / Cursor

## 1. Cách làm việc bắt buộc

- Chỉ làm **một epic tại một thời điểm**.
- Không sửa toàn repo trong một lần.
- Mỗi lần commit phải có:
  - mục tiêu
  - file sửa
  - migration nếu có
  - test plan
  - rollback note

## 2. Thứ tự bắt buộc

1. Epic 1 — Workspace Supervisor + Network Policy Manager
2. Epic 2 — Media Intelligence Layer
3. Epic 3 — Packaging & Installer Hardening

## 3. Prompt discipline

Mỗi run với AI coder phải nói rõ:
- chỉ sửa những file nào
- không được refactor unrelated modules
- giữ backward compatibility cho API/UI hiện có nếu chưa migrate xong

## 4. Phase output format bắt buộc

AI coder phải trả về:
1. Summary
2. File changes
3. Migrations
4. Risks
5. Test instructions
6. Next step

## 5. Repo safety rules

- Không đổi tên thư mục lớn nếu không có lý do cực mạnh.
- Không xóa API cũ đang dùng trong UI hiện tại.
- Không đưa optional dependency thành hard dependency nếu chưa có fallback.
- Không để startup import optional modules dễ fail toàn app.
- Không hardcode secrets / routes / paths.

## 6. Specific instructions for Epic 1

- Ưu tiên backend runtime registry trước UI polishing.
- Không viết anti-detect.
- Dùng persistent context per workspace.
- Tạo policy resolver rõ ràng DIRECT / WORKSPACE_ROUTE / BLOCK.
- Chỉ upload/studio jobs mới đi route workspace.

## 7. Specific instructions for Epic 2

- Không bỏ heuristic mode cũ ngay.
- Embeddings phải cache.
- Index phải rebuild/warmup được.
- Low confidence phải vào review queue.

## 8. Specific instructions for Epic 3

- Tách dev mode và release mode rõ ràng.
- Ưu tiên packaged sidecar.
- Diagnostics phải giúp user tự biết đang thiếu gì.
- Không yêu cầu user đoán lỗi sidecar.

## 9. Definition of done theo mỗi epic

### Epic 1 Done
- runtime endpoints hoạt động
- session verify hoạt động
- route policy events hoạt động
- UI xem được runtime + route state

### Epic 2 Done
- asset ingest/index hoạt động
- match run hoạt động
- scene inspector hoạt động
- review items auto tạo khi confidence thấp

### Epic 3 Done
- diagnostics đầy đủ
- packaged startup flow rõ ràng
- support bundle export được
- smoke test release pass
