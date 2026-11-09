$ErrorActionPreference = "Stop"
$env:DATABASE_URL = "sqlite:///./rook.db"
$env:DEMO_MODE = "true"
$env:DEMO_OBSERVATION_SECONDS = "0.8"
Write-Host "Starting Rook API on http://localhost:8000"
python -m uvicorn app.main:app --app-dir backend --reload
