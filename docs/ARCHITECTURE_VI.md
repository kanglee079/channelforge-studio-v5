
# Kiến trúc đề xuất của YouTube Auto Studio V4

## 1. Core layers
- `Pipeline Core` (giữ từ V3): idea -> research -> script -> voice -> subtitle -> footage -> render -> upload
- `Admin API`: FastAPI để quản trị channel, jobs, content, trends
- `Web UI`: React dashboard
- `Trend Assistant`: thu thập trend từ Google Trends, RSS, GDELT, NewsAPI, SerpApi
- `Research Layer`: Scrapling, Trafilatura, YouTube transcript, Wikipedia
- `Scheduler`: APScheduler quét trend định kỳ
- `Queue`: SQLite + retry/backoff

## 2. Màn hình chính
- Dashboard
- Channels
- Jobs & Queue
- Content Studio
- Trend Radar
- Settings

## 3. Nâng cấp tiếp theo rất nên làm
- auth đăng nhập admin
- WebSocket log streaming
- drag/drop content calendar
- approval workflow trước khi upload
- A/B test title & thumbnail
- scoring engine để chọn idea tốt nhất
- financial dashboard theo channel
- nhiều user / nhiều workspace
