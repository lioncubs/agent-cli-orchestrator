"""Tool policy enforcement for read-only and admin operations."""

from enum import Enum
from typing import List, Set, Optional


class OperationTier(str, Enum):
    """Operation tier levels."""
    READ_ONLY = "read_only"
    STANDARD = "standard"
    ADMIN = "admin"


class Operation(str, Enum):
    """Available operations."""
    # Read operations
    READ_FILE = "read_file"
    LIST_FILES = "list_files"
    SEARCH_CODE = "search_code"
    GET_COMMIT = "get_commit"
    GET_BRANCH = "get_branch"
    LIST_BRANCHES = "list_branches"
    
    # Write operations
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    CREATE_BRANCH = "create_branch"
    COMMIT_CHANGES = "commit_changes"
    PUSH_CHANGES = "push_changes"
    
    # Worktree operations
    CREATE_WORKTREE = "create_worktree"
    DELETE_WORKTREE = "delete_worktree"
    
    # Admin operations
    DELETE_SESSION = "delete_session"
    FORCE_PUSH = "force_push"
    DELETE_BRANCH = "delete_branch"


class ToolPolicy:
    """
    Enforce operation restrictions based on session type and user permissions.
    
    Implements strict limits for read-only tiers and guards admin operations.
    """
    
    # Define read-only operations
    READ_ONLY_OPERATIONS: Set[Operation] = {
        Operation.READ_FILE,
        Operation.LIST_FILES,
        Operation.SEARCH_CODE,
        Operation.GET_COMMIT,
        Operation.GET_BRANCH,
        Operation.LIST_BRANCHES,
    }
    
    # Define admin operations
    ADMIN_OPERATIONS: Set[Operation] = {
        Operation.DELETE_SESSION,
        Operation.FORCE_PUSH,
        Operation.DELETE_BRANCH,
    }
    
    def __init__(self, default_tier: OperationTier = OperationTier.STANDARD):
        """
        Initialize tool policy.
        
        Args:
            default_tier: Default operation tier for new sessions
        """
        self.default_tier = default_tier
        self._session_tiers = {}  # session_id -> tier mapping
    
    def set_session_tier(self, session_id: str, tier: OperationTier) -> None:
        """
        Set the operation tier for a session.
        
        Args:
            session_id: Session identifier
            tier: Operation tier to assign
        """
        self._session_tiers[session_id] = tier
    
    def get_session_tier(self, session_id: str) -> OperationTier:
        """
        Get the operation tier for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Operation tier for the session
        """
        return self._session_tiers.get(session_id, self.default_tier)
    
    def is_operation_allowed(
        self,
        operation: Operation,
        session_id: Optional[str] = None,
        tier: Optional[OperationTier] = None
    ) -> bool:
        """
        Check if an operation is allowed.
        
        Args:
            operation: Operation to check
            session_id: Optional session ID (will look up tier)
            tier: Optional explicit tier (overrides session_id lookup)
            
        Returns:
            True if operation is allowed, False otherwise
        """
        # Determine the effective tier
        if tier is None:
            if session_id is None:
                tier = self.default_tier
            else:
                tier = self.get_session_tier(session_id)
        
        # Check admin operations
        if operation in self.ADMIN_OPERATIONS:
            return tier == OperationTier.ADMIN
        
        # Check read-only restrictions
        if tier == OperationTier.READ_ONLY:
            return operation in self.READ_ONLY_OPERATIONS
        
        # Standard tier allows all non-admin operations
        if tier == OperationTier.STANDARD:
            return operation not in self.ADMIN_OPERATIONS
        
        # Admin tier allows everything
        return tier == OperationTier.ADMIN
    
    def check_operation(
        self,
        operation: Operation,
        session_id: Optional[str] = None,
        tier: Optional[OperationTier] = None
    ) -> None:
        """
        Check if an operation is allowed, raise exception if not.
        
        Args:
            operation: Operation to check
            session_id: Optional session ID
            tier: Optional explicit tier
            
        Raises:
            PermissionError: If operation is not allowed
        """
        if not self.is_operation_allowed(operation, session_id, tier):
            effective_tier = tier or self.get_session_tier(session_id) if session_id else self.default_tier
            raise PermissionError(
                f"Operation '{operation.value}' not allowed for tier '{effective_tier.value}'"
            )
    
    def get_allowed_operations(
        self,
        session_id: Optional[str] = None,
        tier: Optional[OperationTier] = None
    ) -> List[Operation]:
        """
        Get list of allowed operations for a tier.
        
        Args:
            session_id: Optional session ID
            tier: Optional explicit tier
            
        Returns:
            List of allowed operations
        """
        effective_tier = tier or self.get_session_tier(session_id) if session_id else self.default_tier
        
        if effective_tier == OperationTier.READ_ONLY:
            return list(self.READ_ONLY_OPERATIONS)
        elif effective_tier == OperationTier.STANDARD:
            return [op for op in Operation if op not in self.ADMIN_OPERATIONS]
        else:  # ADMIN
            return list(Operation)
    
    def remove_session(self, session_id: str) -> None:
        """
        Remove a session from tier tracking.
        
        Args:
            session_id: Session identifier to remove
        """
        self._session_tiers.pop(session_id, None)
