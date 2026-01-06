"""Tests for MCP context manager."""

import pytest
from datetime import datetime
from uuid import uuid4

from src.session.models import Session, SessionType, SessionStatus, Turn
from src.mcp.context_manager import ContextManager


class TestContextManager:
    """Test ContextManager functionality."""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager instance."""
        return ContextManager(max_turns=5, max_chars_per_turn=1000)
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample session with turns."""
        now = datetime.utcnow()
        session = Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            created_at=now,
            last_activity_at=now,
            base_branch="main"
        )
        
        # Add some turns
        for i in range(3):
            turn = Turn(
                id=i + 1,
                prompt=f"Question {i + 1}",
                response=f"Answer {i + 1} with detailed information",
                response_summary=f"Summary {i + 1}",
                files_analyzed=[f"file{i}.py"] if i > 0 else [],
                files_changed=[f"file{i}.py"] if i > 1 else [],
                timestamp=now
            )
            session.turns.append(turn)
        
        if session.turns:
            session.files_changed = ["file2.py"]
        
        return session
    
    def test_build_context_with_history(self, context_manager, sample_session):
        """Test building context with conversation history."""
        context = context_manager.build_context(
            session=sample_session,
            current_prompt="New question"
        )
        
        assert "Session Type: query" in context
        assert "Repository: test-repo" in context
        assert "Base Branch: main" in context
        assert "Previous Conversation" in context
        assert "Question 1" in context
        assert "Summary 1" in context
        assert "Current Request" in context
        assert "New question" in context
    
    def test_build_context_no_history(self, context_manager):
        """Test building context for new session without history."""
        now = datetime.utcnow()
        session = Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            created_at=now,
            last_activity_at=now
        )
        
        context = context_manager.build_context(
            session=session,
            current_prompt="First question"
        )
        
        assert "Session Type: query" in context
        assert "Repository: test-repo" in context
        assert "Current Request" in context
        assert "First question" in context
        assert "Previous Conversation" not in context
    
    def test_build_context_with_files(self, context_manager, sample_session):
        """Test building context includes file information."""
        context = context_manager.build_context(
            session=sample_session,
            current_prompt="New question",
            include_files=True
        )
        
        assert "Files analyzed:" in context or "Files changed:" in context
        assert "Files Changed in Session" in context
    
    def test_build_context_without_files(self, context_manager, sample_session):
        """Test building context without file information."""
        context = context_manager.build_context(
            session=sample_session,
            current_prompt="New question",
            include_files=False
        )
        
        assert "Files analyzed:" not in context
        assert "Files changed:" not in context
        assert "Files Changed in Session" not in context
    
    def test_build_context_max_turns_limit(self, context_manager):
        """Test that context respects max turns limit."""
        now = datetime.utcnow()
        session = Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            created_at=now,
            last_activity_at=now
        )
        
        # Add more turns than max_turns
        for i in range(10):
            turn = Turn(
                id=i + 1,
                prompt=f"Question {i + 1}",
                response=f"Answer {i + 1}",
                response_summary=f"Summary {i + 1}",
                timestamp=now
            )
            session.turns.append(turn)
        
        context = context_manager.build_context(
            session=session,
            current_prompt="New question"
        )
        
        # Should only include last 5 turns
        assert "Turn 6:" in context
        assert "Turn 10:" in context
        assert "Turn 1:" not in context
        assert "Turn 5:" not in context
    
    def test_build_simple_context(self, context_manager, sample_session):
        """Test building simple context from last turn."""
        context = context_manager.build_simple_context(
            session=sample_session,
            current_prompt="New question"
        )
        
        assert "Previous: Summary 3" in context
        assert "Current: New question" in context
        assert "Question 1" not in context  # Earlier turns not included
    
    def test_build_simple_context_no_history(self, context_manager):
        """Test building simple context for new session."""
        now = datetime.utcnow()
        session = Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            created_at=now,
            last_activity_at=now
        )
        
        context = context_manager.build_simple_context(
            session=session,
            current_prompt="First question"
        )
        
        # Should just return the prompt
        assert context == "First question"
    
    def test_truncate_long_text(self, context_manager):
        """Test that long text is truncated."""
        long_text = "x" * 2000
        truncated = context_manager._truncate(long_text, 1000)
        
        assert len(truncated) == 1000
        assert truncated.endswith("...")
    
    def test_truncate_short_text(self, context_manager):
        """Test that short text is not truncated."""
        short_text = "Short text"
        result = context_manager._truncate(short_text, 1000)
        
        assert result == short_text
    
    def test_extract_files_from_response(self, context_manager):
        """Test extracting file paths from response text."""
        response = """
        I modified the following files:
        - src/app.py
        - tests/test_app.py
        - config/settings.yaml
        And also looked at ./docs/README.md
        """
        
        files = context_manager.extract_files_from_response(response)
        
        assert "src/app.py" in files
        assert "tests/test_app.py" in files
        assert "config/settings.yaml" in files
        assert "./docs/README.md" in files
    
    def test_extract_files_no_duplicates(self, context_manager):
        """Test that duplicate files are removed."""
        response = """
        Modified src/app.py and then updated src/app.py again.
        Also changed src/app.py in multiple places.
        """
        
        files = context_manager.extract_files_from_response(response)
        
        # Should only have one instance of src/app.py
        assert files.count("src/app.py") == 1
    
    def test_extract_files_filters_false_positives(self, context_manager):
        """Test that common false positives are filtered."""
        response = """
        Visit example.com or github.io for more info.
        The file is at src/main.py
        """
        
        files = context_manager.extract_files_from_response(response)
        
        # Should include the actual file
        assert "src/main.py" in files
        # Should not include URLs
        assert "example.com" not in files
        assert "github.io" not in files
    
    def test_get_recent_turns_all_fits(self, context_manager):
        """Test getting recent turns when all fit."""
        turns = [
            Turn(id=i, prompt=f"Q{i}", response=f"A{i}", 
                 response_summary=f"S{i}", timestamp=datetime.utcnow())
            for i in range(3)
        ]
        
        recent = context_manager._get_recent_turns(turns)
        assert len(recent) == 3
    
    def test_get_recent_turns_limit(self, context_manager):
        """Test getting recent turns when limit is exceeded."""
        turns = [
            Turn(id=i, prompt=f"Q{i}", response=f"A{i}", 
                 response_summary=f"S{i}", timestamp=datetime.utcnow())
            for i in range(10)
        ]
        
        recent = context_manager._get_recent_turns(turns)
        assert len(recent) == 5  # max_turns is 5
        assert recent[0].id == 5  # Should be the last 5 turns
        assert recent[-1].id == 9
    
    def test_context_manager_custom_limits(self):
        """Test creating context manager with custom limits."""
        cm = ContextManager(max_turns=3, max_chars_per_turn=500)
        
        assert cm.max_turns == 3
        assert cm.max_chars_per_turn == 500
