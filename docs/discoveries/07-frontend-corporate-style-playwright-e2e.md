# Discovery 07: Frontend Corporate-Tech Refresh + Playwright E2E

## Date
2026-03-06

## Scope
Capture the finalized frontend modernization workflow and repeatable e2e verification path.

## What Changed
- Replaced baseline prototype styling with a tokenized corporate-tech system in `frontend/app/globals.css`.
- Refined app shell and state surfaces in `frontend/app/page.tsx`.
- Updated component UX and hierarchy in:
  - `frontend/components/SearchForm.tsx`
  - `frontend/components/SkillEditor.tsx`
  - `frontend/components/CandidateTable.tsx`
  - `frontend/components/ScoreBreakdown.tsx`
- Added committed Playwright harness:
  - `frontend/playwright.config.ts`
  - `frontend/e2e/app.spec.ts`
- Added frontend scripts:
  - `npm.cmd run test:e2e`
  - `npm.cmd run test:e2e:headed`
  - `npm.cmd run test:e2e:report`

## Deterministic Test Strategy
- E2E specs mock backend API routes (`/api/postings`, `/api/extract-skills`, `/api/search`).
- Tests validate both style+function outcomes without requiring live FastAPI backend uptime.
- Coverage includes:
  - Req-number search flow
  - Role-description extraction flow
  - Async submit-button gating (`Wait for skill sync...`)
  - Table sort/selection/evidence behavior
  - Mobile viewport table horizontal scroll usability

## Commands Run
```powershell
cd frontend
npm.cmd run lint
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

## Results
- `npm.cmd run lint`: pass with one existing non-blocking warning from TanStack `useReactTable`.
- `npm.cmd run build`: pass.
- `npm.cmd run test:e2e`: `3 passed`.

## Operational Notes
- Corporate network can block `next/font/google`; local font stacks avoid build-time TLS fetch failures.
- If a local `next dev` instance is already running, Playwright should reuse it to avoid `.next/dev/lock` conflicts.
- First-time Playwright setup on a host requires browser bootstrap (`npx.cmd playwright install chromium`).

## Recommendation
- Keep `npm.cmd run test:e2e` as the frontend pre-commit gate alongside lint/build.
- Retain mocked e2e route responses as the default deterministic path; add optional live-backend e2e suite only when needed.
