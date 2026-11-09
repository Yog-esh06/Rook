from enum import StrEnum

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


class Role(StrEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


ROLE_ORDER = {Role.VIEWER: 1, Role.OPERATOR: 2, Role.ADMIN: 3}


def require_role(required: Role):
    async def dependency(
        role_header: str | None = Header(default=None, alias="X-Rook-Role"),
    ) -> Role:
        settings = get_settings()
        if not settings.auth_enabled:
            return Role.OPERATOR
        raw_role = (role_header or Role.VIEWER.value).lower()
        try:
            role = Role(raw_role)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Unknown role"
            ) from exc
        if ROLE_ORDER[role] < ROLE_ORDER[required]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return role

    return dependency
