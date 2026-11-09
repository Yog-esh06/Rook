# API notes

Rook exposes OpenAPI at `/docs` and `/openapi.json`. The canonical route list and PowerShell examples are in the root [README](../README.md#api-reference).

Mutation errors use standard HTTP responses:

| Code | Meaning |
|---:|---|
| 400 | Domain validation or an active release conflict |
| 403 | Role is not permitted for the action |
| 404 | Workload, release, incident, or resource does not exist |
| 409 | Release is already in a non-creatable state |
| 422 | Pydantic or experiment payload validation failed |

Every response includes an `X-Request-ID` header. Send one when correlating an operator action with structured logs and audit events.
