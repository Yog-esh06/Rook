# Development guide

```powershell
python -m pip install -e "backend[test,quality]"
python -m pytest -q
python -m ruff check backend
Set-Location frontend
npm install --no-audit --no-fund
node node_modules/typescript/bin/tsc --noEmit
npm run build
```

Use `scripts/start-local.ps1` for the API, `scripts/run_local_demo.py` for a full healthy and unhealthy evidence run, and `scripts/reset_demo.py` to remove the local SQLite database. Kubernetes manifest and Helm structure checks are provided under `scripts/`.
