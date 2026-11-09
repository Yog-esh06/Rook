# Telemetry flow

The sample workload exposes `/metrics` in Prometheus text format. The local gateway collects request status and latency samples directly from real FastAPI responses. The control plane stores those observations on each rollout step and exposes them through `/api/v1/workloads/{id}/telemetry`.

```mermaid
sequenceDiagram
  participant E as Evaluator
  participant G as Traffic gateway
  participant S as Stable app
  participant C as Canary app
  participant D as Decision record
  E->>G: Observe stage percentage
  G->>S: Route stable requests
  G->>C: Route canary requests
  S-->>G: HTTP status and latency
  C-->>G: HTTP status and latency
  G-->>E: samples, p95, errors, readiness
  E->>D: Persist observation and reason
```
