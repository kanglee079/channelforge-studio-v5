# PHASE E PROMPT — PACKAGING / INSTALLER / RELEASE HARDENING

Dán prompt này vào Antigravity để code **Phase E only**.

---

You are working on `channelforge-studio-v5`.
Implement **Phase E only**.

# Phase E Goal

Make the project feel like a serious desktop product rather than a developer-only repo.
Phase E is about packaging, installer readiness, sidecar bundling, release validation, and first-run reliability.

# What Phase E must solve

## E1. Sidecar strategy hardening

The desktop app already launches the Python backend. Make this robust and release-oriented.

Requirements:
- prefer bundled sidecar/external binary strategy for release builds
- maintain a workable dev mode path
- clearly separate dev boot from packaged boot
- expose clear backend state to the desktop shell
- handle startup timeout, retries, and failure explanation

## E2. Release build consistency

Ensure release build assumptions are synchronized across:
- Tauri config
- app version metadata
- sidecar naming/path conventions
- scripts/build_engine_sidecar.py or equivalent
- release check scripts
- docs

## E3. Installer readiness

Make the Windows-first release flow coherent.
At minimum the repo should support a documented and validated path to produce a desktop installer.

Requirements:
- release prerequisites documented
- build order deterministic
- sidecar presence checked before bundle
- release checklist script or command exists
- output locations documented

## E4. First-run resilience in packaged app

The packaged app should degrade gracefully if runtime pieces are missing or broken.
Examples:
- cannot start engine
- DB migration failed
- FFmpeg missing
- browser dependencies missing
- invalid config

The desktop UI must surface these states clearly and point the user to remediation via diagnostics/setup.

## E5. Support bundle / troubleshooting package

Implement or harden a support bundle export that can collect non-sensitive diagnostics such as:
- app version
- OS info
- diagnostics results
- migration status
- logs
- feature availability matrix

Must be sanitized and exclude secrets/credentials.

## E6. Release validation automation

Create or improve a release validation script/checklist that verifies:
- version sync
- frontend build success
- backend import success
- migration readiness
- sidecar binary existence
- expected output bundle paths
- critical docs present

## E7. Documentation quality

Update docs so a real operator can:
- set up dev environment
- build sidecar
- build desktop app
- troubleshoot common failures
- understand what is bundled vs expected externally

# Files likely in scope

- `src-tauri/tauri.conf.json`
- `src-tauri/src/lib.rs`
- packaging/build scripts under `scripts/`
- docs/release/setup files
- diagnostics/setup UI if required to support packaged mode
- README sections related to build/release

# Strong constraints

- Do not turn Phase E into a huge architectural rewrite
- Prefer improving existing sidecar/release flow
- Keep dev workflow usable while strengthening packaged workflow
- Do not add secrets into build outputs

# Acceptance criteria

Phase E is complete only if all are true:

1. There is a coherent dev-vs-release backend startup model.
2. Release scripts/checks can verify the app is packageable.
3. Installer/build documentation is accurate and aligned with code.
4. Packaged app failure states are surfaced clearly.
5. Support bundle export is sanitized and useful.
6. The repo feels significantly closer to a releasable desktop product.

# Validation you must run

- frontend build
- backend import/boot sanity
- release check script
- any sidecar build script sanity check
- tauri config validation if feasible

If full desktop bundling cannot be executed in the environment, state clearly which parts were structurally implemented and what remains environment-dependent.

# Output format after implementation

Return exactly:
1. Scope completed
2. Packaging/release architecture summary
3. Files changed
4. Scripts/docs added or updated
5. Validation commands run
6. Validation results
7. Known limitations
8. Final readiness summary
