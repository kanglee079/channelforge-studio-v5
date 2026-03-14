
# Backend - YouTube Auto Studio V4

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs:
- http://localhost:8000/docs

This backend reuses the V3 pipeline and adds:
- FastAPI admin API
- trend assistant cache + background refresh
- profile CRUD
- queue / worker actions via HTTP
- content library scan
