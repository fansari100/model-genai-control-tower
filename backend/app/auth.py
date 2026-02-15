"""
JWT / OIDC authentication middleware for the Control Tower API.

Validates bearer tokens issued by Keycloak using RS256 JWKS verification.
Extracts user identity and roles, provides FastAPI dependencies for RBAC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

import httpx
import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

logger = structlog.get_logger()

security = HTTPBearer(auto_error=False)


class Role(str, Enum):
    ADMIN = "admin"
    MODEL_RISK_OFFICER = "model_risk_officer"
    MODEL_CONTROL_ANALYST = "model_control_analyst"
    BUSINESS_LINE_HEAD = "business_line_head"
    AUDITOR = "auditor"
    DEVELOPER = "developer"


@dataclass
class CurrentUser:
    """Resolved identity from a validated JWT token."""

    sub: str
    username: str
    email: str
    full_name: str
    roles: list[Role] = field(default_factory=list)

    @property
    def is_admin(self) -> bool:
        return Role.ADMIN in self.roles

    @property
    def is_approver(self) -> bool:
        return bool(
            {Role.ADMIN, Role.MODEL_RISK_OFFICER, Role.BUSINESS_LINE_HEAD} & set(self.roles)
        )

    @property
    def can_write(self) -> bool:
        return Role.AUDITOR not in self.roles or self.is_admin


# ── JWKS cache ───────────────────────────────────────────────────────────────
_jwks_cache: dict | None = None


async def _fetch_jwks() -> dict:
    """Fetch and cache the Keycloak JWKS for token verification."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    settings = get_settings()
    jwks_url = (
        f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
        f"/protocol/openid-connect/certs"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            logger.info("jwks_fetched", url=jwks_url, keys=len(_jwks_cache.get("keys", [])))
            return _jwks_cache
    except Exception as e:
        logger.warning("jwks_fetch_failed", url=jwks_url, error=str(e))
        return {"keys": []}


def _clear_jwks_cache() -> None:
    """Clear JWKS cache (call on 401 to force refresh)."""
    global _jwks_cache
    _jwks_cache = None


async def _decode_token(token: str) -> dict:
    """Decode and verify a Keycloak-issued JWT using JWKS."""
    settings = get_settings()

    try:
        from jose import jwt, JWTError, jwk
        from jose.utils import base64url_decode

        # Fetch JWKS from Keycloak
        jwks = await _fetch_jwks()

        # Decode header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find the matching key
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            # Key not found — clear cache and retry once
            _clear_jwks_cache()
            jwks = await _fetch_jwks()
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token signing key not found in JWKS",
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            options={"verify_aud": True, "verify_exp": True},
        )
        return payload

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("jwt_decode_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Development user (used when Keycloak is unreachable) ─────────────────────
_DEV_USER = CurrentUser(
    sub="dev-user-001",
    username="dev",
    email="dev@controltower.local",
    full_name="Development User",
    roles=[Role.ADMIN],
)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    """
    FastAPI dependency – resolves the current user from the Authorization header.

    Behavior:
    - Production: validates JWT via Keycloak JWKS. 401 if invalid.
    - Development: if no token is provided AND Keycloak is unreachable,
      returns a dev user. If a token IS provided, it is always validated.
    """
    settings = get_settings()

    if credentials is None:
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Non-production: attempt JWKS connectivity check
        try:
            jwks = await _fetch_jwks()
            if not jwks.get("keys"):
                # Keycloak not running — allow dev bypass
                return _DEV_USER
        except Exception:
            return _DEV_USER

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required (Keycloak is reachable)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token provided — always validate regardless of environment
    payload = await _decode_token(credentials.credentials)

    realm_access = payload.get("realm_access", {})
    token_roles = realm_access.get("roles", [])
    mapped_roles: list[Role] = []
    for r in token_roles:
        try:
            mapped_roles.append(Role(r))
        except ValueError:
            pass  # Ignore roles not in our enum

    return CurrentUser(
        sub=payload.get("sub", ""),
        username=payload.get("preferred_username", ""),
        email=payload.get("email", ""),
        full_name=payload.get("name", ""),
        roles=mapped_roles,
    )


# ── Role-checking dependency factories ───────────────────────────────────────


def require_roles(*required: Role):
    """Return a dependency that checks the user has at least one of the required roles."""

    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.is_admin:
            return user
        if not (set(required) & set(user.roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {[r.value for r in required]}",
            )
        return user

    return _check


require_admin = require_roles(Role.ADMIN)
require_approver = require_roles(Role.ADMIN, Role.MODEL_RISK_OFFICER, Role.BUSINESS_LINE_HEAD)
require_analyst = require_roles(Role.ADMIN, Role.MODEL_CONTROL_ANALYST, Role.MODEL_RISK_OFFICER)
require_write = require_roles(
    Role.ADMIN, Role.MODEL_CONTROL_ANALYST, Role.MODEL_RISK_OFFICER, Role.DEVELOPER
)
