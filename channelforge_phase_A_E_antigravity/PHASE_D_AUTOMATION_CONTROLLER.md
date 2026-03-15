# PHASE D PROMPT — AUTOMATION CONTROLLER / END-TO-END ORCHESTRATION

Dán prompt này vào Antigravity để code **Phase D only**.

---

You are working on `channelforge-studio-v5`.
Implement **Phase D only**.

# Phase D Goal

Create the orchestration layer that can drive the system from research/ideas through content generation, media matching, rendering, QC, and publish queue preparation.

This phase should make the app capable of **running a repeatable workflow automatically**, even if some publish steps still remain gated by review or workspace verification.

# What Phase D must solve

## D1. Unified pipeline controller

Create a clear orchestration service responsible for sequencing jobs such as:
- trend ingestion
- idea selection
- research pack creation
- script generation
- scene/media planning
- voice/subtitle generation
- rendering
- QC/review gate
- enqueue for publish

This should not be spread randomly across routers.
Create or harden a dedicated controller/service layer.

## D2. Job model and stage progression

The repo already has job concepts. Formalize them into stage-based execution.
Possible pipeline stages:
- `idea_pending`
- `research_pending`
- `script_pending`
- `media_match_pending`
- `voice_pending`
- `subtitle_pending`
- `render_pending`
- `qc_pending`
- `review_pending`
- `publish_queue_pending`
- `ready_to_publish`
- `published`
- `failed`
- `paused`

Requirements:
- stage transitions persisted
- retries persisted
- per-stage timestamps
- actionable error reasons
- idempotent enough to resume after interruption

## D3. Per-channel automation policy

Each channel/workspace should be able to define automation preferences such as:
- content niche
- preferred sources/providers
- language
- review strictness
- max daily videos
- quality threshold
- local-vs-cloud provider routing
- whether thumbnail generation is enabled
- whether publish can be automatic or requires approval

## D4. Scheduler / queue prioritization

Build or refine scheduling logic so jobs can be:
- queued
- prioritized by channel
- paused/resumed
- retried with backoff
- rate-limited per channel
- soft-capped per day

Local processing should be kept busy without accidentally saturating publishing workflows.

## D5. Human review checkpoints

Not every job should publish automatically.
The controller must honor review gates from:
- low-confidence media match
- script safety/content policy failures if you have them
- missing workspace verification
- missing route binding for publish
- failed QC

The controller should stop cleanly at these checkpoints and explain why.

## D6. Cost router / provider strategy

Add a provider-routing strategy so the pipeline can decide when to use:
- local inference/model
- cheaper provider
- premium provider

Examples:
- default to local/free assets first
- use local TTS/STT when quality threshold allows
- reserve premium API usage for selected channels or high-value jobs

Track provider usage and estimated cost per run.

## D7. Channel batch operations

Enable channel-aware operations such as:
- run one idea cycle for one channel
- run N queued jobs for one channel
- run daily batch across selected active channels
- dry-run planning without publish

## D8. Failure handling

Implement structured failure behavior:
- retry transient failures
- do not retry permanent validation failures indefinitely
- persist last failure cause and stage
- allow manual requeue from UI

## D9. UI integration

Expose orchestration state in UI pages such as:
- queue/jobs page
- content studio page
- channel page
- dashboard summaries

Must surface:
- current stage
- retries
- blockers
- review waits
- next scheduled action
- cost/use metrics if available

# Files likely in scope

- queue/job-related backend modules
- controller/orchestrator services
- relevant routers for queue/content/research/review
- DB and migrations
- frontend queue/jobs/content/channel pages
- provider/cost routing service layer

# Strong constraints

- Do not rebuild every feature from scratch
- Reuse existing jobs/content/review/research structures where possible
- Do not couple render logic directly to publish logic in fragile ways
- Respect Phase B workspace policy and Phase C review gates

# Acceptance criteria

Phase D is complete only if all are true:

1. There is a clear controller that sequences the pipeline end-to-end.
2. Jobs have persisted stage-based progression.
3. The system can stop at review checkpoints instead of blindly continuing.
4. Per-channel automation policy exists.
5. Retry/backoff/pause/resume are supported at least for core stages.
6. UI exposes operational job state well enough for an operator to manage automation.
7. Cost/provider routing is visible and configurable enough to be useful.

# Validation you must run

- backend import/boot
- migration check
- orchestrator/controller sanity tests
- one dry-run pipeline test
- queue stage transition test
- UI build sanity test

# Output format after implementation

Return exactly:
1. Scope completed
2. Controller architecture summary
3. Stage model summary
4. Files changed
5. Migrations added
6. API/UI changes
7. Validation commands run
8. Validation results
9. Known limitations
10. Recommended Phase E handoff
