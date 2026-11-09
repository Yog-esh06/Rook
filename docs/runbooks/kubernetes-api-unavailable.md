# Runbook: Kubernetes API unavailable

1. Check the selected context with `kubectl config current-context`.
2. Check namespace visibility with `kubectl get ns` and `kubectl -n rook-demo get deploy,pods,events`.
3. Verify the Rook service account has only the permissions in `deployment/kubernetes/control-plane-rbac.yaml`.
4. Treat workload state as stale until a successful observation timestamp is recorded.
5. Do not label a rollback recovered because the API command returned. Wait for readiness and application health.
