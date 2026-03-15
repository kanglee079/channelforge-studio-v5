# MASTER ORCHESTRATION PROMPT — CHANNELFORGE V5.8

Dán prompt này sau `GLOBAL_RULES_AND_GUARDRAILS.md`.

---

You are the implementation lead for the repository `channelforge-studio-v5`.

Your job is to evolve the current codebase into a stable, desktop-first, all-in-one YouTube channel operating system without breaking the existing structure.

## Current repo context to respect

The repo already presents itself as ChannelForge Studio v5.8 with:
- Tauri 2 desktop shell
- React + TypeScript frontend
- Python FastAPI engine
- SQLite database
- workspace pages and proxy UI
- media intelligence modules and routes
- system/setup/diagnostics pages
- script → media match → render → upload positioning

However, the repository must now be hardened and completed in phases so it can move from an alpha-quality desktop app to an operational system.

## Global objective

Implement the remaining work in **five tightly scoped phases**:

- Phase A: Foundation, dependency readiness, bootstrap, docs, diagnostics synchronization
- Phase B: Workspace Supervisor + Network Policy Manager
- Phase C: Media Intelligence Layer
- Phase D: Automation Controller
- Phase E: Packaging, installer hardening, release readiness

## Critical instruction

Do **not** attempt all phases at once.

When I send the next phase-specific prompt, work **only** on that phase.

## Required output before coding each phase

Before modifying code, produce these artifacts:

1. Phase understanding
2. Exact files you plan to touch
3. New files you plan to create
4. DB migrations needed
5. Dependency changes needed
6. Validation plan
7. Risk list and mitigation

Then implement.

## Required output after coding each phase

Return:

1. Summary of what was built
2. File-by-file change list
3. Commands to validate
4. Validation results
5. Known limitations
6. Suggested prompt for the next phase handoff

## Additional constraints

- Preserve repo shape where possible
- Prefer additive changes over destructive rewrites
- Keep current UI routes stable where practical
- Keep current API prefixes stable unless migration is explicitly provided
- Keep current DB usable and migrate forward safely
- Build for Windows-first desktop usage, without blocking future macOS/Linux support
- Prefer local processing by default, with cloud providers as optional adapters

Acknowledge readiness for Phase A only. Do not implement anything until the Phase A prompt is provided.
