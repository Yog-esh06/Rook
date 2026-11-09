from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.domain.enums import RolloutDecision


def percentile(values: list[float], percentile_rank: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    if percentile_rank <= 0:
        return float(ordered[0])
    if percentile_rank >= 100:
        return float(ordered[-1])
    index = (len(ordered) - 1) * percentile_rank / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return float(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction)


@dataclass(frozen=True)
class SLOThresholds:
    error_threshold: float = 0.05
    latency_threshold_ms: float = 350.0
    readiness_target: float = 1.0
    minimum_sample_count: int = 20
    observation_window_seconds: int = 60
    max_restart_count: int = 0
    max_resource_pressure: float = 0.85


@dataclass(frozen=True)
class ReleaseSignal:
    stage_index: int
    final_stage_index: int
    sample_count: int
    error_rate: float | None
    latency_samples_ms: list[float]
    readiness: bool | None
    restart_count: int | None
    resource_pressure: float | None
    telemetry_available: bool
    observed_at: datetime | None
    now: datetime | None = None


@dataclass(frozen=True)
class Decision:
    decision: RolloutDecision
    reason: str
    observed_p95_latency_ms: float | None
    evidence_complete: bool


def evaluate_release(signal: ReleaseSignal, thresholds: SLOThresholds) -> Decision:
    now = signal.now or datetime.now(UTC)
    if not signal.telemetry_available:
        return Decision(
            RolloutDecision.INSUFFICIENT_EVIDENCE,
            "Telemetry is unavailable, so Rook will not treat this stage as healthy.",
            percentile(signal.latency_samples_ms, 95),
            False,
        )
    if signal.observed_at is None:
        return Decision(
            RolloutDecision.INSUFFICIENT_EVIDENCE,
            "No observation timestamp is available for this rollout stage.",
            percentile(signal.latency_samples_ms, 95),
            False,
        )
    if now - signal.observed_at > timedelta(seconds=thresholds.observation_window_seconds):
        return Decision(
            RolloutDecision.INSUFFICIENT_EVIDENCE,
            "The telemetry sample is stale and cannot support a rollout decision.",
            percentile(signal.latency_samples_ms, 95),
            False,
        )
    if signal.sample_count < thresholds.minimum_sample_count:
        return Decision(
            RolloutDecision.INSUFFICIENT_EVIDENCE,
            f"Only {signal.sample_count} requests were observed; at least {thresholds.minimum_sample_count} are required.",
            percentile(signal.latency_samples_ms, 95),
            False,
        )

    p95 = percentile(signal.latency_samples_ms, 95)
    violations: list[str] = []
    if signal.error_rate is None:
        violations.append("error rate is missing")
    elif signal.error_rate > thresholds.error_threshold:
        violations.append(
            f"error rate {signal.error_rate:.2%} exceeds {thresholds.error_threshold:.2%}"
        )
    if p95 is None:
        violations.append("latency samples are missing")
    elif p95 > thresholds.latency_threshold_ms:
        violations.append(
            f"p95 latency {p95:.1f} ms exceeds {thresholds.latency_threshold_ms:.1f} ms"
        )
    if signal.readiness is not True:
        violations.append("readiness is not healthy")
    if signal.restart_count is not None and signal.restart_count > thresholds.max_restart_count:
        violations.append(
            f"restart count {signal.restart_count} exceeds {thresholds.max_restart_count}"
        )
    if (
        signal.resource_pressure is not None
        and signal.resource_pressure > thresholds.max_resource_pressure
    ):
        violations.append(
            f"resource pressure {signal.resource_pressure:.0%} exceeds {thresholds.max_resource_pressure:.0%}"
        )

    if violations:
        reason = "Release health threshold breached: " + "; ".join(violations) + "."
        decision = RolloutDecision.ROLLBACK if signal.stage_index > 0 else RolloutDecision.HALT
        return Decision(decision, reason, p95, True)

    if signal.stage_index >= signal.final_stage_index:
        return Decision(
            RolloutDecision.PROMOTE,
            "All configured health signals are within threshold at the final traffic stage.",
            p95,
            True,
        )
    return Decision(
        RolloutDecision.PROMOTE,
        "Health signals are within threshold with sufficient fresh evidence for the next stage.",
        p95,
        True,
    )
