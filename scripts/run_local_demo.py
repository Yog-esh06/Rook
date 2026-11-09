import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


BASE_URL = os.getenv("ROOK_API_URL", "http://127.0.0.1:8000")
ROOT = Path(__file__).resolve().parents[1]


def wait_for_api(client: httpx.Client) -> None:
    for _ in range(30):
        try:
            if client.get("/api/v1/health").is_success:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise SystemExit("Rook API did not become ready")


def wait_for_release(client: httpx.Client, release_id: str) -> dict:
    terminal = {"SUCCEEDED", "ROLLED_BACK", "FAILED"}
    for _ in range(120):
        response = client.get(f"/api/v1/releases/{release_id}")
        response.raise_for_status()
        release = response.json()
        if release["status"] in terminal:
            return release
        time.sleep(0.25)
    raise SystemExit(f"Release {release_id} did not reach a terminal state")


with httpx.Client(base_url=BASE_URL, timeout=30) as client:
    wait_for_api(client)
    workload = client.get("/api/v1/workloads").raise_for_status().json()[0]
    healthy = client.post(
        "/api/v1/releases",
        json={
            "workload_id": workload["id"],
            "release_version": "demo-v2",
            "image_reference": "rook/sample-app:demo-v2",
            "strategy": "canary",
        },
    ).raise_for_status().json()
    client.post(f"/api/v1/releases/{healthy['id']}/run").raise_for_status()
    healthy_detail = wait_for_release(client, healthy["id"])
    failed = client.post(
        "/api/v1/releases",
        json={
            "workload_id": workload["id"],
            "release_version": "demo-v3-fault",
            "image_reference": "rook/sample-app:demo-v3-fault",
            "strategy": "canary",
            "failure_mode": "elevated_errors",
        },
    ).raise_for_status().json()
    client.post(f"/api/v1/releases/{failed['id']}/run").raise_for_status()
    failed_detail = wait_for_release(client, failed["id"])
    incidents = client.get("/api/v1/incidents")
    incidents.raise_for_status()
    incident = next(item for item in incidents.json() if item["release_id"] == failed["id"])

result = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "api_url": BASE_URL,
    "workload_id": workload["id"],
    "healthy_release": healthy_detail,
    "unhealthy_release": failed_detail,
    "incident": incident,
}
output = ROOT / "experiments" / "latest-run.json"
output.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"Wrote evidence to {output.relative_to(ROOT)}")
print(f"Healthy release: {healthy_detail['status']}; unhealthy release: {failed_detail['status']}; recovery: {incident['recovery_status']}")
