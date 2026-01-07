"""API routes for metrics and analytics."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from src.metrics.collector import get_metrics_collector
from src.metrics.analytics import get_analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_current_metrics(
    minutes: int = Query(60, ge=1, le=1440, description="Minutes to look back")
):
    """
    Get current API metrics summary.
    
    Args:
        minutes: Number of minutes to look back (default: 60, max: 1440)
        
    Returns:
        Dictionary with current metrics
    """
    try:
        collector = get_metrics_collector()
        summary = await collector.get_api_metrics_summary(minutes=minutes)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": summary
        }
    except Exception as e:
        logger.error(f"Failed to get current metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Get detailed performance analytics.
    
    Args:
        hours: Number of hours to analyze (default: 24, max: 168)
        use_cache: Whether to use cached results
        
    Returns:
        Dictionary with performance analytics
    """
    try:
        analytics_service = get_analytics_service()
        analytics = await analytics_service.get_performance_analytics(
            hours=hours,
            use_cache=use_cache
        )
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "analytics": analytics
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage")
async def get_usage_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Get usage analytics.
    
    Args:
        hours: Number of hours to analyze (default: 24, max: 168)
        use_cache: Whether to use cached results
        
    Returns:
        Dictionary with usage analytics
    """
    try:
        analytics_service = get_analytics_service()
        analytics = await analytics_service.get_usage_analytics(
            hours=hours,
            use_cache=use_cache
        )
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "analytics": analytics
        }
    except Exception as e:
        logger.error(f"Failed to get usage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_health_metrics():
    """
    Get current system health metrics.
    
    Returns:
        Dictionary with system health metrics
    """
    try:
        collector = get_metrics_collector()
        system_metrics = await collector.get_system_metrics_latest()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics
        }
    except Exception as e:
        logger.error(f"Failed to get health metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints")
async def get_endpoint_metrics(
    minutes: int = Query(60, ge=1, le=1440, description="Minutes to look back")
):
    """
    Get metrics grouped by endpoint.
    
    Args:
        minutes: Number of minutes to look back
        
    Returns:
        Dictionary with per-endpoint metrics
    """
    try:
        collector = get_metrics_collector()
        endpoint_metrics = await collector.get_endpoint_metrics(minutes=minutes)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": endpoint_metrics
        }
    except Exception as e:
        logger.error(f"Failed to get endpoint metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics router
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


@analytics_router.get("/dashboard")
async def get_dashboard_analytics(
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Get comprehensive dashboard analytics.
    
    Args:
        use_cache: Whether to use cached results
        
    Returns:
        Dictionary with comprehensive dashboard data
    """
    try:
        analytics_service = get_analytics_service()
        dashboard = await analytics_service.get_dashboard_data(use_cache=use_cache)
        
        return {
            "status": "success",
            "dashboard": dashboard
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def init_metrics_routes(app):
    """
    Initialize and include metrics routes in the app.
    
    Args:
        app: FastAPI application instance
    """
    app.include_router(router)
    app.include_router(analytics_router)
    logger.info("Metrics and analytics routes initialized")
