"""FastMCP server for Agent CLI Orchestrator."""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from src.mcp.tools.query import QueryTools
from src.mcp.tools.session import SessionTools
from src.mcp.tools.delegation import DelegationTools
from src.mcp.tools.repository import RepositoryTools
from src.mcp.resources import MCPResources
from src.mcp.models import (
    QueryInput,
    StartResearchInput,
    CompleteResearchInput,
    ContinueSessionInput,
    ListSessionsInput,
    GetSessionInput,
    CloseSessionInput,
    StartDelegationInput,
    CommitChangesInput,
    CreatePRInput,
    ListReposInput,
    GetRepoInput
)


class MCPServer:
    """MCP server for the orchestrator."""
    
    def __init__(
        self,
        query_tools: QueryTools,
        session_tools: SessionTools,
        delegation_tools: DelegationTools,
        repository_tools: RepositoryTools,
        resources: MCPResources
    ):
        """
        Initialize MCP server.
        
        Args:
            query_tools: Query and research tools
            session_tools: Session management tools
            delegation_tools: Delegation tools
            repository_tools: Repository tools
            resources: MCP resources
        """
        self.query_tools = query_tools
        self.session_tools = session_tools
        self.delegation_tools = delegation_tools
        self.repository_tools = repository_tools
        self.resources = resources
        
        # Initialize FastMCP server
        self.mcp = FastMCP(
            "Agent CLI Orchestrator",
            version="1.0.0"
        )
        
        # Register all tools
        self._register_tools()
        # Register resources
        self._register_resources()
    
    def _register_tools(self):
        """Register all MCP tools."""
        
        # Query tools
        @self.mcp.tool()
        async def query(repo_name: str, prompt: str, session_id: str = None) -> Dict[str, Any]:
            """
            Execute a read-only query on a repository.
            
            Args:
                repo_name: Repository name
                prompt: Query prompt
                session_id: Optional session ID to continue
                
            Returns:
                Query result with response
            """
            from uuid import UUID
            input_data = QueryInput(
                repo_name=repo_name,
                prompt=prompt,
                session_id=UUID(session_id) if session_id else None
            )
            return await self.query_tools.query(input_data)
        
        @self.mcp.tool()
        async def start_research(repo_name: str, prompt: str, base_branch: str = None) -> Dict[str, Any]:
            """
            Start a research session with temporary worktree.
            
            Args:
                repo_name: Repository name
                prompt: Research prompt
                base_branch: Optional base branch
                
            Returns:
                New research session details
            """
            input_data = StartResearchInput(
                repo_name=repo_name,
                prompt=prompt,
                base_branch=base_branch
            )
            return await self.query_tools.start_research(input_data)
        
        @self.mcp.tool()
        async def complete_research(session_id: str) -> Dict[str, Any]:
            """
            Complete a research session and generate artifact.
            
            Args:
                session_id: Research session ID
                
            Returns:
                Research artifact with findings and recommendations
            """
            from uuid import UUID
            input_data = CompleteResearchInput(session_id=UUID(session_id))
            return await self.query_tools.complete_research(input_data)
        
        # Session tools
        @self.mcp.tool()
        async def continue_session(session_id: str, prompt: str) -> Dict[str, Any]:
            """
            Continue an existing session with a follow-up prompt.
            
            Args:
                session_id: Session ID
                prompt: Follow-up prompt
                
            Returns:
                Turn result with response
            """
            from uuid import UUID
            input_data = ContinueSessionInput(
                session_id=UUID(session_id),
                prompt=prompt
            )
            return await self.session_tools.continue_session(input_data)
        
        @self.mcp.tool()
        async def list_sessions(
            type: str = None,
            status: str = None,
            repo_name: str = None,
            user_id: str = None,
            limit: int = 10
        ) -> Dict[str, Any]:
            """
            List sessions with optional filters.
            
            Args:
                type: Filter by session type (query, research, delegation)
                status: Filter by status (active, completed, etc.)
                repo_name: Filter by repository
                user_id: Filter by user
                limit: Maximum number of sessions to return
                
            Returns:
                List of sessions
            """
            from src.session.models import SessionType, SessionStatus
            input_data = ListSessionsInput(
                type=SessionType(type) if type else None,
                status=SessionStatus(status) if status else None,
                repo_name=repo_name,
                user_id=user_id,
                limit=limit
            )
            return await self.session_tools.list_sessions(input_data)
        
        @self.mcp.tool()
        async def get_session(session_id: str) -> Dict[str, Any]:
            """
            Get details of a specific session.
            
            Args:
                session_id: Session ID
                
            Returns:
                Session details
            """
            from uuid import UUID
            input_data = GetSessionInput(session_id=UUID(session_id))
            return await self.session_tools.get_session(input_data)
        
        @self.mcp.tool()
        async def close_session(session_id: str, abandon: bool = False) -> Dict[str, Any]:
            """
            Close or abandon a session.
            
            Args:
                session_id: Session ID
                abandon: Mark as abandoned instead of completed
                
            Returns:
                Success message
            """
            from uuid import UUID
            input_data = CloseSessionInput(
                session_id=UUID(session_id),
                abandon=abandon
            )
            return await self.session_tools.close_session(input_data)
        
        # Delegation tools
        @self.mcp.tool()
        async def start_delegation(
            repo_name: str,
            prompt: str,
            user_id: str,
            user_name: str,
            user_email: str,
            base_branch: str = None,
            research_id: str = None,
            task_slug: str = None
        ) -> Dict[str, Any]:
            """
            Start a delegation session.
            
            Args:
                repo_name: Repository name
                prompt: Delegation task description
                user_id: User ID
                user_name: User's Git name
                user_email: User's Git email
                base_branch: Optional base branch
                research_id: Optional research ID to base on
                task_slug: Optional short task identifier
                
            Returns:
                New delegation session details
            """
            from uuid import UUID
            from src.session.models import GitIdentity
            
            input_data = StartDelegationInput(
                repo_name=repo_name,
                prompt=prompt,
                base_branch=base_branch,
                research_id=UUID(research_id) if research_id else None,
                user_id=user_id,
                user_identity=GitIdentity(name=user_name, email=user_email),
                task_slug=task_slug
            )
            return await self.delegation_tools.start_delegation(input_data)
        
        @self.mcp.tool()
        async def commit_changes(session_id: str, message: str = None) -> Dict[str, Any]:
            """
            Commit changes in a delegation session.
            
            Args:
                session_id: Delegation session ID
                message: Optional custom commit message
                
            Returns:
                Commit details
            """
            from uuid import UUID
            input_data = CommitChangesInput(
                session_id=UUID(session_id),
                message=message
            )
            return await self.delegation_tools.commit_changes(input_data)
        
        @self.mcp.tool()
        async def create_pr(
            session_id: str,
            title: str = None,
            body: str = None,
            draft: bool = False
        ) -> Dict[str, Any]:
            """
            Create a pull request for delegation session.
            
            Args:
                session_id: Delegation session ID
                title: Optional PR title
                body: Optional PR body
                draft: Create as draft PR
                
            Returns:
                PR details with URL
            """
            from uuid import UUID
            input_data = CreatePRInput(
                session_id=UUID(session_id),
                title=title,
                body=body,
                draft=draft
            )
            return await self.delegation_tools.create_pr(input_data)
        
        # Repository tools
        @self.mcp.tool()
        async def list_repos() -> Dict[str, Any]:
            """
            List all configured repositories.
            
            Returns:
                List of repositories with details
            """
            input_data = ListReposInput()
            return await self.repository_tools.list_repos(input_data)
        
        @self.mcp.tool()
        async def get_repo(repo_name: str) -> Dict[str, Any]:
            """
            Get details of a specific repository.
            
            Args:
                repo_name: Repository name
                
            Returns:
                Repository details
            """
            input_data = GetRepoInput(repo_name=repo_name)
            return await self.repository_tools.get_repo(input_data)
    
    def _register_resources(self):
        """Register MCP resources."""
        
        @self.mcp.resource("orchestrator://sessions")
        async def get_sessions_resource() -> str:
            """Get all active sessions."""
            result = await self.resources.get_resource("orchestrator://sessions")
            import json
            return json.dumps(result, indent=2)
        
        @self.mcp.resource("orchestrator://research")
        async def get_research_resource() -> str:
            """Get all research artifacts."""
            result = await self.resources.get_resource("orchestrator://research")
            import json
            return json.dumps(result, indent=2)
    
    def get_app(self):
        """
        Get the MCP app for mounting.
        
        Returns:
            FastMCP app
        """
        return self.mcp


def create_mcp_server(
    query_tools: QueryTools,
    session_tools: SessionTools,
    delegation_tools: DelegationTools,
    repository_tools: RepositoryTools,
    resources: MCPResources
) -> MCPServer:
    """
    Create and configure MCP server.
    
    Args:
        query_tools: Query and research tools
        session_tools: Session management tools
        delegation_tools: Delegation tools
        repository_tools: Repository tools
        resources: MCP resources
        
    Returns:
        Configured MCP server
    """
    return MCPServer(
        query_tools=query_tools,
        session_tools=session_tools,
        delegation_tools=delegation_tools,
        repository_tools=repository_tools,
        resources=resources
    )
