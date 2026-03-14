# V5 AI Execution Brief

AI coder phải xem toàn bộ bộ tài liệu V5 trước khi code.

## Quy tắc bắt buộc

1. Không rewrite toàn bộ project trong một commit.
2. Phải đi theo từng epic và từng task.
3. Mỗi task phải cập nhật cả backend types lẫn frontend types nếu liên quan.
4. Nếu thêm DB schema mới phải có migration.
5. Không được bỏ qua review queue cho các trường hợp confidence thấp/rủi ro cao.
6. Không triển khai anti-detect, fingerprint spoofing, stealth bypass.
7. Mọi provider mới phải qua adapter interface.
8. Mọi hành động dài phải có progress event.
9. Mọi file generated phải trace được source/project/channel.
10. Nếu có điểm mơ hồ, ưu tiên giải pháp an toàn, desktop-first, local-first, channel-first.

## Ưu tiên build

1. Workspace Engine
2. Visual Match Engine
3. Research Assistant 2.0
4. Review + Cost Router
5. Desktop packaging hardening

## Output expected from AI coder

Mỗi phase phải xuất ra:
- changed files list
- migration notes
- env/config changes
- testing steps
- known limitations
- next recommended tasks
