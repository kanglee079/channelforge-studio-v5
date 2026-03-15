# PROJECT CONSTRAINTS — Desktop YouTube Studio V5

## 1. Product scope boundaries
This project is a **desktop application for legitimate multi-channel content operations**.

The system must **not** implement:
- fingerprint spoofing
- anti-detection logic
- stealth automation
- CAPTCHA bypass
- account farming systems
- rate-limit evasion
- behavior randomization intended to deceive platforms
- proxy rotation specifically designed to hide abusive automation
- mass account creation flows

If the user asks for these, redirect implementation toward:
- isolated browser workspaces
- session persistence
- audit logging
- manual review controls
- policy-aware automation

---

## 2. Architecture constraints
- Desktop shell: prefer **Tauri 2** unless a documented decision record justifies otherwise.
- Frontend: **React + TypeScript**.
- Backend engine: preserve and extend the current **Python** pipeline.
- Internal API: **FastAPI**.
- Local DB: **SQLite**.
- Browser session layer: **Playwright**.
- Media pipeline: **FFmpeg**.
- Subtitle/transcript pipeline: **WhisperX** or **faster-whisper**.
- Optional rendering engine: **Remotion**.
- Optional local LLM provider: **Ollama**.

Do not rewrite the whole system into Node-only unless explicitly approved.

---

## 3. Codebase rules
- Keep code modular.
- Avoid giant files.
- Prefer clear domain folders over random utility sprawl.
- No hardcoded API keys, tokens, cookies, or secrets.
- No hardcoded absolute local paths.
- Use typed DTOs / schemas at API boundaries.
- Every background job must be resumable or safely retryable.
- Every destructive action must be explicit.
- Every provider integration must be wrapped behind an interface.

---

## 4. Desktop UX rules
- Build for **power users**.
- Support batch operations.
- Use strong status indicators.
- Show job state and failure reasons clearly.
- Avoid overly playful UI.
- Prefer productivity over decoration.
- Support keyboard shortcuts where sensible.
- Preserve local state between sessions.

---

## 5. Data and storage rules
All important entities must be persisted locally.

Minimum persistent entities:
- channels
- strategies
- workspaces
- trend signals
- research snapshots
- ideas
- briefs
- scripts
- asset plans
- renders
- uploads
- analytics snapshots
- provider usage
- audit logs

Use migrations.
Never make breaking schema changes silently.

---

## 6. Browser workspace rules
Each channel must be able to bind to exactly one browser workspace by default.
A workspace must have:
- dedicated persistent storage directory
- cookie/localStorage/IndexedDB separation
- controlled download directory
- session health metadata
- login status metadata
- last verification timestamp

Do not market or describe this as antidetect.
This is **workspace isolation** only.

---

## 7. Provider and cost rules
All AI/media providers must be abstracted behind adapters.
Each adapter must report:
- provider name
- model or voice id
- estimated or actual cost
- token or character usage if available
- request status
- failure reason

Support routing policies such as:
- cheap provider for research
- premium provider for final scripts
- local transcription by default
- premium TTS only for selected channels

---

## 8. Research and scraping rules
Research sources must be explicit and traceable.
Every research snapshot should store:
- source URL
- source title
- extraction time
- extractor used
- cleaned text
- metadata
- channel relevance score

Respect source terms, robots, and usage limits where applicable.
Do not silently scrape everything.
Use allowlists where possible.

---

## 9. Content quality rules
Before a script is considered ready:
- it must have source references or a declared low-confidence warning
- it must pass duplicate checks
- it must pass channel-style checks
- risky claims must be flagged
- title and thumbnail text must be checked for repetition

The system should prefer **fewer strong videos** over many weak duplicates.

---

## 10. Rendering rules
- FFmpeg remains the default renderer.
- Burned-in subtitles should be the default safe path.
- Template packs must be reusable and data-driven.
- Output directories must be deterministic.
- Render jobs must emit logs and artifact metadata.

---

## 11. Upload rules
- Respect YouTube API quota constraints.
- Do not assume unlimited uploads.
- Support schedule queues and soft daily caps.
- Track upload state transitions.
- Require explicit channel binding for upload jobs.
- Keep failed upload payloads inspectable.

---

## 12. Logging and observability rules
At minimum, log:
- job start/finish/failure
- provider calls
- browser workspace actions
- upload attempts
- render attempts
- moderation decisions
- user overrides

Logs must be filterable in the UI.

---

## 13. Testing rules
Add tests for:
- provider routing
- retry/backoff logic
- duplicate detection
- DB migrations
- critical API contracts
- workspace path creation

Smoke tests are mandatory for:
- app startup
- worker startup
- render queue enqueue
- upload queue enqueue

---

## 14. Documentation rules
Keep these docs updated:
- architecture overview
- local setup guide
- Windows build guide
- environment variables reference
- provider setup guide
- migration notes
- known limitations

---

## 15. Output quality rules for coding AI
When generating code:
- produce real file structures
- prefer complete modules over pseudo-code
- keep TODOs specific
- avoid repetitive placeholder text
- do not invent fake API responses
- document assumptions clearly

If a feature is high-risk or not appropriate, mark it explicitly and propose the safer alternative.
