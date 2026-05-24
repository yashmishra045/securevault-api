from collections import defaultdict, deque
from time import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self._request_log: dict = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in ("/health", "/health/"):
            return await call_next(request)
        ip  = request.client.host if request.client else "unknown"
        now = time()
        dq  = self._request_log[ip]
        while dq and dq[0] < now - self.window_seconds:
            dq.popleft()
        remaining = self.rate_limit - len(dq)
        if remaining <= 0:
            return JSONResponse(status_code=429, content={"error": {"code": 429, "message": "Rate limit exceeded"}}, headers={"X-RateLimit-Limit": str(self.rate_limit), "X-RateLimit-Remaining": "0"})
        dq.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        return response
