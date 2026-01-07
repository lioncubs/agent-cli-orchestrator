"""Tests for MCP session tools."""

import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime

from src.mcp.tools.session import SessionTools
from src.mcp.models import (
    ContinueSessionInput,
    ListSessionsInput,
    GetSessionInput,
    CloseSessionInput
)
from src.session.models import Session, SessionType, SessionStatus


@pytest.fixture
def mock_session_manager():
    """Create mock session manager."""
    manager = Mock()
    manager.continue_session = AsyncMock()
    manager.cleanup_session = AsyncMock()
    return manager


@pytest.fixture
def mock_session_store():
    """Create mock session store."""
    store = Mock()
    store.list_sessions = AsyncMock()
    store.get_session = AsyncMock()
    store.update_session = AsyncMock()
    return store


@pytest.fixture
def session_tools(mock_session_manager, mock_session_store):
    """Create SessionTools instance."""
    return SessionTools(
        session_manager=mock_session_manager,
        session_store=mock_session_store
    )


@pytest.mark.asyncio
async def test_continue_session_success(session_tools, mock_session_manager):
    """Test successful session continuation."""
    session_id = uuid4()
    mock_session_manager.continue_session.return_value = {
        "turn_id": 2,
        "response": "Continued response",
        "response_summary": "Summary",
        "files_analyzed": [],
        "files_changed": [],
        "timestamp": datetime.now()
    }
    
    input_data = ContinueSessionInput(
        session_id=session_id,
        prompt="Continue from here"
    )
    
    result = await session_tools.continue_session(input_data)
    
    assert result is not None
    assert result["turn_id"] == 2
    assert result["prompt"] == "Continue from here"
    mock_session_manager.continue_session.assert_called_once()


@pytest.mark.asyncio
async def test_continue_session_error(session_tools, mock_session_manager):
    """Test session continuation error handling."""
    session_id = uuid4()
    mock_session_manager.continue_session.side_effect = Exception("Session not found")
    
    input_data = ContinueSessionInput(
        session_id=session_id,
        prompt="This will fail"
    )
    
    result = await session_tools.continue_session(input_data)
    
    assert "error" in result
    assert "Failed to continue session" in result["error"]


@pytest.mark.asyncio
async def test_list_sessions_all(session_tools, mock_session_store):
    """Test listing all sessions."""
    sessions = [
        Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="repo1",
            user_id="user1",
            created_at=datetime.now(),
            last_activity_at=datetime.now()
        ),
        Session(
            id=uuid4(),
            type=SessionType.RESEARCH,
            status=SessionStatus.COMPLETED,
            repo_name="repo2",
            user_id="user2",
            created_at=datetime.now(),
            last_activity_at=datetime.now()
        )
    ]
    mock_session_store.list_sessions.return_value = sessions
    
    input_data = ListSessionsInput(limit=10)
    
    result = await session_tools.list_sessions(input_data)
    
    assert "sessions" in result
    assert result["total"] == 2
    assert len(result["sessions"]) == 2


@pytest.mark.asyncio
async def test_list_sessions_with_filters(session_tools, mock_session_store):
    """Test listing sessions with filters."""
    session = Session(
        id=uuid4(),
        type=SessionType.DELEGATION,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.list_sessions.return_value = [session]
    
    input_data = ListSessionsInput(
        type=SessionType.DELEGATION,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="alice",
        limit=10
    )
    
    result = await session_tools.list_sessions(input_data)
    
    assert result["total"] == 1
    assert result["sessions"][0]["type"] == SessionType.DELEGATION
    assert result["sessions"][0]["user_id"] == "alice"


@pytest.mark.asyncio
async def test_list_sessions_with_limit(session_tools, mock_session_store):
    """Test listing sessions respects limit."""
    sessions = [
        Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name=f"repo{i}",
            user_id="user",
            created_at=datetime.now(),
            last_activity_at=datetime.now()
        )
        for i in range(20)
    ]
    mock_session_store.list_sessions.return_value = sessions
    
    input_data = ListSessionsInput(limit=5)
    
    result = await session_tools.list_sessions(input_data)
    
    assert len(result["sessions"]) == 5
    assert result["total"] == 5


@pytest.mark.asyncio
async def test_list_sessions_error(session_tools, mock_session_store):
    """Test list sessions error handling."""
    mock_session_store.list_sessions.side_effect = Exception("Database error")
    
    input_data = ListSessionsInput(limit=10)
    
    result = await session_tools.list_sessions(input_data)
    
    assert "error" in result
    assert "Failed to list sessions" in result["error"]


@pytest.mark.asyncio
async def test_get_session_success(session_tools, mock_session_store):
    """Test getting session details."""
    session_id = uuid4()
    session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.COMMITTED,
        repo_name="test-repo",
        user_id="alice",
        created_at=datetime.now(),
        last_activity_at=datetime.now(),
        files_changed=["file1.py", "file2.py"],
        pr_url="https://github.com/test/pr/1"
    )
    mock_session_store.get_session.return_value = session
    
    input_data = GetSessionInput(session_id=session_id)
    
    result = await session_tools.get_session(input_data)
    
    assert result is not None
    assert result["session_id"] == session_id
    assert result["type"] == SessionType.DELEGATION
    assert result["files_changed"] == ["file1.py", "file2.py"]
    assert result["pr_url"] == "https://github.com/test/pr/1"


@pytest.mark.asyncio
async def test_get_session_not_found(session_tools, mock_session_store):
    """Test getting non-existent session."""
    session_id = uuid4()
    mock_session_store.get_session.return_value = None
    
    input_data = GetSessionInput(session_id=session_id)
    
    result = await session_tools.get_session(input_data)
    
    assert "error" in result
    assert "Session not found" in result["error"]


@pytest.mark.asyncio
async def test_get_session_error(session_tools, mock_session_store):
    """Test get session error handling."""
    session_id = uuid4()
    mock_session_store.get_session.side_effect = Exception("Database error")
    
    input_data = GetSessionInput(session_id=session_id)
    
    result = await session_tools.get_session(input_data)
    
    assert "error" in result
    assert "Failed to get session" in result["error"]


@pytest.mark.asyncio
async def test_close_session_normal(session_tools, mock_session_store, mock_session_manager):
    """Test closing session normally."""
    session_id = uuid4()
    session = Session(
        id=session_id,
        type=SessionType.QUERY,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="user",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = session
    
    input_data = CloseSessionInput(session_id=session_id, abandon=False)
    
    result = await session_tools.close_session(input_data)
    
    assert result["success"] is True
    assert result["status"] == SessionStatus.CLOSED.value
    assert "closed" in result["message"]
    mock_session_store.update_session.assert_called_once()
    mock_session_manager.cleanup_session.assert_called_once()


@pytest.mark.asyncio
async def test_close_session_abandon(session_tools, mock_session_store, mock_session_manager):
    """Test abandoning session."""
    session_id = uuid4()
    session = Session(
        id=session_id,
        type=SessionType.DELEGATION,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="user",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = session
    
    input_data = CloseSessionInput(session_id=session_id, abandon=True)
    
    result = await session_tools.close_session(input_data)
    
    assert result["success"] is True
    assert result["status"] == SessionStatus.ABANDONED.value
    assert "abandoned" in result["message"]


@pytest.mark.asyncio
async def test_close_session_not_found(session_tools, mock_session_store):
    """Test closing non-existent session."""
    session_id = uuid4()
    mock_session_store.get_session.return_value = None
    
    input_data = CloseSessionInput(session_id=session_id)
    
    result = await session_tools.close_session(input_data)
    
    assert "error" in result
    assert "Session not found" in result["error"]


@pytest.mark.asyncio
async def test_close_session_error(session_tools, mock_session_store):
    """Test close session error handling."""
    session_id = uuid4()
    mock_session_store.get_session.side_effect = Exception("Database error")
    
    input_data = CloseSessionInput(session_id=session_id)
    
    result = await session_tools.close_session(input_data)
    
    assert "error" in result
    assert "Failed to close session" in result["error"]
