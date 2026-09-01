"""In-memory presence for live class sessions (TTL-based online status)."""

from __future__ import annotations

import threading
import time
from typing import Any, Optional

_LOCK = threading.Lock()
# class_code.upper() -> { name_key: {ts, name, status, assignment_code} }
_STORE: dict[str, dict[str, dict[str, Any]]] = {}

ONLINE_TTL_SEC = 45.0


def _key(name: str) -> str:
    return " ".join(str(name or "").strip().split()).casefold()


def touch(
    class_code: str,
    student_name: str,
    *,
    status: str = "online",
    assignment_code: Optional[str] = None,
) -> None:
    code = str(class_code or "").strip().upper()
    name = " ".join(str(student_name or "").strip().split())
    if not code or not name:
        return
    st = str(status or "online").strip().lower()
    if st not in ("online", "working", "idle"):
        st = "online"
    nk = _key(name)
    now = time.time()
    with _LOCK:
        bucket = _STORE.setdefault(code, {})
        prev = bucket.get(nk) or {}
        bucket[nk] = {
            "ts": now,
            "name": name,
            "status": st,
            "assignment_code": (
                str(assignment_code or prev.get("assignment_code") or "").strip().upper()
                or None
            ),
        }


def snapshot(class_code: str) -> dict[str, dict[str, Any]]:
    """Return live presence map for class (only fresh entries)."""
    code = str(class_code or "").strip().upper()
    if not code:
        return {}
    now = time.time()
    with _LOCK:
        bucket = _STORE.get(code) or {}
        alive: dict[str, dict[str, Any]] = {}
        stale: list[str] = []
        for nk, row in bucket.items():
            ts = float(row.get("ts") or 0)
            if now - ts > ONLINE_TTL_SEC:
                stale.append(nk)
                continue
            alive[nk] = dict(row)
        for nk in stale:
            bucket.pop(nk, None)
        if not bucket and code in _STORE:
            _STORE.pop(code, None)
        return alive
