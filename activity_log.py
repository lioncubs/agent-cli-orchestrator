"""Simple in-memory activity log for API actions."""

from datetime import datetime
from typing import Any, Dict, List, Optional


class ActivityLog:
    """Ring buffer style activity log.

    Args:
        max_entries: Maximum number of entries to keep in memory.
    """

    def __init__(self, max_entries: int = 200):
        self.max_entries = max_entries
        self._entries: List[Dict[str, Any]] = []

    def add(self, action: str, status: str, payload: Optional[Dict[str, Any]] = None,
            result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Append a log entry and trim when over capacity.

        Args:
            action: Short action name (e.g., "prompt", "list_worktrees").
            status: Outcome label such as "success" or "error".
            payload: Optional request context payload.
            result: Optional result payload.

        Returns:
            Newly created log entry.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "status": status,
            "payload": payload or {},
            "result": result or {}
        }
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        return entry

    def list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return the most recent log entries.

        Args:
            limit: Optional maximum number of entries to return.

        Returns:
            List of log entries ordered oldest->newest.
        """
        if limit and limit > 0:
            return self._entries[-limit:]
        return list(self._entries)


activity_log = ActivityLog()
