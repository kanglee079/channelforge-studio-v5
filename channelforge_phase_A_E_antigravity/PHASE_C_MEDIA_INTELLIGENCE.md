# PHASE C PROMPT — MEDIA INTELLIGENCE LAYER

Dán prompt này vào Antigravity để code **Phase C only**.

---

You are working on `channelforge-studio-v5`.
Implement **Phase C only**.

# Phase C Goal

Upgrade the current media matching pipeline from mostly metadata/keyword-based retrieval into a more reliable **Media Intelligence Layer** that can better match visuals to script meaning.

The repo already contains media intelligence modules such as scene spec building, embedding, index store, retriever, reranker, shot planner, and review gate. Phase C must harden and connect them into a coherent, higher-quality pipeline.

# Why this phase matters

The main user complaint is that videos can render successfully but visuals sometimes do not match the spoken content closely enough.
This phase is about improving semantic relevance and operational reviewability.

# What Phase C must solve

## C1. Scene spec quality

Improve or complete the scene specification generation step.
Each scene spec should aim to capture structured intent, such as:
- scene index
- spoken text
- visual intent
- must-have objects/entities
- must-not-show hints
- mood / tone
- setting/location hints
- time-period hints if applicable
- desired motion style or asset preference if useful

The scene spec builder should degrade gracefully if LLM enrichment is unavailable.

## C2. Local media asset normalization

Build or refine a consistent media asset representation for local cache and remote-ingested assets.
Support fields like:
- asset key
- provider
- local path / source URL
- type (image/video)
- duration
- size / dimensions
- tags / derived metadata
- extracted frames (for videos)
- embedding status
- quality metadata
- licensing notes if stored

## C3. Embedding and index flow

Harden the embedding/index layer.
Requirements:
- support at least text embedding for scene specs and asset metadata
- if image/frame embedding is available, use it optionally
- local vector index should load/save/warm safely
- when optional acceleration libs are missing, fallback mode must still work
- do not crash if FAISS or advanced models are unavailable

## C4. Candidate retrieval

Improve retrieval so it can combine multiple sources:
- local cache first when possible
- remote providers next (Pexels, Pixabay, etc.)
- query generation from scene spec rather than naïve script chunking
- dedupe candidates across providers

## C5. Reranking model

Implement a structured scoring pipeline.
At minimum include sub-scores such as:
- semantic relevance
- object/entity alignment
- mood/style alignment
- quality/readability
- duration fit for the shot
- duplication penalty
- mismatch penalty

Return explainability fields so the review layer and UI can show *why* a candidate won.

## C6. Confidence labels and review gate

Each scene result should end with a confidence label such as:
- high
- medium
- low
- pinned

Low confidence scenes must automatically surface into review workflows.
Do not silently let weak matches pass as final.

## C7. Shot planning

Build or harden a shot planner that can transform selected scene assets into render-ready shot instructions.
Examples:
- start time
- end time / target duration
- crop/pan hints
- frame source
- fallback style if video asset unavailable
- still-image motion treatment if needed

## C8. Fallback chain

When ideal semantic media is not available, the system should degrade intelligently instead of choosing obviously wrong footage.
Suggested fallback order:
1. local asset with good semantic fit
2. remote stock asset with acceptable fit
3. still image with motion treatment
4. branded motion template / abstract B-roll
5. review required

## C9. Review UI integration

Integrate results with review surfaces so the operator can:
- inspect match runs
- see scene-by-scene chosen asset
- inspect explanations/scores
- pin an asset
- retry one scene
- mark review complete

## C10. Performance safeguards

Do not make every render path unbearably slow.
Add caching and warmup strategy where useful.
Local-first performance matters.

# Files likely in scope

- `engine/app/routers/media_intel.py`
- `engine/app/media_intel/*`
- `engine/app/db.py`
- `engine/app/migrations/*`
- review-related frontend pages/components
- any API client/types needed by frontend

# Strong constraints

- Keep optional heavy dependencies optional
- Must support heuristic fallback mode if semantic stack not installed
- Do not rewrite the entire render system in this phase
- Do not entangle this phase with publish workflow logic

# Data expectations

Add DB structures as needed for:
- media assets v2/v3
- embedding/index metadata
- scene match runs
- scene match items
- review-required queues
- pinned/manual overrides

# Acceptance criteria

Phase C is complete only if all are true:

1. The media pipeline can run end-to-end from script text to match run output.
2. Match results carry explainable scores and confidence labels.
3. Low-confidence scenes are surfaced for review.
4. The system degrades gracefully when advanced semantic dependencies are absent.
5. Operators can manually pin/retry scene choices.
6. The architecture clearly separates scene spec → retrieval → rerank → shot planning → review.

# Validation you must run

- backend import/boot
- media intel endpoint sanity tests
- index rebuild/warmup test
- one sample match run
- UI build sanity test for review-related screens
- migration validation

# Output format after implementation

Return exactly:
1. Scope completed
2. Media pipeline summary
3. Scoring/reranking summary
4. Files changed
5. Migrations added
6. API/UI changes
7. Validation commands run
8. Validation results
9. Known limitations
10. Recommended Phase D handoff
