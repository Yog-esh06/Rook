from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExperimentType


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    database: str
    demo_mode: bool
    timestamp: datetime


class ApplicationResponse(ORMModel):
    id: str
    name: str
    slug: str
    repository_url: str | None
    owner: str
    created_at: datetime


class ClusterResponse(ORMModel):
    id: str
    name: str
    provider_type: str
    environment: str
    connection_status: str
    created_at: datetime


class WorkloadResponse(ORMModel):
    id: str
    application_id: str
    cluster_id: str
    namespace: str
    deployment_name: str
    current_image: str
    current_version: str
    desired_replicas: int
    available_replicas: int
    health_status: str
    traffic_split: dict[str, Any]
    pod_snapshot: list[dict[str, Any]]
    last_observed_at: datetime | None


class SLOPolicyResponse(ORMModel):
    id: str
    workload_id: str
    name: str
    availability_target: float
    error_threshold: float
    latency_threshold_ms: float
    readiness_target: float
    minimum_sample_count: int
    observation_window_seconds: int
    max_restart_count: int
    max_resource_pressure: float


class ReleaseCreate(BaseModel):
    workload_id: str
    release_version: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    image_reference: str = Field(min_length=1, max_length=300)
    strategy: str = Field(default="canary", pattern=r"^[a-zA-Z0-9_-]+$")
    failure_mode: ExperimentType | None = None
    created_by: str = Field(default="local-operator", min_length=1, max_length=120)


class ReleaseResponse(ORMModel):
    id: str
    workload_id: str
    release_version: str
    image_reference: str
    previous_version: str | None
    previous_image: str | None
    strategy: str
    status: str
    failure_mode: str | None
    created_by: str
    current_stage_index: int
    traffic_percentage: int
    started_at: datetime
    completed_at: datetime | None
    last_error: str | None


class RolloutStepResponse(ORMModel):
    id: str
    release_id: str
    step_number: int
    target_traffic_percentage: int
    observed_error_rate: float | None
    observed_p95_latency_ms: float | None
    readiness_status: bool | None
    request_sample_count: int
    restart_count: int | None
    resource_pressure: float | None
    telemetry_available: bool
    telemetry_observed_at: datetime | None
    decision: str
    decision_reason: str
    latency_samples_ms: list[float]
    observed_at: datetime


class ReleaseDetail(ReleaseResponse):
    steps: list[RolloutStepResponse]


class IncidentResponse(ORMModel):
    id: str
    release_id: str
    severity: str
    detected_condition: str
    timeline: list[dict[str, Any]]
    recovery_status: str
    created_at: datetime


class AuditResponse(ORMModel):
    id: str
    actor: str
    action: str
    resource: str
    request_id: str | None
    metadata_json: dict[str, Any]
    created_at: datetime


class ExperimentCreate(BaseModel):
    workload_id: str
    experiment_type: ExperimentType
    release_version: str = Field(default="v2", min_length=1, max_length=80)
    sample_count: int | None = Field(default=None, ge=20, le=5000)


class ExperimentResponse(BaseModel):
    id: str
    release_id: str
    experiment_type: ExperimentType
    status: str
    message: str


class ExperimentRunResponse(ORMModel):
    id: str
    release_id: str
    experiment_type: str
    status: str
    configuration: dict[str, Any]
    result: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None


class SettingsResponse(BaseModel):
    environment: str
    demo_mode: bool
    rollout_stages: list[int]
    observation_seconds: float
    sample_count: int
    auth_enabled: bool


class OverviewResponse(BaseModel):
    cluster_count: int
    connected_clusters: int
    workload_count: int
    active_releases: int
    failed_rollouts: int
    open_incidents: int
    healthy_slos: int
    total_slos: int
    latest_release: ReleaseResponse | None
    latest_incident: IncidentResponse | None
    workloads: list[WorkloadResponse]
