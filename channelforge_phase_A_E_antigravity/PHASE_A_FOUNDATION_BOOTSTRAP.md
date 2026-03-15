# PHASE A PROMPT — FOUNDATION / BOOTSTRAP / READINESS HARDENING

Dán prompt này vào Antigravity để code **Phase A בלבד**.

---

You are working on `channelforge-studio-v5`.
Implement **Phase A only**.
Do not touch unrelated architecture beyond what is necessary for this phase.

# Phase A Goal

Stabilize the project foundation so the repo can be reliably installed, booted, diagnosed, and validated before deeper feature work.

Right now the repo has grown quickly. The current problem is not lack of features; it is lack of synchronization between declared capabilities, actual dependencies, diagnostics, setup flow, and release readiness.

Phase A must make the repository trustworthy as a development and onboarding base.

# What Phase A must solve

## A1. Dependency truth source

Create a clear dependency structure for the Python engine.
The repository currently needs multiple groups of dependencies (core, browser, media, AI, optional acceleration), but installation is still too ambiguous.

Implement a clean structure such as one of these:
- `requirements/base.txt`, `requirements/browser.txt`, `requirements/media.txt`, `requirements/ai.txt`, `requirements/dev.txt`, `requirements/all.txt`
- or another equally clear structure that stays Python/pip friendly

Requirements:
- preserve simple install path for normal users
- keep a single canonical way to install everything needed for desktop local development
- make optional features clearly optional
- avoid hidden runtime dependency surprises

## A2. System diagnostics synchronization

Upgrade the existing system diagnostics so it becomes the single source of runtime truth.

Diagnostics must check and report:
- Python runtime availability
- FFmpeg availability
- Playwright availability and browser installation status
- SQLite DB readiness
- required writable directories
- API key presence status (without exposing secrets)
- sidecar/build readiness flags
- optional model/provider availability
- migration status

For every failed check, diagnostics must also return:
- severity
- human-readable explanation
- suggested fix
- whether it blocks app boot or only a feature subset

## A3. First-run readiness flow

Refine or rebuild the first-run setup experience so a user can open the desktop app and understand exactly what is missing.

The setup flow should include steps like:
- welcome
- environment summary
- dependency checks
- FFmpeg path check
- Playwright/browser check
- storage path check
- API key status
- migration/database readiness
- final readiness summary

Requirements:
- should work even if many dependencies are missing
- should not crash the app
- should expose next actions clearly

## A4. README / version / docs consistency

Synchronize versioning and project messaging across:
- root README
- package.json version expectations
- Tauri app metadata if needed
- setup scripts / release scripts
- diagnostics labels

The repo already presents itself as V5.8; make sure the surrounding text and docs are consistent and not stale.

## A5. Bootstrap commands and validation scripts

Create a small set of canonical bootstrap commands/scripts.
Examples:
- install frontend deps
- install engine deps
- run DB migration
- run diagnostics
- warm minimal app state
- run desktop dev mode

Also add a lightweight validation script or command set to verify:
- frontend build
- backend import/boot health
- migration success
- diagnostics endpoint works

## A6. Strict no-surprise startup behavior

App startup should degrade gracefully.

Rules:
- the desktop app may open even if some optional modules are unavailable
- diagnostics/setup page must explain blockers
- backend health should distinguish `healthy`, `degraded`, `blocked`
- no silent failures for missing core dependencies

# Files likely in scope

You may modify any files needed for Phase A, but prefer these areas first:
- `README.md`
- `engine/requirements*`
- `engine/app/routers/system.py`
- `engine/app/main.py`
- `engine/app/db.py` if needed for migration metadata/readiness
- `src/pages/SystemPage.tsx`
- `src/pages/SettingsPage.tsx` if setup hooks live there
- `src/pages/*` related to setup wizard
- `src-tauri/src/lib.rs` only if needed for startup health reporting
- `scripts/*` for bootstrap and validation
- `docs/*` if necessary

# Files out of scope for Phase A

Do not fully redesign:
- workspace supervisor runtime logic
- media intelligence scoring pipeline
- automation scheduling/publishing engine
- release packaging internals beyond minimal Phase A readiness checks

# Expected deliverables

## Code deliverables
- synchronized dependency/install structure
- improved diagnostics backend
- improved setup wizard / first-run flow in UI
- canonical bootstrap scripts
- readiness state model
- version/docs alignment

## Documentation deliverables
- updated root README development setup
- dependency install matrix
- “common setup failures” section

# Acceptance criteria

Phase A is complete only if all are true:

1. A fresh developer can determine what is missing without guessing.
2. Missing optional dependencies do not crash the app.
3. Missing required dependencies are surfaced clearly with fixes.
4. A canonical install path exists and is documented.
5. Diagnostics return structured results, not just vague messages.
6. README and in-app setup messaging are consistent with current repo state.
7. A validation checklist or script exists and runs.

# Validation you must run

Run and report as many as applicable:
- frontend build
- backend import / boot test
- diagnostics endpoint test
- migration check
- first-run/setup UI sanity verification
- any new script execution

# Output format after implementation

Return exactly:
1. Scope completed
2. Files changed
3. Dependency structure summary
4. Diagnostics changes
5. Setup wizard changes
6. Validation commands run
7. Validation results
8. Known limitations
9. Recommended Phase B handoff
