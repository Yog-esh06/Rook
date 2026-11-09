"""Create Rook control-plane tables."""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("repository_url", sa.String(500)),
        sa.Column("owner", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_applications_slug", "applications", ["slug"], unique=True)
    op.create_table(
        "clusters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("provider_type", sa.String(80), nullable=False),
        sa.Column("environment", sa.String(80), nullable=False),
        sa.Column("connection_status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workloads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "application_id", sa.String(36), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("cluster_id", sa.String(36), sa.ForeignKey("clusters.id"), nullable=False),
        sa.Column("namespace", sa.String(120), nullable=False),
        sa.Column("deployment_name", sa.String(120), nullable=False),
        sa.Column("current_image", sa.String(300), nullable=False),
        sa.Column("current_version", sa.String(80), nullable=False),
        sa.Column("desired_replicas", sa.Integer, nullable=False),
        sa.Column("available_replicas", sa.Integer, nullable=False),
        sa.Column("health_status", sa.String(40), nullable=False),
        sa.Column("traffic_split", sa.JSON, nullable=False),
        sa.Column("pod_snapshot", sa.JSON, nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("namespace", "deployment_name"),
    )
    op.create_table(
        "slo_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workload_id", sa.String(36), sa.ForeignKey("workloads.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("availability_target", sa.Float, nullable=False),
        sa.Column("error_threshold", sa.Float, nullable=False),
        sa.Column("latency_threshold_ms", sa.Float, nullable=False),
        sa.Column("readiness_target", sa.Float, nullable=False),
        sa.Column("minimum_sample_count", sa.Integer, nullable=False),
        sa.Column("observation_window_seconds", sa.Integer, nullable=False),
        sa.Column("max_restart_count", sa.Integer, nullable=False),
        sa.Column("max_resource_pressure", sa.Float, nullable=False),
    )
    op.create_table(
        "releases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workload_id", sa.String(36), sa.ForeignKey("workloads.id"), nullable=False),
        sa.Column("release_version", sa.String(80), nullable=False),
        sa.Column("image_reference", sa.String(300), nullable=False),
        sa.Column("previous_version", sa.String(80)),
        sa.Column("previous_image", sa.String(300)),
        sa.Column("strategy", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("failure_mode", sa.String(80)),
        sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("current_stage_index", sa.Integer, nullable=False),
        sa.Column("traffic_percentage", sa.Integer, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text),
    )
    op.create_index("ix_release_workload_created", "releases", ["workload_id", "started_at"])
    op.create_table(
        "rollout_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("release_id", sa.String(36), sa.ForeignKey("releases.id"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("target_traffic_percentage", sa.Integer, nullable=False),
        sa.Column("observed_error_rate", sa.Float),
        sa.Column("observed_p95_latency_ms", sa.Float),
        sa.Column("readiness_status", sa.Boolean),
        sa.Column("request_sample_count", sa.Integer, nullable=False),
        sa.Column("restart_count", sa.Integer),
        sa.Column("resource_pressure", sa.Float),
        sa.Column("telemetry_available", sa.Boolean, nullable=False),
        sa.Column("telemetry_observed_at", sa.DateTime(timezone=True)),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("decision_reason", sa.Text, nullable=False),
        sa.Column("latency_samples_ms", sa.JSON, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("release_id", "step_number"),
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("release_id", sa.String(36), sa.ForeignKey("releases.id"), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("detected_condition", sa.Text, nullable=False),
        sa.Column("timeline", sa.JSON, nullable=False),
        sa.Column("recovery_status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "experiment_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("release_id", sa.String(36), sa.ForeignKey("releases.id"), nullable=False),
        sa.Column("experiment_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("configuration", sa.JSON, nullable=False),
        sa.Column("result", sa.JSON, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("resource", sa.String(200), nullable=False),
        sa.Column("request_id", sa.String(100)),
        sa.Column("metadata_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "audit_events",
        "experiment_runs",
        "incidents",
        "rollout_steps",
        "releases",
        "slo_policies",
        "workloads",
        "clusters",
        "applications",
    ]:
        op.drop_table(table)
