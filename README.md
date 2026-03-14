
# YouTube Auto Studio V4

Bản nâng cấp từ pipeline CLI thành **ứng dụng quản trị có giao diện**.

## Có gì trong bản này
- FastAPI backend
- React frontend
- quản lý channels / niche / queue / content library
- trend assistant quét Google Trends / GDELT / NewsAPI / SerpApi
- nền pipeline V3 vẫn giữ nguyên
- background scheduler để refresh trend cache
- docs setup, api key, chi phí, kiến trúc bằng tiếng Việt

## Chạy nhanh
### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows dùng .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Tài liệu
- `docs/SETUP_VI.md`
- `docs/API_KEYS_VI.md`
- `docs/COSTS_VI.md`
- `docs/ARCHITECTURE_VI.md`
- `docs/LIBRARIES_VI.md`

## Lưu ý quan trọng
- Không tích hợp logic lách quota / lách rate limit bằng cách spam nhiều tài khoản.
- Thay vào đó dự án hỗ trợ nhiều provider hợp lệ + local models để tối ưu chi phí.
