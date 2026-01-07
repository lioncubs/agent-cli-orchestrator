"""Middleware for automatic metrics collection."""

import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from src.metrics.collector import get_metrics_collector

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect API metrics."""
    
    def __init__(self, app: ASGIApp, collect_system_metrics: bool = True, system_metrics_interval: int = 60):
        """
        Initialize metrics middleware.
        
        Args:
            app: ASGI application
            collect_system_metrics: Whether to collect system metrics periodically
            system_metrics_interval: Interval in seconds for system metrics collection
        """
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
        self.collect_system_metrics = collect_system_metrics
        self.system_metrics_interval = system_metrics_interval
        self._system_metrics_task = None
        
        if collect_system_metrics:
            # Start background task for system metrics collection
            self._start_system_metrics_collection()
    
    def _start_system_metrics_collection(self):
        """Start background task for collecting system metrics."""
        async def collect_periodically():
            while True:
                try:
                    await self.metrics_collector.record_system_metrics()
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.system_metrics_interval)
        
        # Create task but don't await it
        self._system_metrics_task = asyncio.create_task(collect_periodically())
        logger.info(f"System metrics collection started (interval: {self.system_metrics_interval}s)")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        # Record start time
        start_time = time.time()
        
        # Extract user info if available
        user_id = None
        session_id = None
        
        # Check for user in request state (set by auth middleware)
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None) or getattr(request.state.user, "email", None)
        
        # Check for session ID in headers or cookies
        session_id = request.headers.get("X-Session-ID") or request.cookies.get("session_id")
        
        # Process request
        response = None
        error_message = None
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error processing request: {e}")
            raise
        finally:
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract repo name from query params if present
            repo_name = request.query_params.get("repo_name")
            
            # Record metric asynchronously (don't block response)
            asyncio.create_task(
                self.metrics_collector.record_api_metric(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    user_id=user_id,
                    session_id=session_id,
                    repo_name=repo_name,
                    error_message=error_message
                )
            )
        
        return response


def create_metrics_middleware(
    collect_system_metrics: bool = True,
    system_metrics_interval: int = 60
) -> type:
    """
    Create a metrics middleware instance.
    
    Args:
        collect_system_metrics: Whether to collect system metrics
        system_metrics_interval: Interval for system metrics collection
        
    Returns:
        MetricsMiddleware class configured with parameters
    """
    class ConfiguredMetricsMiddleware(MetricsMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(app, collect_system_metrics, system_metrics_interval)
    
    return ConfiguredMetricsMiddleware
