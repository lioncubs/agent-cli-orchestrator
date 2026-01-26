"""Analytics service with caching and aggregation."""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import select, func, and_, or_
from cachetools import TTLCache
import logging

from src.metrics.models import APIMetric, SystemMetric, UserActivity, AnalyticsCache
from src.metrics.database import get_db_manager

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for computing and caching analytics."""
    
    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Initialize analytics service.
        
        Args:
            cache_ttl_seconds: Time-to-live for in-memory cache (default 5 minutes)
        """
        self.db_manager = get_db_manager()
        # In-memory cache for frequently accessed data
        self.memory_cache = TTLCache(maxsize=100, ttl=cache_ttl_seconds)
        self.cache_ttl_seconds = cache_ttl_seconds
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a cache key from parameters.
        
        Args:
            prefix: Cache key prefix
            **kwargs: Parameters to include in key
            
        Returns:
            Cache key string
        """
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{params_hash}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Get value from cache (memory first, then database).
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached value or None
        """
        # Check memory cache first
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # Check database cache
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(AnalyticsCache).where(
                        and_(
                            AnalyticsCache.cache_key == cache_key,
                            or_(
                                AnalyticsCache.expires_at.is_(None),
                                AnalyticsCache.expires_at > datetime.utcnow()
                            )
                        )
                    )
                )
                cache_entry = result.scalar_one_or_none()
                
                if cache_entry:
                    value = json.loads(cache_entry.cache_value)
                    # Store in memory cache
                    self.memory_cache[cache_key] = value
                    return value
        except Exception as e:
            logger.error(f"Failed to get from database cache: {e}")
        
        return None
    
    async def _set_in_cache(self, cache_key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Store value in cache (both memory and database).
        
        Args:
            cache_key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (optional)
        """
        # Store in memory cache
        self.memory_cache[cache_key] = value
        
        # Store in database cache
        try:
            async with self.db_manager.get_session() as session:
                # Calculate expiration
                expires_at = None
                if ttl_seconds:
                    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
                
                # Check if cache entry exists
                result = await session.execute(
                    select(AnalyticsCache).where(AnalyticsCache.cache_key == cache_key)
                )
                cache_entry = result.scalar_one_or_none()
                
                if cache_entry:
                    # Update existing entry
                    cache_entry.cache_value = json.dumps(value)
                    cache_entry.computed_at = datetime.utcnow()
                    cache_entry.expires_at = expires_at
                else:
                    # Create new entry
                    cache_entry = AnalyticsCache(
                        cache_key=cache_key,
                        cache_value=json.dumps(value),
                        computed_at=datetime.utcnow(),
                        expires_at=expires_at
                    )
                    session.add(cache_entry)
        except Exception as e:
            logger.error(f"Failed to set in database cache: {e}")
    
    async def get_performance_analytics(
        self,
        hours: int = 24,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance analytics.
        
        Args:
            hours: Number of hours to analyze
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with performance analytics
        """
        cache_key = self._generate_cache_key("performance", hours=hours)
        
        # Check cache if enabled
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                cached["from_cache"] = True
                return cached
        
        # Compute analytics
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.db_manager.get_session() as session:
                # Overall metrics - simplified for SQLite compatibility
                result = await session.execute(
                    select(
                        func.count(APIMetric.id).label('total_requests'),
                        func.avg(APIMetric.response_time_ms).label('avg_response_time'),
                        func.max(APIMetric.response_time_ms).label('max_response_time')
                    ).where(APIMetric.timestamp >= start_time)
                )
                overall = result.first()
                
                # Get all response times for percentile calculation
                response_times_result = await session.execute(
                    select(APIMetric.response_time_ms)
                    .where(APIMetric.timestamp >= start_time)
                    .order_by(APIMetric.response_time_ms)
                )
                response_times = [row[0] for row in response_times_result.fetchall()]
                
                # Calculate percentiles manually
                p50 = 0.0
                p95 = 0.0
                p99 = 0.0
                if response_times:
                    import statistics
                    try:
                        p50 = statistics.median(response_times) if len(response_times) > 0 else 0.0
                        if len(response_times) > 1:
                            p95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else response_times[-1]
                            p99 = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else response_times[-1]
                    except Exception:
                        # Fallback if quantiles fail
                        idx_50 = int(len(response_times) * 0.5)
                        idx_95 = int(len(response_times) * 0.95)
                        idx_99 = int(len(response_times) * 0.99)
                        p50 = response_times[min(idx_50, len(response_times) - 1)]
                        p95 = response_times[min(idx_95, len(response_times) - 1)]
                        p99 = response_times[min(idx_99, len(response_times) - 1)]
                
                # Endpoint-specific metrics
                endpoint_result = await session.execute(
                    select(
                        APIMetric.endpoint,
                        func.count(APIMetric.id).label('count'),
                        func.avg(APIMetric.response_time_ms).label('avg_time'),
                        func.max(APIMetric.response_time_ms).label('max_time')
                    ).where(
                        APIMetric.timestamp >= start_time
                    ).group_by(APIMetric.endpoint).order_by(func.count(APIMetric.id).desc())
                )
                
                endpoints = []
                for row in endpoint_result:
                    endpoints.append({
                        "endpoint": row.endpoint,
                        "request_count": row.count,
                        "avg_response_time_ms": float(row.avg_time or 0),
                        "max_response_time_ms": float(row.max_time or 0)
                    })
                
                # Error rate by endpoint
                error_result = await session.execute(
                    select(
                        APIMetric.endpoint,
                        func.count(APIMetric.id).label('error_count')
                    ).where(
                        and_(
                            APIMetric.timestamp >= start_time,
                            APIMetric.status_code >= 400
                        )
                    ).group_by(APIMetric.endpoint)
                )
                
                errors_by_endpoint = {}
                for row in error_result:
                    errors_by_endpoint[row.endpoint] = row.error_count
                
                analytics = {
                    "period_hours": hours,
                    "overall": {
                        "total_requests": overall.total_requests or 0,
                        "avg_response_time_ms": float(overall.avg_response_time or 0),
                        "p50_response_time_ms": float(p50),
                        "p95_response_time_ms": float(p95),
                        "p99_response_time_ms": float(p99),
                        "max_response_time_ms": float(overall.max_response_time or 0)
                    },
                    "endpoints": endpoints[:20],  # Top 20 endpoints
                    "errors_by_endpoint": errors_by_endpoint,
                    "from_cache": False
                }
                
                # Cache the result
                if use_cache:
                    await self._set_in_cache(cache_key, analytics, ttl_seconds=self.cache_ttl_seconds)
                
                return analytics
                
        except Exception as e:
            logger.error(f"Failed to get performance analytics: {e}")
            return {
                "period_hours": hours,
                "overall": {},
                "endpoints": [],
                "errors_by_endpoint": {},
                "error": str(e)
            }
    
    async def get_usage_analytics(
        self,
        hours: int = 24,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get usage analytics.
        
        Args:
            hours: Number of hours to analyze
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with usage analytics
        """
        cache_key = self._generate_cache_key("usage", hours=hours)
        
        # Check cache if enabled
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                cached["from_cache"] = True
                return cached
        
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.db_manager.get_session() as session:
                # User activity stats
                user_result = await session.execute(
                    select(
                        func.count(func.distinct(UserActivity.user_id)).label('active_users'),
                        func.count(UserActivity.id).label('total_actions')
                    ).where(UserActivity.timestamp >= start_time)
                )
                user_stats = user_result.first()
                
                # Top actions
                action_result = await session.execute(
                    select(
                        UserActivity.action,
                        func.count(UserActivity.id).label('count')
                    ).where(
                        UserActivity.timestamp >= start_time
                    ).group_by(UserActivity.action).order_by(func.count(UserActivity.id).desc())
                )
                
                top_actions = []
                for row in action_result:
                    top_actions.append({
                        "action": row.action,
                        "count": row.count
                    })
                
                analytics = {
                    "period_hours": hours,
                    "active_users": user_stats.active_users or 0,
                    "total_actions": user_stats.total_actions or 0,
                    "top_actions": top_actions[:10],  # Top 10 actions
                    "from_cache": False
                }
                
                # Cache the result
                if use_cache:
                    await self._set_in_cache(cache_key, analytics, ttl_seconds=self.cache_ttl_seconds)
                
                return analytics
                
        except Exception as e:
            logger.error(f"Failed to get usage analytics: {e}")
            return {
                "period_hours": hours,
                "active_users": 0,
                "total_actions": 0,
                "top_actions": [],
                "error": str(e)
            }
    
    async def get_dashboard_data(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with dashboard data
        """
        cache_key = self._generate_cache_key("dashboard")
        
        # Check cache if enabled
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                cached["from_cache"] = True
                return cached
        
        try:
            # Get various analytics
            from src.metrics.collector import get_metrics_collector
            collector = get_metrics_collector()
            
            # Fetch data in parallel
            performance_1h = await self.get_performance_analytics(hours=1, use_cache=False)
            performance_24h = await self.get_performance_analytics(hours=24, use_cache=False)
            usage_24h = await self.get_usage_analytics(hours=24, use_cache=False)
            system_metrics = await collector.get_system_metrics_latest()
            api_summary = await collector.get_api_metrics_summary(minutes=60)
            
            dashboard = {
                "timestamp": datetime.utcnow().isoformat(),
                "performance": {
                    "last_hour": performance_1h,
                    "last_24_hours": performance_24h
                },
                "usage": usage_24h,
                "system": system_metrics,
                "api_summary": api_summary,
                "from_cache": False
            }
            
            # Cache the result
            if use_cache:
                await self._set_in_cache(cache_key, dashboard, ttl_seconds=60)  # Cache for 1 minute
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }


# Global analytics service instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service(cache_ttl_seconds: int = 300) -> AnalyticsService:
    """
    Get or create the global analytics service instance.
    
    Args:
        cache_ttl_seconds: Time-to-live for cache
        
    Returns:
        AnalyticsService instance
    """
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(cache_ttl_seconds)
    return _analytics_service
