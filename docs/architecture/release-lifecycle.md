# Release lifecycle

```mermaid
stateDiagram-v2
  [*] --> CREATED
  CREATED --> VALIDATING
  VALIDATING --> DEPLOYING_CANARY
  DEPLOYING_CANARY --> OBSERVING
  OBSERVING --> PROMOTING: fresh evidence passes
  PROMOTING --> OBSERVING: next stage
  OBSERVING --> SUCCEEDED: 100% passes
  OBSERVING --> HALTED: first-stage breach
  OBSERVING --> ROLLING_BACK: later-stage breach
  HALTED --> ROLLING_BACK
  ROLLING_BACK --> VERIFYING
  VERIFYING --> ROLLED_BACK: stable recovers
  VERIFYING --> FAILED: recovery fails
```

Rook never treats missing, stale, or undersampled telemetry as a pass. The decision record includes the observed error rate, p95 latency, readiness, restart count, resource pressure, sample count, and reason.
