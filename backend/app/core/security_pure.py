"""
Pure security helper functions — no DB, no I/O, no side effects.

Extracted from security.py for testability.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def build_token_payload(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    *,
    now: Optional[datetime] = None,
) -> dict:
    """
    Build a JWT payload with expiration, without actually encoding.

    Pure function — caller is responsible for jwt.encode().
    """
    if now is None:
        now = datetime.utcnow()
    to_encode = data.copy()
    expire = now + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return to_encode


def extract_token_fields(payload: dict) -> Dict[str, Any]:
    """
    Extract standard fields from a decoded JWT payload.

    Returns {"user_id", "username", "role"} — all may be None.
    """
    return {
        "user_id": payload.get("user_id"),
        "username": payload.get("sub"),
        "role": payload.get("role"),
    }


def is_token_payload_valid(payload: dict) -> bool:
    """Check whether a decoded JWT payload contains at least one identity field."""
    return payload.get("user_id") is not None or payload.get("sub") is not None


def build_user_response(
    user_id: int,
    username: str,
    email: Optional[str],
    role: str,
    is_superuser: bool,
    is_active: bool,
) -> Dict[str, Any]:
    """
    Build the dict returned by get_current_user.

    Pure — no ORM, no HTTP.
    """
    return {
        "id": user_id,
        "user_id": user_id,
        "username": username,
        "email": email,
        "roles": [role],
        "is_superuser": is_superuser,
        "is_active": is_active,
    }
