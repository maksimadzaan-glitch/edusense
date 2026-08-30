"""HMAC session tokens for EduSense API auth."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = "edusense-dev-session-secret-change-me"

SESSION_TTL_SEC = int(
    os.environ.get("EDUSENSE_SESSION_TTL_SEC")
    or str(int(os.environ.get("EDUSENSE_SESSION_TTL_DAYS", "30")) * 24 * 60 * 60)
)


def session_secret() -> str:
    return (
        os.environ.get("EDUSENSE_SESSION_SECRET")
        or os.environ.get("SECRET_KEY")
        or _DEFAULT_SECRET
    )


def warn_if_insecure_secret() -> None:
    secret = session_secret()
    env = (os.environ.get("EDUSENSE_ENV") or os.environ.get("ENV") or "").strip().lower()
    if secret == _DEFAULT_SECRET and env in ("production", "prod"):
        logger.critical(
            "EDUSENSE_SESSION_SECRET is not set in production — sessions can be forged. "
            "Set EDUSENSE_SESSION_SECRET in the server environment."
        )


def issue_access_token(user_id: int) -> str:
    exp = int(time.time()) + SESSION_TTL_SEC
    payload = f"{int(user_id)}.{exp}"
    sig = hmac.new(
        session_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:40]
    return f"{payload}.{sig}"


def verify_access_token(token: str) -> Optional[int]:
    raw = str(token or "").strip()
    if not raw:
        return None
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    parts = raw.split(".")
    if len(parts) != 3:
        return None
    uid_s, exp_s, sig = parts
    try:
        uid = int(uid_s)
        exp = int(exp_s)
    except ValueError:
        return None
    if exp < int(time.time()):
        return None
    payload = f"{uid}.{exp}"
    expected = hmac.new(
        session_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:40]
    if not hmac.compare_digest(expected, sig):
        return None
    return uid


def extract_bearer(
    authorization: Optional[str] = None, x_edusense_token: Optional[str] = None
) -> str:
    if authorization and authorization.strip():
        return authorization.strip()
    if x_edusense_token and x_edusense_token.strip():
        return x_edusense_token.strip()
    return ""
