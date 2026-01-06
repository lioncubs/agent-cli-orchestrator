"""Tests for tool policy enforcement."""

import pytest

from src.permissions.tool_policy import (
    ToolPolicy,
    Operation,
    OperationTier
)


class TestOperationTier:
    """Test OperationTier enum."""
    
    def test_operation_tiers(self):
        """Test all operation tier values."""
        assert OperationTier.READ_ONLY == "read_only"
        assert OperationTier.STANDARD == "standard"
        assert OperationTier.ADMIN == "admin"


class TestOperation:
    """Test Operation enum."""
    
    def test_read_operations(self):
        """Test read operation values."""
        assert Operation.READ_FILE == "read_file"
        assert Operation.LIST_FILES == "list_files"
        assert Operation.SEARCH_CODE == "search_code"
        assert Operation.GET_COMMIT == "get_commit"
        assert Operation.GET_BRANCH == "get_branch"
        assert Operation.LIST_BRANCHES == "list_branches"
    
    def test_write_operations(self):
        """Test write operation values."""
        assert Operation.WRITE_FILE == "write_file"
        assert Operation.DELETE_FILE == "delete_file"
        assert Operation.CREATE_BRANCH == "create_branch"
        assert Operation.COMMIT_CHANGES == "commit_changes"
        assert Operation.PUSH_CHANGES == "push_changes"
    
    def test_worktree_operations(self):
        """Test worktree operation values."""
        assert Operation.CREATE_WORKTREE == "create_worktree"
        assert Operation.DELETE_WORKTREE == "delete_worktree"
    
    def test_admin_operations(self):
        """Test admin operation values."""
        assert Operation.DELETE_SESSION == "delete_session"
        assert Operation.FORCE_PUSH == "force_push"
        assert Operation.DELETE_BRANCH == "delete_branch"


class TestToolPolicy:
    """Test ToolPolicy class."""
    
    def test_default_tier(self):
        """Test default tier initialization."""
        policy = ToolPolicy()
        assert policy.default_tier == OperationTier.STANDARD
        
        policy_read_only = ToolPolicy(default_tier=OperationTier.READ_ONLY)
        assert policy_read_only.default_tier == OperationTier.READ_ONLY
    
    def test_set_and_get_session_tier(self):
        """Test setting and getting session tier."""
        policy = ToolPolicy()
        session_id = "test-session-123"
        
        # Default should be STANDARD
        assert policy.get_session_tier(session_id) == OperationTier.STANDARD
        
        # Set to READ_ONLY
        policy.set_session_tier(session_id, OperationTier.READ_ONLY)
        assert policy.get_session_tier(session_id) == OperationTier.READ_ONLY
        
        # Set to ADMIN
        policy.set_session_tier(session_id, OperationTier.ADMIN)
        assert policy.get_session_tier(session_id) == OperationTier.ADMIN
    
    def test_read_only_tier_restrictions(self):
        """Test that read-only tier only allows read operations."""
        policy = ToolPolicy()
        session_id = "read-only-session"
        policy.set_session_tier(session_id, OperationTier.READ_ONLY)
        
        # Read operations should be allowed
        assert policy.is_operation_allowed(Operation.READ_FILE, session_id)
        assert policy.is_operation_allowed(Operation.LIST_FILES, session_id)
        assert policy.is_operation_allowed(Operation.SEARCH_CODE, session_id)
        assert policy.is_operation_allowed(Operation.GET_COMMIT, session_id)
        assert policy.is_operation_allowed(Operation.GET_BRANCH, session_id)
        assert policy.is_operation_allowed(Operation.LIST_BRANCHES, session_id)
        
        # Write operations should be denied
        assert not policy.is_operation_allowed(Operation.WRITE_FILE, session_id)
        assert not policy.is_operation_allowed(Operation.DELETE_FILE, session_id)
        assert not policy.is_operation_allowed(Operation.CREATE_BRANCH, session_id)
        assert not policy.is_operation_allowed(Operation.COMMIT_CHANGES, session_id)
        assert not policy.is_operation_allowed(Operation.PUSH_CHANGES, session_id)
        
        # Worktree operations should be denied
        assert not policy.is_operation_allowed(Operation.CREATE_WORKTREE, session_id)
        assert not policy.is_operation_allowed(Operation.DELETE_WORKTREE, session_id)
        
        # Admin operations should be denied
        assert not policy.is_operation_allowed(Operation.DELETE_SESSION, session_id)
        assert not policy.is_operation_allowed(Operation.FORCE_PUSH, session_id)
        assert not policy.is_operation_allowed(Operation.DELETE_BRANCH, session_id)
    
    def test_standard_tier_permissions(self):
        """Test that standard tier allows non-admin operations."""
        policy = ToolPolicy()
        session_id = "standard-session"
        policy.set_session_tier(session_id, OperationTier.STANDARD)
        
        # Read operations should be allowed
        assert policy.is_operation_allowed(Operation.READ_FILE, session_id)
        assert policy.is_operation_allowed(Operation.LIST_FILES, session_id)
        
        # Write operations should be allowed
        assert policy.is_operation_allowed(Operation.WRITE_FILE, session_id)
        assert policy.is_operation_allowed(Operation.DELETE_FILE, session_id)
        assert policy.is_operation_allowed(Operation.COMMIT_CHANGES, session_id)
        
        # Worktree operations should be allowed
        assert policy.is_operation_allowed(Operation.CREATE_WORKTREE, session_id)
        assert policy.is_operation_allowed(Operation.DELETE_WORKTREE, session_id)
        
        # Admin operations should be denied
        assert not policy.is_operation_allowed(Operation.DELETE_SESSION, session_id)
        assert not policy.is_operation_allowed(Operation.FORCE_PUSH, session_id)
        assert not policy.is_operation_allowed(Operation.DELETE_BRANCH, session_id)
    
    def test_admin_tier_permissions(self):
        """Test that admin tier allows all operations."""
        policy = ToolPolicy()
        session_id = "admin-session"
        policy.set_session_tier(session_id, OperationTier.ADMIN)
        
        # All operations should be allowed
        for operation in Operation:
            assert policy.is_operation_allowed(operation, session_id), \
                f"Admin should allow {operation}"
    
    def test_check_operation_success(self):
        """Test check_operation allows permitted operations."""
        policy = ToolPolicy()
        session_id = "test-session"
        policy.set_session_tier(session_id, OperationTier.STANDARD)
        
        # Should not raise exception for allowed operation
        policy.check_operation(Operation.READ_FILE, session_id)
        policy.check_operation(Operation.WRITE_FILE, session_id)
    
    def test_check_operation_failure(self):
        """Test check_operation raises exception for forbidden operations."""
        policy = ToolPolicy()
        session_id = "read-only-session"
        policy.set_session_tier(session_id, OperationTier.READ_ONLY)
        
        # Should raise PermissionError for write operations
        with pytest.raises(PermissionError) as exc_info:
            policy.check_operation(Operation.WRITE_FILE, session_id)
        assert "not allowed" in str(exc_info.value).lower()
        
        # Should raise PermissionError for admin operations
        with pytest.raises(PermissionError) as exc_info:
            policy.check_operation(Operation.DELETE_SESSION, session_id)
        assert "not allowed" in str(exc_info.value).lower()
    
    def test_check_operation_with_explicit_tier(self):
        """Test check_operation with explicit tier parameter."""
        policy = ToolPolicy()
        
        # Use explicit tier, ignore session
        policy.check_operation(Operation.READ_FILE, tier=OperationTier.READ_ONLY)
        
        with pytest.raises(PermissionError):
            policy.check_operation(Operation.WRITE_FILE, tier=OperationTier.READ_ONLY)
    
    def test_get_allowed_operations_read_only(self):
        """Test getting allowed operations for read-only tier."""
        policy = ToolPolicy()
        session_id = "read-only-session"
        policy.set_session_tier(session_id, OperationTier.READ_ONLY)
        
        allowed = policy.get_allowed_operations(session_id)
        
        # Should only contain read operations
        assert Operation.READ_FILE in allowed
        assert Operation.LIST_FILES in allowed
        assert Operation.SEARCH_CODE in allowed
        
        # Should not contain write or admin operations
        assert Operation.WRITE_FILE not in allowed
        assert Operation.DELETE_SESSION not in allowed
    
    def test_get_allowed_operations_standard(self):
        """Test getting allowed operations for standard tier."""
        policy = ToolPolicy()
        session_id = "standard-session"
        policy.set_session_tier(session_id, OperationTier.STANDARD)
        
        allowed = policy.get_allowed_operations(session_id)
        
        # Should contain read and write operations
        assert Operation.READ_FILE in allowed
        assert Operation.WRITE_FILE in allowed
        assert Operation.CREATE_WORKTREE in allowed
        
        # Should not contain admin operations
        assert Operation.DELETE_SESSION not in allowed
        assert Operation.FORCE_PUSH not in allowed
    
    def test_get_allowed_operations_admin(self):
        """Test getting allowed operations for admin tier."""
        policy = ToolPolicy()
        session_id = "admin-session"
        policy.set_session_tier(session_id, OperationTier.ADMIN)
        
        allowed = policy.get_allowed_operations(session_id)
        
        # Should contain all operations
        for operation in Operation:
            assert operation in allowed
    
    def test_remove_session(self):
        """Test removing a session from tier tracking."""
        policy = ToolPolicy()
        session_id = "test-session"
        
        # Set tier
        policy.set_session_tier(session_id, OperationTier.ADMIN)
        assert policy.get_session_tier(session_id) == OperationTier.ADMIN
        
        # Remove session
        policy.remove_session(session_id)
        
        # Should revert to default
        assert policy.get_session_tier(session_id) == policy.default_tier
    
    def test_remove_nonexistent_session(self):
        """Test removing a session that doesn't exist."""
        policy = ToolPolicy()
        
        # Should not raise exception
        policy.remove_session("nonexistent-session")
    
    def test_operation_allowed_with_no_session(self):
        """Test operation check with no session ID uses default tier."""
        policy = ToolPolicy(default_tier=OperationTier.READ_ONLY)
        
        # Should use default tier (READ_ONLY)
        assert policy.is_operation_allowed(Operation.READ_FILE)
        assert not policy.is_operation_allowed(Operation.WRITE_FILE)
    
    def test_explicit_tier_overrides_session(self):
        """Test that explicit tier parameter overrides session tier."""
        policy = ToolPolicy()
        session_id = "test-session"
        policy.set_session_tier(session_id, OperationTier.ADMIN)
        
        # Explicit tier should override
        assert not policy.is_operation_allowed(
            Operation.WRITE_FILE,
            session_id=session_id,
            tier=OperationTier.READ_ONLY
        )
