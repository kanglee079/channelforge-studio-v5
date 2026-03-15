# ChannelForge Studio V5 — Tổng kết tính năng

> **Ứng dụng desktop cho người Việt** vận hành nhiều kênh YouTube ngoại ngữ. Video tiếng Anh, tool tiếng Việt.

---

## Kiến trúc hệ thống

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|---------|
| **Vỏ desktop** | Tauri 2 (Rust) | Đóng gói thành `.exe`, quản lý vòng đời backend |
| **Giao diện** | React + TypeScript + Vite | 14 trang, dark theme chuyên nghiệp, 100% tiếng Việt |
| **Máy chủ nội bộ** | Python FastAPI | Xử lý pipeline, gọi API, quản lý job queue |
| **Cơ sở dữ liệu** | SQLite | Local-first, tự chạy migration, không cần server DB |
| **Trình duyệt** | Playwright (Chromium) | Mỗi kênh có browser riêng biệt, cookie tách rời |
| **Render video** | FFmpeg | Ghép hình/video + giọng đọc + phụ đề → file MP4 |

---

## 14 Module chức năng

### 📊 1. Tổng quan (Dashboard)
- Thống kê nhanh: tổng jobs, số kênh, đang chờ, hoàn thành, thất bại
- Bảng jobs gần đây kèm trạng thái
- Danh sách kênh với niche và ngôn ngữ

### 📺 2. Quản lý kênh (Channels)
- Tạo/sửa kênh YouTube với đầy đủ cấu hình:
  - Tên, niche (chủ đề), ngôn ngữ video
  - Định dạng mặc định (shorts/long)
  - Tags, từ bị chặn
  - Khoảng cách upload, giới hạn upload/ngày
  - YouTube API credentials (client secrets, token)
- Bật/tắt upload tự động cho từng kênh
- Ghi nhận AI tạo (disclosure)

### 🌐 3. Trình duyệt riêng biệt (Workspaces)
- Mỗi kênh có workspace (Playwright browser) riêng:
  - Cookie, localStorage, IndexedDB tách biệt hoàn toàn
  - Đăng nhập YouTube Studio 1 lần, session được lưu lại
- Tạo workspace → gắn với kênh → mở trình duyệt
- Theo dõi trạng thái: Mới tạo / Đang hoạt động / Hết hạn

### ⚙️ 4. Hàng đợi sản xuất (Jobs & Queue)
- Xem toàn bộ jobs đang trong queue với trạng thái rõ ràng
- Chạy 1 job thủ công bằng nút bấm
- Trạng thái tiếng Việt: Chờ xử lý → Đang chạy → Hoàn thành / Thất bại

### 📡 5. Radar xu hướng (Trends)
- Nhập niche + quốc gia → quét xu hướng nội dung
- Kết quả: chủ đề nóng, điểm trending, gợi ý góc tiếp cận
- Nguồn: Google Trends, YouTube trending, tin tức

### 📚 6. Thư viện nghiên cứu (Research Library)
- Nhập URL → tự trích xuất nội dung sạch bằng Trafilatura
- Lưu trữ tài liệu nghiên cứu cho từng kênh
- Xem chi tiết: tiêu đề, nguồn, extractor, full text preview
- Xóa tài liệu không cần thiết

### ✍️ 7. Nội dung (Content Studio)
**Pipeline 3 bước:**

| Bước | Mô tả | Hành động |
|------|-------|-----------|
| **Ý tưởng** | Inbox ý tưởng video mới | Thêm → Approve → Tạo Brief |
| **Brief** | Mô tả chi tiết video cần làm | Format, thời lượng, giọng đọc, CTA |
| **Script** | Bản script hoàn chỉnh | Tạo thủ công hoặc **AI tạo bằng OpenAI** |

- Form thêm ý tưởng: chọn kênh, tiêu đề, góc tiếp cận, nguồn
- AI tạo script tự động từ brief + brand voice của kênh
- Theo dõi số từ, thời lượng ước tính, trạng thái fact-check

### 🎬 8. Sản xuất video (Video Factory)
- Stat grid: Tổng jobs, Chờ xử lý, Đang chạy, Hoàn thành, Thất bại
- Chạy pipeline: chọn kênh (hoặc tất cả), số jobs cần xử lý
- Danh sách video đã hoàn thành với đường dẫn file
- Bảng hàng đợi chi tiết

**Pipeline tự động:**
```
Job → Nghiên cứu → Viết script → TTS giọng đọc → Tìm hình/video → Ghép + render → Output MP4
```

### 🎨 9. Mẫu video (Templates)
5 bộ mẫu có sẵn:

| Template | Loại | Thời lượng | Mô tả |
|----------|------|-----------|-------|
| `shorts_facts` | Ngắn | 30-60s | Hook → facts → CTA |
| `infographic_explainer` | Ngắn | 30-90s | Text overlays + animations |
| `documentary_mini` | Dài | 5-15 phút | Mini documentary nhiều chương |
| `slideshow_top10` | Dài | 5-10 phút | Countdown top 10 |
| `talking_head_faceless` | Dài | 3-10 phút | Voiceover + B-roll |

- Xem chi tiết config: độ phân giải, FPS, phụ đề, hình ảnh, hiệu ứng
- Lọc theo loại: Video ngắn / Video dài
- Tạo mẫu tùy chỉnh của riêng mình

### 📅 10. Lịch đăng (Upload Calendar)
- Jobs nhóm theo từng kênh
- Thống kê: Sẵn sàng upload / Đang chờ xử lý / Số kênh
- Theo dõi trạng thái upload cho từng video

### 📈 11. Thống kê (Analytics)
- Tỷ lệ hoàn thành và thất bại dạng phần trăm
- Phân tích sản lượng theo kênh (jobs/tỷ lệ)
- Phân tích theo trạng thái (queued/done/failed)

### 💰 12. Quản lý chi phí (Cost Control)
- Quy tắc chọn provider cho từng tác vụ:
  - **Viết Script** → OpenAI (chất lượng cao)
  - **Giọng đọc** → OpenAI TTS → ElevenLabs → Kokoro → Piper
  - **Phiên âm** → faster-whisper local (tiết kiệm)
  - **Brainstorm** → Ollama local (miễn phí)
  - **Hình ảnh** → Pexels / Pixabay (miễn phí)
- Theo dõi chi phí thực tế khi pipeline chạy

### ⚙️ 13. Cài đặt (Settings)
- Trạng thái API key cho từng provider (có key / chưa cài)
- Thứ tự ưu tiên provider theo pipeline step
- OpenAI, ElevenLabs, Pexels, Pixabay, NewsAPI, SerpAPI

### 📋 14. Nhật ký (Logs)
- Ghi nhận: Pipeline, Provider calls, Trình duyệt, Upload
- Audit trail cho mọi thao tác

---

## Quy trình vận hành

```
1. Tạo kênh  →  Cấu hình niche, ngôn ngữ, tags
2. Tạo workspace  →  Đăng nhập YouTube Studio
3. Quét xu hướng  →  Tìm ý tưởng video hot
4. Thêm ý tưởng  →  Approve → Tạo brief
5. Tạo script  →  AI viết từ brief + brand voice
6. Chạy pipeline  →  TTS + hình + render = Video MP4
7. Upload  →  Tự động qua YouTube API (hoặc thủ công)
8. Theo dõi  →  Thống kê, chi phí, logs
```

---

## Yêu cầu cài đặt

| Phần mềm | Phiên bản | Ghi chú |
|-----------|-----------|---------|
| Node.js | 22+ | Vite dev server + Tauri CLI |
| Python | 3.11+ | FastAPI backend |
| Rust | 1.94+ | Tauri 2 desktop build |
| FFmpeg | 6+ | Render video |
| Chromium | auto | Playwright tự cài |

### API Keys cần thiết (file [.env](file:///c:/dev/youtube_auto_v4_studio/backend/.env) trong `engine/`)
| Provider | Bắt buộc | Dùng cho |
|----------|---------|---------|
| OpenAI | ✅ | Script, TTS, nghiên cứu |
| ElevenLabs | Tùy chọn | Giọng đọc thay thế |
| Pexels | ✅ | Stock video/images |
| Pixabay | Tùy chọn | Fallback stock media |

---

## Cách chạy

```bash
# Bước 1: Khởi động máy chủ backend
cd engine
.venv\Scripts\activate
python -m uvicorn app.main:app --port 8000

# Bước 2: Chạy giao diện (web mode)
npm run dev                    # → http://localhost:1420

# Hoặc: Chạy ứng dụng desktop (Tauri)
npm run tauri dev              # → cửa sổ desktop native
```

---

## Cấu trúc thư mục

```
youtube_auto_v4_studio/
├── src-tauri/              # Tauri 2 desktop shell
│   ├── tauri.conf.json     # Cấu hình app (tên, cửa sổ, CSP)
│   └── src/lib.rs          # Sidecar lifecycle (tự start/stop Python)
├── src/                    # React frontend (14 trang tiếng Việt)
│   ├── components/         # Sidebar, Card, FormField
│   ├── layouts/            # ShellLayout (topbar + sidebar)
│   ├── pages/              # 14 trang chức năng
│   ├── api/                # API client typed
│   └── styles/             # CSS design system (dark theme)
├── engine/                 # Python backend (FastAPI)
│   ├── app/main.py         # Điểm khởi động, đăng ký routers
│   ├── app/db.py           # SQLite + migration system
│   ├── app/routers/        # API routers (api, workspaces, research, content, templates)
│   ├── app/services/       # Workspace manager (Playwright)
│   ├── app/migrations/     # SQL migration scripts
│   └── profiles/           # Channel profile YAML files
├── package.json            # Root monorepo config
├── vite.config.ts          # Vite + proxy to backend
└── tsconfig.json           # TypeScript config
```

---

## Trạng thái hoàn thiện

| Module | Backend | Frontend | Trạng thái |
|--------|---------|----------|-----------|
| Tổng quan | ✅ | ✅ | Hoạt động bình thường |
| Quản lý kênh | ✅ | ✅ | CRUD đầy đủ |
| Trình duyệt | ✅ | ✅ | Playwright launch OK |
| Hàng đợi | ✅ | ✅ | Pipeline đã test OK |
| Xu hướng | ✅ | ✅ | Quét trending hoạt động |
| Nghiên cứu | ✅ | ✅ | URL extraction OK |
| Nội dung | ✅ | ✅ | AI script generation OK |
| Sản xuất video | ✅ | ✅ | Worker + render OK |
| Mẫu video | ✅ | ✅ | 5 mẫu có sẵn |
| Lịch đăng | ✅ | ✅ | Nhóm theo kênh |
| Thống kê | ✅ | ✅ | Phân tích đầy đủ |
| Chi phí | ⚠️ | ✅ | UI sẵn, tracking chưa ghi nhận |
| Cài đặt | ✅ | ✅ | API status hiển thị đúng |
| Nhật ký | ⚠️ | ✅ | UI sẵn, log filtering chưa có |

> ✅ = Hoạt động đầy đủ | ⚠️ = UI sẵn, backend cần bổ sung thêm

---

## Ảnh giao diện

````carousel
![Tổng quan — sidebar tiếng Việt, stat grid, jobs gần đây, danh sách kênh](C:\Users\ADMIN\.gemini\antigravity\brain\172db6f4-9b0c-4e53-a9b2-4732a133e9a7\vi_dashboard_1773479534633.png)
<!-- slide -->
![Nội dung — pipeline Ý tưởng → Brief → Script, form thêm ý tưởng](C:\Users\ADMIN\.gemini\antigravity\brain\172db6f4-9b0c-4e53-a9b2-4732a133e9a7\vi_content_studio_1773479544596.png)
<!-- slide -->
![Sản xuất video — stat grid tiếng Việt, pipeline runner, video đã xong](C:\Users\ADMIN\.gemini\antigravity\brain\172db6f4-9b0c-4e53-a9b2-4732a133e9a7\vi_video_factory_1773479554474.png)
````

![Demo quá trình duyệt giao diện tiếng Việt](C:\Users\ADMIN\.gemini\antigravity\brain\172db6f4-9b0c-4e53-a9b2-4732a133e9a7\vietnamese_ui_verify_1773479490855.webp)
