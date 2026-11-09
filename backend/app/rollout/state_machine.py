from dataclasses import dataclass

from app.domain.enums import ReleaseStatus

ALLOWED_TRANSITIONS: dict[ReleaseStatus, set[ReleaseStatus]] = {
    ReleaseStatus.CREATED: {ReleaseStatus.VALIDATING, ReleaseStatus.FAILED},
    ReleaseStatus.VALIDATING: {ReleaseStatus.DEPLOYING_CANARY, ReleaseStatus.FAILED},
    ReleaseStatus.DEPLOYING_CANARY: {
        ReleaseStatus.OBSERVING,
        ReleaseStatus.HALTED,
        ReleaseStatus.FAILED,
    },
    ReleaseStatus.OBSERVING: {
        ReleaseStatus.PROMOTING,
        ReleaseStatus.HALTED,
        ReleaseStatus.ROLLING_BACK,
        ReleaseStatus.FAILED,
    },
    ReleaseStatus.PROMOTING: {
        ReleaseStatus.OBSERVING,
        ReleaseStatus.SUCCEEDED,
        ReleaseStatus.HALTED,
    },
    ReleaseStatus.HALTED: {ReleaseStatus.ROLLING_BACK, ReleaseStatus.FAILED},
    ReleaseStatus.ROLLING_BACK: {ReleaseStatus.VERIFYING, ReleaseStatus.FAILED},
    ReleaseStatus.VERIFYING: {
        ReleaseStatus.RECOVERED,
        ReleaseStatus.ROLLED_BACK,
        ReleaseStatus.FAILED,
    },
    ReleaseStatus.SUCCEEDED: set(),
    ReleaseStatus.RECOVERED: set(),
    ReleaseStatus.ROLLED_BACK: set(),
    ReleaseStatus.FAILED: set(),
}


@dataclass(frozen=True)
class TransitionResult:
    previous: ReleaseStatus
    current: ReleaseStatus


class IllegalTransition(ValueError):
    pass


def transition(current: ReleaseStatus | str, target: ReleaseStatus | str) -> TransitionResult:
    current_status = ReleaseStatus(current)
    target_status = ReleaseStatus(target)
    if target_status not in ALLOWED_TRANSITIONS[current_status]:
        raise IllegalTransition(f"Illegal release transition: {current_status} -> {target_status}")
    return TransitionResult(previous=current_status, current=target_status)
