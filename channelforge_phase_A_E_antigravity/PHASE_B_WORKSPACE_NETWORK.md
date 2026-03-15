# PHASE B PROMPT — WORKSPACE SUPERVISOR + NETWORK POLICY MANAGER

Dán prompt này vào Antigravity để code **Phase B only**.

---

You are working on `channelforge-studio-v5`.
Implement **Phase B only**.

# Phase B Goal

Turn the current workspace feature set into a real runtime control system for per-channel browser environments.

The repo already has workspaces, proxy profiles, launch/health/archive concepts, and a Workspaces UI.
Phase B must turn that into a coherent **Workspace Supervisor** plus **Network Policy Manager** so that each channel workspace behaves like a persistent, auditable environment.

Important: this phase is about **workspace isolation and route policy**, not anti-detect or fingerprint spoofing.

# High-level operating model

The app should operate with three planes:

## Local Processing Plane
These remain on default/local networking:
- research ingestion
- script generation
- subtitle generation
- rendering
- local indexing/reranking
- most asset processing

## Workspace Plane
Each channel gets its own isolated workspace:
- persistent browser user data directory
- downloads directory
- screenshots directory
- logs directory
- notes / metadata / policy settings
- health state
- audit trail

## Publish Plane
Only jobs that interact with YouTube Studio/browser publication should use the workspace route policy:
- open studio
- verify session
- upload video
- upload thumbnail (if enabled)
- schedule/publish via browser workflow if used
- manual review sessions inside studio

# What Phase B must solve

## B1. Workspace runtime state machine

Introduce or complete a formal lifecycle for workspaces.
Suggested states:
- `new`
- `initialized`
- `launching`
- `opened`
- `login_required`
- `verifying`
- `verified`
- `upload_ready`
- `degraded`
- `stopped`
- `archived`
- `failed`

Requirements:
- state transitions must be explicit
- timestamps should be persisted
- last error / last verification info should be queryable
- UI should show state clearly

## B2. Runtime registry and supervision

Build or complete an in-memory + persisted supervisor layer that can:
- track live browser runtimes by workspace id
- open workspace runtime
- close gracefully
- relaunch
- force-kill if needed
- heartbeat / liveness updates
- reconcile registry vs DB after restart

If there is already a `workspace_supervisor.py`, harden it instead of rewriting blindly.

## B3. Persistent browser isolation

Each workspace must use its own persistent browser storage.

Requirements:
- unique user data dir per workspace
- never use the user’s default Chrome profile
- clear directory conventions inside workspace storage
- persisted downloads/screenshots/temporary files per workspace
- restart-safe

## B4. Workspace verification

Implement a verifier layer that can tell whether a workspace is:
- merely opened
- requires login
- logged in but not studio-ready
- verified for studio
- upload-ready

Verification should not just check “browser opened”.
Use deterministic checks around expected URLs, DOM markers, cookies/session state if appropriate.
Design this to be resilient rather than brittle.

## B5. Network Policy Manager

Implement a dedicated policy layer for network route decisions.

For each workspace and job type, define policy values like:
- `DIRECT`
- `WORKSPACE_ROUTE`
- `BLOCK`

At minimum support policy for:
- `studio_open`
- `studio_verify`
- `upload_video`
- `upload_thumbnail`
- `analytics_browser_pull`
- `manual_browser_session`

Requirements:
- route decision should be explainable
- every decision should be logged in an audit trail
- if a workspace route is missing for a job requiring it, the action should fail with a clear message
- local processing tasks should not be accidentally routed through workspace network policy

## B6. Proxy/route binding UX hardening

The existing proxy profile UI must become a robust route binding workflow.

Requirements:
- proxy/route profile create/edit/test/bind/unbind
- show last test result, last test time, latency, outward IP if available
- show which workspaces are currently bound to which route
- prevent destructive deletion if a route is still actively bound unless confirmed

## B7. Health + audit trail

Every workspace should accumulate useful runtime history:
- launches
- close/relaunch events
- verification attempts
- network policy decisions
- proxy test events
- runtime failures

Logs should be queryable by workspace and time range.

## B8. UI integration

Update the workspace UI so it becomes operational, not just informational.
It should include:
- workspace list with state badges
- selected workspace detail panel
- runtime actions
- verification panel
- route binding panel
- audit/history view
- health summary

# Files likely in scope

Prefer modifying/extending existing files rather than inventing parallel systems:
- `engine/app/routers/workspaces.py`
- `engine/app/services/workspace_supervisor.py`
- `engine/app/services/workspace_manager.py` if still needed
- `engine/app/services/network_policy_manager.py`
- `engine/app/services/workspace_verifier.py`
- `engine/app/db.py`
- `engine/app/migrations/*`
- `src/pages/WorkspacesPage.tsx`
- related frontend API/types/components

# Strong constraints

- No anti-detect implementation
- No fingerprint spoofing
- No use of default user Chrome profile
- No secret leakage in logs
- No destructive refactor that breaks existing workspace CRUD without migration

# Data model expectations

Add tables/columns as needed for things like:
- workspace runtime state snapshot
- workspace lifecycle events
- route profiles / bindings
- route decision audit trail
- verification history

Use migrations.

# Acceptance criteria

Phase B is complete only if all are true:

1. Each workspace has a real persisted runtime/state model.
2. Browser runtimes can be opened, closed, relaunched, and tracked.
3. Session verification distinguishes login-required vs verified vs upload-ready.
4. Route policy exists and is enforced for browser publication actions.
5. Local processing is not incorrectly coupled to workspace route.
6. UI exposes enough control and observability to manage multiple channel workspaces.
7. Workspace and route actions are logged in an audit trail.

# Validation you must run

- DB migration run
- backend import/boot
- workspace API sanity tests
- route binding/test flow
- runtime open/close/relaunch sanity test
- UI build sanity test

If browser runtime cannot be fully tested in this environment, clearly say which parts are structurally implemented vs fully executed.

# Output format after implementation

Return exactly:
1. Scope completed
2. Runtime state model summary
3. Network policy model summary
4. Files changed
5. Migrations added
6. API/UI changes
7. Validation commands run
8. Validation results
9. Known limitations
10. Recommended Phase C handoff
