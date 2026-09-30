import threading
import time
import os
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= self.max_requests:
                return False
            requests.append(now)
            return True


analyze_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


class RedisRateLimiter:
    def __init__(self, url: str, max_requests: int, window_seconds: int):
        import redis

        self.client = redis.Redis.from_url(url, decode_responses=True)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow(self, key: str) -> bool:
        bucket = f"techscope:rate:{key}"
        with self.client.pipeline() as pipeline:
            pipeline.incr(bucket)
            pipeline.expire(bucket, self.window_seconds)
            count, _ = pipeline.execute()
        return count <= self.max_requests


def _configured_limiter():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return analyze_rate_limiter
    try:
        return RedisRateLimiter(redis_url, max_requests=10, window_seconds=60)
    except ImportError:
        return analyze_rate_limiter


def enforce_analyze_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    if not _configured_limiter().allow(client):
        raise HTTPException(status_code=429, detail="Analysis rate limit exceeded")