# ChannelForge Studio v5.8

**Nền tảng tự động hóa YouTube toàn diện** — Nghiên cứu xu hướng, tạo nội dung, sản xuất video, quản lý kênh, phân tích hiệu suất.

Desktop app (Tauri + React + Python FastAPI).

---

## Tính Năng Chính

### 📊 Dashboard
- Tổng quan tất cả kênh: video, lượt xem, doanh thu
- Biểu đồ thống kê theo thời gian
- Cảnh báo kênh cần chú ý

### 📺 Quản Lý Kênh
- Tạo/quản lý nhiều kênh YouTube
- Profile isolation — mỗi kênh workspace riêng biệt
- Trạng thái kênh: active / paused / archived

### 🌐 Workspace Supervisor (V5.6)
- Quản lý lifecycle browser: open / close / relaunch / force-kill
- Session verification với YouTube Studio
- Network Policy Manager: DIRECT / WORKSPACE_ROUTE / BLOCK per job type
- Route binding (proxy profile per workspace)
- Policy audit trail

### 📡 Nghiên Cứu Xu Hướng
- Trend discovery đa nền tảng
- Watchlist theo dõi chủ đề
- Phân tích competitor
- Research snapshots lưu lịch sử

### ✍️ Nội Dung & Script
- AI script generation (OpenAI GPT)
- Hệ thống template video
- Scene Planner: phân cảnh chi tiết
- Lịch đăng bài tự động

### 🧠 Media Intelligence (V5.7)
- Semantic retrieval: vector search cho assets
- Scene Spec Builder → Retriever → Reranker → Shot Planner
- Multi-factor scoring (7 sub-scores + 2 penalties)
- Confidence labels (high / medium / low)
- Auto review gate khi confidence thấp
- Hỗ trợ CLIP + FAISS (optional) — fallback heuristic mode khi chưa cài

### 🎬 Sản Xuất Video
- Pipeline: script → media match → render → upload
- FFmpeg-based rendering
- Pexels / Pixabay media providers
- ElevenLabs TTS integration

### ✅ Review Center
- Duyệt nội dung trước khi xuất bản
- Filter theo severity / status
- Tích hợp với Media Intelligence review gate

### 📈 Analytics & Chi Phí
- Thống kê API cost per provider
- Token usage tracking
- Biểu đồ chi phí theo thời gian
- Ước tính ROI per kênh

### 🏥 Chẩn Đoán & Đóng Gói (V5.8)
- System health checks (OS, Python, FFmpeg, DB, Playwright)
- Dependency matrix
- Migration status / runner
- First-Run Setup Wizard (7 bước kiểm tra tự động)
- Support Bundle export (sanitized — không chứa credentials)

### ⚙️ Cài Đặt
- API keys management (OpenAI, Pexels, Pixabay, ElevenLabs)
- FFmpeg path configuration
- System diagnostics

---

## Cấu Trúc Project

```
channelforge-studio-v5/
├── src/                          ← Frontend (React + TypeScript)
│   ├── pages/                    ← 16 pages
│   ├── components/               ← UI components
│   ├── api/                      ← API client
│   └── App.tsx                   ← Router
│
├── engine/                       ← Backend (Python + FastAPI)
│   ├── app/
│   │   ├── routers/              ← API endpoints
│   │   │   ├── workspaces.py     ← Workspace + V5.6 endpoints
│   │   │   ├── media_intel.py    ← V5.7 Media Intelligence
│   │   │   ├── system.py         ← V5.8 Diagnostics + System
│   │   │   ├── research_v5.py    ← Trends + Research
│   │   │   ├── content.py        ← Content management
│   │   │   └── ...
│   │   ├── services/             ← Business logic
│   │   │   ├── workspace_supervisor.py
│   │   │   ├── network_policy_manager.py
│   │   │   ├── workspace_verifier.py
│   │   │   ├── diagnostics.py
│   │   │   └── ...
│   │   ├── media_intel/          ← V5.7 modules
│   │   │   ├── scene_spec_builder.py
│   │   │   ├── embedder.py
│   │   │   ├── index_store.py
│   │   │   ├── retriever.py
│   │   │   ├── reranker.py
│   │   │   ├── shot_planner.py
│   │   │   ├── review_gate.py
│   │   │   └── frame_extractor.py
│   │   ├── migrations/           ← DB migrations (001-007)
│   │   ├── db.py                 ← SQLite + auto migration
│   │   └── main.py               ← FastAPI app
│   └── .venv/                    ← Python virtual environment
│
├── src-tauri/                    ← Desktop shell (Tauri v2)
├── scripts/                      ← Build & release scripts
├── docs/                         ← Documentation
└── package.json
```

---

## Cách Chạy (Development)

### Yêu Cầu
- **Node.js** >= 18
- **Python** >= 3.11
- **FFmpeg** (cho render video)
- **Rust** + Tauri CLI (cho desktop app)

### 1. Cài dependencies

```bash
# Frontend
npm install

# Backend
cd engine
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements/base.txt      # Core only
pip install -r requirements/browser.txt   # + Playwright
pip install -r requirements/media.txt     # + Video/audio
pip install -r requirements/ai.txt        # + AI/ML (optional)
# Hoặc cài tất cả:
pip install -r requirements/all.txt
```

### 2. Cấu hình API keys

Tạo file `engine/.env`:
```env
OPENAI_API_KEY=sk-xxx
PEXELS_API_KEY=xxx
PIXABAY_API_KEY=xxx
ELEVENLABS_API_KEY=xxx
```

### 3. Chạy Backend

```bash
cd engine
.venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend sẽ tự tạo database + chạy migrations khi khởi động.

### 3.5. Kiểm tra môi trường (Doctor)

```bash
python scripts/doctor.py
```

Doctor kiểm tra: Python, Node.js, FFmpeg, packages, DB, .env, Playwright, version sync.
Báo rõ PASS / WARN / FAIL + cách fix cho từng mục.

### 4. Chạy Frontend (Dev)

```bash
npm run dev
```

Mở browser: `http://localhost:5173`

### 5. Chạy Desktop App (Dev)

```bash
npm run tauri dev
```

---

## Đóng Gói Desktop (.exe)

### Bước 1: Build engine sidecar

```bash
# Cài PyInstaller
pip install pyinstaller

# Build engine thành executable
python scripts/build_engine_sidecar.py --target windows
```

Output: `src-tauri/binaries/channelforge-engine-x86_64-pc-windows-msvc.exe`

### Bước 2: Build desktop app

```bash
npm run tauri build
```

Output: `src-tauri/target/release/bundle/msi/ChannelForge Studio_*.msi`

### Bước 3: Kiểm tra trước release

```bash
python scripts/release/check_release.py
```

Kiểm tra: version sync, TypeScript 0 errors, migrations, sidecar binary.

### Lưu Ý Đóng Gói
- User cuối **không cần** cài Python — engine sidecar đã bundle sẵn
- FFmpeg: bundle kèm hoặc hướng dẫn cài qua First-Run Wizard
- Hỗ trợ: Windows (.msi), macOS (.dmg), Linux (.AppImage)

---

## API Endpoints Tổng Quan

| Nhóm | Prefix | Endpoints |
|-------|--------|-----------|
| Health | `/api/health` | 1 |
| Channels | `/api/v2/channels` | 5 |
| Workspaces | `/api/v2/workspaces` | 20+ |
| Research | `/api/v2/research` | 8 |
| Content | `/api/v2/content` | 6 |
| Templates | `/api/v2/templates` | 5 |
| Visual Match | `/api/v2/visual-match` | 4 |
| Trends | `/api/v5/trends` | 6 |
| Review/Analytics/Cost | `/api/v5/review`, `/analytics`, `/cost` | 9 |
| Media Intelligence | `/api/v2/media-intel` | 9 |
| System/Diagnostics | `/api/v5/system` | 10+ |

---

## Database

SQLite (`engine/data/channelforge.db`) — tự động tạo khi khởi động.

| Migration | Nội dung |
|-----------|---------|
| 001 | Core workspace tables |
| 002 | Proxy profile management |
| 003 | Audit logging |
| 004 | V5 entities (content, research, templates, etc.) |
| 005 | V5.6 Workspace Supervisor + Network Policy |
| 006 | V5.7 Media Intelligence |
| 007 | V5.8 App config + Crash logs |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop Shell | Tauri v2 (Rust) |
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python 3.11+ + FastAPI + SQLite |
| Video Render | FFmpeg |
| AI | OpenAI GPT API |
| TTS | ElevenLabs API |
| Media | Pexels + Pixabay APIs |
| Browser | Playwright (workspace automation) |
| Optional | CLIP, FAISS, sentence-transformers (semantic search) |

---

## License

Private — © 2024-2026 KangLee
