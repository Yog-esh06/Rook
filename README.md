# Rook

Release safely. Detect failure. Recover with evidence.

Rook is a local-first release and reliability control plane for Kubernetes workloads. The project focuses on safe progressive delivery decisions using observable runtime signals such as request volume, latency, error rate, readiness, restarts, resource pressure, and telemetry freshness.

The repository includes a working local demo mode and an optional Kubernetes deployment layout for teams that want to extend the same control-plane model beyond a laptop environment.

## What is in this repository

- FastAPI control plane in `backend/`
- SQLAlchemy models, rollout logic, telemetry evaluation, and audit records in `backend/app/`
- Next.js operations portal in `frontend/`
- Sample workload used for local canary stress and recovery scenarios in `sample-app/`
- Compose and Kubernetes assets in `deployment/`
- Reproducible demo evidence in `experiments/latest-run.json`
- Validation and demo scripts in `scripts/`

## Verified local workflow

The core local release flow is implemented and verified in this repository:

- create a workload release
- run a canary rollout across 10, 25, 50, and 100 percent traffic
- evaluate fresh evidence against configured SLO thresholds
- halt a failing canary when the breach is detected
- roll back to the previous healthy version
- verify recovery and record the incident timeline

The main verification check is the backend test suite. It covers rollout state transitions, latency percentile evaluation, minimum sample safeguards, stale telemetry handling, threshold decisions, API validation, rollback and recovery behavior, and audit-visible outcomes.

## Quick start

### 1. Install Python dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -e "backend[test]"
```

### 2. Install frontend dependencies

```powershell
Set-Location frontend
npm install
Set-Location ..
```

### 3. Start the API

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```

### 4. Start the portal

```powershell
Set-Location frontend
npm run dev
```

Then open:

- http://127.0.0.1:3000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/api/v1/health

No login is required in the default local mode.

## Run the automated demo

The local demo script exercises a healthy release and a controlled rollback path against the sample workload.

```powershell
python scripts/run_local_demo.py
```

This writes a fresh evidence record to `experiments/latest-run.json`.

## API highlights

The FastAPI app exposes the main operational endpoints:

- GET `/api/v1/health`
- GET `/api/v1/workloads`
- GET `/api/v1/releases`
- POST `/api/v1/releases`
- POST `/api/v1/releases/{id}/run`
- GET `/api/v1/incidents`
- GET `/api/v1/audit`
- GET `/api/v1/slo-policies`
- GET `/api/v1/experiments`
- POST `/api/v1/experiments`
- GET `/api/v1/settings`

The OpenAPI docs are available at http://127.0.0.1:8000/docs.

## Testing

Run the project tests from the repository root:

```powershell
python -m pytest -q
```

This is the validated baseline for the project as currently implemented.

## Optional deployment paths

The repository also includes deployment assets for Docker Compose and Kubernetes:

- `docker-compose.yml`
- `deployment/kubernetes/`
- `deployment/helm/rook/`
- `deployment/prometheus/`
- `deployment/grafana/`

These files are included for local and platform-oriented deployment workflows, but the live-cluster paths were not validated against a real Kubernetes cluster in this environment.

## Project layout

```text
Rook/
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
├── deployment/
├── docs/
├── experiments/
├── sample-app/
├── scripts/
├── docker-compose.yml
├── pytest.ini
├── README.md
├── LICENSE
└── .gitignore
```

## Notes

- Local mode uses SQLite by default and does not require a cluster or cloud account.
- The sample runtime is intentionally deterministic and runs through the ASGI gateway for realistic request handling without external infrastructure.
- Docker and Kubernetes assets are present, but they are optional components for broader deployment workflows.

## Creator

Built by YOGESH R MEHTA

GitHub: https://github.com/Yog-esh06
LinkedIn: https://www.linkedin.com/in/yog-esh06/
