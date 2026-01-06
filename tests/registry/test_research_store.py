"""Tests for research artifact store."""

import pytest
from datetime import datetime
from uuid import uuid4

from src.session.models import (
    ResearchArtifact,
    ResearchFinding,
    TurnSummary
)
from src.registry.research_store import ResearchStore


@pytest.fixture
def research_store():
    """Create a fresh research store for testing."""
    return ResearchStore()


@pytest.fixture
def sample_artifact():
    """Create a sample research artifact."""
    now = datetime.utcnow()
    return ResearchArtifact(
        research_id=uuid4(),
        repo_name="test-repo",
        base_branch="main",
        base_commit="abc123",
        created_at=now,
        user_id="user-123",
        summary="Test research summary",
        findings=[
            ResearchFinding(
                file="test.py",
                lines="10-20",
                note="Test finding",
                code_snippet="def test(): pass"
            )
        ],
        recommendations=["Fix issue 1", "Improve test 2"],
        conversation=[
            TurnSummary(
                id=1,
                prompt="Test prompt",
                response_summary="Test summary",
                files_analyzed=["test.py"],
                files_changed=[],
                timestamp=now
            )
        ],
        suggested_delegation_prompt="Fix the test issues",
        relevant_files=["test.py", "test2.py"]
    )


class TestResearchStore:
    """Test ResearchStore class."""
    
    def test_create_artifact(self, research_store, sample_artifact):
        """Test creating a research artifact."""
        created = research_store.create(sample_artifact)
        
        assert created.research_id == sample_artifact.research_id
        assert created.repo_name == sample_artifact.repo_name
        assert created.summary == sample_artifact.summary
        assert len(created.findings) == 1
        assert len(created.recommendations) == 2
    
    def test_create_duplicate_artifact(self, research_store, sample_artifact):
        """Test creating duplicate artifact raises error."""
        research_store.create(sample_artifact)
        
        with pytest.raises(ValueError) as exc_info:
            research_store.create(sample_artifact)
        
        assert "already exists" in str(exc_info.value)
    
    def test_get_artifact(self, research_store, sample_artifact):
        """Test getting an artifact by ID."""
        research_store.create(sample_artifact)
        
        retrieved = research_store.get(sample_artifact.research_id)
        
        assert retrieved is not None
        assert retrieved.research_id == sample_artifact.research_id
        assert retrieved.summary == sample_artifact.summary
    
    def test_get_nonexistent_artifact(self, research_store):
        """Test getting a nonexistent artifact returns None."""
        result = research_store.get(uuid4())
        assert result is None
    
    def test_update_artifact(self, research_store, sample_artifact):
        """Test updating an artifact."""
        research_store.create(sample_artifact)
        
        # Modify artifact
        sample_artifact.summary = "Updated summary"
        sample_artifact.recommendations.append("New recommendation")
        
        updated = research_store.update(sample_artifact)
        
        assert updated.summary == "Updated summary"
        assert len(updated.recommendations) == 3
        
        # Verify persistence
        retrieved = research_store.get(sample_artifact.research_id)
        assert retrieved.summary == "Updated summary"
    
    def test_update_nonexistent_artifact(self, research_store, sample_artifact):
        """Test updating nonexistent artifact raises error."""
        with pytest.raises(ValueError) as exc_info:
            research_store.update(sample_artifact)
        
        assert "not found" in str(exc_info.value)
    
    def test_delete_artifact(self, research_store, sample_artifact):
        """Test deleting an artifact."""
        research_store.create(sample_artifact)
        
        success = research_store.delete(sample_artifact.research_id)
        assert success is True
        
        # Verify deletion
        retrieved = research_store.get(sample_artifact.research_id)
        assert retrieved is None
    
    def test_delete_nonexistent_artifact(self, research_store):
        """Test deleting nonexistent artifact returns False."""
        result = research_store.delete(uuid4())
        assert result is False
    
    def test_list_all_artifacts(self, research_store):
        """Test listing all artifacts."""
        # Create multiple artifacts
        artifacts = []
        for i in range(3):
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name=f"repo-{i}",
                base_branch="main",
                base_commit=f"commit-{i}",
                created_at=datetime.utcnow(),
                user_id=f"user-{i}",
                summary=f"Summary {i}",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            artifacts.append(artifact)
            research_store.create(artifact)
        
        all_artifacts = research_store.list()
        assert len(all_artifacts) == 3
    
    def test_list_artifacts_by_repo(self, research_store):
        """Test listing artifacts filtered by repository."""
        # Create artifacts for different repos
        for repo in ["repo-a", "repo-b", "repo-a"]:
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name=repo,
                base_branch="main",
                base_commit="abc123",
                created_at=datetime.utcnow(),
                user_id="user-1",
                summary="Summary",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            research_store.create(artifact)
        
        repo_a_artifacts = research_store.list(repo_name="repo-a")
        assert len(repo_a_artifacts) == 2
        assert all(a.repo_name == "repo-a" for a in repo_a_artifacts)
        
        repo_b_artifacts = research_store.list(repo_name="repo-b")
        assert len(repo_b_artifacts) == 1
        assert repo_b_artifacts[0].repo_name == "repo-b"
    
    def test_list_artifacts_by_user(self, research_store):
        """Test listing artifacts filtered by user."""
        # Create artifacts for different users
        for user in ["user-1", "user-2", "user-1"]:
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name="test-repo",
                base_branch="main",
                base_commit="abc123",
                created_at=datetime.utcnow(),
                user_id=user,
                summary="Summary",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            research_store.create(artifact)
        
        user_1_artifacts = research_store.list(user_id="user-1")
        assert len(user_1_artifacts) == 2
        assert all(a.user_id == "user-1" for a in user_1_artifacts)
    
    def test_list_artifacts_by_branch(self, research_store):
        """Test listing artifacts filtered by base branch."""
        # Create artifacts for different branches
        for branch in ["main", "develop", "main"]:
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name="test-repo",
                base_branch=branch,
                base_commit="abc123",
                created_at=datetime.utcnow(),
                user_id="user-1",
                summary="Summary",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            research_store.create(artifact)
        
        main_artifacts = research_store.list(base_branch="main")
        assert len(main_artifacts) == 2
        assert all(a.base_branch == "main" for a in main_artifacts)
    
    def test_list_artifacts_with_pagination(self, research_store):
        """Test listing artifacts with pagination."""
        # Create 10 artifacts
        for i in range(10):
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name="test-repo",
                base_branch="main",
                base_commit=f"commit-{i}",
                created_at=datetime.utcnow(),
                user_id="user-1",
                summary=f"Summary {i}",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            research_store.create(artifact)
        
        # Get first page
        page_1 = research_store.list(limit=5, offset=0)
        assert len(page_1) == 5
        
        # Get second page
        page_2 = research_store.list(limit=5, offset=5)
        assert len(page_2) == 5
        
        # Ensure no overlap
        page_1_ids = {a.research_id for a in page_1}
        page_2_ids = {a.research_id for a in page_2}
        assert len(page_1_ids.intersection(page_2_ids)) == 0
    
    def test_list_artifacts_sorted_by_date(self, research_store):
        """Test that artifacts are sorted by created_at descending."""
        import time
        
        # Create artifacts with slight time differences
        artifacts = []
        for i in range(3):
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name="test-repo",
                base_branch="main",
                base_commit=f"commit-{i}",
                created_at=datetime.utcnow(),
                user_id="user-1",
                summary=f"Summary {i}",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            artifacts.append(artifact)
            research_store.create(artifact)
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        listed = research_store.list()
        
        # Most recent should be first
        for i in range(len(listed) - 1):
            assert listed[i].created_at >= listed[i + 1].created_at
    
    def test_count_all_artifacts(self, research_store):
        """Test counting all artifacts."""
        # Create multiple artifacts
        for i in range(5):
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name="test-repo",
                base_branch="main",
                base_commit=f"commit-{i}",
                created_at=datetime.utcnow(),
                user_id="user-1",
                summary=f"Summary {i}",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            research_store.create(artifact)
        
        count = research_store.count()
        assert count == 5
    
    def test_count_artifacts_with_filters(self, research_store):
        """Test counting artifacts with filters."""
        # Create artifacts
        for repo in ["repo-a", "repo-b", "repo-a"]:
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name=repo,
                base_branch="main",
                base_commit="abc123",
                created_at=datetime.utcnow(),
                user_id="user-1",
                summary="Summary",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            research_store.create(artifact)
        
        count_repo_a = research_store.count(repo_name="repo-a")
        assert count_repo_a == 2
        
        count_repo_b = research_store.count(repo_name="repo-b")
        assert count_repo_b == 1
    
    def test_clear_store(self, research_store, sample_artifact):
        """Test clearing all artifacts from store."""
        research_store.create(sample_artifact)
        assert research_store.count() == 1
        
        research_store.clear()
        assert research_store.count() == 0
    
    def test_get_by_repo(self, research_store):
        """Test get_by_repo helper method."""
        # Create artifacts for different repos
        for repo in ["repo-a", "repo-b", "repo-a"]:
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name=repo,
                base_branch="main",
                base_commit="abc123",
                created_at=datetime.utcnow(),
                user_id="user-1",
                summary="Summary",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            research_store.create(artifact)
        
        repo_artifacts = research_store.get_by_repo("repo-a")
        assert len(repo_artifacts) == 2
        assert all(a.repo_name == "repo-a" for a in repo_artifacts)
    
    def test_get_by_user(self, research_store):
        """Test get_by_user helper method."""
        # Create artifacts for different users
        for user in ["user-1", "user-2", "user-1"]:
            artifact = ResearchArtifact(
                research_id=uuid4(),
                repo_name="test-repo",
                base_branch="main",
                base_commit="abc123",
                created_at=datetime.utcnow(),
                user_id=user,
                summary="Summary",
                findings=[],
                recommendations=[],
                conversation=[],
                suggested_delegation_prompt="",
                relevant_files=[]
            )
            research_store.create(artifact)
        
        user_artifacts = research_store.get_by_user("user-1")
        assert len(user_artifacts) == 2
        assert all(a.user_id == "user-1" for a in user_artifacts)
