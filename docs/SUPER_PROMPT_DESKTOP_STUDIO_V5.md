# SUPER PROMPT — Desktop YouTube Studio V5

## Mission
Build a **desktop-first, all-in-one YouTube channel operating system** from the existing V4 codebase.

This is **not** a simple video generator anymore.
It must evolve into a **serious desktop super app** that helps operate multiple long-term YouTube channels, where each channel has a fixed niche, fixed content strategy, fixed brand voice, and its own isolated workspace.

The app must become a **local-first channel management platform** for:
- channel portfolio management
- content system design
- idea research and trend monitoring
- script / asset / video production
- review / approval / scheduling
- performance tracking
- browser workspace isolation per channel
- cost governance
- reusable automation

## Important safety and platform boundary
Do **not** build fingerprint spoofing, stealth evasion, anti-detection, account farming, or platform-bypass features.
Do **not** attempt to disguise automation as human activity.
Do **not** create systems for mass account abuse.

Instead, implement a **compliant channel workspace isolation architecture**:
- one isolated browser workspace per channel
- persistent authenticated session per workspace
- separate cookies, local storage, IndexedDB, downloads, and settings per channel
- optional proxy configuration per workspace only when legitimately owned and configured by the user
- explicit audit logs for automation actions
- manual approval gates for sensitive actions
- clear risk flags when using automation on third-party platforms

The product goal is **professional channel operations**, not evasion.

---

## Product vision
Create a desktop application called **ChannelForge Studio** (working name) that acts like a **YouTube Operating System** for serious faceless channel builders.

The application should support:
1. managing many channels at once
2. assigning one fixed niche / strategy to each channel
3. researching trends and source material continuously
4. converting research into a structured content pipeline
5. producing videos with reusable templates
6. storing all project state locally first
7. letting the user inspect, approve, edit, and override every important step
8. routing work between cloud AI providers and local AI providers for cost control
9. keeping browser sessions separated per channel
10. scaling in a maintainable way for long-term use

---

## Mandatory architecture direction
Use a **desktop app architecture**, not web-only architecture.

Preferred implementation:
- **Tauri 2** as desktop shell
- **React + TypeScript** frontend
- **Python backend sidecar** to preserve and extend the existing pipeline
- **FastAPI** for internal local API between desktop shell and Python services
- **SQLite** as the default local database
- **Playwright** for browser workspaces and channel session isolation
- **FFmpeg** for render pipeline
- **WhisperX / faster-whisper** for subtitles and transcript workflows
- optional **Remotion** rendering service for premium templates
- optional **Ollama** integration for local LLM tasks

If a different implementation is chosen, justify it clearly in architecture docs.

---

## Core product modules

### 1. Desktop shell + system integration
Implement:
- native desktop window
- tray icon
- background worker control
- notifications
- file system access
- secure local settings
- auto-update support
- crash-safe recovery
- offline-tolerant operation

### 2. Multi-channel portfolio manager
Each channel must have:
- channel name
- platform(s)
- niche
- subtopics
- language
- content format (Shorts, long-form, mixed)
- brand voice profile
- risk profile
- source whitelist
- monetization notes
- scheduling policy
- cost budget
- browser workspace binding
- upload credentials status
- template pack binding

### 3. Channel workspace isolation
Each channel gets a separate browser workspace:
- persistent session directory
- isolated cookies / local storage / IndexedDB
- separate downloads folder
- browser launch policy
- optional extension compatibility plan
- manual login flow
- session health status
- account checkpoint warning system

Do not use the words or concepts of “antidetect” in the codebase or UI.
Use the language:
- Workspace
- Browser Profile
- Session Vault
- Channel Environment

### 4. Trend Radar / Research assistant
Build a research system that continuously collects and scores opportunities from:
- Google Trends / Trending Now
- RSS feeds
- selected news providers
- YouTube transcripts from selected competitor videos
- website scraping from approved sources
- Wikipedia / knowledge sources
- user-provided seed URLs
- keyword monitoring

The assistant must:
- deduplicate topics
- cluster related ideas
- score opportunity vs competition vs channel fit
- flag risky / unverifiable claims
- save usable research snapshots
- propose content angles per channel
- show evidence links per finding
- support manual curation

### 5. Content OS
Implement a full content operating pipeline:
- idea inbox
- research board
- brief generator
- title generator
- outline generator
- script writer
- fact-check queue
- asset planner
- shot list / scene list
- voice generation
- subtitle generation
- thumbnail ideation
- render queue
- QA review
- upload scheduling
- post-publish performance review
- repurposing / recycling workflow

### 6. Brand and niche memory system
Per channel, store:
- content bible
- tone of voice
- forbidden claims
- formatting rules
- thumbnail style rules
- CTA style
- target audience
- topic boundaries
- evergreen topics
- seasonal topics
- banned competitors / banned sources if defined by the user

The AI must use these memories when generating content.

### 7. Cost orchestration layer
Add a provider router that can decide per task whether to use:
- OpenAI
- ElevenLabs
- local TTS
- local STT
- Ollama/local LLM
- free or cached research

The user must be able to define rules like:
- premium voice only for flagship channels
- local models for ideation and classification
- cloud model only for final scripts
- subtitles should default to local transcription when possible

### 8. Review, approval, and safety
Add:
- content moderation queue
- duplicate / near-duplicate detection
- claim risk warnings
- source coverage score
- policy checklist before upload
- manual approval requirement for high-risk content
- logs of what model/provider generated each output

### 9. Video template system
Add reusable template packs:
- Shorts templates
- documentary templates
- slideshow templates
- talking-head faceless templates
- top-10 list templates
- infographic templates

Templates must define:
- timing rules
- text animation rules
- subtitle style
- footage style
- voice pacing
- B-roll rules
- brand colors
- CTA placement

### 10. Analytics and learning loop
Track:
- uploads
- status
- publish date
- titles
- thumbnails
- tags
- description versions
- CTR notes
- retention notes
- outcome labels
- niche performance trends
- reusable winning patterns

The app should use this to improve future suggestions.

---

## UX requirements
Design for a serious operator, not a toy app.

Required navigation:
- Dashboard
- Channels
- Workspaces
- Trend Radar
- Research Library
- Content Studio
- Video Factory
- Templates
- Upload Calendar
- Analytics
- Cost Control
- Settings
- Logs

Required UX principles:
- dense but readable information layout
- keyboard shortcuts for power users
- batch operations
- timeline / queue views
- strong filtering and searching
- explicit status chips
- undo-friendly edits where possible
- no hidden magic for destructive actions

---

## Desktop-specific requirements
The desktop app must:
- run well on Windows first
- be packagable for macOS later
- support local file caching and large media libraries
- support resumable jobs
- allow long-running background processes
- avoid requiring a remote server for core usage
- keep sensitive tokens local by default

---

## Recommended open-source / library integration candidates
Use these where appropriate instead of reinventing them:
- Scrapling for adaptive scraping and crawling
- Trafilatura for clean article/body extraction
- Playwright for browser automation and isolated workspaces
- WhisperX or faster-whisper for subtitle/transcript generation
- Remotion for premium scene-based rendering workflows
- FFmpeg for core media processing
- Ollama for local model routing
- yt-dlp only where the user has the right to process relevant media and metadata

Before adding a dependency, verify:
- maintenance status
- license compatibility
- install complexity on Windows
- whether it is optional or mandatory

---

## Data model expectations
You must introduce or refine entities such as:
- Channel
- ChannelStrategy
- BrowserWorkspace
- TopicCluster
- TrendSignal
- ResearchSource
- ResearchSnapshot
- ContentIdea
- ContentBrief
- ScriptDraft
- FactCheckItem
- AssetPlan
- VoiceAsset
- SubtitleAsset
- ThumbnailAsset
- RenderJob
- UploadJob
- PublishRecord
- TemplatePack
- ProviderRule
- CostLedger
- AuditLog

---

## Non-functional requirements
- modular architecture
- strong type safety in frontend
- service boundaries in backend
- resumable queues
- idempotent jobs
- detailed logs
- structured config
- no hardcoded secrets
- deterministic output directories
- migration support for database
- testable service interfaces

---

## Deliverables required from the coding AI
Produce:
1. updated folder architecture
2. architecture decision record explaining desktop stack choice
3. database schema
4. migration plan from V4 web app to desktop app
5. backend services and API routes
6. desktop shell integration
7. frontend screens and navigation
8. browser workspace manager
9. trend assistant pipeline
10. content pipeline orchestration
11. setup instructions for Windows
12. environment variable template
13. build instructions
14. sample seed data
15. clear TODO markers only for genuinely unfinished optional items

---

## Implementation order
Build in phases:

### Phase 1
- desktop shell
- backend sidecar integration
- existing V4 features running inside desktop shell
- SQLite migration
- channel manager
- workspace manager

### Phase 2
- trend radar
- research library
- content studio
- queue orchestration
- template system

### Phase 3
- analytics
- cost governance
- local AI router
- updater
- power-user shortcuts
- packaging and release flow

### Phase 4
- advanced approvals
- learning loop
- optional premium rendering mode
- multi-language support

---

## Final instruction to the coding AI
Do not produce a toy prototype.
Do not collapse the app into a single file.
Do not replace the existing Python pipeline without reason.
Do not add vague placeholders where real structure is possible.
Preserve the current working engine and evolve it into a desktop operating system for serious multi-channel YouTube operations.
