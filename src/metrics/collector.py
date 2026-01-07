"""Metrics collection service."""

import time
import psutil
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.metrics.models import APIMetric, SystemMetric, UserActivity
from src.metrics.database import get_db_manager

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Service for collecting and storing metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.db_manager = get_db_manager()
    
    async def record_api_metric(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        repo_name: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record an API request metric.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            user_id: Optional user identifier
            session_id: Optional session identifier
            repo_name: Optional repository name
            error_message: Optional error message
        """
        try:
            async with self.db_manager.get_session() as session:
                metric = APIMetric(
                    timestamp=datetime.utcnow(),
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    user_id=user_id,
                    session_id=session_id,
                    repo_name=repo_name,
                    error_message=error_message
                )
                session.add(metric)
        except Exception as e:
            logger.error(f"Failed to record API metric: {e}")
    
    async def record_system_metrics(self) -> None:
        """Record current system resource metrics."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            async with self.db_manager.get_session() as session:
                metric = SystemMetric(
                    timestamp=datetime.utcnow(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    disk_percent=disk.percent,
                    active_sessions=0,  # Will be updated by session manager
                    active_connections=0  # Will be updated by connection manager
                )
                session.add(metric)
        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")
    
    async def record_user_activity(
        self,
        user_id: str,
        action: str,
        status: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Record user activity.
        
        Args:
            user_id: User identifier
            action: Action performed
            status: Status of the action (success, error, etc.)
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details in JSON format
            ip_address: User's IP address
        """
        try:
            async with self.db_manager.get_session() as session:
                activity = UserActivity(
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    status=status,
                    details=details,
                    ip_address=ip_address
                )
                session.add(activity)
        except Exception as e:
            logger.error(f"Failed to record user activity: {e}")
    
    async def get_api_metrics_summary(
        self,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get summary of API metrics for the last N minutes.
        
        Args:
            minutes: Number of minutes to look back
            
        Returns:
            Dictionary with metrics summary
        """
        try:
            from datetime import timedelta
            start_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            async with self.db_manager.get_session() as session:
                # Query metrics
                result = await session.execute(
                    select(
                        func.count(APIMetric.id).label('total_requests'),
                        func.avg(APIMetric.response_time_ms).label('avg_response_time'),
                        func.min(APIMetric.response_time_ms).label('min_response_time'),
                        func.max(APIMetric.response_time_ms).label('max_response_time'),
                        func.count(APIMetric.id).filter(APIMetric.status_code >= 400).label('error_count')
                    ).where(APIMetric.timestamp >= start_time)
                )
                row = result.first()
                
                return {
                    "total_requests": row.total_requests or 0,
                    "avg_response_time_ms": float(row.avg_response_time or 0),
                    "min_response_time_ms": float(row.min_response_time or 0),
                    "max_response_time_ms": float(row.max_response_time or 0),
                    "error_count": row.error_count or 0,
                    "error_rate": (row.error_count / row.total_requests * 100) if row.total_requests > 0 else 0,
                    "period_minutes": minutes
                }
        except Exception as e:
            logger.error(f"Failed to get API metrics summary: {e}")
            return {
                "total_requests": 0,
                "avg_response_time_ms": 0,
                "min_response_time_ms": 0,
                "max_response_time_ms": 0,
                "error_count": 0,
                "error_rate": 0,
                "period_minutes": minutes
            }
    
    async def get_endpoint_metrics(
        self,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get metrics grouped by endpoint.
        
        Args:
            minutes: Number of minutes to look back
            
        Returns:
            Dictionary with per-endpoint metrics
        """
        try:
            from datetime import timedelta
            start_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(
                        APIMetric.endpoint,
                        func.count(APIMetric.id).label('count'),
                        func.avg(APIMetric.response_time_ms).label('avg_time')
                    ).where(
                        APIMetric.timestamp >= start_time
                    ).group_by(APIMetric.endpoint)
                )
                
                endpoints = []
                for row in result:
                    endpoints.append({
                        "endpoint": row.endpoint,
                        "request_count": row.count,
                        "avg_response_time_ms": float(row.avg_time or 0)
                    })
                
                return {
                    "endpoints": endpoints,
                    "period_minutes": minutes
                }
        except Exception as e:
            logger.error(f"Failed to get endpoint metrics: {e}")
            return {"endpoints": [], "period_minutes": minutes}
    
    async def get_system_metrics_latest(self) -> Dict[str, Any]:
        """
        Get the latest system metrics.
        
        Returns:
            Dictionary with latest system metrics
        """
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(SystemMetric)
                    .order_by(SystemMetric.timestamp.desc())
                    .limit(1)
                )
                metric = result.scalar_one_or_none()
                
                if metric:
                    return {
                        "timestamp": metric.timestamp.isoformat(),
                        "cpu_percent": metric.cpu_percent,
                        "memory_percent": metric.memory_percent,
                        "memory_used_mb": metric.memory_used_mb,
                        "disk_percent": metric.disk_percent,
                        "active_sessions": metric.active_sessions,
                        "active_connections": metric.active_connections
                    }
                else:
                    # Return current metrics if no data in DB
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    return {
                        "timestamp": datetime.utcnow().isoformat(),
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_used_mb": memory.used / (1024 * 1024),
                        "disk_percent": disk.percent,
                        "active_sessions": 0,
                        "active_connections": 0
                    }
        except Exception as e:
            logger.error(f"Failed to get latest system metrics: {e}")
            return {}


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get or create the global metrics collector instance.
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
