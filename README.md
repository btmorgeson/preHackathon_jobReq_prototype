# Job Req -> Candidate Ranking Prototype

FastAPI + Neo4j + Next.js prototype that ranks synthetic employees against job requirements using a calibrated 3-pillar score:
- Skill match
- Role-history similarity
- Experience chunk similarity

## Architecture
- Data pipeline: O*NET fetch -> synthetic data generation -> graph CSV export -> Neo4j import -> embedding/index creation
- Backend API: `src/api`
- Frontend app: `frontend`
- Orchestrator scripts: `scripts`
- Local Neo4j runtime options:
  - Vagrant + VirtualBox (work-machine default)
  - Docker Compose (alternate path)

## Vagrant + VirtualBox Quickstart (Windows PowerShell)
1. Ensure VirtualBox CLI is reachable in the current shell:
```powershell
if (-not (Test-Path "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe")) {
  throw "VirtualBox not found at C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
}
$env:Path += ";C:\Program Files\Oracle\VirtualBox"
```
2. Boot VM and provision Neo4j:
```powershell
vagrant up
```
Note: provisioning is secure-first and includes an automatic TLS fallback for corporate intercept environments.
3. Build graph CSV exports on host:
```powershell
python scripts/03_build_graph_csv.py
```
4. Create a fresh Neo4j graph database inside VM:
```powershell
vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"
```
5. Validate environment:
```powershell
python scripts/validate_env.py --profile pipeline
```
6. Start API:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task api
```
7. Start frontend (new terminal):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task frontend
```
8. Run smoke tests (new terminal):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task smoke
```

## Docker Compose Quickstart (Alternate)
If you need the container path instead of Vagrant:
```powershell
docker compose up -d neo4j
python scripts/validate_env.py --profile pipeline
python scripts/run_pipeline.py
```

## Task Matrix
- `powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task setup`: env contract validation
- `powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task pipeline`: full pipeline with quality gates
- `powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task api`: FastAPI dev server
- `powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task frontend`: Next.js dev server
- `powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task smoke`: API smoke test suite
- `powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task vagrant-up`: boot/provision VM
- `powershell -ExecutionPolicy Bypass -File scripts/tasks.ps1 -Task vagrant-reset`: rebuild fresh graph DB in VM

## Key API Contracts
- `POST /api/search`
  - supports `req_number`, `role_title`, `role_description`, `query_context`, skills, weights, `top_k`
  - returns `request_id`, `timings_ms`, ranked candidates
- `GET /api/postings/{req_number}`
- `POST /api/extract-skills`

Errors return a consistent envelope:
```json
{
  "error": {
    "code": "validation_error|http_error|internal_error",
    "message": "human-readable message",
    "request_id": "uuid",
    "details": {}
  }
}
```

## Testing and CI
- Backend unit tests: `pytest -q`
- Frontend checks: `npm.cmd run lint`, `npm.cmd run build` from `frontend/`
- Frontend e2e checks: `npm.cmd run test:e2e` from `frontend/`
  - First-time local setup: `npx.cmd playwright install chromium`
- CI workflow: `.github/workflows/ci.yml`
