# V5.4 — Research / Trend Assistant 2.0

## 1. Mục tiêu

Biến phần trend assistant hiện tại từ một bộ fetch source đơn giản thành một **always-on research layer** có thể:
- theo dõi trend liên tục;
- cào và làm sạch dữ liệu từ nhiều nguồn;
- đánh giá trend theo channel-specific niche;
- biến trend thành idea, angle, title pack và research packs;
- lưu lại tri thức để tái sử dụng.

## 2. Kết quả mong muốn

- tạo được nguồn idea đều đặn cho từng channel;
- giảm ý tưởng rỗng hoặc trùng lặp;
- có watchlists, niche monitors và alerts;
- source rõ ràng, freshness rõ ràng;
- dùng được cả free data lẫn paid data tùy budget.

## 3. Core responsibilities

### 3.1 Ingestion
Nguồn vào gồm:
- Google Trends / Trending Now feed nếu có
- NewsAPI
- GDELT
- SerpApi
- Wikipedia summary/pages
- YouTube transcripts công khai
- RSS feeds
- web scraping với Scrapling / Trafilatura
- manually added URLs

### 3.2 Cleaning
- deduplicate
- extract main text
- normalize titles
- language detection
- source domain scoring
- freshness estimation
- entity extraction

### 3.3 Trend scoring
Mỗi trend/item phải được chấm theo:
- freshness
- relevance to channel niche
- novelty
- contentability (dễ làm video không)
- risk level
- source confidence
- monetization potential
- search intent strength

### 3.4 Idea generation
Từ trend/research item, assistant phải tạo:
- 3–10 video ideas
- angles khác nhau
- title options
- shorts vs long-form suitability
- evergreen vs trend classification

### 3.5 Research packs
Mỗi idea có thể mở ra research pack gồm:
- key facts
- source links
- claim confidence
- suggested hook
- suggested CTA
- visual opportunities
- forbidden claims

## 4. Internal architecture

```text
engine/app/research/
  ingestion/
    trends.py
    news.py
    gdelt.py
    serp.py
    wikipedia.py
    youtube_transcript.py
    rss.py
    scraping.py
  cleaning/
    normalize.py
    dedupe.py
    extract.py
  scoring/
    trend_score.py
    risk_score.py
    niche_relevance.py
  generation/
    idea_generator.py
    angle_generator.py
    research_pack.py
  memory/
    entity_graph.py
    topic_memory.py
```

## 5. Database changes

### 5.1 trend_items
- id
- source_type
- source_ref
- title
- snippet
- url
- language
- region
- fetched_at
- freshness_score
- source_confidence_score
- raw_json
- normalized_hash

### 5.2 topic_clusters
- id
- canonical_topic
- aliases_json
- cluster_score
- first_seen_at
- last_seen_at

### 5.3 channel_trend_scores
- id
- channel_id
- trend_item_id
- relevance_score
- monetization_score
- risk_score
- final_score
- recommended_action

### 5.4 research_packs
- id
- channel_id
- idea_id
- summary_json
- source_refs_json
- fact_blocks_json
- visual_opportunities_json
- risk_notes_json

## 6. Watchlists

Channel có thể tạo watchlist:
- keywords
- entities
- competitor channels
- subreddits/forums in future
- domain sources
- category trends

Watchlist phải support:
- daily refresh
- alert on spike
- alert on new cluster
- alert on competitor overlap

## 7. Niche relevance engine

### Inputs
- channel niche profile
- content tone
- target audience
- language
- banned themes

### Outputs
- relevance score
- recommended format
- angle suggestions
- why relevant
- why risky

## 8. Contentability scoring

Một trend tốt chưa chắc làm video tốt. Contentability engine phải đánh giá:
- có đủ data không
- có visual opportunities không
- có hook mạnh không
- có dễ fact-check không
- có dễ vi phạm policy không
- có quá bão hòa không

## 9. Assistant UI specification

### 9.1 Trend Radar 2.0
- trending feed by source
- clustered topics
- spikes chart
- sort by relevance to selected channel
- convert to idea button

### 9.2 Research Inbox
- scraped sources
- cleaned docs
- quality warnings
- dedupe suggestions
- promote to research pack

### 9.3 Topic Memory
- entity graph
- repeated themes
- what already covered by this channel
- stale ideas

## 10. Scraping subsystem design

### 10.1 Source adapters
- generic HTTP fetch
- Trafilatura extraction
- Scrapling advanced crawl
- RSS fetch
- transcript fetch

### 10.2 Source rules
Each source config:
- name
- fetch method
- rate hints
- parsing template
- robots/policy notes
- tags

### 10.3 Respectful scraping
- request pacing
- source allowlists
- manual review for fragile sources
- license/policy notes stored with data

## 11. Idea generation pipeline

```text
Trend item(s)
 -> cluster
 -> score per channel
 -> generate ideas
 -> dedupe against channel history
 -> create idea cards
 -> optional research pack
 -> push to content backlog
```

## 12. API design

### 12.1 Refresh trends
`POST /api/v5/research/refresh`

### 12.2 Get trend feed
`GET /api/v5/research/trends?channel_id=...`

### 12.3 Convert trend to idea
`POST /api/v5/research/trends/{trend_id}/to-idea`

### 12.4 Create research pack
`POST /api/v5/research/ideas/{idea_id}/pack`

### 12.5 Add source URL
`POST /api/v5/research/source-url`

### 12.6 Get watchlists
`GET /api/v5/research/watchlists`

## 13. Review gates

Trend/research item phải vào review nếu:
- source confidence thấp
- freshness quá cũ
- duplicate cluster quá dày
- channel policy conflict
- claim confidence thấp

## 14. Acceptance criteria

### Must-have
- ingest multi-source items
- dedupe and cluster basic topics
- score relevance per channel
- generate ideas from trend
- build research pack

### Nice-to-have
- topic memory graph
- alerting on spikes
- competitor overlap detection

## 15. Tests

### Unit
- normalize title
- dedupe hash
- trend scoring
- niche relevance rules

### Integration
- source URL -> cleaned doc -> cluster -> idea

## 16. Future extensions
- competitor channel ingestion
- semantic search over internal research memory
- multilingual entity normalization
