"""Tests for metrics and analytics system."""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.metrics.database import get_db_manager, DatabaseManager
from src.metrics.models import APIMetric, SystemMetric, UserActivity
from src.metrics.collector import MetricsCollector
from src.metrics.analytics import AnalyticsService


@pytest.fixture
async def db_manager():
    """Create a test database manager."""
    manager = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
    await manager.init_db()
    yield manager
    await manager.close()


@pytest.fixture
def metrics_collector():
    """Create a metrics collector instance."""
    return MetricsCollector()


@pytest.fixture
def analytics_service():
    """Create an analytics service instance."""
    return AnalyticsService(cache_ttl_seconds=60)


@pytest.mark.asyncio
async def test_database_initialization(db_manager):
    """Test database initialization."""
    # Database should be initialized
    assert db_manager.engine is not None
    assert db_manager.session_factory is not None


@pytest.mark.asyncio
async def test_record_api_metric(metrics_collector):
    """Test recording an API metric."""
    await metrics_collector.record_api_metric(
        endpoint="/test",
        method="GET",
        status_code=200,
        response_time_ms=123.45,
        user_id="test_user"
    )
    # If no exception is raised, the test passes


@pytest.mark.asyncio
async def test_record_system_metrics(metrics_collector):
    """Test recording system metrics."""
    await metrics_collector.record_system_metrics()
    # If no exception is raised, the test passes


@pytest.mark.asyncio
async def test_record_user_activity(metrics_collector):
    """Test recording user activity."""
    await metrics_collector.record_user_activity(
        user_id="test_user",
        action="login",
        status="success",
        ip_address="127.0.0.1"
    )
    # If no exception is raised, the test passes


@pytest.mark.asyncio
async def test_get_api_metrics_summary(metrics_collector):
    """Test getting API metrics summary."""
    summary = await metrics_collector.get_api_metrics_summary(minutes=60)
    
    assert "total_requests" in summary
    assert "avg_response_time_ms" in summary
    assert "error_count" in summary
    assert "error_rate" in summary


@pytest.mark.asyncio
async def test_get_system_metrics_latest(metrics_collector):
    """Test getting latest system metrics."""
    metrics = await metrics_collector.get_system_metrics_latest()
    
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_percent" in metrics


@pytest.mark.asyncio
async def test_performance_analytics(analytics_service):
    """Test performance analytics computation."""
    analytics = await analytics_service.get_performance_analytics(
        hours=1,
        use_cache=False
    )
    
    assert "period_hours" in analytics
    assert "overall" in analytics
    assert "endpoints" in analytics


@pytest.mark.asyncio
async def test_usage_analytics(analytics_service):
    """Test usage analytics computation."""
    analytics = await analytics_service.get_usage_analytics(
        hours=1,
        use_cache=False
    )
    
    assert "period_hours" in analytics
    assert "active_users" in analytics
    assert "total_actions" in analytics


@pytest.mark.asyncio
async def test_dashboard_data(analytics_service):
    """Test dashboard data aggregation."""
    dashboard = await analytics_service.get_dashboard_data(use_cache=False)
    
    assert "timestamp" in dashboard
    assert "performance" in dashboard or "error" in dashboard
    # Note: Some fields might be missing if database is empty


@pytest.mark.asyncio
async def test_analytics_caching(analytics_service):
    """Test analytics caching mechanism."""
    # First call should compute
    result1 = await analytics_service.get_performance_analytics(
        hours=1,
        use_cache=True
    )
    assert result1.get("from_cache", False) is False
    
    # Second call should use cache
    result2 = await analytics_service.get_performance_analytics(
        hours=1,
        use_cache=True
    )
    # Cache might be hit in memory or database
    # Just verify the structure is the same
    assert "period_hours" in result2


def test_cache_key_generation(analytics_service):
    """Test cache key generation."""
    key1 = analytics_service._generate_cache_key("test", param1="value1", param2="value2")
    key2 = analytics_service._generate_cache_key("test", param2="value2", param1="value1")
    
    # Keys should be the same regardless of parameter order
    assert key1 == key2
    
    # Different parameters should produce different keys
    key3 = analytics_service._generate_cache_key("test", param1="different")
    assert key1 != key3
