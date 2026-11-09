# Runbook: rollback verification failure

If the stable version does not pass its recovery sample, Rook leaves the release in `FAILED` and records an incident with `recovery_status=FAILED`.

1. Preserve the incident and audit evidence.
2. Inspect pod readiness, restart count, and image reference.
3. Confirm the previous image still exists and can be pulled.
4. Repair the workload or image availability before attempting a new release.
5. Re-run the recovery check and record the result.
