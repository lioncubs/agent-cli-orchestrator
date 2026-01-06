"""Tests for research service."""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
import subprocess

from src.query.research_service import ResearchService
from src.query.service import QueryService
from src.registry.research_store import ResearchStore
from src.permissions.tool_policy import ToolPolicy, OperationTier
from src.session.models import (
    Session,
    SessionType,
    SessionStatus,
    Turn,
    ResearchArtifact
)


@pytest.fixture
def research_store():
    """Create a fresh research store."""
    return ResearchStore()


@pytest.fixture
def query_service():
    """Create a query service."""
    return QueryService()


@pytest.fixture
def research_service(research_store, query_service):
    """Create a research service."""
    return ResearchService(research_store, query_service)


@pytest.fixture
def sample_session():
    """Create a sample research session."""
    now = datetime.utcnow()
    session = Session(
        id=uuid4(),
        type=SessionType.RESEARCH,
        status=SessionStatus.ACTIVE,
        repo_name="test-repo",
        user_id="user-123",
        created_at=now,
        last_activity_at=now,
        base_branch="main",
        base_commit="abc123",
        worktree_path="/tmp/worktree-test",
        turns=[
            Turn(
                id=1,
                prompt="Research the codebase",
                response="Found several issues",
                response_summary="Analyzed code",
                files_analyzed=["file1.py", "file2.py"],
                files_changed=[],
                timestamp=now
            )
        ]
    )
    return session


class TestResearchService:
    """Test ResearchService class."""
    
    def test_initialization(self, research_store):
        """Test research service initialization."""
        service = ResearchService(research_store)
        assert service.research_store == research_store
        assert service.query_service is not None
        assert service.tool_policy is not None
    
    def test_initialization_with_custom_components(self):
        """Test initialization with custom components."""
        store = ResearchStore()
        query = QueryService()
        policy = ToolPolicy(default_tier=OperationTier.ADMIN)
        
        service = ResearchService(store, query, policy)
        assert service.research_store == store
        assert service.query_service == query
        assert service.tool_policy == policy
    
    @patch('subprocess.run')
    def test_create_research_worktree_success(self, mock_run, research_service, tmp_path):
        """Test creating a research worktree."""
        # Mock git worktree add
        def side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0
            
            if 'worktree' in cmd:
                result.stdout = "Preparing worktree"
            elif 'rev-parse' in cmd:
                result.stdout = "abc123def456\n"
            
            return result
        
        mock_run.side_effect = side_effect
        
        result = research_service.create_research_worktree(
            repo_path="/fake/repo",
            base_branch="main",
            worktree_base_path=str(tmp_path)
        )
        
        assert result["status"] == "success"
        assert "worktree_path" in result
        assert result["base_branch"] == "main"
        assert result["commit_sha"] == "abc123def456"
    
    @patch('subprocess.run')
    def test_create_research_worktree_error(self, mock_run, research_service, tmp_path):
        """Test worktree creation error handling."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['git'], stderr="fatal: invalid reference"
        )
        
        result = research_service.create_research_worktree(
            repo_path="/fake/repo",
            base_branch="invalid-branch",
            worktree_base_path=str(tmp_path)
        )
        
        assert result["status"] == "error"
        assert "failed" in result["message"].lower()
    
    @patch('subprocess.run')
    def test_cleanup_research_worktree_success(self, mock_run, research_service):
        """Test cleaning up a research worktree."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Removing worktree"
        mock_run.return_value = mock_result
        
        result = research_service.cleanup_research_worktree(
            repo_path="/fake/repo",
            worktree_path="/fake/worktree"
        )
        
        assert result["status"] == "success"
        assert "removed" in result["message"].lower()
    
    @patch('subprocess.run')
    def test_cleanup_research_worktree_error(self, mock_run, research_service):
        """Test worktree cleanup error handling."""
        mock_run.side_effect = subprocess.CalledProcessError(
            128, ['git'], stderr="fatal: not a git repository"
        )
        
        result = research_service.cleanup_research_worktree(
            repo_path="/fake/repo",
            worktree_path="/fake/worktree"
        )
        
        assert result["status"] == "error"
    
    def test_generate_research_artifact(self, research_service, sample_session):
        """Test generating a research artifact from a session."""
        findings = [
            {
                "file": "test.py",
                "lines": "10-20",
                "note": "Found issue here",
                "code_snippet": "def test(): pass"
            },
            {
                "file": "main.py",
                "note": "Another issue",
            }
        ]
        
        recommendations = [
            "Fix the test function",
            "Add error handling"
        ]
        
        artifact = research_service.generate_research_artifact(
            session=sample_session,
            summary="Research completed successfully",
            findings=findings,
            recommendations=recommendations,
            suggested_delegation_prompt="Fix the identified issues",
            relevant_files=["test.py", "main.py"]
        )
        
        assert isinstance(artifact, ResearchArtifact)
        assert artifact.repo_name == "test-repo"
        assert artifact.base_branch == "main"
        assert artifact.base_commit == "abc123"
        assert artifact.user_id == "user-123"
        assert artifact.summary == "Research completed successfully"
        assert len(artifact.findings) == 2
        assert len(artifact.recommendations) == 2
        assert len(artifact.conversation) == 1
        assert artifact.suggested_delegation_prompt == "Fix the identified issues"
        assert len(artifact.relevant_files) == 2
    
    def test_generate_artifact_wrong_session_type(self, research_service):
        """Test that generating artifact fails for non-research sessions."""
        now = datetime.utcnow()
        delegation_session = Session(
            id=uuid4(),
            type=SessionType.DELEGATION,  # Not RESEARCH
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user-123",
            created_at=now,
            last_activity_at=now
        )
        
        with pytest.raises(ValueError) as exc_info:
            research_service.generate_research_artifact(
                session=delegation_session,
                summary="Test",
                findings=[],
                recommendations=[]
            )
        
        assert "must be of type RESEARCH" in str(exc_info.value)
    
    def test_finalize_research_session(self, research_service, sample_session):
        """Test finalizing a research session."""
        findings = [
            {
                "file": "test.py",
                "note": "Issue found"
            }
        ]
        
        result = research_service.finalize_research_session(
            session=sample_session,
            summary="Research complete",
            findings=findings,
            recommendations=["Fix issue"],
            cleanup_worktree=False  # Don't cleanup for test
        )
        
        assert result["status"] == "success"
        assert "research_id" in result
        assert "artifact" in result
    
    @patch.object(ResearchService, 'cleanup_research_worktree')
    def test_finalize_with_cleanup(self, mock_cleanup, research_service, sample_session):
        """Test finalization with worktree cleanup."""
        mock_cleanup.return_value = {"status": "success", "message": "Cleaned up"}
        
        result = research_service.finalize_research_session(
            session=sample_session,
            summary="Research complete",
            findings=[],
            recommendations=[],
            cleanup_worktree=True,
            repo_path="/fake/repo"
        )
        
        assert result["status"] == "success"
        assert "cleanup" in result
        mock_cleanup.assert_called_once()
    
    def test_get_research_artifact(self, research_service, sample_session):
        """Test retrieving a research artifact."""
        # Create an artifact
        artifact = research_service.generate_research_artifact(
            session=sample_session,
            summary="Test",
            findings=[],
            recommendations=[]
        )
        
        # Retrieve it
        retrieved = research_service.get_research_artifact(artifact.research_id)
        
        assert retrieved is not None
        assert retrieved.research_id == artifact.research_id
        assert retrieved.summary == "Test"
    
    def test_get_nonexistent_artifact(self, research_service):
        """Test retrieving nonexistent artifact returns None."""
        result = research_service.get_research_artifact(uuid4())
        assert result is None
    
    def test_list_research_artifacts(self, research_service, sample_session):
        """Test listing research artifacts."""
        # Create multiple artifacts
        for i in range(3):
            research_service.generate_research_artifact(
                session=sample_session,
                summary=f"Summary {i}",
                findings=[],
                recommendations=[]
            )
        
        artifacts = research_service.list_research_artifacts()
        assert len(artifacts) == 3
    
    def test_list_artifacts_with_filters(self, research_service):
        """Test listing artifacts with filters."""
        # Create sessions for different repos
        for repo in ["repo-a", "repo-b"]:
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=SessionType.RESEARCH,
                status=SessionStatus.ACTIVE,
                repo_name=repo,
                user_id="user-123",
                created_at=now,
                last_activity_at=now,
                base_branch="main",
                base_commit="abc123"
            )
            
            research_service.generate_research_artifact(
                session=session,
                summary="Test",
                findings=[],
                recommendations=[]
            )
        
        # Filter by repo
        repo_a_artifacts = research_service.list_research_artifacts(repo_name="repo-a")
        assert len(repo_a_artifacts) == 1
        assert repo_a_artifacts[0].repo_name == "repo-a"
    
    def test_list_artifacts_with_pagination(self, research_service, sample_session):
        """Test listing artifacts with pagination."""
        # Create 10 artifacts
        for i in range(10):
            research_service.generate_research_artifact(
                session=sample_session,
                summary=f"Summary {i}",
                findings=[],
                recommendations=[]
            )
        
        # Get first page
        page_1 = research_service.list_research_artifacts(limit=5, offset=0)
        assert len(page_1) == 5
        
        # Get second page
        page_2 = research_service.list_research_artifacts(limit=5, offset=5)
        assert len(page_2) == 5
