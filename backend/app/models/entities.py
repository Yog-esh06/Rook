from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    repository_url: Mapped[str | None] = mapped_column(String(500))
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    workloads: Mapped[list["Workload"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(80), nullable=False)
    environment: Mapped[str] = mapped_column(String(80), nullable=False)
    connection_status: Mapped[str] = mapped_column(String(40), nullable=False, default="CONNECTED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    workloads: Mapped[list["Workload"]] = relationship(
        back_populates="cluster", cascade="all, delete-orphan"
    )


class Workload(Base):
    __tablename__ = "workloads"
    __table_args__ = (
        UniqueConstraint("namespace", "deployment_name", name="uq_workload_namespace_deployment"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    cluster_id: Mapped[str] = mapped_column(
        ForeignKey("clusters.id", ondelete="CASCADE"), index=True
    )
    namespace: Mapped[str] = mapped_column(String(120), nullable=False)
    deployment_name: Mapped[str] = mapped_column(String(120), nullable=False)
    current_image: Mapped[str] = mapped_column(String(300), nullable=False)
    current_version: Mapped[str] = mapped_column(String(80), nullable=False)
    desired_replicas: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    available_replicas: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    health_status: Mapped[str] = mapped_column(String(40), nullable=False, default="HEALTHY")
    traffic_split: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=lambda: {"stable": 100, "canary": 0}
    )
    pod_snapshot: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    application: Mapped[Application] = relationship(back_populates="workloads")
    cluster: Mapped[Cluster] = relationship(back_populates="workloads")
    releases: Mapped[list["Release"]] = relationship(
        back_populates="workload", cascade="all, delete-orphan"
    )
    policies: Mapped[list["SLOPolicy"]] = relationship(
        back_populates="workload", cascade="all, delete-orphan"
    )


class SLOPolicy(Base):
    __tablename__ = "slo_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workload_id: Mapped[str] = mapped_column(
        ForeignKey("workloads.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    availability_target: Mapped[float] = mapped_column(Float, nullable=False, default=0.99)
    error_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    latency_threshold_ms: Mapped[float] = mapped_column(Float, nullable=False, default=350.0)
    readiness_target: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    minimum_sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    observation_window_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    max_restart_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_resource_pressure: Mapped[float] = mapped_column(Float, nullable=False, default=0.85)
    workload: Mapped[Workload] = relationship(back_populates="policies")


class Release(Base):
    __tablename__ = "releases"
    __table_args__ = (Index("ix_release_workload_created", "workload_id", "started_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workload_id: Mapped[str] = mapped_column(
        ForeignKey("workloads.id", ondelete="CASCADE"), index=True
    )
    release_version: Mapped[str] = mapped_column(String(80), nullable=False)
    image_reference: Mapped[str] = mapped_column(String(300), nullable=False)
    previous_version: Mapped[str | None] = mapped_column(String(80))
    previous_image: Mapped[str | None] = mapped_column(String(300))
    strategy: Mapped[str] = mapped_column(String(80), nullable=False, default="canary")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="CREATED", index=True)
    failure_mode: Mapped[str | None] = mapped_column(String(80))
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="local-operator")
    current_stage_index: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
    traffic_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    workload: Mapped[Workload] = relationship(back_populates="releases")
    steps: Mapped[list["RolloutStep"]] = relationship(
        back_populates="release", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="release", cascade="all, delete-orphan"
    )


class RolloutStep(Base):
    __tablename__ = "rollout_steps"
    __table_args__ = (
        Index("ix_rollout_step_release_number", "release_id", "step_number", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    release_id: Mapped[str] = mapped_column(
        ForeignKey("releases.id", ondelete="CASCADE"), index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    target_traffic_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_error_rate: Mapped[float | None] = mapped_column(Float)
    observed_p95_latency_ms: Mapped[float | None] = mapped_column(Float)
    readiness_status: Mapped[bool | None] = mapped_column()
    request_sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    restart_count: Mapped[int | None] = mapped_column(Integer)
    resource_pressure: Mapped[float | None] = mapped_column(Float)
    telemetry_available: Mapped[bool] = mapped_column(nullable=False, default=True)
    telemetry_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    latency_samples_ms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    release: Mapped[Release] = relationship(back_populates="steps")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    release_id: Mapped[str] = mapped_column(
        ForeignKey("releases.id", ondelete="CASCADE"), index=True
    )
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="HIGH")
    detected_condition: Mapped[str] = mapped_column(Text, nullable=False)
    timeline: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recovery_status: Mapped[str] = mapped_column(String(40), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    release: Mapped[Release] = relationship(back_populates="incidents")


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    release_id: Mapped[str] = mapped_column(
        ForeignKey("releases.id", ondelete="CASCADE"), index=True
    )
    experiment_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="QUEUED")
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_created_at", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(200), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(100), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
