import threading
import time
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


def enforce_analyze_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    if not analyze_rate_limiter.allow(client):
        raise HTTPException(status_code=429, detail="Analysis rate limit exceeded")