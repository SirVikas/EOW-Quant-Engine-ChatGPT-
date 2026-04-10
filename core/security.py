from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import cfg, parse_control_api_keys


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    role: str
    token_preview: str


def ensure_auth_ready_for_mode() -> None:
    """Fail closed in LIVE mode if privileged API auth cannot be enforced."""
    if cfg.TRADE_MODE == "LIVE" and not cfg.AUTH_ENABLED:
        raise RuntimeError("AUTH_ENABLED must be true in LIVE mode")
    if cfg.AUTH_ENABLED and not parse_control_api_keys(cfg.CONTROL_API_KEYS):
        raise RuntimeError("CONTROL_API_KEYS is empty or invalid while AUTH_ENABLED=true")


def _resolve_auth(credentials: HTTPAuthorizationCredentials | None) -> AuthContext:
    if not cfg.AUTH_ENABLED:
        return AuthContext(role="admin", token_preview="auth-disabled")

    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = credentials.credentials.strip()
    role = parse_control_api_keys(cfg.CONTROL_API_KEYS).get(token)
    if not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return AuthContext(role=role, token_preview=f"{token[:4]}***")


def require_roles(*roles: str):
    allowed = {r.lower() for r in roles}

    def _guard(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> AuthContext:
        ctx = _resolve_auth(credentials)
        if ctx.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return ctx

    return _guard
