"""Security audit logging for tracking authentication and authorization events."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of security audit events."""
    
    # Authentication events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_INVALID_KEY = "auth_invalid_key"
    AUTH_EXPIRED_KEY = "auth_expired_key"
    
    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    
    # API key events
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_USED = "api_key_used"
    
    # Permission events
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_GRANTED = "permission_granted"
    
    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Security violations
    INVALID_INPUT = "invalid_input"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AuditLog:
    """
    Security audit log for tracking authentication and authorization events.
    
    Separate from the general activity log to ensure security events
    are properly tracked and retained.
    """
    
    def __init__(self, max_entries: int = 1000):
        """
        Initialize audit log.
        
        Args:
            max_entries: Maximum number of entries to keep in memory
        """
        self.max_entries = max_entries
        self._entries: List[Dict[str, Any]] = []
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> Dict[str, Any]:
        """
        Log a security audit event.
        
        Args:
            event_type: Type of event
            user_id: User ID if available
            user_email: User email if available
            ip_address: Client IP address
            path: Request path
            details: Additional event details
            severity: Event severity (info, warning, error, critical)
            
        Returns:
            The created audit entry
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "path": path,
            "details": details or {},
            "severity": severity
        }
        
        self._entries.append(entry)
        
        # Trim if over capacity
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        
        # Log to standard logging system based on severity
        log_message = f"Security event: {event_type.value} - User: {user_email or user_id or 'unknown'} - IP: {ip_address or 'unknown'}"
        if details:
            log_message += f" - Details: {details}"
        
        if severity == "critical":
            logger.critical(log_message)
        elif severity == "error":
            logger.error(log_message)
        elif severity == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return entry
    
    def log_auth_success(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
        method: str = "api_key"
    ):
        """Log successful authentication."""
        self.log_event(
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            details={"method": method},
            severity="info"
        )
    
    def log_auth_failure(
        self,
        ip_address: Optional[str] = None,
        reason: str = "invalid_credentials",
        attempted_user: Optional[str] = None
    ):
        """Log failed authentication attempt."""
        self.log_event(
            event_type=AuditEventType.AUTH_FAILURE,
            ip_address=ip_address,
            user_email=attempted_user,
            details={"reason": reason},
            severity="warning"
        )
    
    def log_permission_denied(
        self,
        user_id: str,
        user_email: str,
        path: str,
        required_permission: str,
        ip_address: Optional[str] = None
    ):
        """Log permission denial."""
        self.log_event(
            event_type=AuditEventType.PERMISSION_DENIED,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            path=path,
            details={"required_permission": required_permission},
            severity="warning"
        )
    
    def log_rate_limit(
        self,
        client_id: str,
        ip_address: Optional[str] = None,
        path: Optional[str] = None
    ):
        """Log rate limit violation."""
        self.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            path=path,
            details={"client_id": client_id},
            severity="warning"
        )
    
    def log_suspicious_activity(
        self,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log suspicious activity."""
        self.log_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "description": description,
                **(details or {})
            },
            severity="error"
        )
    
    def list_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List audit events with optional filtering.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            severity: Filter by severity
            limit: Maximum number of entries to return
            
        Returns:
            List of audit entries
        """
        entries = self._entries
        
        # Apply filters
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type.value]
        
        if user_id:
            entries = [e for e in entries if e["user_id"] == user_id]
        
        if severity:
            entries = [e for e in entries if e["severity"] == severity]
        
        # Apply limit
        if limit and limit > 0:
            entries = entries[-limit:]
        
        return entries
    
    def get_security_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recent security events.
        
        Returns:
            Summary statistics
        """
        total = len(self._entries)
        
        if total == 0:
            return {
                "total_events": 0,
                "by_type": {},
                "by_severity": {},
                "recent_critical": []
            }
        
        # Count by type
        by_type = {}
        for entry in self._entries:
            event_type = entry["event_type"]
            by_type[event_type] = by_type.get(event_type, 0) + 1
        
        # Count by severity
        by_severity = {}
        for entry in self._entries:
            severity = entry["severity"]
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Get recent critical events
        recent_critical = [
            e for e in self._entries
            if e["severity"] in ["critical", "error"]
        ][-10:]  # Last 10 critical/error events
        
        return {
            "total_events": total,
            "by_type": by_type,
            "by_severity": by_severity,
            "recent_critical": recent_critical
        }


# Global audit log instance
security_audit_log = AuditLog()
