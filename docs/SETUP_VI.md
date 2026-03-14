
# Setup cụ thể từ đầu đến chạy được app

## 1) Cài phần mềm nền
### Windows
- Cài Python 3.11 hoặc 3.12
- Cài Node.js 20 LTS
- Cài FFmpeg và thêm vào PATH
- Cài Git

### macOS
```bash
brew install python@3.12 node ffmpeg git
```

## 2) Chuẩn bị backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

## 3) Chạy backend
```bash
uvicorn app.main:app --reload --port 8000
```

## 4) Chạy frontend
```bash
cd ../frontend
npm install
npm run dev
```

## 5) Mở giao diện
- UI: http://localhost:5173
- API docs: http://localhost:8000/docs

## 6) Tạo profile channel đầu tiên
- Vào trang `Channels`
- Điền `name`, `niche`, `language`, `format`
- Bật `upload_enabled` nếu đã xong OAuth YouTube

## 7) Tạo job
- Vào `Jobs & Queue`
- Chọn channel
- Điền niche hoặc seed topic
- Bấm `Enqueue`
- Bấm `Run worker`

## 8) Theo dõi nội dung
- `Content Studio`: xem file output, title, tags, upload result
- `Trend Radar`: quét xu hướng mới theo geo và niche

## 9) Build production
### Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
npm run build
```

Sau khi build frontend xong, backend có thể serve static từ `frontend/dist`.
