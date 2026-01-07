"""MCP resources for the orchestrator."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from src.session.store import SessionStore
from src.registry.research_store import ResearchStore


class MCPResources:
    """
    Provides MCP resources for clients.
    
    Resources are read-only data that clients can access.
    """
    
    def __init__(
        self,
        session_store: SessionStore,
        research_store: ResearchStore
    ):
        """
        Initialize MCP resources.
        
        Args:
            session_store: Session storage
            research_store: Research artifact storage
        """
        self.session_store = session_store
        self.research_store = research_store
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        List all available resources.
        
        Returns:
            List of resource descriptors
        """
        resources = [
            {
                "type": "sessions",
                "name": "Active Sessions",
                "description": "List of active orchestrator sessions",
                "uri": "orchestrator://sessions"
            },
            {
                "type": "research",
                "name": "Research Artifacts",
                "description": "Completed research findings and recommendations",
                "uri": "orchestrator://research"
            }
        ]
        return resources
    
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """
        Get a specific resource by URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource data
            
        Raises:
            ValueError: If URI is invalid
        """
        if uri == "orchestrator://sessions":
            return await self._get_sessions_resource()
        elif uri == "orchestrator://research":
            return await self._get_research_resource()
        elif uri.startswith("orchestrator://sessions/"):
            session_id = uri.replace("orchestrator://sessions/", "")
            return await self._get_session_resource(UUID(session_id))
        elif uri.startswith("orchestrator://research/"):
            research_id = uri.replace("orchestrator://research/", "")
            return await self._get_research_artifact_resource(UUID(research_id))
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
    
    async def _get_sessions_resource(self) -> Dict[str, Any]:
        """Get all active sessions."""
        sessions = await self.session_store.list_sessions()
        
        return {
            "uri": "orchestrator://sessions",
            "type": "sessions",
            "data": {
                "total": len(sessions),
                "sessions": [
                    {
                        "id": str(s.id),
                        "type": s.type.value,
                        "status": s.status.value,
                        "repo_name": s.repo_name,
                        "created_at": s.created_at.isoformat(),
                        "uri": f"orchestrator://sessions/{s.id}"
                    }
                    for s in sessions
                ]
            }
        }
    
    async def _get_session_resource(self, session_id: UUID) -> Dict[str, Any]:
        """Get a specific session."""
        session = await self.session_store.get_session(session_id)
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        return {
            "uri": f"orchestrator://sessions/{session_id}",
            "type": "session",
            "data": {
                "id": str(session.id),
                "type": session.type.value,
                "status": session.status.value,
                "repo_name": session.repo_name,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "last_activity_at": session.last_activity_at.isoformat(),
                "base_branch": session.base_branch,
                "session_branch": session.session_branch,
                "worktree_path": session.worktree_path,
                "turns_count": len(session.turns),
                "files_changed": session.files_changed,
                "pr_url": session.pr_url
            }
        }
    
    async def _get_research_resource(self) -> Dict[str, Any]:
        """Get all research artifacts."""
        artifacts = await self.research_store.list_artifacts()
        
        return {
            "uri": "orchestrator://research",
            "type": "research",
            "data": {
                "total": len(artifacts),
                "artifacts": [
                    {
                        "id": str(a.research_id),
                        "repo_name": a.repo_name,
                        "summary": a.summary[:200] + "..." if len(a.summary) > 200 else a.summary,
                        "created_at": a.created_at.isoformat(),
                        "uri": f"orchestrator://research/{a.research_id}"
                    }
                    for a in artifacts
                ]
            }
        }
    
    async def _get_research_artifact_resource(self, research_id: UUID) -> Dict[str, Any]:
        """Get a specific research artifact."""
        artifact = await self.research_store.get_artifact(research_id)
        
        if not artifact:
            raise ValueError(f"Research artifact not found: {research_id}")
        
        return {
            "uri": f"orchestrator://research/{research_id}",
            "type": "research_artifact",
            "data": {
                "id": str(artifact.research_id),
                "repo_name": artifact.repo_name,
                "base_branch": artifact.base_branch,
                "base_commit": artifact.base_commit,
                "created_at": artifact.created_at.isoformat(),
                "user_id": artifact.user_id,
                "summary": artifact.summary,
                "findings": [
                    {
                        "file": f.file,
                        "lines": f.lines,
                        "note": f.note,
                        "code_snippet": f.code_snippet
                    }
                    for f in artifact.findings
                ],
                "recommendations": artifact.recommendations,
                "suggested_delegation_prompt": artifact.suggested_delegation_prompt,
                "relevant_files": artifact.relevant_files
            }
        }
