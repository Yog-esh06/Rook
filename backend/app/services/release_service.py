import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import SessionLocal
from app.domain.enums import ReleaseStatus, RolloutDecision
from app.models import ExperimentRun, Incident, Release, RolloutStep, SLOPolicy, Workload
from app.rollout.decision import ReleaseSignal, SLOThresholds, evaluate_release
from app.rollout.state_machine import IllegalTransition, transition
from app.services.audit import record_audit
from app.services.traffic_gateway import LocalTrafficGateway, TrafficObservation
from app.telemetry.metrics import (
    active_releases,
    observation_latency,
    release_observations,
    release_outcomes,
    release_rollbacks,
)

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _change_status(db: Session, release: Release, target: ReleaseStatus, reason: str) -> None:
    previous_status = release.status
    transition(release.status, target)
    release.status = target.value
    record_audit(
        db,
        actor=release.created_by,
        action="release.transition",
        resource=f"release/{release.id}",
        request_id=None,
        metadata={"from": previous_status, "to": target.value, "reason": reason},
    )


def create_release(
    db: Session,
    *,
    workload_id: str,
    release_version: str,
    image_reference: str,
    strategy: str,
    failure_mode: str | None,
    created_by: str,
) -> Release:
    workload = db.get(Workload, workload_id)
    if workload is None:
        raise ValueError("Workload not found")
    active = db.scalar(
        select(Release).where(
            Release.workload_id == workload_id,
            Release.status.in_(
                [
                    ReleaseStatus.VALIDATING.value,
                    ReleaseStatus.DEPLOYING_CANARY.value,
                    ReleaseStatus.OBSERVING.value,
                    ReleaseStatus.PROMOTING.value,
                    ReleaseStatus.HALTED.value,
                    ReleaseStatus.ROLLING_BACK.value,
                    ReleaseStatus.VERIFYING.value,
                ]
            ),
        )
    )
    if active is not None:
        raise ValueError("A release is already active for this workload")
    release = Release(
        workload_id=workload_id,
        release_version=release_version,
        image_reference=image_reference,
        previous_version=workload.current_version,
        previous_image=workload.current_image,
        strategy=strategy,
        failure_mode=failure_mode,
        created_by=created_by,
    )
    db.add(release)
    db.flush()
    record_audit(
        db,
        actor=created_by,
        action="release.created",
        resource=f"release/{release.id}",
        request_id=None,
        metadata={"version": release_version, "strategy": strategy, "failure_mode": failure_mode},
    )
    db.commit()
    db.refresh(release)
    return release


def _policy_for(db: Session, workload_id: str) -> SLOPolicy:
    policy = db.scalar(select(SLOPolicy).where(SLOPolicy.workload_id == workload_id))
    if policy is None:
        raise ValueError("No SLO policy is configured for this workload")
    return policy


def _thresholds(policy: SLOPolicy) -> SLOThresholds:
    return SLOThresholds(
        error_threshold=policy.error_threshold,
        latency_threshold_ms=policy.latency_threshold_ms,
        readiness_target=policy.readiness_target,
        minimum_sample_count=policy.minimum_sample_count,
        observation_window_seconds=policy.observation_window_seconds,
        max_restart_count=policy.max_restart_count,
        max_resource_pressure=policy.max_resource_pressure,
    )


def _observation_to_signal(
    observation: TrafficObservation,
    *,
    stage_index: int,
    final_stage_index: int,
) -> ReleaseSignal:
    return ReleaseSignal(
        stage_index=stage_index,
        final_stage_index=final_stage_index,
        sample_count=observation.request_sample_count,
        error_rate=observation.error_rate,
        latency_samples_ms=observation.latency_samples_ms,
        readiness=observation.readiness,
        restart_count=observation.restart_count,
        resource_pressure=observation.resource_pressure,
        telemetry_available=observation.telemetry_available,
        observed_at=observation.observed_at,
        now=_now(),
    )


def _timeline_event(
    kind: str, message: str, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "timestamp": _now().isoformat(),
        "kind": kind,
        "message": message,
        "metadata": metadata or {},
    }


async def run_release(release_id: str, *, sample_count: int | None = None) -> None:
    settings = get_settings()
    gateway = LocalTrafficGateway()
    db = SessionLocal()
    try:
        release = db.get(Release, release_id)
        if release is None:
            return
        if release.status != ReleaseStatus.CREATED.value:
            return
        workload = db.get(Workload, release.workload_id)
        policy = _policy_for(db, release.workload_id)
        if workload is None:
            raise ValueError("Workload disappeared before rollout started")
        sample_total = sample_count or settings.demo_sample_count
        stages = settings.rollout_stages
        final_stage_index = len(stages) - 1

        _change_status(db, release, ReleaseStatus.VALIDATING, "Validating workload and policy")
        db.commit()
        await asyncio.sleep(0.05)
        _change_status(
            db,
            release,
            ReleaseStatus.DEPLOYING_CANARY,
            "Applying the candidate version to the demo gateway",
        )
        active_releases.inc()
        db.commit()
        await asyncio.sleep(0.05)

        for stage_index, target in enumerate(stages):
            release = db.get(Release, release_id)
            workload = db.get(Workload, release.workload_id) if release else None
            if release is None or workload is None:
                raise ValueError("Release or workload disappeared during rollout")
            if release.status == ReleaseStatus.DEPLOYING_CANARY.value:
                _change_status(
                    db, release, ReleaseStatus.OBSERVING, f"Observing {target}% canary traffic"
                )
            elif release.status == ReleaseStatus.PROMOTING.value:
                _change_status(
                    db, release, ReleaseStatus.OBSERVING, f"Observing {target}% canary traffic"
                )
            release.current_stage_index = stage_index
            release.traffic_percentage = target
            workload.traffic_split = {"stable": 100 - target, "canary": target}
            workload.last_observed_at = _now()
            db.commit()

            await asyncio.sleep(settings.demo_observation_seconds)
            observation_started = time.perf_counter()
            observation = await gateway.observe(
                stable_version=release.previous_version or workload.current_version,
                candidate_version=release.release_version,
                failure_mode=release.failure_mode,
                target_traffic_percentage=target,
                sample_count=sample_total,
            )
            observation_latency.observe(time.perf_counter() - observation_started)
            decision = evaluate_release(
                _observation_to_signal(
                    observation, stage_index=stage_index, final_stage_index=final_stage_index
                ),
                _thresholds(policy),
            )
            step = RolloutStep(
                release_id=release.id,
                step_number=stage_index + 1,
                target_traffic_percentage=target,
                observed_error_rate=observation.error_rate,
                observed_p95_latency_ms=decision.observed_p95_latency_ms,
                readiness_status=observation.readiness,
                request_sample_count=observation.request_sample_count,
                restart_count=observation.restart_count,
                resource_pressure=observation.resource_pressure,
                telemetry_available=observation.telemetry_available,
                telemetry_observed_at=observation.observed_at,
                decision=decision.decision.value,
                decision_reason=decision.reason,
                latency_samples_ms=observation.latency_samples_ms,
            )
            db.add(step)
            release_observations.labels(decision=decision.decision.value).inc()
            record_audit(
                db,
                actor=release.created_by,
                action="release.observation",
                resource=f"release/{release.id}",
                request_id=None,
                metadata={
                    "stage": target,
                    "decision": decision.decision.value,
                    "error_rate": observation.error_rate,
                    "p95_latency_ms": decision.observed_p95_latency_ms,
                    "sample_count": observation.request_sample_count,
                },
            )
            db.commit()

            if decision.decision not in {RolloutDecision.PROMOTE}:
                await _rollback_release(release_id, decision.reason, observation)
                return

            if stage_index == final_stage_index:
                release = db.get(Release, release_id)
                workload = db.get(Workload, release.workload_id) if release else None
                if release is None or workload is None:
                    raise ValueError("Release or workload disappeared before promotion")
                _change_status(
                    db, release, ReleaseStatus.PROMOTING, "Final stage passed all health checks"
                )
                workload.current_version = release.release_version
                workload.current_image = release.image_reference
                workload.health_status = "HEALTHY"
                workload.available_replicas = workload.desired_replicas
                workload.traffic_split = {"stable": 100, "canary": 0}
                workload.pod_snapshot = [
                    {
                        "name": f"{workload.deployment_name}-{release.release_version}-1",
                        "image": release.image_reference,
                        "ready": True,
                        "restarts": 0,
                    },
                    {
                        "name": f"{workload.deployment_name}-{release.release_version}-2",
                        "image": release.image_reference,
                        "ready": True,
                        "restarts": 0,
                    },
                ]
                _change_status(
                    db, release, ReleaseStatus.SUCCEEDED, "Candidate promoted at 100% traffic"
                )
                release.completed_at = _now()
                active_releases.dec()
                release_outcomes.labels(outcome="succeeded").inc()
                db.commit()
                return

            release = db.get(Release, release_id)
            if release is not None:
                _change_status(
                    db,
                    release,
                    ReleaseStatus.PROMOTING,
                    f"Promoting from {target}% to the next stage",
                )
                db.commit()

        raise RuntimeError("Rollout exited without a terminal state")
    except (IllegalTransition, Exception) as exc:
        logger.exception("Release execution failed", extra={"release_id": release_id})
        db.rollback()
        release = db.get(Release, release_id)
        if release is not None and release.status not in {
            ReleaseStatus.SUCCEEDED.value,
            ReleaseStatus.ROLLED_BACK.value,
        }:
            release.status = ReleaseStatus.FAILED.value
            release.last_error = str(exc)
            release.completed_at = _now()
            record_audit(
                db,
                actor=release.created_by,
                action="release.failed",
                resource=f"release/{release.id}",
                request_id=None,
                metadata={"error": str(exc)},
            )
            db.commit()
    finally:
        db.close()


async def _rollback_release(
    release_id: str, reason: str, failed_observation: TrafficObservation
) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        release_rollbacks.inc()
        release = db.get(Release, release_id)
        if release is None:
            return
        workload = db.get(Workload, release.workload_id)
        if workload is None:
            return
        _change_status(db, release, ReleaseStatus.HALTED, reason)
        incident = Incident(
            release_id=release.id,
            severity="HIGH",
            detected_condition=reason,
            timeline=[
                _timeline_event(
                    "release_started",
                    "Canary observation began",
                    {"traffic": release.traffic_percentage},
                ),
                _timeline_event(
                    "threshold_breach",
                    reason,
                    {
                        "error_rate": failed_observation.error_rate,
                        "candidate_requests": failed_observation.candidate_requests,
                    },
                ),
            ],
            recovery_status="OPEN",
        )
        db.add(incident)
        record_audit(
            db,
            actor=release.created_by,
            action="release.halted",
            resource=f"release/{release.id}",
            request_id=None,
            metadata={"reason": reason},
        )
        db.commit()
        await asyncio.sleep(0.05)

        release = db.get(Release, release_id)
        workload = db.get(Workload, release.workload_id) if release else None
        if release is None or workload is None:
            return
        _change_status(
            db, release, ReleaseStatus.ROLLING_BACK, "Restoring the last healthy version"
        )
        workload.traffic_split = {"stable": 100, "canary": 0}
        workload.health_status = "DEGRADED"
        db.commit()
        await asyncio.sleep(settings.demo_observation_seconds / 2)

        stable_version = release.previous_version or workload.current_version
        verification = await LocalTrafficGateway().observe(
            stable_version=stable_version,
            candidate_version=stable_version,
            failure_mode=None,
            target_traffic_percentage=100,
            sample_count=settings.demo_sample_count,
        )
        decision = evaluate_release(
            ReleaseSignal(
                stage_index=0,
                final_stage_index=0,
                sample_count=verification.request_sample_count,
                error_rate=verification.error_rate,
                latency_samples_ms=verification.latency_samples_ms,
                readiness=verification.readiness,
                restart_count=verification.restart_count,
                resource_pressure=verification.resource_pressure,
                telemetry_available=verification.telemetry_available,
                observed_at=verification.observed_at,
                now=_now(),
            ),
            _thresholds(_policy_for(db, release.workload_id)),
        )
        release = db.get(Release, release_id)
        incident = db.scalar(
            select(Incident)
            .where(Incident.release_id == release_id)
            .order_by(Incident.created_at.desc())
        )
        if release is None or incident is None:
            return
        _change_status(db, release, ReleaseStatus.VERIFYING, "Checking the restored stable version")
        incident.timeline.append(
            _timeline_event(
                "rollback_verification",
                "Stable version was exercised after rollback",
                {
                    "decision": decision.decision.value,
                    "error_rate": verification.error_rate,
                    "p95_latency_ms": decision.observed_p95_latency_ms,
                },
            )
        )
        if decision.decision == RolloutDecision.PROMOTE:
            _change_status(
                db, release, ReleaseStatus.ROLLED_BACK, "Previous healthy version recovered"
            )
            workload.current_version = stable_version
            workload.current_image = release.previous_image or workload.current_image
            workload.health_status = "HEALTHY"
            workload.available_replicas = workload.desired_replicas
            workload.traffic_split = {"stable": 100, "canary": 0}
            incident.recovery_status = "RECOVERED"
            incident.timeline.append(
                _timeline_event("recovered", "Recovery checks passed on the previous version")
            )
            release.completed_at = _now()
            active_releases.dec()
            release_outcomes.labels(outcome="rolled_back").inc()
            record_audit(
                db,
                actor=release.created_by,
                action="release.rollback_recovered",
                resource=f"release/{release.id}",
                request_id=None,
                metadata={"version": stable_version},
            )
        else:
            _change_status(db, release, ReleaseStatus.FAILED, "Rollback verification did not pass")
            incident.recovery_status = "FAILED"
            incident.timeline.append(_timeline_event("recovery_failed", decision.reason))
            release.last_error = decision.reason
            release.completed_at = _now()
            active_releases.dec()
            release_outcomes.labels(outcome="failed").inc()
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Rollback failed", extra={"release_id": release_id})
        release = db.get(Release, release_id)
        if release is not None:
            release.status = ReleaseStatus.FAILED.value
            release.last_error = "Rollback execution failed before recovery could be verified."
            release.completed_at = _now()
            db.commit()
    finally:
        db.close()


async def run_experiment(experiment_id: str, *, sample_count: int | None = None) -> None:
    db = SessionLocal()
    try:
        experiment = db.get(ExperimentRun, experiment_id)
        if experiment is None:
            return
        experiment.status = "RUNNING"
        experiment.started_at = _now()
        db.commit()
        await run_release(experiment.release_id, sample_count=sample_count)
        db = SessionLocal()
        experiment = db.get(ExperimentRun, experiment_id)
        if experiment is None:
            return
        release = db.get(Release, experiment.release_id)
        steps = sorted(release.steps, key=lambda item: item.step_number) if release else []
        incident = db.scalar(
            select(Incident)
            .where(Incident.release_id == experiment.release_id)
            .order_by(Incident.created_at.desc())
        )
        experiment.status = (
            "COMPLETED"
            if release
            and release.status in {ReleaseStatus.SUCCEEDED.value, ReleaseStatus.ROLLED_BACK.value}
            else "FAILED"
        )
        experiment.result = {
            "release_status": release.status if release else "UNKNOWN",
            "steps": [
                {
                    "traffic": step.target_traffic_percentage,
                    "sample_count": step.request_sample_count,
                    "error_rate": step.observed_error_rate,
                    "p95_latency_ms": step.observed_p95_latency_ms,
                    "decision": step.decision,
                }
                for step in steps
            ],
            "incident_id": incident.id if incident else None,
            "recovery_status": incident.recovery_status if incident else None,
        }
        experiment.completed_at = _now()
        db.commit()
    except Exception as exc:
        db.rollback()
        experiment = db.get(ExperimentRun, experiment_id)
        if experiment is not None:
            experiment.status = "FAILED"
            experiment.result = {"error": str(exc)}
            experiment.completed_at = _now()
            db.commit()
    finally:
        db.close()
