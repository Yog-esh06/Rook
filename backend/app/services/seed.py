from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application, Cluster, SLOPolicy, Workload


def ensure_demo_data(db: Session) -> tuple[Application, Cluster, Workload, SLOPolicy]:
    application = db.scalar(select(Application).where(Application.slug == "checkout-api"))
    if application is None:
        application = Application(
            name="Checkout API",
            slug="checkout-api",
            repository_url="https://github.com/Yog-esh06/Rook/tree/main/sample_app",
            owner="platform-team",
        )
        db.add(application)
        db.flush()

    cluster = db.scalar(select(Cluster).where(Cluster.name == "rook-local"))
    if cluster is None:
        cluster = Cluster(
            name="rook-local",
            provider_type="local-gateway",
            environment="demo",
            connection_status="CONNECTED",
        )
        db.add(cluster)
        db.flush()

    workload = db.scalar(select(Workload).where(Workload.deployment_name == "checkout-api"))
    if workload is None:
        workload = Workload(
            application_id=application.id,
            cluster_id=cluster.id,
            namespace="rook-demo",
            deployment_name="checkout-api",
            current_image="rook/sample-app:v1",
            current_version="v1",
            desired_replicas=2,
            available_replicas=2,
            health_status="HEALTHY",
            traffic_split={"stable": 100, "canary": 0},
            pod_snapshot=[
                {
                    "name": "checkout-api-7cc84d9c6d-1",
                    "image": "rook/sample-app:v1",
                    "ready": True,
                    "restarts": 0,
                },
                {
                    "name": "checkout-api-7cc84d9c6d-2",
                    "image": "rook/sample-app:v1",
                    "ready": True,
                    "restarts": 0,
                },
            ],
        )
        db.add(workload)
        db.flush()

    policy = db.scalar(select(SLOPolicy).where(SLOPolicy.workload_id == workload.id))
    if policy is None:
        policy = SLOPolicy(
            workload_id=workload.id,
            name="Checkout production guardrail",
            availability_target=0.99,
            error_threshold=0.05,
            latency_threshold_ms=350.0,
            readiness_target=1.0,
            minimum_sample_count=20,
            observation_window_seconds=60,
            max_restart_count=0,
            max_resource_pressure=0.85,
        )
        db.add(policy)
    db.commit()
    return application, cluster, workload, policy
