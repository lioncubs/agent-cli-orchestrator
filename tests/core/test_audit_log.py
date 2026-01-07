"""Tests for security audit logging."""

import pytest
from src.core.audit_log import AuditLog, AuditEventType


class TestAuditLog:
    """Tests for security audit log."""
    
    @pytest.fixture
    def audit_log(self):
        """Create a fresh audit log for each test."""
        return AuditLog(max_entries=100)
    
    def test_log_event(self, audit_log):
        """Test logging a basic audit event."""
        entry = audit_log.log_event(
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id="user123",
            user_email="user@example.com",
            ip_address="192.168.1.1",
            path="/api/sessions",
            details={"method": "api_key"},
            severity="info"
        )
        
        assert entry["event_type"] == "auth_success"
        assert entry["user_id"] == "user123"
        assert entry["user_email"] == "user@example.com"
        assert entry["ip_address"] == "192.168.1.1"
        assert entry["path"] == "/api/sessions"
        assert entry["details"]["method"] == "api_key"
        assert entry["severity"] == "info"
        assert "timestamp" in entry
    
    def test_log_auth_success(self, audit_log):
        """Test logging successful authentication."""
        audit_log.log_auth_success(
            user_id="user456",
            user_email="test@example.com",
            ip_address="10.0.0.1",
            method="password"
        )
        
        events = audit_log.list_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "auth_success"
        assert events[0]["details"]["method"] == "password"
    
    def test_log_auth_failure(self, audit_log):
        """Test logging failed authentication."""
        audit_log.log_auth_failure(
            ip_address="192.168.1.100",
            reason="invalid_key",
            attempted_user="attacker@example.com"
        )
        
        events = audit_log.list_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "auth_failure"
        assert events[0]["details"]["reason"] == "invalid_key"
        assert events[0]["severity"] == "warning"
    
    def test_log_permission_denied(self, audit_log):
        """Test logging permission denial."""
        audit_log.log_permission_denied(
            user_id="user789",
            user_email="limited@example.com",
            path="/admin/users",
            required_permission="admin",
            ip_address="192.168.1.50"
        )
        
        events = audit_log.list_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "permission_denied"
        assert events[0]["details"]["required_permission"] == "admin"
    
    def test_log_rate_limit(self, audit_log):
        """Test logging rate limit violation."""
        audit_log.log_rate_limit(
            client_id="user:123",
            ip_address="192.168.1.25",
            path="/api/query"
        )
        
        events = audit_log.list_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "rate_limit_exceeded"
        assert events[0]["severity"] == "warning"
    
    def test_log_suspicious_activity(self, audit_log):
        """Test logging suspicious activity."""
        audit_log.log_suspicious_activity(
            description="Multiple failed login attempts",
            user_id="user999",
            ip_address="192.168.1.200",
            details={"attempts": 5, "timeframe": "1 minute"}
        )
        
        events = audit_log.list_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "suspicious_activity"
        assert events[0]["severity"] == "error"
        assert "Multiple failed login attempts" in events[0]["details"]["description"]
    
    def test_list_events_filter_by_type(self, audit_log):
        """Test filtering events by type."""
        audit_log.log_auth_success("u1", "u1@example.com")
        audit_log.log_auth_failure(reason="test")
        audit_log.log_auth_success("u2", "u2@example.com")
        
        success_events = audit_log.list_events(
            event_type=AuditEventType.AUTH_SUCCESS
        )
        assert len(success_events) == 2
        assert all(e["event_type"] == "auth_success" for e in success_events)
    
    def test_list_events_filter_by_user(self, audit_log):
        """Test filtering events by user ID."""
        audit_log.log_auth_success("user1", "u1@example.com")
        audit_log.log_auth_success("user2", "u2@example.com")
        audit_log.log_permission_denied("user1", "u1@example.com", "/admin", "admin")
        
        user1_events = audit_log.list_events(user_id="user1")
        assert len(user1_events) == 2
        assert all(e["user_id"] == "user1" for e in user1_events)
    
    def test_list_events_filter_by_severity(self, audit_log):
        """Test filtering events by severity."""
        audit_log.log_auth_success("u1", "u1@example.com")  # info
        audit_log.log_auth_failure()  # warning
        audit_log.log_suspicious_activity("test")  # error
        
        warning_events = audit_log.list_events(severity="warning")
        assert len(warning_events) == 1
        assert warning_events[0]["severity"] == "warning"
    
    def test_list_events_with_limit(self, audit_log):
        """Test limiting number of returned events."""
        for i in range(10):
            audit_log.log_auth_success(f"user{i}", f"user{i}@example.com")
        
        events = audit_log.list_events(limit=5)
        assert len(events) == 5
    
    def test_max_entries_enforcement(self):
        """Test that log enforces max entries limit."""
        audit_log = AuditLog(max_entries=5)
        
        # Add more than max
        for i in range(10):
            audit_log.log_auth_success(f"user{i}", f"user{i}@example.com")
        
        # Should only have the last 5
        events = audit_log.list_events()
        assert len(events) == 5
        assert events[0]["user_id"] == "user5"  # Oldest kept entry
        assert events[-1]["user_id"] == "user9"  # Newest entry
    
    def test_get_security_summary_empty(self, audit_log):
        """Test security summary with no events."""
        summary = audit_log.get_security_summary()
        
        assert summary["total_events"] == 0
        assert summary["by_type"] == {}
        assert summary["by_severity"] == {}
        assert summary["recent_critical"] == []
    
    def test_get_security_summary_with_events(self, audit_log):
        """Test security summary with various events."""
        audit_log.log_auth_success("u1", "u1@example.com")
        audit_log.log_auth_success("u2", "u2@example.com")
        audit_log.log_auth_failure()
        audit_log.log_suspicious_activity("test", severity="critical")
        
        summary = audit_log.get_security_summary()
        
        assert summary["total_events"] == 4
        assert summary["by_type"]["auth_success"] == 2
        assert summary["by_type"]["auth_failure"] == 1
        assert summary["by_type"]["suspicious_activity"] == 1
        assert summary["by_severity"]["info"] == 2
        assert summary["by_severity"]["warning"] == 1
        assert summary["by_severity"]["critical"] == 1
        assert len(summary["recent_critical"]) == 1
