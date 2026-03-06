# Frontend

Next.js frontend for the candidate ranking prototype.

## Commands
From `frontend/`:
```bash
npm run dev
npm run lint
npm run build
npm run test:e2e
```

The app expects `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).
Playwright e2e tests mock API endpoints (`/api/postings`, `/api/extract-skills`, `/api/search`) and do not require a live backend.

Use the root [README](../README.md) for full system startup and pipeline instructions.
