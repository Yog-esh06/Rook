from enum import StrEnum


class ReleaseStatus(StrEnum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    DEPLOYING_CANARY = "DEPLOYING_CANARY"
    OBSERVING = "OBSERVING"
    PROMOTING = "PROMOTING"
    SUCCEEDED = "SUCCEEDED"
    HALTED = "HALTED"
    ROLLING_BACK = "ROLLING_BACK"
    VERIFYING = "VERIFYING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class RolloutDecision(StrEnum):
    PROMOTE = "PROMOTE"
    CONTINUE = "CONTINUE_OBSERVATION"
    HALT = "HALT"
    ROLLBACK = "ROLLBACK"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ExperimentType(StrEnum):
    ELEVATED_ERRORS = "elevated_errors"
    DELAYED_RESPONSES = "delayed_responses"
    READINESS_FAILURE = "readiness_failure"
    CRASH_LOOP = "crash_loop"
    RESOURCE_PRESSURE = "resource_pressure"
    TELEMETRY_UNAVAILABLE = "telemetry_unavailable"


class HealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
