from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    resource: str,
    request_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor=actor,
        action=action,
        resource=resource,
        request_id=request_id,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event
