# Security notes

The local preview is intentionally frictionless and has authentication disabled. Set `AUTH_ENABLED=true` before using mutation routes outside the local preview. The role dependency recognizes `viewer`, `operator`, and `admin` through the configured `X-Rook-Role` header.

The Kubernetes integration is namespace-scoped. Raw kubeconfig material is not stored in application records. Deployment manifests use non-root execution, a runtime default seccomp profile, dropped Linux capabilities, read-only root filesystems, and explicit resource limits.

The local defaults are not production credentials. Use a managed secret store, restrictive CORS origins, signed sessions, and external identity in a real deployment.
