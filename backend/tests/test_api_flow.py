from fastapi.testclient import TestClient

from app.main import app


def test_healthy_release_then_controlled_rollback() -> None:
    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        workload = client.get("/api/v1/workloads").json()[0]

        healthy = client.post(
            "/api/v1/releases",
            json={
                "workload_id": workload["id"],
                "release_version": "test-v2",
                "image_reference": "rook/sample-app:test-v2",
                "strategy": "canary",
            },
        )
        assert healthy.status_code == 201
        healthy_id = healthy.json()["id"]
        assert client.post(f"/api/v1/releases/{healthy_id}/run").status_code == 202
        healthy_detail = client.get(f"/api/v1/releases/{healthy_id}").json()
        assert healthy_detail["status"] == "SUCCEEDED"
        assert [step["target_traffic_percentage"] for step in healthy_detail["steps"]] == [10, 25, 50, 100]

        failed = client.post(
            "/api/v1/releases",
            json={
                "workload_id": workload["id"],
                "release_version": "test-v3",
                "image_reference": "rook/sample-app:test-v3",
                "strategy": "canary",
                "failure_mode": "elevated_errors",
            },
        )
        assert failed.status_code == 201
        failed_id = failed.json()["id"]
        assert client.post(f"/api/v1/releases/{failed_id}/run").status_code == 202
        failed_detail = client.get(f"/api/v1/releases/{failed_id}").json()
        assert failed_detail["status"] == "ROLLED_BACK"
        assert client.get("/api/v1/incidents").json()[0]["recovery_status"] == "RECOVERED"
        assert client.get(f"/api/v1/workloads/{workload['id']}").json()["current_version"] == "test-v2"


def test_experiment_route_rejects_invalid_sample_counts() -> None:
    with TestClient(app) as client:
        workload = client.get("/api/v1/workloads").json()[0]

        response = client.post(
            "/api/v1/experiments",
            json={
                "workload_id": workload["id"],
                "experiment_type": "elevated_errors",
                "release_version": "v2",
                "sample_count": 5,
            },
        )

        assert response.status_code == 422
