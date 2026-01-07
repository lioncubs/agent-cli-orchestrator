"""Rate limiting middleware to prevent abuse."""

import time
from typing import Callable, Dict, Tuple
from collections import defaultdict, deque
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting using a sliding window algorithm.
    
    Tracks requests per user/IP and enforces configurable limits.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst: int = 10,
        exclude_paths: list[str] = None
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: The ASGI application
            requests_per_minute: Maximum requests allowed per minute
            burst: Maximum burst size for short-term spikes
            exclude_paths: List of path prefixes to exclude from rate limiting
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.window_size = 60.0  # 1 minute in seconds
        
        # Track requests by client identifier (user_id or IP)
        self._request_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Cleanup old entries periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
        # Paths to exclude from rate limiting
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/_health",
        ]
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get a unique identifier for the client.
        
        Args:
            request: The incoming request
            
        Returns:
            Client identifier (user ID if authenticated, IP otherwise)
        """
        # Prefer user ID if authenticated
        if hasattr(request.state, "user"):
            return f"user:{request.state.user.id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _cleanup_old_entries(self):
        """Remove old request history entries to prevent memory leaks."""
        current_time = time.time()
        
        # Only cleanup periodically
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = current_time - self.window_size
        
        # Clean up old entries
        for client_id in list(self._request_history.keys()):
            history = self._request_history[client_id]
            
            # Remove timestamps older than window
            while history and history[0] < cutoff_time:
                history.popleft()
            
            # Remove empty histories
            if not history:
                del self._request_history[client_id]
        
        self._last_cleanup = current_time
        logger.debug(f"Cleaned up rate limit history. Active clients: {len(self._request_history)}")
    
    def _is_rate_limited(self, client_id: str) -> Tuple[bool, Dict[str, any]]:
        """
        Check if a client has exceeded rate limits.
        
        Args:
            client_id: The client identifier
            
        Returns:
            Tuple of (is_limited, rate_limit_info)
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_size
        
        # Get request history for this client
        history = self._request_history[client_id]
        
        # Remove old requests outside the window
        while history and history[0] < cutoff_time:
            history.popleft()
        
        # Count requests in window
        requests_in_window = len(history)
        
        # Check burst limit (last N requests in short time)
        burst_window = 10.0  # 10 seconds for burst detection
        burst_cutoff = current_time - burst_window
        burst_count = sum(1 for ts in history if ts >= burst_cutoff)
        
        # Rate limit info for headers
        rate_limit_info = {
            "limit": self.requests_per_minute,
            "remaining": max(0, self.requests_per_minute - requests_in_window),
            "reset": int(current_time + self.window_size - (history[0] if history else current_time)),
            "burst_limit": self.burst,
            "burst_remaining": max(0, self.burst - burst_count)
        }
        
        # Check if limits exceeded
        if requests_in_window >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_id}: {requests_in_window}/{self.requests_per_minute}")
            return True, rate_limit_info
        
        if burst_count >= self.burst:
            logger.warning(f"Burst limit exceeded for {client_id}: {burst_count}/{self.burst}")
            return True, rate_limit_info
        
        # Add current request to history
        history.append(current_time)
        
        return False, rate_limit_info
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process each request through rate limiting.
        
        Args:
            request: The incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response from the next handler or rate limit error
        """
        # Check if path is excluded
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Periodic cleanup
        self._cleanup_old_entries()
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Check rate limits
        is_limited, rate_info = self._is_rate_limited(client_id)
        
        if is_limited:
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "error": "rate_limit_exceeded",
                    "limit": rate_info["limit"],
                    "reset_at": rate_info["reset"]
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["reset"] - int(time.time()))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Add rate limit info to headers
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
        
        return response
