import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.security import Role, require_role
from app.db import SessionLocal, get_db, init_db
from app.domain.enums import ReleaseStatus
from app.models import (
    Application,
    AuditEvent,
    Cluster,
    ExperimentRun,
    Incident,
    Release,
    SLOPolicy,
    Workload,
)
from app.schemas.api import (
    ApplicationResponse,
    AuditResponse,
    ClusterResponse,
    ExperimentCreate,
    ExperimentResponse,
    ExperimentRunResponse,
    HealthResponse,
    IncidentResponse,
    OverviewResponse,
    ReleaseCreate,
    ReleaseDetail,
    ReleaseResponse,
    SettingsResponse,
    SLOPolicyResponse,
    WorkloadResponse,
)
from app.services.audit import record_audit
from app.services.release_service import create_release, run_experiment, run_release
from app.services.seed import ensure_demo_data

settings = get_settings()
logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings.log_level)
    init_db()
    db = SessionLocal()
    try:
        ensure_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Rook Control Plane",
    version="0.1.0",
    description="Release safely. Detect failure. Recover with evidence.",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID", "X-Rook-Role"],
)
app.mount("/metrics", make_asgi_app())


def _release_response(release: Release) -> ReleaseResponse:
    return ReleaseResponse.model_validate(release, from_attributes=True)


def _incident_response(incident: Incident) -> IncidentResponse:
    return IncidentResponse.model_validate(incident, from_attributes=True)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def health(db: Session = Depends(get_db)) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        database="reachable",
        demo_mode=settings.demo_mode,
        timestamp=datetime.now(UTC),
    )


@app.get("/api/v1/overview", response_model=OverviewResponse, tags=["overview"])
def overview(db: Session = Depends(get_db)) -> OverviewResponse:
    workloads = list(db.scalars(select(Workload).order_by(Workload.created_at)))
    connected_clusters = (
        db.scalar(select(func.count(Cluster.id)).where(Cluster.connection_status == "CONNECTED"))
        or 0
    )
    total_slos = db.scalar(select(func.count(SLOPolicy.id))) or 0
    healthy_slos = (
        db.scalar(
            select(func.count(SLOPolicy.id))
            .join(Workload)
            .where(Workload.health_status == "HEALTHY")
        )
        or 0
    )
    active_statuses = [
        ReleaseStatus.VALIDATING.value,
        ReleaseStatus.DEPLOYING_CANARY.value,
        ReleaseStatus.OBSERVING.value,
        ReleaseStatus.PROMOTING.value,
        ReleaseStatus.HALTED.value,
        ReleaseStatus.ROLLING_BACK.value,
        ReleaseStatus.VERIFYING.value,
    ]
    active_releases = (
        db.scalar(select(func.count(Release.id)).where(Release.status.in_(active_statuses))) or 0
    )
    failed_rollouts = (
        db.scalar(
            select(func.count(Release.id)).where(
                Release.status.in_([ReleaseStatus.FAILED.value, ReleaseStatus.ROLLED_BACK.value])
            )
        )
        or 0
    )
    open_incidents = (
        db.scalar(select(func.count(Incident.id)).where(Incident.recovery_status == "OPEN")) or 0
    )
    latest_release = db.scalar(select(Release).order_by(Release.started_at.desc()).limit(1))
    latest_incident = db.scalar(select(Incident).order_by(Incident.created_at.desc()).limit(1))
    return OverviewResponse(
        cluster_count=db.scalar(select(func.count(Cluster.id))) or 0,
        connected_clusters=connected_clusters,
        workload_count=len(workloads),
        active_releases=active_releases,
        failed_rollouts=failed_rollouts,
        open_incidents=open_incidents,
        healthy_slos=healthy_slos,
        total_slos=total_slos,
        latest_release=_release_response(latest_release) if latest_release else None,
        latest_incident=_incident_response(latest_incident) if latest_incident else None,
        workloads=[
            WorkloadResponse.model_validate(item, from_attributes=True) for item in workloads
        ],
    )


@app.get("/api/v1/applications", response_model=list[ApplicationResponse], tags=["catalog"])
def applications(db: Session = Depends(get_db)) -> list[Application]:
    return list(db.scalars(select(Application).order_by(Application.name)))


@app.get("/api/v1/clusters", response_model=list[ClusterResponse], tags=["catalog"])
def clusters(db: Session = Depends(get_db)) -> list[Cluster]:
    return list(db.scalars(select(Cluster).order_by(Cluster.name)))


@app.get("/api/v1/workloads", response_model=list[WorkloadResponse], tags=["workloads"])
def workloads(db: Session = Depends(get_db)) -> list[Workload]:
    return list(db.scalars(select(Workload).order_by(Workload.deployment_name)))


@app.get("/api/v1/workloads/{workload_id}", response_model=WorkloadResponse, tags=["workloads"])
def workload(workload_id: str, db: Session = Depends(get_db)) -> Workload:
    item = db.get(Workload, workload_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Workload not found")
    return item


@app.get(
    "/api/v1/workloads/{workload_id}/events", response_model=list[AuditResponse], tags=["workloads"]
)
def workload_events(workload_id: str, db: Session = Depends(get_db)) -> list[AuditEvent]:
    return list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.resource.in_([f"workload/{workload_id}", "seed/demo"]))
            .order_by(AuditEvent.created_at.desc())
            .limit(50)
        )
    )


@app.get("/api/v1/workloads/{workload_id}/telemetry", tags=["telemetry"])
def workload_telemetry(workload_id: str, db: Session = Depends(get_db)) -> dict:
    if db.get(Workload, workload_id) is None:
        raise HTTPException(status_code=404, detail="Workload not found")
    releases = list(
        db.scalars(
            select(Release)
            .where(Release.workload_id == workload_id)
            .order_by(Release.started_at.desc())
            .limit(5)
        )
    )
    steps = [
        step
        for release in releases
        for step in sorted(release.steps, key=lambda item: item.observed_at, reverse=True)
    ]
    return {
        "workload_id": workload_id,
        "available": bool(steps),
        "last_observed_at": steps[0].observed_at if steps else None,
        "samples": [
            {
                "release_id": step.release_id,
                "version": next(
                    (
                        release.release_version
                        for release in releases
                        if release.id == step.release_id
                    ),
                    "unknown",
                ),
                "traffic": step.target_traffic_percentage,
                "sample_count": step.request_sample_count,
                "error_rate": step.observed_error_rate,
                "p95_latency_ms": step.observed_p95_latency_ms,
                "readiness": step.readiness_status,
                "telemetry_available": step.telemetry_available,
                "observed_at": step.observed_at,
            }
            for step in steps[:20]
        ],
    }


@app.get("/api/v1/slo-policies", response_model=list[SLOPolicyResponse], tags=["slo"])
def slo_policies(db: Session = Depends(get_db)) -> list[SLOPolicy]:
    return list(db.scalars(select(SLOPolicy).order_by(SLOPolicy.name)))


@app.get("/api/v1/releases", response_model=list[ReleaseResponse], tags=["releases"])
def releases(db: Session = Depends(get_db)) -> list[Release]:
    return list(db.scalars(select(Release).order_by(Release.started_at.desc()).limit(50)))


@app.get("/api/v1/releases/{release_id}", response_model=ReleaseDetail, tags=["releases"])
def release_detail(release_id: str, db: Session = Depends(get_db)) -> Release:
    item = db.get(Release, release_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return item


@app.post(
    "/api/v1/releases",
    response_model=ReleaseResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["releases"],
)
def create_release_route(
    payload: ReleaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: Role = Depends(require_role(Role.OPERATOR)),
) -> Release:
    try:
        item = create_release(
            db,
            workload_id=payload.workload_id,
            release_version=payload.release_version,
            image_reference=payload.image_reference,
            strategy=payload.strategy,
            failure_mode=payload.failure_mode.value if payload.failure_mode else None,
            created_by=payload.created_by,
        )
        record_audit(
            db,
            actor=payload.created_by,
            action="release.requested",
            resource=f"release/{item.id}",
            request_id=request.state.request_id,
            metadata={"version": payload.release_version},
        )
        db.commit()
        return item
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/api/v1/releases/{release_id}/run", status_code=status.HTTP_202_ACCEPTED, tags=["releases"]
)
def run_release_route(
    release_id: str,
    background_tasks: BackgroundTasks,
    sample_count: int | None = Query(default=None, ge=20, le=5000),
    db: Session = Depends(get_db),
    _: Role = Depends(require_role(Role.OPERATOR)),
) -> dict:
    item = db.get(Release, release_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Release not found")
    if item.status != ReleaseStatus.CREATED.value:
        raise HTTPException(status_code=409, detail=f"Release is already {item.status}")
    background_tasks.add_task(run_release, release_id, sample_count=sample_count)
    return {"release_id": release_id, "status": "QUEUED", "message": "Release execution started"}


@app.get("/api/v1/incidents", response_model=list[IncidentResponse], tags=["incidents"])
def incidents(db: Session = Depends(get_db)) -> list[Incident]:
    return list(db.scalars(select(Incident).order_by(Incident.created_at.desc()).limit(50)))


@app.get("/api/v1/incidents/{incident_id}", response_model=IncidentResponse, tags=["incidents"])
def incident(incident_id: str, db: Session = Depends(get_db)) -> Incident:
    item = db.get(Incident, incident_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return item


@app.get("/api/v1/audit", response_model=list[AuditResponse], tags=["audit"])
def audit(
    action: str | None = None,
    actor: str | None = None,
    db: Session = Depends(get_db),
) -> list[AuditEvent]:
    query = select(AuditEvent)
    if action:
        query = query.where(AuditEvent.action == action)
    if actor:
        query = query.where(AuditEvent.actor == actor)
    return list(db.scalars(query.order_by(AuditEvent.created_at.desc()).limit(200)))


@app.get("/api/v1/experiments", response_model=list[ExperimentRunResponse], tags=["experiments"])
def experiments(db: Session = Depends(get_db)) -> list[ExperimentRun]:
    return list(
        db.scalars(select(ExperimentRun).order_by(ExperimentRun.started_at.desc()).limit(50))
    )


@app.post(
    "/api/v1/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["experiments"],
)
def create_experiment(
    payload: ExperimentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: Role = Depends(require_role(Role.OPERATOR)),
) -> ExperimentResponse:
    workload_id = payload.workload_id
    experiment_type = payload.experiment_type
    release_version = payload.release_version
    sample_count = (
        payload.sample_count if payload.sample_count is not None else settings.demo_sample_count
    )
    if db.get(Workload, workload_id) is None:
        raise HTTPException(status_code=404, detail="Workload not found")
    try:
        release = create_release(
            db,
            workload_id=workload_id,
            release_version=release_version,
            image_reference=f"rook/sample-app:{release_version}",
            strategy="canary",
            failure_mode=experiment_type.value,
            created_by="reliability-lab",
        )
        experiment = ExperimentRun(
            release_id=release.id,
            experiment_type=experiment_type.value,
            status="QUEUED",
            configuration={"sample_count": sample_count, "failure_mode": experiment_type.value},
        )
        db.add(experiment)
        db.flush()
        record_audit(
            db,
            actor="reliability-lab",
            action="experiment.started",
            resource=f"experiment/{experiment.id}",
            request_id=None,
            metadata={"type": experiment_type.value, "release_id": release.id},
        )
        db.commit()
        background_tasks.add_task(run_experiment, experiment.id, sample_count=sample_count)
        return ExperimentResponse(
            id=experiment.id,
            release_id=release.id,
            experiment_type=experiment_type,
            status="QUEUED",
            message="Controlled experiment queued against the disposable demo workload",
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/settings", response_model=SettingsResponse, tags=["settings"])
def app_settings() -> SettingsResponse:
    return SettingsResponse(
        environment=settings.environment,
        demo_mode=settings.demo_mode,
        rollout_stages=settings.rollout_stages,
        observation_seconds=settings.demo_observation_seconds,
        sample_count=settings.demo_sample_count,
        auth_enabled=settings.auth_enabled,
    )


@app.websocket("/api/v1/ws/releases/{release_id}")
async def release_socket(websocket: WebSocket, release_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                release = db.get(Release, release_id)
                if release is None:
                    await websocket.send_json({"error": "Release not found"})
                    return
                payload = ReleaseDetail.model_validate(release, from_attributes=True).model_dump(
                    mode="json"
                )
            finally:
                db.close()
            await websocket.send_json(payload)
            if release.status in {
                ReleaseStatus.SUCCEEDED.value,
                ReleaseStatus.ROLLED_BACK.value,
                ReleaseStatus.FAILED.value,
            }:
                return
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
