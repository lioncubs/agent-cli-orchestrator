"""Database models for metrics and analytics."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class APIMetric(Base):
    """Model for storing API request/response metrics."""
    
    __tablename__ = "api_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    repo_name = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_timestamp_endpoint', 'timestamp', 'endpoint'),
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )


class SystemMetric(Base):
    """Model for storing system resource metrics."""
    
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    memory_used_mb = Column(Float, nullable=True)
    disk_percent = Column(Float, nullable=True)
    active_sessions = Column(Integer, nullable=True)
    active_connections = Column(Integer, nullable=True)


class UserActivity(Base):
    """Model for storing user activity logs."""
    
    __tablename__ = "user_activity"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_user_activity_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_user_activity_action_timestamp', 'action', 'timestamp'),
    )


class AnalyticsCache(Base):
    """Model for caching computed analytics."""
    
    __tablename__ = "analytics_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    cache_value = Column(Text, nullable=False)
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True, index=True)
