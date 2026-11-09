# Rook architecture

Rook separates the control plane from cluster state, telemetry, rollout evaluation, and the operator portal.

```mermaid
flowchart LR
  UI[Next.js operations console] --> API[FastAPI control plane]
  API --> DB[(PostgreSQL or SQLite)]
  API --> AUDIT[Audit and incident records]
  API --> DECIDE[Deterministic decision engine]
  DECIDE --> GATE[Local traffic gateway]
  DECIDE --> K8S[Kubernetes adapter]
  GATE --> STABLE[Stable workload]
  GATE --> CANARY[Canary workload]
  STABLE --> METRICS[Prometheus metrics]
  CANARY --> METRICS
  METRICS --> API
```

The default preview uses SQLite and an in-process gateway so it can run without a paid cloud account or a local cluster. The Kubernetes adapter is an explicit integration boundary. The cluster deployment manifests are provided for Kind, k3d, or an external cluster.
