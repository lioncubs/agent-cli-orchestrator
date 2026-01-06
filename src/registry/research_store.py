"""Storage and retrieval of research artifacts."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from src.session.models import ResearchArtifact


class ResearchStore:
    """
    Persistent store for research artifacts.
    
    Provides CRUD operations and filtering capabilities for research results.
    
    Note: Currently uses in-memory storage which will lose data on restart.
    For production use, consider implementing persistent storage (e.g., database).
    """
    
    def __init__(self):
        """Initialize the research store."""
        self._artifacts: Dict[UUID, ResearchArtifact] = {}
    
    def create(self, artifact: ResearchArtifact) -> ResearchArtifact:
        """
        Create a new research artifact.
        
        Args:
            artifact: Research artifact to store
            
        Returns:
            Created artifact
            
        Raises:
            ValueError: If artifact with same ID already exists
        """
        if artifact.research_id in self._artifacts:
            raise ValueError(f"Research artifact {artifact.research_id} already exists")
        
        self._artifacts[artifact.research_id] = artifact
        return artifact
    
    def get(self, research_id: UUID) -> Optional[ResearchArtifact]:
        """
        Get a research artifact by ID.
        
        Args:
            research_id: Research artifact UUID
            
        Returns:
            Research artifact if found, None otherwise
        """
        return self._artifacts.get(research_id)
    
    def update(self, artifact: ResearchArtifact) -> ResearchArtifact:
        """
        Update an existing research artifact.
        
        Args:
            artifact: Research artifact with updated data
            
        Returns:
            Updated artifact
            
        Raises:
            ValueError: If artifact not found
        """
        if artifact.research_id not in self._artifacts:
            raise ValueError(f"Research artifact {artifact.research_id} not found")
        
        self._artifacts[artifact.research_id] = artifact
        return artifact
    
    def delete(self, research_id: UUID) -> bool:
        """
        Delete a research artifact.
        
        Args:
            research_id: Research artifact UUID
            
        Returns:
            True if deleted, False if not found
        """
        if research_id in self._artifacts:
            del self._artifacts[research_id]
            return True
        return False
    
    def list(
        self,
        repo_name: Optional[str] = None,
        user_id: Optional[str] = None,
        base_branch: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ResearchArtifact]:
        """
        List research artifacts with optional filters.
        
        Args:
            repo_name: Filter by repository name
            user_id: Filter by user ID
            base_branch: Filter by base branch
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching research artifacts
        """
        artifacts = list(self._artifacts.values())
        
        # Apply filters
        if repo_name:
            artifacts = [a for a in artifacts if a.repo_name == repo_name]
        if user_id:
            artifacts = [a for a in artifacts if a.user_id == user_id]
        if base_branch:
            artifacts = [a for a in artifacts if a.base_branch == base_branch]
        
        # Sort by created_at descending (most recent first)
        artifacts.sort(key=lambda a: a.created_at, reverse=True)
        
        # Apply pagination
        if offset:
            artifacts = artifacts[offset:]
        if limit:
            artifacts = artifacts[:limit]
        
        return artifacts
    
    def count(
        self,
        repo_name: Optional[str] = None,
        user_id: Optional[str] = None,
        base_branch: Optional[str] = None
    ) -> int:
        """
        Count research artifacts matching filters.
        
        Args:
            repo_name: Filter by repository name
            user_id: Filter by user ID
            base_branch: Filter by base branch
            
        Returns:
            Number of matching artifacts
        """
        artifacts = list(self._artifacts.values())
        
        if repo_name:
            artifacts = [a for a in artifacts if a.repo_name == repo_name]
        if user_id:
            artifacts = [a for a in artifacts if a.user_id == user_id]
        if base_branch:
            artifacts = [a for a in artifacts if a.base_branch == base_branch]
        
        return len(artifacts)
    
    def clear(self) -> None:
        """Clear all research artifacts from the store."""
        self._artifacts.clear()
    
    def get_by_repo(self, repo_name: str) -> List[ResearchArtifact]:
        """
        Get all research artifacts for a specific repository.
        
        Args:
            repo_name: Repository name
            
        Returns:
            List of research artifacts for the repository
        """
        return self.list(repo_name=repo_name)
    
    def get_by_user(self, user_id: str) -> List[ResearchArtifact]:
        """
        Get all research artifacts for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of research artifacts for the user
        """
        return self.list(user_id=user_id)
