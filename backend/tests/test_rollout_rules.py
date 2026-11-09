from datetime import UTC, datetime, timedelta

import pytest

from app.domain.enums import ReleaseStatus, RolloutDecision
from app.rollout.decision import ReleaseSignal, SLOThresholds, evaluate_release, percentile
from app.rollout.state_machine import IllegalTransition, transition


def healthy_signal(**overrides) -> ReleaseSignal:
    values = {
        "stage_index": 0,
        "final_stage_index": 1,
        "sample_count": 50,
        "error_rate": 0.01,
        "latency_samples_ms": [100.0, 120.0, 140.0, 160.0, 180.0] * 10,
        "readiness": True,
        "restart_count": 0,
        "resource_pressure": 0.2,
        "telemetry_available": True,
        "observed_at": datetime.now(UTC),
        "now": datetime.now(UTC),
    }
    values.update(overrides)
    return ReleaseSignal(**values)


def test_percentile_uses_distribution_not_average() -> None:
    value = percentile([10.0, 20.0, 30.0, 40.0, 1000.0], 95)
    assert value is not None and value > 800


def test_healthy_stage_promotes() -> None:
    decision = evaluate_release(healthy_signal(), SLOThresholds())
    assert decision.decision == RolloutDecision.PROMOTE
    assert decision.evidence_complete is True


def test_small_sample_is_not_healthy() -> None:
    decision = evaluate_release(healthy_signal(sample_count=5), SLOThresholds(minimum_sample_count=20))
    assert decision.decision == RolloutDecision.INSUFFICIENT_EVIDENCE


def test_stale_telemetry_is_not_healthy() -> None:
    observed_at = datetime.now(UTC) - timedelta(seconds=120)
    decision = evaluate_release(healthy_signal(observed_at=observed_at), SLOThresholds(observation_window_seconds=60))
    assert decision.decision == RolloutDecision.INSUFFICIENT_EVIDENCE


def test_error_breach_halts_first_stage_and_rolls_back_later() -> None:
    first = evaluate_release(healthy_signal(error_rate=0.4, stage_index=0), SLOThresholds())
    later = evaluate_release(healthy_signal(error_rate=0.4, stage_index=1), SLOThresholds())
    assert first.decision == RolloutDecision.HALT
    assert later.decision == RolloutDecision.ROLLBACK


def test_illegal_state_transition_is_rejected() -> None:
    assert transition(ReleaseStatus.CREATED, ReleaseStatus.VALIDATING).current == ReleaseStatus.VALIDATING
    with pytest.raises(IllegalTransition):
        transition(ReleaseStatus.SUCCEEDED, ReleaseStatus.OBSERVING)
