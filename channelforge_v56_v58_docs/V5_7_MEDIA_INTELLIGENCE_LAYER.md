# V5.7 — Media Intelligence Layer (AI-Ready)

## 1. Mục tiêu

Thay Visual Match Engine hiện tại từ mức:
- scene decomposition bằng LLM/fallback
- keyword-based retrieval
- heuristic scoring

thành:
- **Media Intelligence Layer** có semantic retrieval, vector index, rerank, shot planning, fallback strategy, review surface

Mục tiêu cuối:
- footage/hình ảnh **bám sát content hơn rõ rệt**
- có lý do giải thích vì sao asset được chọn
- giảm số scene phải sửa tay

---

## 2. Hiện trạng repo

### 2.1 Các file hiện có
- `engine/app/visual_match/schema.py`
- `engine/app/visual_match/scene_decomposer.py`
- `engine/app/visual_match/scorer.py`

### 2.2 Điểm yếu
- `scene_decomposer.py` chưa sinh scene spec đủ chặt
- `scorer.py` thiên về keyword overlap/quality heuristic
- chưa có asset frame embeddings
- chưa có vector index
- chưa có local asset intelligence
- chưa có shot planner
- chưa có confidence gating đủ mạnh
- chưa có review queue cho semantic mismatch

---

## 3. Kết quả cuối phase

Sau V5.7, mỗi scene phải có pipeline như sau:

```text
script
  → scene decomposition
  → scene spec normalization
  → candidate retrieval (provider + local library)
  → frame extraction / metadata normalization
  → multimodal embeddings
  → vector search
  → rule-based rerank
  → confidence label
  → fallback plan
  → timeline suggestion
  → review item if confidence low
```

---

## 4. Non-goals

Không làm ở phase này:
- generative image/video synthesis mới từ đầu
- full motion graphics editor
- auto deepfake / face synthesis
- editor timeline kiểu Premiere

Được làm:
- still image + motion parallax fallback
- text card fallback
- map/diagram fallback nếu scene không tìm được footage phù hợp
- local asset library intelligence

---

## 5. Kiến trúc mục tiêu

## 5.1 Modules mới

### `engine/app/media_intel/scene_spec_builder.py`
Input:
- raw script
- channel niche
- format
- optional style pack

Output:
- list `SceneSpec`

### `engine/app/media_intel/frame_extractor.py`
- extract representative frames từ candidate video
- lưu thumbnails/cache

### `engine/app/media_intel/embedder.py`
- text embedding cho scene queries
- image embedding cho representative frames
- model adapter để đổi giữa:
  - multilingual CLIP
  - OpenCLIP
  - remote embedding provider nếu sau này cần

### `engine/app/media_intel/index_store.py`
- build/load/save vector index
- metadata store song song
- FAISS preferred; fallback flat search nếu chưa có dependency

### `engine/app/media_intel/retriever.py`
- truy vấn index
- trộn local assets + provider assets
- diversify candidate set

### `engine/app/media_intel/reranker.py`
- semantic similarity
- must-have coverage
- must-not penalty
- mood/style fit
- historical reuse penalty
- aspect ratio fit
- duration fit
- provider trust/licensing rules

### `engine/app/media_intel/shot_planner.py`
- với video asset: chọn clip segment tốt nhất
- với image asset: chọn motion effect fallback
- nếu video dài: chia sub-shots

### `engine/app/media_intel/review_gate.py`
- nếu confidence thấp hoặc mismatch cao → tạo review item

---

## 6. Schema mới

## 6.1 SceneSpec
```python
@dataclass
class SceneSpec:
    scene_index: int
    spoken_text: str
    visual_goal: str
    must_have_objects: list[str]
    must_not_show: list[str]
    mood: str
    location_hint: str
    time_period: str
    camera_style: str
    asset_preference: str
    fallback_strategy: str
    duration_sec: float
    search_queries: list[str]
```

## 6.2 AssetFingerprint
```python
@dataclass
class AssetFingerprint:
    asset_id: str
    provider: str
    asset_type: str
    local_path: str
    preview_frame_paths: list[str]
    width: int
    height: int
    duration_sec: float
    fps: float
    tags: list[str]
    license_notes: str
    embedding_id: str
```

## 6.3 MatchDecision
```python
@dataclass
class MatchDecision:
    scene_index: int
    selected_asset_id: str | None
    selected_segment: tuple[float, float] | None
    confidence_score: float
    confidence_label: str
    reasons: dict
    fallback_used: str | None
    requires_review: bool
```

---

## 7. DB additions

## 7.1 `media_assets`
```sql
CREATE TABLE IF NOT EXISTS media_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_key TEXT UNIQUE NOT NULL,
  provider TEXT NOT NULL,
  source_id TEXT DEFAULT '',
  source_url TEXT DEFAULT '',
  local_path TEXT DEFAULT '',
  asset_type TEXT NOT NULL,
  width INTEGER DEFAULT 0,
  height INTEGER DEFAULT 0,
  duration_sec REAL DEFAULT 0,
  fps REAL DEFAULT 0,
  tags_json TEXT DEFAULT '[]',
  license_notes TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## 7.2 `asset_embeddings`
```sql
CREATE TABLE IF NOT EXISTS asset_embeddings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER NOT NULL,
  frame_path TEXT DEFAULT '',
  model_name TEXT NOT NULL,
  vector_dim INTEGER NOT NULL,
  vector_store_key TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## 7.3 `scene_match_runs`
```sql
CREATE TABLE IF NOT EXISTS scene_match_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER DEFAULT 0,
  channel_name TEXT DEFAULT '',
  model_name TEXT NOT NULL,
  status TEXT NOT NULL,
  summary_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);
```

## 7.4 `scene_match_items`
```sql
CREATE TABLE IF NOT EXISTS scene_match_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  scene_index INTEGER NOT NULL,
  selected_asset_id INTEGER DEFAULT 0,
  confidence_score REAL DEFAULT 0,
  confidence_label TEXT DEFAULT 'low',
  fallback_used TEXT DEFAULT '',
  requires_review INTEGER DEFAULT 0,
  explain_json TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);
```

---

## 8. Local data plane

Tạo thư mục mới:
- `engine/data/media_cache/`
- `engine/data/media_cache/frames/`
- `engine/data/media_cache/index/`
- `engine/data/media_cache/providers/`
- `engine/data/media_cache/projects/`

Quy tắc:
- mọi asset tải về phải có metadata JSON
- mọi video nên có ít nhất 3 representative frames
- embeddings phải cache
- rerun không được embed lại nếu cache chưa invalid

---

## 9. Scene decomposition mới

## 9.1 Thay vì chỉ `visual_intent`, builder phải sinh:
- `visual_goal`
- `search_queries`
- `camera_style`
- `time_period`
- `fallback_strategy`

## 9.2 Logic decomposition
1. Dùng LLM nếu có.
2. Validate schema chặt.
3. Normalize:
   - duration min/max
   - empty objects -> derive từ spoken_text
   - strip duplicates
4. Nếu LLM fail:
   - fallback sentence splitter + noun extraction đơn giản
   - build at least workable SceneSpec

---

## 10. Retrieval strategy

## 10.1 Candidate sources
- local media cache
- Pexels
- Pixabay
- project-specific uploaded assets
- future: user asset packs

## 10.2 Retrieval order
1. local cache theo semantic similarity
2. local cache theo tags/query overlap
3. providers external
4. fallback assets

## 10.3 Query diversification
Mỗi scene phải sinh 3 kiểu query:
- exact intent query
- object-focused query
- mood/location query

---

## 11. Semantic retrieval

## 11.1 Embedding model
Default target:
- multilingual CLIP / sentence-transformers multilingual CLIP text encoder + image encoder compatibility

Fallback:
- OpenCLIP
- no-embedding heuristic mode nếu optional deps chưa cài

## 11.2 Vector index
Preferred:
- FAISS index stored on disk

Fallback:
- brute-force cosine similarity trên số lượng nhỏ

## 11.3 Similarity pipeline
- embed scene text query
- retrieve top-k image/video frames
- aggregate per asset
- normalize score 0..1
- pass sang reranker

---

## 12. Reranking rules

Final score gợi ý:
```text
final_score =
  semantic_score * 0.45
+ must_have_score * 0.20
+ mood_style_score * 0.10
+ quality_score * 0.10
+ aspect_ratio_fit * 0.05
+ duration_fit * 0.05
- negative_penalty * 0.03
- duplicate_penalty * 0.02
```

### Mandatory penalties
- missing must-have object
- contains blocked keywords
- watermark hints
- too short duration
- portrait asset for landscape project (or ngược lại)
- reused too recently in same channel

### Confidence labels
- `high`: final_score >= 0.82
- `medium`: 0.65–0.819
- `low`: < 0.65

Low confidence:
- auto create review item
- fallback strategy nếu có

---

## 13. Shot Planner

## 13.1 Với video
- extract representative frames
- nếu candidate video dài, chọn segment gần với motion/content peaks
- mặc định segment length = scene duration ± tolerance
- nếu không xác định được segment tốt, dùng head segment hoặc mid segment nhưng phải đánh confidence thấp hơn

## 13.2 Với image
- chọn effect:
  - pan-left
  - pan-right
  - zoom-in
  - zoom-out
  - parallax-light
- effect phụ thuộc mood + scene duration

## 13.3 Fallback ladder
1. video semantic match
2. image semantic match + motion
3. local template background
4. text/emphasis card
5. manual review required

---

## 14. Review integration

Tích hợp với bảng `review_items` có sẵn.

Tạo review item khi:
- confidence thấp
- must_have coverage < threshold
- only fallback assets found
- scene contains highly specific named entity nhưng candidate không chắc chắn
- multiple candidates tie score quá gần

Review payload phải gồm:
- scene spec
- top 5 candidates
- explain scores
- selected candidate
- fallback reason

---

## 15. API mới

### `POST /api/v2/media-intel/index/rebuild`
Rebuild local vector index.

### `POST /api/v2/media-intel/assets/ingest`
Ingest asset vào cache/index.

### `GET /api/v2/media-intel/assets`
List asset cache.

### `POST /api/v2/media-intel/match/run`
Run match cho project/script/channel.

### `GET /api/v2/media-intel/match/runs`
List runs.

### `GET /api/v2/media-intel/match/runs/{run_id}`
Get run details.

### `POST /api/v2/media-intel/match/runs/{run_id}/pin`
Pin candidate cho scene.

### `POST /api/v2/media-intel/match/runs/{run_id}/retry-scene`
Retry một scene.

### `POST /api/v2/media-intel/index/warmup`
Precompute embeddings cho recent assets.

---

## 16. UI cần thêm

## 16.1 Trang mới
- `src/pages/MediaIntelligencePage.tsx`

## 16.2 Khu vực chính
### A. Index Health
- số asset đã index
- số embedding
- model đang dùng
- last rebuild
- disk usage

### B. Match Runs
- run list
- channel
- project
- status
- matched scenes
- review scenes

### C. Scene Inspector
Cho từng scene:
- spoken text
- visual goal
- candidate cards
- selected asset
- explain breakdown
- confidence
- pin/replace/retry buttons

### D. Asset Library
- search/filter assets
- provider
- local path
- tags
- preview frames
- ingest new asset

---

## 17. File change map

### Create
- `engine/app/media_intel/__init__.py`
- `engine/app/media_intel/scene_spec_builder.py`
- `engine/app/media_intel/frame_extractor.py`
- `engine/app/media_intel/embedder.py`
- `engine/app/media_intel/index_store.py`
- `engine/app/media_intel/retriever.py`
- `engine/app/media_intel/reranker.py`
- `engine/app/media_intel/shot_planner.py`
- `engine/app/media_intel/review_gate.py`
- `engine/app/routers/media_intel.py`
- `src/pages/MediaIntelligencePage.tsx`
- `src/components/media-intel/*`
- tests for each module

### Modify
- `engine/app/visual_match/schema.py`
- `engine/app/visual_match/scene_decomposer.py`
- `engine/app/visual_match/scorer.py`
- `engine/app/main.py`
- `engine/requirements-optional.txt`
- navigation/sidebar in frontend

---

## 18. Dependency strategy

### Required optional deps
- `scenedetect[opencv]`
- `faiss-cpu` (or conditional)
- `sentence-transformers`
- `torch`
- `Pillow`
- maybe `opencv-python-headless`

### Graceful fallback
Nếu optional deps chưa có:
- app vẫn chạy
- UI phải báo “heuristic mode”
- match run vẫn possible nhưng đánh dấu degraded quality mode

---

## 19. Acceptance criteria

- Có thể ingest 100+ assets local.
- Có thể build vector index local.
- Có thể chạy 1 match run cho script 10 scenes.
- Mỗi scene có top 5 candidates + explain.
- Ít nhất 70% scenes có confidence >= medium trên sample benchmark nội bộ.
- Low confidence scenes tự đẩy vào review queue.
- Có UI để pin candidate cho scene.
- Có cache reuse giữa nhiều run.

---

## 20. Test plan

### Unit
- scene spec normalization
- embedding cache
- reranker scoring
- fallback ladder
- confidence labeling

### Integration
- ingest assets -> build index -> run match -> review items generated
- rerun after cache warmup faster than first run
- optional dependency missing -> heuristic mode still works

### Manual
- chạy match run từ UI
- xem preview scene
- pin/retry candidate
- render thử timeline với asset đã chọn

---

## 21. Anti-regression constraints

- Không xóa heuristic scorer cũ ngay; giữ làm fallback.
- Không hardcode một embedding model duy nhất.
- Không buộc GPU.
- Không để build index khóa UI quá lâu; phải background job hoặc async task.
- Không bỏ qua licensing/provider notes.

---

## 22. Handoff note

AI coder phải xuất:
- sample benchmark script + kết quả match
- ảnh chụp Scene Inspector
- thống kê cache hit / index size / median run time
