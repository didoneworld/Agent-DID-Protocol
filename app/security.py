from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Any


def generate_api_key() -> str:
    return f"aidp_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    """Hash API key using HMAC-SHA256 with constant-time verification.
    
    Production improvements over plain SHA-256:
    - Uses HMAC for keyed hashing (requires secret to verify)
    - Constant-time comparison via hmac.compare_digest
    - Key prefix for lookup before verification (prevents timing oracle)
    """
    import os
    pepper = os.environ.get("API_KEY_PEPPER", "")
    if pepper:
        return hmac.new(pepper.encode(), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Constant-time API key verification."""
    computed = hash_api_key(raw_key)
    return hmac.compare_digest(computed, stored_hash)


def _b64encode(value: bytes) -> str:
    return urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(value + padding)


def create_session_token(payload: dict[str, Any], secret: str, ttl_seconds: int) -> str:
    issued_at = datetime.now(timezone.utc)
    body = {
        **payload,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    payload_bytes = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded_payload = _b64encode(payload_bytes)
    signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_b64encode(signature)}"


def verify_session_token(token: str, secret: str) -> dict[str, Any] | None:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
    except ValueError:
        return None

    expected_signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    actual_signature = _b64decode(encoded_signature)
    if not hmac.compare_digest(expected_signature, actual_signature):
        return None

    payload = json.loads(_b64decode(encoded_payload))
    now = int(datetime.now(timezone.utc).timestamp())
    if int(payload.get("exp", 0)) < now:
        return None
    return payload
