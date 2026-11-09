# Runbook: telemetry unavailable

Rook treats telemetry unavailability as insufficient evidence. Do not force promotion to unblock the rollout.

1. Check the control-plane health endpoint.
2. Check the sample workload `/metrics` endpoint.
3. Inspect the last observation timestamp in Release Center.
4. Verify that the observation window has not gone stale.
5. Re-run the stage only after telemetry is readable and sample count meets policy.
