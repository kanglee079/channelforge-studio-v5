
# Các tài khoản cần tạo, cách lấy API key, OAuth

## 1) OpenAI
### Dùng để:
- viết script
- TTS nếu chọn OpenAI voice
- thumbnail text / image nếu bật AI thumbnail
- moderation / transcription tùy cấu hình

### Cách tạo:
1. Tạo tài khoản tại OpenAI Platform
2. Vào Billing nạp tiền API
3. Vào API keys tạo key mới
4. Điền vào `.env`:
```env
OPENAI_API_KEY=...
# hoặc nhiều key hợp lệ do bạn sở hữu
OPENAI_API_KEYS=key1,key2
```

## 2) ElevenLabs
### Dùng để:
- giọng đọc chất lượng cao

### Cách tạo:
1. Tạo tài khoản ElevenLabs
2. Chọn plan phù hợp
3. Tạo API key
4. Lấy `voice_id` của giọng bạn muốn dùng
5. Điền vào `.env`
```env
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

## 3) Pexels
### Dùng để:
- stock footage free

### Cách tạo:
1. Tạo tài khoản Pexels
2. Xin API key
3. Điền vào `.env`
```env
PEXELS_API_KEY=...
```

## 4) Pixabay
### Dùng để:
- video/images backup khi Pexels thiếu footage

### Cách tạo:
1. Tạo tài khoản Pixabay
2. Lấy API key trong account
3. Điền vào `.env`
```env
PIXABAY_API_KEY=...
```

## 5) YouTube Data API + OAuth
### Dùng để:
- upload video
- schedule publish
- set metadata
- thumbnail upload nếu bật

### Tạo project:
1. Đăng nhập Google Cloud Console
2. Tạo project mới
3. Enable `YouTube Data API v3`
4. Tạo OAuth consent screen
5. Tạo OAuth Client ID kiểu Desktop App
6. Tải file JSON về, đặt tên `client_secret.json`
7. Đặt vào thư mục `backend/`
8. Trong `.env`:
```env
YOUTUBE_CLIENT_SECRETS=client_secret.json
YOUTUBE_TOKEN_JSON=token.json
UPLOAD_TO_YOUTUBE=true
```

### Lần đầu xác thực:
- Chạy flow OAuth của module upload hoặc script cấp quyền
- File `token.json` sẽ được tạo ra sau khi đăng nhập Google

## 6) NewsAPI
### Dùng để:
- quét tin nóng theo niche

```env
NEWSAPI_KEY=...
```

## 7) SerpApi
### Dùng để:
- truy vấn Google Trends / SERP dễ hơn khi muốn scale

```env
SERPAPI_KEY=...
```
