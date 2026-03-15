# V5.1 — Visual Match Engine

## 1. Mục tiêu

Visual Match Engine giải quyết pain point lớn nhất hiện tại: **video render ra nhưng hình ảnh/footage không bám sát nội dung**.

Module này biến pipeline từ:

`script -> keyword search -> ghép clip`

thành:

`script -> scene intent -> candidate retrieval -> semantic scoring -> shot planning -> review -> render`

## 2. Kết quả mong muốn

- mỗi scene có clip/ảnh tương ứng phù hợp hơn với nội dung nói;
- giảm footage generic, lệch chủ đề hoặc lặp lại;
- cho phép fallback thông minh khi không tìm thấy footage tốt;
- cung cấp explainability: vì sao engine chọn asset đó.

## 3. Functional requirements

### 3.1 Scene decomposition
Từ script project, engine phải tách được script thành nhiều scene.

Mỗi scene phải có schema:

```json
{
  "scene_index": 1,
  "spoken_text": "...",
  "visual_intent": "close-up of shark teeth / underwater predator motion",
  "must_have_objects": ["shark", "ocean"],
  "must_not_show": ["cartoon", "human presenter"],
  "mood": "dramatic",
  "location_hint": "ocean",
  "time_period": "modern",
  "asset_preference": "video",
  "fallback_strategy": "photo_parallax"
}
```

### 3.2 Candidate retrieval
Cho mỗi scene, engine phải lấy candidate từ:
- local asset library
- Pexels
- Pixabay
- curated internal packs
- optional image search provider sau này

### 3.3 Candidate preprocessing
Mỗi candidate phải được:
- đọc metadata;
- sinh thumbnails representative frames;
- kiểm tra duration/aspect ratio/resolution;
- detect watermark thô nếu có;
- chuẩn hóa tags/provider/license notes.

### 3.4 Semantic scoring
Mỗi candidate phải được chấm điểm theo nhiều lớp:

#### Điểm thành phần
- `semantic_score` — độ gần nghĩa giữa visual intent và candidate
- `object_match_score` — có chứa object bắt buộc không
- `negative_penalty` — có vi phạm must_not_show không
- `quality_score` — độ sắc nét/resolution/composition cơ bản
- `style_match_score` — tone/mood có hợp channel style không
- `novelty_penalty` — clip đã dùng quá nhiều chưa
- `license_confidence` — thông tin nguồn có ổn không

#### Công thức gợi ý
```text
final_score =
  0.40 * semantic_score +
  0.20 * object_match_score +
  0.10 * quality_score +
  0.10 * style_match_score +
  0.10 * novelty_bonus +
  0.10 * provider_trust_score -
  negative_penalty - duplicate_penalty
```

### 3.5 Shot planning
Nếu candidate là video dài, engine phải:
- detect shot/scene boundaries;
- cắt phần hay nhất;
- tránh đoạn mở đầu hoặc watermark area;
- align độ dài clip với scene duration;
- apply motion crop nếu cần cho shorts.

### 3.6 Fallback policy
Nếu không đạt ngưỡng score:
1. thử provider khác
2. thử asset type khác
3. thử prompt paraphrase visual intent
4. fallback sang ảnh + parallax
5. fallback sang motion graphic template
6. đẩy vào review queue nếu vẫn thấp

### 3.7 Human review
Người dùng phải thấy:
- top 5 candidates cho từng scene
- điểm từng candidate
- lý do chọn
- cảnh báo nếu score thấp
- nút replace / pin / blacklist / retry

## 4. Kiến trúc nội bộ

### 4.1 Packages
```text
engine/app/visual_match/
  __init__.py
  service.py
  scene_decomposer.py
  candidate_retriever.py
  preprocessing.py
  scorer.py
  shot_planner.py
  fallback.py
  reviewer.py
  embeddings.py
  duplicate_guard.py
  schema.py
```

### 4.2 Data flow
```text
Script Project
  -> Scene Decomposer
  -> Candidate Retriever
  -> Candidate Preprocessing
  -> Embedding Generator
  -> Scorer
  -> Shot Planner
  -> Review Gate
  -> Timeline Output
```

## 5. Suggested OSS/libraries

### 5.1 CLIP multilingual
Dùng để embed text + image vào cùng vector space, hỗ trợ tốt hơn với tiếng Việt/đa ngôn ngữ.

Use cases:
- semantic matching
- zero-shot labeling
- mismatch detection

### 5.2 FAISS
Dùng để index local asset embeddings để search cực nhanh khi media library lớn.

### 5.3 PySceneDetect
Dùng detect shot boundaries để cắt candidate video thành clip usable.

### 5.4 imagehash / perceptual hash
Dùng chống duplicate footage hoặc gần-duplicate.

### 5.5 optional object detector
Giai đoạn sau có thể thêm YOLO/OWL-ViT để cải thiện object_match_score.

## 6. Database changes

### 6.1 scene_match_results
- id
- script_project_id
- scene_index
- scene_json
- selected_asset_id
- selected_clip_start_sec
- selected_clip_end_sec
- final_score
- confidence_label
- status
- created_at
- updated_at

### 6.2 scene_match_candidates
- id
- scene_match_result_id
- asset_id
- semantic_score
- object_match_score
- style_match_score
- quality_score
- negative_penalty
- duplicate_penalty
- final_score
- explain_json

### 6.3 asset_embeddings
- id
- asset_id
- embedding_model
- vector_dim
- vector_blob_path
- updated_at

## 7. API design

### 7.1 Start visual matching
`POST /api/v5/visual-match/projects/{script_project_id}/run`

Body:
```json
{
  "channel_id": "...",
  "mode": "auto",
  "provider_preferences": ["local_cache", "pexels", "pixabay"],
  "min_score_threshold": 0.62,
  "allow_fallback_to_images": true
}
```

### 7.2 Get scene matches
`GET /api/v5/visual-match/projects/{script_project_id}`

### 7.3 Replace selected candidate
`POST /api/v5/visual-match/scene/{scene_match_result_id}/select`

### 7.4 Blacklist asset for scene/channel
`POST /api/v5/assets/{asset_id}/blacklist`

### 7.5 Re-run only low confidence scenes
`POST /api/v5/visual-match/projects/{script_project_id}/rerun-low-confidence`

## 8. UI specification

### 8.1 Scene Planner page
Layout 3 cột:
- cột trái: script scenes list
- cột giữa: selected preview + timeline
- cột phải: candidate tray + scoring breakdown

### 8.2 Each scene card shows
- scene index
- spoken text
- visual intent
- selected asset thumbnail
- confidence badge
- duration
- provider
- replace button
- pin button
- notes

### 8.3 Filters
- only low confidence
- only duplicate risk
- only unresolved
- by asset type
- by provider

## 9. Timeline output contract

Output cho render engine:

```json
{
  "project_id": "...",
  "timeline": [
    {
      "scene_index": 1,
      "asset_id": "...",
      "asset_type": "video",
      "src_path": "...",
      "trim_start": 2.4,
      "trim_end": 6.8,
      "motion_effect": "none",
      "subtitle_segment_ids": [1,2,3],
      "transition": "cut"
    }
  ]
}
```

## 10. Scoring implementation notes

### 10.1 Fast path
- dùng local embeddings cache trước
- chỉ gọi remote provider khi thiếu asset

### 10.2 Quality heuristics
- min resolution threshold
- face/text/watermark heuristics
- penalize vertical crop from ultra-wide if unsafe

### 10.3 Duplicate guard
- same asset không dùng quá X lần trong N video gần đây của cùng channel
- near-duplicate hash cũng bị phạt

## 11. Review rules

Scene phải vào review queue nếu:
- final_score < threshold
- negative_penalty > 0
- asset license notes thiếu
- candidate duration quá ngắn
- duplicated too often
- scene unresolved sau 2 fallback cycles

## 12. Observability

Mỗi run phải log:
- số scene
- candidate count per scene
- average score
- low confidence count
- provider hit rate
- cache hit rate
- repeated asset count
- total time spent

## 13. Acceptance criteria

### Must-have
- scene decomposition chạy được
- semantic scoring hoạt động với local embeddings
- có top 5 candidate per scene
- có manual replace
- có timeline output cho render

### Success metric
- tỉ lệ scene bị user replace giảm ít nhất 30% so với baseline keyword search
- tỉ lệ scene confidence >= medium đạt ít nhất 80%

## 14. Tests

### Unit tests
- scene parsing
- score aggregation
- duplicate penalty
- fallback logic

### Integration tests
- script -> scene -> candidate -> select -> timeline

### Golden tests
- 10 scripts mẫu và expected top assets

## 15. Implementation order

1. DB schema
2. scene decomposition
3. basic retriever
4. CLIP embeddings
5. scorer
6. UI scene planner read-only
7. manual replace
8. shot planner
9. fallback logic
10. review integration

## 16. Non-goals for V5.1
- không làm video synthesis generative hoàn toàn
- không build full object detection studio ngay từ đầu
- không tối ưu GPU cluster

## 17. Prompt contract for AI coder

AI phải code theo hướng incremental:
- phase 1: backend-only, no UI complexity
- phase 2: read-only UI
- phase 3: interactive review UI
- phase 4: optimization and cache
