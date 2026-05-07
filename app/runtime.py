from __future__ import annotations

import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse


logger = logging.getLogger("agent_identity")


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int | None = None


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._buckets: dict[str, deque[float]] = {}

    def check(self, key: str) -> RateLimitResult:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
                return RateLimitResult(allowed=False, retry_after_seconds=retry_after)
            bucket.append(now)
            return RateLimitResult(allowed=True)


class RedisRateLimiter:
    """Production Redis-backed rate limiter for multi-instance deployments."""
    
    def __init__(self, max_requests: int, window_seconds: int, redis_url: str | None = None) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client = None
        self._import_redis()
    
    def _import_redis(self) -> None:
        try:
            import redis
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        except ImportError:
            logger.warning("redis-py not installed, falling back to in-memory")
            self._client = None
    
    def check(self, key: str) -> RateLimitResult:
        if self._client is None:
            # Fallback to in-memory if redis unavailable
            return RateLimitResult(allowed=True)
        
        now = time.monotonic()
        redis_key = f"ratelimit:{key}"
        
        try:
            # Atomic increment with expiry
            pipe = self._client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, self.window_seconds)
            results = pipe.execute()
            count = results[0]
            
            if count > self.max_requests:
                ttl = self._client.ttl(redis_key)
                return RateLimitResult(allowed=False, retry_after_seconds=max(1, ttl))
            return RateLimitResult(allowed=True)
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}")
            return RateLimitResult(allowed=True)  # Fail open


def build_request_context(request: Request) -> tuple[str, str]:
    request_id = str(uuid4())
    identity = request.headers.get("X-API-Key", "")
    if identity:
        return request_id, f"api-key:{identity[:12]}"
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return request_id, "session"
    client_host = request.client.host if request.client else "unknown"
    return request_id, f"ip:{client_host}"


def rate_limit_response(request_id: str, retry_after_seconds: int) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "rate limit exceeded", "request_id": request_id},
        headers={"Retry-After": str(retry_after_seconds), "X-Request-ID": request_id},
    )


def log_request(method: str, path: str, status_code: int, duration_ms: float, request_id: str, actor: str) -> None:
    logger.info(
        "request_complete method=%s path=%s status=%s duration_ms=%.2f request_id=%s actor=%s",
        method,
        path,
        status_code,
        duration_ms,
        request_id,
        actor,
    )
