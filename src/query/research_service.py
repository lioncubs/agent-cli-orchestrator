"""Research service for deeper repository analysis."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from src.session.models import (
    ResearchArtifact,
    ResearchFinding,
    TurnSummary,
    Session,
    SessionType
)
from src.registry.research_store import ResearchStore
from src.query.service import QueryService
from src.permissions.tool_policy import ToolPolicy, Operation, OperationTier


class ResearchService:
    """
    Execute deeper research workflows with temporary worktree support.
    
    Provides capabilities for analyzing repositories and generating research artifacts.
    """
    
    def __init__(
        self,
        research_store: ResearchStore,
        query_service: Optional[QueryService] = None,
        tool_policy: Optional[ToolPolicy] = None
    ):
        """
        Initialize research service.
        
        Args:
            research_store: Store for research artifacts
            query_service: Query service for read operations
            tool_policy: Tool policy for operation validation
        """
        self.research_store = research_store
        self.query_service = query_service or QueryService()
        self.tool_policy = tool_policy or ToolPolicy(default_tier=OperationTier.STANDARD)
    
    def create_research_worktree(
        self,
        repo_path: str,
        base_branch: str,
        worktree_base_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a temporary worktree for research.
        
        Args:
            repo_path: Path to main repository
            base_branch: Branch to base research on
            worktree_base_path: Base path for worktrees
            session_id: Optional session ID for policy check
            
        Returns:
            Dict containing worktree information
            
        Raises:
            PermissionError: If operation not allowed
        """
        self.tool_policy.check_operation(Operation.CREATE_WORKTREE, session_id)
        
        try:
            # Generate unique worktree path
            worktree_name = f"research-{uuid4().hex[:8]}"
            worktree_path = Path(worktree_base_path) / worktree_name
            
            # Ensure base path exists
            worktree_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create worktree
            result = subprocess.run(
                ['git', 'worktree', 'add', str(worktree_path), base_branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get commit SHA
            commit_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                check=True
            )
            commit_sha = commit_result.stdout.strip()
            
            return {
                "status": "success",
                "worktree_path": str(worktree_path),
                "base_branch": base_branch,
                "commit_sha": commit_sha,
                "message": f"Worktree created at {worktree_path}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Failed to create worktree: {e.stderr}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error creating worktree: {str(e)}"
            }
    
    def cleanup_research_worktree(
        self,
        repo_path: str,
        worktree_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clean up a research worktree.
        
        Args:
            repo_path: Path to main repository
            worktree_path: Path to worktree to remove
            session_id: Optional session ID for policy check
            
        Returns:
            Dict containing cleanup result
            
        Raises:
            PermissionError: If operation not allowed
        """
        self.tool_policy.check_operation(Operation.DELETE_WORKTREE, session_id)
        
        try:
            # Remove worktree
            result = subprocess.run(
                ['git', 'worktree', 'remove', worktree_path, '--force'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "status": "success",
                "message": f"Worktree removed: {worktree_path}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Failed to remove worktree: {e.stderr}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error removing worktree: {str(e)}"
            }
    
    def analyze_files(
        self,
        repo_path: str,
        file_patterns: List[str],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze specific files in the repository.
        
        Args:
            repo_path: Path to repository
            file_patterns: List of file patterns to analyze
            session_id: Optional session ID for policy check
            
        Returns:
            Dict containing analysis results
        """
        try:
            analyzed_files = []
            
            for pattern in file_patterns:
                files_result = self.query_service.list_files(
                    repo_path,
                    pattern=pattern,
                    session_id=session_id
                )
                
                if files_result.get("status") == "success":
                    for file_info in files_result.get("files", []):
                        file_path = file_info["path"]
                        content_result = self.query_service.read_file(
                            repo_path,
                            file_path,
                            session_id=session_id
                        )
                        
                        if content_result.get("status") == "success":
                            analyzed_files.append({
                                "path": file_path,
                                "size": file_info["size"],
                                "lines": content_result.get("lines", 0)
                            })
            
            return {
                "status": "success",
                "analyzed_files": analyzed_files,
                "total_files": len(analyzed_files)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing files: {str(e)}"
            }
    
    def generate_research_artifact(
        self,
        session: Session,
        summary: str,
        findings: List[Dict[str, Any]],
        recommendations: List[str],
        suggested_delegation_prompt: str = "",
        relevant_files: Optional[List[str]] = None
    ) -> ResearchArtifact:
        """
        Generate a research artifact from a research session.
        
        Args:
            session: Research session
            summary: Summary of research
            findings: List of findings (will be converted to ResearchFinding objects)
            recommendations: List of recommendations
            suggested_delegation_prompt: Suggested prompt for delegation
            relevant_files: List of relevant files
            
        Returns:
            Created research artifact
            
        Raises:
            ValueError: If session is not a research session
        """
        if session.type != SessionType.RESEARCH:
            raise ValueError("Session must be of type RESEARCH")
        
        # Convert findings to ResearchFinding objects
        research_findings = []
        for finding in findings:
            research_findings.append(ResearchFinding(
                file=finding.get("file", ""),
                lines=finding.get("lines"),
                note=finding.get("note", ""),
                code_snippet=finding.get("code_snippet")
            ))
        
        # Convert turns to TurnSummary objects
        conversation = []
        for turn in session.turns:
            conversation.append(TurnSummary(
                id=turn.id,
                prompt=turn.prompt,
                response_summary=turn.response_summary,
                files_analyzed=turn.files_analyzed,
                files_changed=turn.files_changed,
                timestamp=turn.timestamp
            ))
        
        # Create research artifact
        artifact = ResearchArtifact(
            research_id=uuid4(),
            repo_name=session.repo_name,
            base_branch=session.base_branch or "main",
            base_commit=session.base_commit or "",
            created_at=datetime.utcnow(),
            user_id=session.user_id,
            summary=summary,
            findings=research_findings,
            recommendations=recommendations,
            conversation=conversation,
            suggested_delegation_prompt=suggested_delegation_prompt,
            relevant_files=relevant_files or []
        )
        
        # Store the artifact
        return self.research_store.create(artifact)
    
    def finalize_research_session(
        self,
        session: Session,
        summary: str,
        findings: List[Dict[str, Any]],
        recommendations: List[str],
        suggested_delegation_prompt: str = "",
        cleanup_worktree: bool = True,
        repo_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Finalize a research session by creating artifact and cleaning up.
        
        Args:
            session: Research session to finalize
            summary: Research summary
            findings: List of findings
            recommendations: List of recommendations
            suggested_delegation_prompt: Suggested delegation prompt
            cleanup_worktree: Whether to clean up the worktree
            repo_path: Repository path (required if cleanup_worktree is True)
            
        Returns:
            Dict containing finalization result with artifact ID
        """
        try:
            # Generate artifact
            artifact = self.generate_research_artifact(
                session=session,
                summary=summary,
                findings=findings,
                recommendations=recommendations,
                suggested_delegation_prompt=suggested_delegation_prompt,
                relevant_files=session.files_changed
            )
            
            result = {
                "status": "success",
                "research_id": str(artifact.research_id),
                "artifact": artifact.model_dump()
            }
            
            # Clean up worktree if requested
            if cleanup_worktree and session.worktree_path and repo_path:
                cleanup_result = self.cleanup_research_worktree(
                    repo_path=repo_path,
                    worktree_path=session.worktree_path
                )
                result["cleanup"] = cleanup_result
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error finalizing research: {str(e)}"
            }
    
    def get_research_artifact(self, research_id: UUID) -> Optional[ResearchArtifact]:
        """
        Get a research artifact by ID.
        
        Args:
            research_id: Research artifact UUID
            
        Returns:
            Research artifact if found
        """
        return self.research_store.get(research_id)
    
    def list_research_artifacts(
        self,
        repo_name: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ResearchArtifact]:
        """
        List research artifacts with filters.
        
        Args:
            repo_name: Filter by repository
            user_id: Filter by user
            limit: Maximum results
            offset: Results offset
            
        Returns:
            List of research artifacts
        """
        return self.research_store.list(
            repo_name=repo_name,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
