"""Tests for MCP query tools."""

import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime

from src.mcp.tools.query import QueryTools
from src.mcp.models import QueryInput, StartResearchInput, CompleteResearchInput
from src.session.models import Session, SessionType, SessionStatus, ResearchArtifact, GitIdentity


@pytest.fixture
def mock_query_service():
    """Create mock query service."""
    service = Mock()
    service.execute_query = AsyncMock()
    return service


@pytest.fixture
def mock_research_service():
    """Create mock research service."""
    service = Mock()
    service.start_research = AsyncMock()
    service.complete_research = AsyncMock()
    return service


@pytest.fixture
def mock_session_store():
    """Create mock session store."""
    store = Mock()
    store.get_session = AsyncMock()
    return store


@pytest.fixture
def mock_research_store():
    """Create mock research store."""
    return Mock()


@pytest.fixture
def query_tools(mock_query_service, mock_research_service, mock_session_store, mock_research_store):
    """Create QueryTools instance."""
    return QueryTools(
        query_service=mock_query_service,
        research_service=mock_research_service,
        session_store=mock_session_store,
        research_store=mock_research_store
    )


@pytest.mark.asyncio
async def test_query_success(query_tools, mock_query_service):
    """Test successful query execution."""
    # Setup
    mock_query_service.execute_query.return_value = {
        "turn_id": 1,
        "response": "Test response",
        "response_summary": "Summary",
        "files_analyzed": ["file1.py"],
        "files_changed": []
    }
    
    input_data = QueryInput(
        repo_name="test-repo",
        prompt="What is this code doing?"
    )
    
    # Execute
    result = await query_tools.query(input_data)
    
    # Verify
    assert result is not None
    assert "turn_id" in result
    assert result["prompt"] == "What is this code doing?"
    assert result["response"] == "Test response"
    assert mock_query_service.execute_query.called


@pytest.mark.asyncio
async def test_query_with_session_id(query_tools, mock_query_service):
    """Test query with existing session ID."""
    session_id = uuid4()
    mock_query_service.execute_query.return_value = {
        "turn_id": 2,
        "response": "Continued response",
        "response_summary": "Continued",
        "files_analyzed": [],
        "files_changed": []
    }
    
    input_data = QueryInput(
        repo_name="test-repo",
        prompt="Tell me more",
        session_id=session_id
    )
    
    result = await query_tools.query(input_data)
    
    assert result is not None
    assert result["turn_id"] == 2
    mock_query_service.execute_query.assert_called_once()


@pytest.mark.asyncio
async def test_query_error_handling(query_tools, mock_query_service):
    """Test query error handling."""
    mock_query_service.execute_query.side_effect = Exception("Query failed")
    
    input_data = QueryInput(
        repo_name="test-repo",
        prompt="This will fail"
    )
    
    result = await query_tools.query(input_data)
    
    assert "error" in result
    assert "Query execution failed" in result["error"]


@pytest.mark.asyncio
async def test_start_research_success(query_tools, mock_research_service):
    """Test successful research session start."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.RESEARCH,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="test-user",
        created_at=datetime.now(),
        last_activity_at=datetime.now(),
        base_branch="main",
        session_branch="research-branch",
        worktree_path="/tmp/worktree"
    )
    mock_research_service.start_research.return_value = mock_session
    
    input_data = StartResearchInput(
        repo_name="test-repo",
        prompt="Research this codebase",
        base_branch="main"
    )
    
    result = await query_tools.start_research(input_data)
    
    assert result is not None
    assert result["session_id"] == session_id
    assert result["type"] == SessionType.RESEARCH
    assert result["repo_name"] == "test-repo"
    mock_research_service.start_research.assert_called_once()


@pytest.mark.asyncio
async def test_start_research_without_base_branch(query_tools, mock_research_service):
    """Test research start without specifying base branch."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.RESEARCH,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="test-user",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_research_service.start_research.return_value = mock_session
    
    input_data = StartResearchInput(
        repo_name="test-repo",
        prompt="Research this"
    )
    
    result = await query_tools.start_research(input_data)
    
    assert result is not None
    assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_start_research_error(query_tools, mock_research_service):
    """Test research start error handling."""
    mock_research_service.start_research.side_effect = Exception("Failed to create worktree")
    
    input_data = StartResearchInput(
        repo_name="test-repo",
        prompt="This will fail"
    )
    
    result = await query_tools.start_research(input_data)
    
    assert "error" in result
    assert "Failed to start research session" in result["error"]


@pytest.mark.asyncio
async def test_complete_research_success(query_tools, mock_session_store, mock_research_service):
    """Test successful research completion."""
    session_id = uuid4()
    research_id = uuid4()
    
    mock_session = Session(
        id=session_id,
        type=SessionType.RESEARCH,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="test-user",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    
    mock_artifact = ResearchArtifact(
        research_id=research_id,
        repo_name="test-repo",
        base_branch="main",
        base_commit="abc123",
        created_at=datetime.now(),
        user_id="test-user",
        summary="Research summary",
        findings=[],
        recommendations=[],
        conversation=[],
        suggested_delegation_prompt="Fix the issues",
        relevant_files=[]
    )
    mock_research_service.complete_research.return_value = mock_artifact
    
    input_data = CompleteResearchInput(session_id=session_id)
    
    result = await query_tools.complete_research(input_data)
    
    assert result is not None
    assert result["research_id"] == research_id
    assert result["summary"] == "Research summary"
    mock_session_store.get_session.assert_called_once_with(session_id)
    mock_research_service.complete_research.assert_called_once()


@pytest.mark.asyncio
async def test_complete_research_session_not_found(query_tools, mock_session_store):
    """Test research completion with missing session."""
    session_id = uuid4()
    mock_session_store.get_session.return_value = None
    
    input_data = CompleteResearchInput(session_id=session_id)
    
    result = await query_tools.complete_research(input_data)
    
    assert "error" in result
    assert "Session not found" in result["error"]
    assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_complete_research_wrong_session_type(query_tools, mock_session_store):
    """Test research completion with wrong session type."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.DELEGATION,  # Wrong type
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="test-user",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    
    input_data = CompleteResearchInput(session_id=session_id)
    
    result = await query_tools.complete_research(input_data)
    
    assert "error" in result
    assert "not a research session" in result["error"]


@pytest.mark.asyncio
async def test_complete_research_error(query_tools, mock_session_store, mock_research_service):
    """Test research completion error handling."""
    session_id = uuid4()
    mock_session = Session(
        id=session_id,
        type=SessionType.RESEARCH,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="test-user",
        created_at=datetime.now(),
        last_activity_at=datetime.now()
    )
    mock_session_store.get_session.return_value = mock_session
    mock_research_service.complete_research.side_effect = Exception("Completion failed")
    
    input_data = CompleteResearchInput(session_id=session_id)
    
    result = await query_tools.complete_research(input_data)
    
    assert "error" in result
    assert "Failed to complete research" in result["error"]
