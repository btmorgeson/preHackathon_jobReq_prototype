# AGENTS.md

## Purpose
Repo-level operating rules for Codex in `preHackathon_jobReq_prototype`.

## Scope
This file applies to this repository root and all child paths. If a deeper `AGENTS.md` exists in a subdirectory, the deeper file overrides this one for files in that subtree.

## Instruction Precedence
Use this precedence order when instructions conflict:
1. System/developer/user prompt instructions
2. Deeper `AGENTS.md` files (closer to the edited file)
3. This root `AGENTS.md`
4. Referenced docs (for example `CLAUDE.md`, runbooks)

## Startup Checklist
1. Confirm current `cwd` and active branch.
2. Read this `AGENTS.md`.
3. Read `CLAUDE.md`.
4. For non-trivial tasks, read:
   - `memory-bank/activeContext.md`
   - `memory-bank/progress.md`
5. Run targeted checks before and after changes; do not assume behavior.

## Execution Policy
1. Plan first for non-trivial changes.
2. Prefer additive, minimal, and reversible edits over rewrites unless replacement is explicitly requested.
3. Reproduce defects before fixing where practical.
4. Validate with targeted tests/checks after edits.
5. Explicitly report risks, potential regressions, and missing tests in review-style outputs.

## Command Source of Truth
Keep concrete runtime commands, architecture notes, and operational runbooks in `CLAUDE.md` and repository docs. Do not duplicate large command/runbook blocks in this file.

## Windows Notes
1. Prefer `npm.cmd` and `npx.cmd` in PowerShell/Git Bash environments with shim restrictions.
2. Use `python -m uvicorn` instead of assuming `uvicorn` is on `PATH`.
3. Keep `PYTHONPATH=.` expectations aligned with `CLAUDE.md`.

## Codex Local Inputs
The following local files commonly influence Codex behavior for this repo and workstation:
1. `AGENTS.md` (this file, repo-scoped instructions)
2. `CLAUDE.md` (repo command/architecture guidance; canonical command source)
3. `memory-bank/activeContext.md` (current working context)
4. `memory-bank/progress.md` (execution history and validation state)
5. `C:\Users\%USERNAME%\.codex\AGENTS.md` (global Codex policy)
6. `C:\Users\%USERNAME%\.codex\config.toml` (Codex config/profiles)
7. `C:\Users\%USERNAME%\.codex\skills\*\SKILL.md` (skill instructions when triggered by task)

## Out of Scope
1. Do not store volatile command outputs in this file.
2. Do not copy large procedural runbooks into this file.
3. Link to `CLAUDE.md` and `docs/` for detailed operational procedures.
