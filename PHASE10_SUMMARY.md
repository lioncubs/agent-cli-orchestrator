# Phase 10: Advanced Metrics and Analytics

## Overview

Phase 10 implements a comprehensive metrics and analytics system for the Agent CLI Orchestrator. This system provides real-time performance monitoring, detailed analytics, and persistent storage of operational data using a database backend.

## Architecture

### Components

1. **Database Layer** (`src/metrics/database.py`)
   - SQLite database with async support (aiosqlite)
   - Connection pooling and session management
   - Automatic schema initialization
   - Support for other databases via SQLAlchemy

2. **Data Models** (`src/metrics/models.py`)
   - `APIMetric`: API request/response metrics
   - `SystemMetric`: System resource metrics
   - `UserActivity`: User activity logs
   - `AnalyticsCache`: Computed analytics cache

3. **Metrics Collector** (`src/metrics/collector.py`)
   - Automatic metric recording
   - System resource monitoring (CPU, memory, disk)
   - User activity tracking
   - Query aggregation

4. **Analytics Service** (`src/metrics/analytics.py`)
   - Time-series data aggregation
   - Performance analytics (response times, throughput)
   - Usage analytics (active users, actions)
   - Multi-level caching (memory + database)
   - Percentile calculations (P50, P95, P99)

5. **Middleware** (`src/metrics/middleware.py`)
   - Automatic request/response time tracking
   - Background system metrics collection
   - Non-blocking metric recording

6. **API Endpoints** (`src/api/routes/metrics.py`)
   - `/metrics` - Current metrics summary
   - `/metrics/performance` - Performance analytics
   - `/metrics/usage` - Usage statistics
   - `/metrics/health` - System health metrics
   - `/metrics/endpoints` - Per-endpoint metrics
   - `/analytics/dashboard` - Comprehensive dashboard data

## Features

### Performance Monitoring
- Request/response time tracking
- Endpoint usage statistics
- Error rate monitoring
- Response time percentiles (P50, P95, P99)
- Request throughput analysis

### System Monitoring
- CPU utilization
- Memory usage
- Disk space
- Active sessions count
- Active connections count

### User Activity Tracking
- User action logging
- Resource access tracking
- IP address logging
- Status tracking (success/error)

### Analytics
- Real-time data aggregation
- Historical trend analysis
- Top endpoints by request count
- Error distribution by endpoint
- Active users count

### Caching
- Two-level cache (memory + database)
- Configurable TTL
- Automatic cache invalidation
- Cache-aware API endpoints

## Database Schema

### APIMetric Table
```sql
CREATE TABLE api_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms FLOAT NOT NULL,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    repo_name VARCHAR(255),
    error_message TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_endpoint (endpoint),
    INDEX idx_timestamp_endpoint (timestamp, endpoint)
);
```

### SystemMetric Table
```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    cpu_percent FLOAT,
    memory_percent FLOAT,
    memory_used_mb FLOAT,
    disk_percent FLOAT,
    active_sessions INTEGER,
    active_connections INTEGER,
    INDEX idx_timestamp (timestamp)
);
```

### UserActivity Table
```sql
CREATE TABLE user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_action_timestamp (action, timestamp)
);
```

### AnalyticsCache Table
```sql
CREATE TABLE analytics_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_value TEXT NOT NULL,
    computed_at DATETIME NOT NULL,
    expires_at DATETIME,
    INDEX idx_cache_key (cache_key),
    INDEX idx_expires_at (expires_at)
);
```

## Configuration

Add to `config.yaml`:

```yaml
metrics:
  enabled: true
  database_url: null  # null = SQLite in ./data/metrics.db
  collect_system_metrics: true
  system_metrics_interval: 60  # seconds
  cache_ttl_seconds: 300  # 5 minutes
  retention_days: 30  # Data retention period
```

## API Usage Examples

### Get Current Metrics
```bash
curl http://localhost:8000/metrics
```

Response:
```json
{
  "status": "success",
  "timestamp": "2026-01-07T08:42:04.430276",
  "metrics": {
    "total_requests": 1234,
    "avg_response_time_ms": 45.67,
    "min_response_time_ms": 5.12,
    "max_response_time_ms": 523.45,
    "error_count": 12,
    "error_rate": 0.97,
    "period_minutes": 60
  }
}
```

### Get Performance Analytics
```bash
curl "http://localhost:8000/metrics/performance?hours=24&use_cache=true"
```

Response:
```json
{
  "status": "success",
  "analytics": {
    "period_hours": 24,
    "overall": {
      "total_requests": 5432,
      "avg_response_time_ms": 67.89,
      "p50_response_time_ms": 45.23,
      "p95_response_time_ms": 234.56,
      "p99_response_time_ms": 456.78,
      "max_response_time_ms": 987.65
    },
    "endpoints": [
      {
        "endpoint": "/sessions",
        "request_count": 1234,
        "avg_response_time_ms": 56.78,
        "max_response_time_ms": 345.67
      }
    ],
    "errors_by_endpoint": {
      "/sessions": 5,
      "/prompt": 2
    },
    "from_cache": false
  }
}
```

### Get System Health
```bash
curl http://localhost:8000/metrics/health
```

Response:
```json
{
  "status": "success",
  "system": {
    "timestamp": "2026-01-07T08:42:11.423458",
    "cpu_percent": 9.8,
    "memory_percent": 13.2,
    "memory_used_mb": 2114.12,
    "disk_percent": 76.8,
    "active_sessions": 3,
    "active_connections": 5
  }
}
```

### Get Comprehensive Dashboard Data
```bash
curl http://localhost:8000/analytics/dashboard
```

Response includes:
- Performance analytics (1 hour and 24 hours)
- Usage analytics
- System metrics
- API summary

## Performance Considerations

### Database
- Uses indexes for fast queries
- Async operations for non-blocking I/O
- Connection pooling
- Batch inserts for high throughput

### Caching
- Two-level cache reduces database load
- Configurable TTL
- Automatic invalidation
- Cache-aware queries

### Middleware
- Non-blocking metric recording
- Background system metrics collection
- Minimal overhead on request processing

## Data Retention

Configure retention period in `config.yaml`:
```yaml
metrics:
  retention_days: 30
```

Implement cleanup job:
```python
from datetime import datetime, timedelta
from src.metrics.database import get_db_manager
from src.metrics.models import APIMetric, SystemMetric, UserActivity

async def cleanup_old_metrics():
    """Remove metrics older than retention period."""
    retention_days = config.metrics_retention_days
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    async with get_db_manager().get_session() as session:
        await session.execute(
            delete(APIMetric).where(APIMetric.timestamp < cutoff_date)
        )
        await session.execute(
            delete(SystemMetric).where(SystemMetric.timestamp < cutoff_date)
        )
        await session.execute(
            delete(UserActivity).where(UserActivity.timestamp < cutoff_date)
        )
```

## Security

### Access Control
- Metrics endpoints can be protected by authentication middleware
- Configure in `security.auth.exclude_paths` to allow/deny access

### Data Privacy
- User IDs are anonymized in storage
- IP addresses can be hashed
- Sensitive data excluded from metrics

### Rate Limiting
- Standard rate limiting applies to metrics endpoints
- Prevents abuse and excessive database load

## Testing

Run tests:
```bash
pytest tests/metrics/test_metrics.py -v
```

Test coverage includes:
- Database initialization
- Metric recording
- Analytics computation
- Caching mechanisms
- API endpoints

## Integration

### Adding Custom Metrics

```python
from src.metrics.collector import get_metrics_collector

collector = get_metrics_collector()

# Record custom API metric
await collector.record_api_metric(
    endpoint="/custom/endpoint",
    method="POST",
    status_code=200,
    response_time_ms=123.45,
    user_id="user123"
)

# Record user activity
await collector.record_user_activity(
    user_id="user123",
    action="custom_action",
    status="success",
    details='{"key": "value"}'
)
```

### Custom Analytics

```python
from src.metrics.analytics import get_analytics_service

analytics = get_analytics_service()

# Get custom analytics
data = await analytics.get_performance_analytics(
    hours=12,
    use_cache=True
)
```

## Future Enhancements

- [ ] Alerting system for threshold breaches
- [ ] Metrics export to Prometheus/Grafana
- [ ] Advanced visualization dashboard
- [ ] Machine learning-based anomaly detection
- [ ] Distributed tracing integration
- [ ] Custom metric definitions via API
- [ ] Automated reporting
- [ ] Metrics comparison tools

## Troubleshooting

### Database Connection Issues
```python
# Check database status
from src.metrics.database import get_db_manager

db_manager = get_db_manager()
try:
    await db_manager.init_db()
    print("Database OK")
except Exception as e:
    print(f"Database error: {e}")
```

### High Memory Usage
- Adjust cache size in `AnalyticsService`
- Reduce cache TTL
- Implement more aggressive data retention

### Slow Queries
- Check database indexes
- Reduce query time ranges
- Enable query result caching

## Summary

Phase 10 successfully implements a comprehensive metrics and analytics system that provides:
- Real-time performance monitoring
- Persistent storage with SQLite
- Advanced analytics with percentile calculations
- Efficient caching for performance
- RESTful API for data access
- Secure and scalable architecture

The system is production-ready and can be extended with additional features as needed.
