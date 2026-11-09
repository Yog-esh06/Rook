# Runbook: failed release

1. Open Release Center and select the failed release.
2. Read the stage evidence. Confirm the breach reason and sample count.
3. Open Incident Timeline and verify the halt, rollback, and recovery events.
4. Inspect Workload Explorer. Confirm stable traffic is 100 percent and replicas are ready.
5. If recovery is not verified, keep the incident open and inspect `/api/v1/workloads/{id}/telemetry` and the API logs.

The local rollback is not considered recovered until a fresh stable request sample passes the same SLO policy.
