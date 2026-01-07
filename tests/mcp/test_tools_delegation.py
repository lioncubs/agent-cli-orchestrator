"""Tests for MCP delegation tools."""

import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime

from src.mcp.tools.delegation import DelegationTools
from src.mcp.models import (
    StartDelegationInput,
    CommitChangesInput,
    CreatePRInput
)
from src.session.models import Session, SessionType, SessionStatus, GitIdentity


@pytest.fixture
def mock_delegation_service():
    """Create mock delegation service."""
    service = Mock()
    service.initialize_delegation = AsyncMock()
    service.commit_changes = AsyncMock()
    service.create_pull_request = AsyncMock()
    return service


@pytest.fixture
def mock_session_store():
    """Create mock session store."""
    store = Mock()
    store.get_session = AsyncMock()
    return store


@pytest.fixture
def delegation_tools(mock_delegation_service, mock_session_store):
    """Create DelegationTools instance."""
    return DelegationTools(
        delegation_service=mock_delegation_service,
        session_store=mock_session_store
    )


@pytest.mark.asyncio
async def test_start_delegation_success(delegation_tools, mock_delegation_service):
    """Test successful delegation start."""
    session_id = uuid4()
    user_identity = GitIdentity(name="Alice", email="alice@example.com")
    
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now(),
        base_branch="main",
        session_branch="agent/alice/abc123-fix-bug",
        worktree_path="/tmp/worktree"
    )
    mock_delegation_service.initialize_delegation.return_value = mock_session
    
    input_data = StartDelegationInput(
        repo_name="test-repo",
        prompt="Fix the bug in auth module",
        user_id="alice",
        user_identity=user_identity,
        base_branch="main",
        task_slug="fix-bug"
    )
    
    result = await delegation_tools.start_delegation(input_data)
    
    assert result is not None
    assert result["session_id"] == session_id
    assert result["type"] == SessionType.DELEGATION
    assert result["session_branch"] == "agent/alice/abc123-fix-bug"
    mock_delegation_service.initialize_delegation.assert_called_once()


@pytest.mark.asyncio
async def test_start_delegation_without_optional_params(delegation_tools, mock_delegation_service):
    """Test delegation start without optional parameters."""
    session_id = uuid4()
    user_identity = GitIdentity(name="Bob", email="bob@example.com")
    
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="bob",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_delegation_service.initialize_delegation.return_value = mock_session
    
    input_data = StartDelegationInput(
        repo_name="test-repo",
        prompt="Add new feature",
        user_id="bob",
        user_identity=user_identity
    )
    
    result = await delegation_tools.start_delegation(input_data)
    
    assert result is not None
    assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_start_delegation_error(delegation_tools, mock_delegation_service):
    """Test delegation start error handling."""
    user_identity = GitIdentity(name="Alice", email="alice@example.com")
    mock_delegation_service.initialize_delegation.side_effect = Exception("Failed to create worktree")
    
    input_data = StartDelegationInput(
        repo_name="test-repo",
        prompt="This will fail",
        user_id="alice",
        user_identity=user_identity
    )
    
    result = await delegation_tools.start_delegation(input_data)
    
    assert "error" in result
    assert "Failed to start delegation" in result["error"]


@pytest.mark.asyncio
async def test_commit_changes_success(delegation_tools, mock_session_store, mock_delegation_service):
    """Test successful commit."""
    session_id = uuid4()
    user_identity = GitIdentity(name="Alice", email="alice@example.com")
    agent_identity = GitIdentity(name="Agent", email="agent@orchestrator.local")
    
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    
    mock_delegation_service.commit_changes.return_value = {
        "commit_sha": "abc123def456",
        "files_changed": ["file1.py", "file2.py"],
        "message": "Fix authentication bug",
        "author": user_identity,
        "committer": agent_identity
    }
    
    input_data = CommitChangesInput(
        session_id=session_id,
        message="Fix authentication bug"
    )
    
    result = await delegation_tools.commit_changes(input_data)
    
    assert result is not None
    assert result["commit_sha"] == "abc123def456"
    assert len(result["files_changed"]) == 2
    assert result["commit_message"] == "Fix authentication bug"
    mock_delegation_service.commit_changes.assert_called_once()


@pytest.mark.asyncio
async def test_commit_changes_without_message(delegation_tools, mock_session_store, mock_delegation_service):
    """Test commit with auto-generated message."""
    session_id = uuid4()
    user_identity = GitIdentity(name="Alice", email="alice@example.com")
    agent_identity = GitIdentity(name="Agent", email="agent@orchestrator.local")
    
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    
    mock_delegation_service.commit_changes.return_value = {
        "commit_sha": "def789",
        "files_changed": ["file3.py"],
        "message": "Agent delegation changes",
        "author": user_identity,
        "committer": agent_identity
    }
    
    input_data = CommitChangesInput(session_id=session_id)
    
    result = await delegation_tools.commit_changes(input_data)
    
    assert result is not None
    assert result["commit_message"] == "Agent delegation changes"


@pytest.mark.asyncio
async def test_commit_changes_session_not_found(delegation_tools, mock_session_store):
    """Test commit with missing session."""
    session_id = uuid4()
    mock_session_store.get_session.return_value = None
    
    input_data = CommitChangesInput(session_id=session_id)
    
    result = await delegation_tools.commit_changes(input_data)
    
    assert "error" in result
    assert "Session not found" in result["error"]


@pytest.mark.asyncio
async def test_commit_changes_wrong_session_type(delegation_tools, mock_session_store):
    """Test commit with wrong session type."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.QUERY,  # Wrong type
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    
    input_data = CommitChangesInput(session_id=session_id)
    
    result = await delegation_tools.commit_changes(input_data)
    
    assert "error" in result
    assert "not a delegation session" in result["error"]


@pytest.mark.asyncio
async def test_commit_changes_error(delegation_tools, mock_session_store, mock_delegation_service):
    """Test commit error handling."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    mock_delegation_service.commit_changes.side_effect = Exception("Git error")
    
    input_data = CommitChangesInput(session_id=session_id)
    
    result = await delegation_tools.commit_changes(input_data)
    
    assert "error" in result
    assert "Failed to commit changes" in result["error"]


@pytest.mark.asyncio
async def test_create_pr_success(delegation_tools, mock_session_store, mock_delegation_service):
    """Test successful PR creation."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.COMMITTED,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    
    # Mock delegation service to return updated session with PR URL
    mock_updated_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.PR_CREATED,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now(),
        pr_url="https://github.com/test/repo/pull/123",
        session_branch="agent/alice/abc-fix",
        base_branch="main"
    )
    mock_delegation_service.create_pull_request.return_value = mock_updated_session
    
    input_data = CreatePRInput(
        session_id=session_id,
        title="Fix authentication bug",
        body="This PR fixes the auth bug",
        draft=False
    )
    
    result = await delegation_tools.create_pr(input_data)
    
    assert result is not None
    assert result["pr_url"] == "https://github.com/test/repo/pull/123"
    assert result["head_branch"] == "agent/alice/abc-fix"
    mock_delegation_service.create_pull_request.assert_called_once()


@pytest.mark.asyncio
async def test_create_pr_as_draft(delegation_tools, mock_session_store, mock_delegation_service):
    """Test creating draft PR."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.COMMITTED,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    
    # Mock delegation service to return updated session
    mock_updated_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.PR_CREATED,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now(),
        pr_url="https://github.com/test/repo/pull/124",
        session_branch="agent/alice/abc-wip",
        base_branch="main"
    )
    mock_delegation_service.create_pull_request.return_value = mock_updated_session
    
    input_data = CreatePRInput(
        session_id=session_id,
        draft=True
    )
    
    result = await delegation_tools.create_pr(input_data)
    
    assert result["draft"] is True


@pytest.mark.asyncio
async def test_create_pr_session_not_found(delegation_tools, mock_session_store):
    """Test PR creation with missing session."""
    session_id = uuid4()
    mock_session_store.get_session.return_value = None
    
    input_data = CreatePRInput(session_id=session_id)
    
    result = await delegation_tools.create_pr(input_data)
    
    assert "error" in result
    assert "Session not found" in result["error"]


@pytest.mark.asyncio
async def test_create_pr_wrong_session_type(delegation_tools, mock_session_store):
    """Test PR creation with wrong session type."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.RESEARCH,  # Wrong type
        status=SessionStatus.COMPLETED,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    
    input_data = CreatePRInput(session_id=session_id)
    
    result = await delegation_tools.create_pr(input_data)
    
    assert "error" in result
    assert "not a delegation session" in result["error"]


@pytest.mark.asyncio
async def test_create_pr_error(delegation_tools, mock_session_store, mock_delegation_service):
    """Test PR creation error handling."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.COMMITTED,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    mock_delegation_service.create_pull_request.side_effect = Exception("GitHub API error")
    
    input_data = CreatePRInput(session_id=session_id)
    
    result = await delegation_tools.create_pr(input_data)
    
    assert "error" in result
    assert "Failed to create pull request" in result["error"]
