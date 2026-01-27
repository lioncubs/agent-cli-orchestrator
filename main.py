"""Main FastAPI application for agent-cli-orchestrator."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
from pathlib import Path
from contextlib import asynccontextmanager
import os
import asyncio
import logging

from config_loader import config
from git_operations import GitOperations
from copilot_cli import copilot_cli
from activity_log import activity_log

# Import session management components
from src.session.store import SessionStore
from src.session.manager import SessionManager
from src.api.routes.sessions import router as sessions_router, init_session_routes
from src.integrations.git import GitOperations as GitOpsIntegration
from src.integrations.copilot import CopilotCLI

# Import query and research components
from src.api.routes.query import router as query_router, init_query_routes
from src.query.service import QueryService
from src.query.research_service import ResearchService
from src.registry.research_store import ResearchStore
from src.permissions.tool_policy import ToolPolicy

# Import delegation components
from src.api.routes.delegation import router as delegation_router, init_delegation_routes
from src.delegation.service import DelegationService
from src.session.models import GitIdentity

# Import authentication components
from src.api.routes.auth import router as auth_router, init_auth_routes
from src.auth.service import AuthService
from src.storage.yaml_backend import YAMLBackend

# Import security middleware
from src.api.middleware.auth import AuthMiddleware
from src.api.middleware.rate_limit import RateLimitMiddleware
from src.api.middleware.security_headers import SecurityHeadersMiddleware, setup_cors

# Import MCP components
from src.mcp.server import create_mcp_server
from src.mcp.tools.query import QueryTools
from src.mcp.tools.session import SessionTools
from src.mcp.tools.delegation import DelegationTools
from src.mcp.tools.repository import RepositoryTools
from src.mcp.resources import MCPResources

# Import metrics components
from src.metrics.database import get_db_manager
from src.metrics.middleware import MetricsMiddleware
from src.api.routes.metrics import init_metrics_routes

# Import Copilot PAT components
from src.api.routes.copilot_pat import init_copilot_pat_routes

# Import memory components
from src.api.routes.memory import router as memory_router, init_memory_routes
from src.memory.service import MemoryService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models
class PromptRequest(BaseModel):
    prompt: str
    options: Optional[Dict[str, Any]] = None
    repo_name: Optional[str] = None
    show_full_output: Optional[bool] = False


class BranchSelectRequest(BaseModel):
    branch: str
    repo_name: Optional[str] = None


class WorktreeCreateRequest(BaseModel):
    path: str
    branch: str
    create_branch: Optional[bool] = False
    repo_name: Optional[str] = None



def resolve_repo_path(repo_name: Optional[str] = None) -> str:
    """Resolve repository name to absolute path.
    
    Args:
        repo_name: Repository name from config, or None for default
        
    Returns:
        Absolute path to the repository
        
    Raises:
        HTTPException: If repo_name is not found in configuration
    """
    repo_path = config.get_repository_path(repo_name)
    if repo_path is None:
        if repo_name:
            raise HTTPException(
                status_code=404, 
                detail=f"Repository '{repo_name}' not found in configuration"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="No default repository configured"
            )
    
    # Convert to absolute path
    if not os.path.isabs(repo_path):
        repo_path = os.path.abspath(repo_path)
    
    return repo_path


# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting up application...")
    
    # Initialize metrics database if enabled
    if config.metrics_enabled:
        try:
            db_manager = get_db_manager(
                database_url=config.metrics_database_url,
                echo=False
            )
            await db_manager.init_db()
            logger.info("Metrics database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize metrics database: {e}")
            logger.warning("Metrics collection will be disabled")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Close database connections
    if config.metrics_enabled:
        try:
            db_manager = get_db_manager()
            await db_manager.close()
            logger.info("Metrics database connections closed")
        except Exception as e:
            logger.error(f"Error closing metrics database: {e}")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Agent CLI Orchestrator",
    description="Multi-CLI orchestration system with GitHub Copilot CLI support",
    version="0.1.0",
    lifespan=lifespan
)

# Setup CORS with configuration
cors_config = config.get("security.cors", {})
if cors_config.get("enabled", True):
    setup_cors(
        app,
        allow_origins=cors_config.get("allow_origins"),
        allow_credentials=cors_config.get("allow_credentials", True)
    )
    logger.info("CORS configured")

# Add security headers middleware
security_headers_config = config.get("security.headers", {})
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=security_headers_config.get("enable_hsts", False),
    hsts_max_age=security_headers_config.get("hsts_max_age", 31536000),
    enable_csp=security_headers_config.get("enable_csp", True)
)
logger.info("Security headers middleware configured")

# Add rate limiting middleware
rate_limit_config = config.get("security.rate_limit", {})
if rate_limit_config.get("enabled", True):
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=rate_limit_config.get("requests_per_minute", 60),
        burst=rate_limit_config.get("burst", 10)
    )
    logger.info("Rate limiting middleware configured")

# Initialize authentication storage and service
auth_storage_dir = "./data/auth"
os.makedirs(auth_storage_dir, exist_ok=True)
auth_storage = YAMLBackend(storage_dir=auth_storage_dir)
auth_service = AuthService(storage=auth_storage)

# Add authentication middleware
auth_config = config.get("security.auth", {})
if auth_config.get("enabled", True):
    app.add_middleware(
        AuthMiddleware,
        auth_service=auth_service,
        exclude_paths=auth_config.get("exclude_paths", [
            "/docs", "/redoc", "/openapi.json", "/health", "/_health", "/", "/ui", "/streaming-test"
        ]),
        require_auth=auth_config.get("require_auth", False)
    )
    logger.info(f"Authentication middleware configured (require_auth={auth_config.get('require_auth', False)})")

# Add metrics collection middleware
if config.metrics_enabled:
    app.add_middleware(
        MetricsMiddleware,
        collect_system_metrics=config.metrics_collect_system,
        system_metrics_interval=config.metrics_system_interval
    )
    logger.info(f"Metrics middleware configured (system interval: {config.metrics_system_interval}s)")


# Initialize Git operations
git_ops = GitOperations()

# Initialize session management
session_store = SessionStore(default_ttl_hours=24)
git_ops_integration = GitOpsIntegration()
copilot_cli_integration = CopilotCLI()
session_manager = SessionManager(
    store=session_store,
    git_ops=git_ops_integration,
    copilot_cli=copilot_cli_integration
)

# Initialize query and research components
research_store = ResearchStore()
query_service = QueryService()
tool_policy = ToolPolicy()
research_service = ResearchService(
    research_store=research_store,
    query_service=query_service,
    tool_policy=tool_policy
)

# Initialize delegation service
# Use default repository path for delegation operations
default_repo_path = config.get_repository_path()
agent_identity = GitIdentity(
    name="Agent CLI Orchestrator",
    email="agent@cli-orchestrator.local"
)
delegation_service = DelegationService(
    session_store=session_store,
    repo_path=default_repo_path or ".",
    agent_identity=agent_identity
)

# Initialize MCP tools and server
query_tools = QueryTools(
    query_service=query_service,
    research_service=research_service,
    session_store=session_store,
    research_store=research_store
)

session_tools = SessionTools(
    session_manager=session_manager,
    session_store=session_store
)

delegation_tools = DelegationTools(
    delegation_service=delegation_service,
    session_store=session_store
)

repository_tools = RepositoryTools(
    session_store=session_store
)

mcp_resources = MCPResources(
    session_store=session_store,
    research_store=research_store
)

mcp_server = create_mcp_server(
    query_tools=query_tools,
    session_tools=session_tools,
    delegation_tools=delegation_tools,
    repository_tools=repository_tools,
    resources=mcp_resources
)

# Initialize and include session routes
init_session_routes(session_store, session_manager)
app.include_router(sessions_router)

# Initialize and include query routes
init_query_routes(
    query_service=query_service,
    research_service=research_service,
    session_manager=session_manager,
    research_store=research_store,
    tool_policy=tool_policy
)
app.include_router(query_router)

# Initialize and include delegation routes
init_delegation_routes(session_store, session_manager, delegation_service)
app.include_router(delegation_router)

# Initialize and include authentication routes
init_auth_routes(storage_dir="./data/auth")
app.include_router(auth_router)

# Initialize and include metrics routes
if config.metrics_enabled:
    init_metrics_routes(app)
    logger.info("Metrics and analytics routes initialized")

# Initialize and include Copilot PAT routes
if config.copilot_pat_enabled:
    init_copilot_pat_routes(app)
    logger.info("Copilot PAT routes initialized")

# Initialize and include memory routes
memory_service = MemoryService(storage_dir="./data/memories")
init_memory_routes(memory_service)
app.include_router(memory_router)
logger.info("Memory routes initialized")

# Mount MCP server at /mcp endpoint
app.mount("/mcp", mcp_server.get_app())

# Mount frontend static files and handle SPA routing
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    # Serve static assets first
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    logger.info(f"Mounted frontend assets at /assets")
    
    # Serve index.html for the dashboard root and any dashboard routes
    @app.get("/dashboard{path:path}", response_class=HTMLResponse)
    async def serve_dashboard(path: str = ""):
        """Serve React dashboard SPA."""
        index_path = os.path.join(frontend_dist, "index.html")
        with open(index_path, 'r') as f:
            return f.read()
    
    logger.info(f"Mounted React dashboard at /dashboard from {frontend_dist}")
else:
    logger.warning(f"Frontend dist directory not found at {frontend_dist}. Dashboard will not be available.")


@app.get("/")
async def root():
    """Root endpoint with welcome message."""
    return {
        "message": "Welcome to Agent CLI Orchestrator",
        "version": "0.1.0",
        "endpoints": {
            "GET /repo": "Get repository name",
            "GET /branch/current": "Get current branch",
            "GET /branches": "List all branches (local and remote)",
            "GET /worktrees": "List all worktrees",
            "GET /copilot/sessions": "List active Copilot CLI sessions",
            "GET /logs": "List recent activity logs",
            "GET /logs/copilot": "List detailed Copilot execution logs with full input/output",
            "POST /branch/select": "Switch to a branch",
            "POST /worktree/create": "Create a new worktree",
            "POST /prompt": "Execute synchronous Copilot CLI prompt",
            "POST /prompt/async": "Execute asynchronous Copilot CLI prompt",
            "POST /prompt/stream": "Execute Copilot CLI prompt with real-time streaming output (SSE)",
            "GET /ui": "Modern React dashboard (primary UI)",
            "GET /legacy-ui": "Legacy HTML interface (simple fallback UI)",
            "GET /streaming-test": "Streaming output test page"
        },
        "session_management": {
            "POST /sessions": "Create a new session",
            "GET /sessions": "List sessions with filters",
            "GET /sessions/{id}": "Get session details",
            "POST /sessions/{id}/continue": "Continue a session",
            "POST /sessions/{id}/complete": "Mark session as completed",
            "DELETE /sessions/{id}": "Delete or abandon a session"
        },
        "query_and_research": {
            "POST /query": "Execute read-only query operations",
            "POST /query/sessions/{id}/complete": "Complete research session and generate artifact",
            "GET /query/research": "List research artifacts",
            "GET /query/research/{id}": "Get specific research artifact",
            "POST /query/research/{id}/delegate": "Create delegation from research artifact",
            "DELETE /query/research/{id}": "Delete research artifact"
        },
        "delegation": {
            "POST /delegation/sessions": "Create a delegation session with worktree",
            "POST /delegation/sessions/{id}/continue": "Continue delegation with new turn",
            "POST /delegation/sessions/{id}/commit": "Commit changes in delegation worktree",
            "POST /delegation/sessions/{id}/pr": "Create pull request for delegation",
            "DELETE /delegation/sessions/{id}": "Abandon delegation and cleanup",
            "GET /delegation/sessions/{id}/status": "Get delegation status"
        },
        "authentication": {
            "POST /auth/register": "Register a new user",
            "POST /auth/login": "Login with email and password",
            "POST /auth/api-keys": "Create a new API key",
            "GET /auth/api-keys": "List user's API keys",
            "DELETE /auth/api-keys/{id}": "Revoke an API key",
            "GET /auth/me": "Get current user information",
            "PUT /auth/me": "Update user settings",
            "POST /auth/credentials": "Add Git credentials",
            "GET /auth/credentials": "List Git credentials (masked)",
            "DELETE /auth/credentials/{id}": "Remove Git credentials"
        },
        "security": {
            "GET /health": "Health check endpoint",
            "GET /security/summary": "Security audit summary (admin only)",
            "features": [
                "Bcrypt password hashing with salt",
                "API key authentication with salted SHA-256",
                "Rate limiting (configurable per minute and burst)",
                "Security headers (CSP, HSTS, X-Frame-Options, etc.)",
                "CORS protection",
                "Input validation and sanitization",
                "Security audit logging",
                "TLS/HTTPS support (configurable)"
            ]
        },
        "mcp_server": {
            "description": "Model Context Protocol server for AI agents",
            "base_path": "/mcp",
            "tools": [
                "query - Execute read-only queries",
                "start_research - Start research session",
                "complete_research - Complete research and generate artifact",
                "continue_session - Continue existing session",
                "list_sessions - List all sessions",
                "get_session - Get session details",
                "close_session - Close or abandon session",
                "start_delegation - Start delegation session",
                "commit_changes - Commit delegation changes",
                "create_pr - Create pull request",
                "list_repos - List configured repositories",
                "get_repo - Get repository details"
            ],
            "resources": [
                "orchestrator://sessions - All active sessions",
                "orchestrator://research - All research artifacts"
            ]
        },
        "metrics_and_analytics": {
            "GET /metrics": "Get current API metrics summary",
            "GET /metrics/performance": "Get detailed performance analytics",
            "GET /metrics/usage": "Get usage analytics",
            "GET /metrics/health": "Get system health metrics",
            "GET /metrics/endpoints": "Get per-endpoint metrics",
            "GET /analytics/dashboard": "Get comprehensive dashboard analytics",
            "features": [
                "Real-time performance monitoring",
                "API request/response tracking",
                "System resource metrics (CPU, memory, disk)",
                "User activity tracking",
                "Automated analytics with caching",
                "Database-backed persistent metrics",
                "Percentile calculations (P50, P95, P99)"
            ]
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns server status and basic configuration info.
    Excluded from authentication requirements.
    """
    from src.core.audit_log import security_audit_log
    
    return {
        "status": "healthy",
        "version": "0.1.0",
        "security": {
            "auth_enabled": auth_config.get("enabled", True),
            "rate_limit_enabled": rate_limit_config.get("enabled", True),
            "cors_enabled": cors_config.get("enabled", True),
            "ssl_enabled": config.config.get("server", {}).get("ssl_enabled", False)
        },
        "audit_events_count": len(security_audit_log._entries)
    }


@app.get("/security/summary")
async def security_summary():
    """
    Get security audit summary.
    
    NOTE: In production, this should be restricted to admin users only.
    For now, it's available to demonstrate security features.
    """
    from src.core.audit_log import security_audit_log
    
    summary = security_audit_log.get_security_summary()
    
    return {
        "status": "success",
        "summary": summary,
        "security_features": {
            "password_hashing": "bcrypt with salt",
            "api_key_hashing": "SHA-256 with salt",
            "rate_limiting": f"{rate_limit_config.get('requests_per_minute', 60)} req/min, burst {rate_limit_config.get('burst', 10)}",
            "security_headers": "enabled",
            "cors": "configured",
            "input_validation": "enabled",
            "audit_logging": "enabled"
        }
    }


@app.get("/streaming-test", response_class=HTMLResponse)
async def streaming_test():
    """Serve the streaming test page."""
    with open("/workspaces/lioncubs/agent-cli-orchestrator/test_streaming.html", "r") as f:
        return f.read()


@app.get("/repos")
async def list_repos():
    """List all configured repositories."""
    try:
        repos = config.repositories()
        repo_list = []
        for repo in repos:
            repo_list.append({
                "name": repo.get("name"),
                "path": repo.get("path"),
                "default": repo.get("default", False),
                "worktrees_path": repo.get("worktrees_path")
            })
        
        activity_log.add(
            action="list_repos",
            status="success",
            payload={},
            result={"repositories": repo_list}
        )
        
        return {
            "status": "success",
            "repositories": repo_list,
            "count": len(repo_list)
        }
    except Exception as e:
        activity_log.add(
            action="list_repos",
            status="error",
            payload={},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/repo")
async def get_repository(repo_name: Optional[str] = None):
    """Get repository name."""
    try:
        repo_path = resolve_repo_path(repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        repo_name_result = temp_git_ops.get_repository_name()
        activity_log.add(
            action="get_repository",
            status="success",
            payload={"repo_name": repo_name},
            result={"repository": repo_name_result, "path": repo_path}
        )
        return {
            "repository": repo_name_result,
            "configured_name": repo_name or config.repository_name,
            "path": repo_path
        }
    except Exception as e:
        activity_log.add(
            action="get_repository",
            status="error",
            payload={"repo_name": repo_name},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/branch/current")
async def get_current_branch(repo_name: Optional[str] = None):
    """Get the current branch."""
    try:
        repo_path = resolve_repo_path(repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        branch = temp_git_ops.get_current_branch()
        activity_log.add(
            action="get_current_branch",
            status="success",
            payload={"repo_name": repo_name},
            result={"branch": branch}
        )
        return {"branch": branch, "repository": repo_name or config.repository_name}
    except Exception as e:
        activity_log.add(
            action="get_current_branch",
            status="error",
            payload={"repo_name": repo_name},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/branches")
async def list_branches(repo_name: Optional[str] = None):
    """List all branches (local and remote)."""
    try:
        repo_path = resolve_repo_path(repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        branches = temp_git_ops.list_branches()
        
        # Count by type
        local_count = sum(1 for b in branches if b.get('type') == 'local')
        remote_count = sum(1 for b in branches if b.get('type') == 'remote')
        
        result = {
            "branches": branches,
            "count": {
                "total": len(branches),
                "local": local_count,
                "remote": remote_count
            }
        }
        activity_log.add(
            action="list_branches",
            status="success",
            payload={"repo_name": repo_name},
            result=result
        )
        return result
    except Exception as e:
        activity_log.add(
            action="list_branches",
            status="error",
            payload={"repo_name": repo_name},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/branch/select")
async def select_branch(request: BranchSelectRequest):
    """Switch to a branch."""
    try:
        repo_path = resolve_repo_path(request.repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        result = temp_git_ops.switch_branch(request.branch)
        
        activity_log.add(
            action="select_branch",
            status="success",
            payload={"branch": request.branch, "repo_name": request.repo_name},
            result=result
        )
        return result
    except RuntimeError as e:
        # Git operation errors (branch not found, etc.)
        activity_log.add(
            action="select_branch",
            status="error",
            payload={"branch": request.branch, "repo_name": request.repo_name},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        activity_log.add(
            action="select_branch",
            status="error",
            payload={"branch": request.branch, "repo_name": request.repo_name},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/worktrees")
async def list_worktrees(repo_name: Optional[str] = None):
    """List all worktrees."""
    try:
        repo_path = resolve_repo_path(repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        worktrees = temp_git_ops.list_worktrees()
        result = {
            "worktrees": worktrees,
            "count": len(worktrees)
        }
        activity_log.add(
            action="list_worktrees",
            status="success",
            payload={"repo_name": repo_name},
            result=result
        )
        return result
    except Exception as e:
        activity_log.add(
            action="list_worktrees",
            status="error",
            payload={"repo_name": repo_name},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/worktree/create")
async def create_worktree(request: WorktreeCreateRequest):
    """Create a new worktree."""
    try:
        repo_path = resolve_repo_path(request.repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        result = temp_git_ops.create_worktree(
            path=request.path,
            branch=request.branch,
            create_branch=request.create_branch
        )
        
        activity_log.add(
            action="create_worktree",
            status="success",
            payload={
                "path": request.path,
                "branch": request.branch,
                "create_branch": request.create_branch,
                "repo_name": request.repo_name
            },
            result=result
        )
        return result
    except RuntimeError as e:
        # Git operation errors
        activity_log.add(
            action="create_worktree",
            status="error",
            payload={
                "path": request.path,
                "branch": request.branch,
                "create_branch": request.create_branch,
                "repo_name": request.repo_name
            },
            result={"message": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        activity_log.add(
            action="create_worktree",
            status="error",
            payload={
                "path": request.path,
                "branch": request.branch,
                "create_branch": request.create_branch,
                "repo_name": request.repo_name
            },
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompt")
async def execute_prompt(request: PromptRequest):
    """Execute a synchronous Copilot CLI prompt."""
    try:
        repo_path = resolve_repo_path(request.repo_name) if request.repo_name else None
        result = copilot_cli.execute_prompt(
            prompt=request.prompt,
            options=request.options,
            cwd=repo_path
        )
        
        if result.get("status") == "error":
            activity_log.add(
                action="execute_prompt",
                status="error",
                payload={
                    "prompt": request.prompt,
                    "options": request.options,
                    "repo_name": request.repo_name
                },
                result=result
            )
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        # Determine response format based on show_full_output flag
        if request.show_full_output:
            response = result  # Include full_stdout and full_stderr
        else:
            # Return simplified response
            response = {
                "status": result.get("status"),
                "output": result.get("output"),
                "prompt": result.get("prompt"),
                "log_file": result.get("log_file")
            }
        
        activity_log.add(
            action="execute_prompt",
            status="success",
            payload={
                "prompt": request.prompt,
                "options": request.options,
                "repo_name": request.repo_name,
                "show_full_output": request.show_full_output
            },
            result=response
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        activity_log.add(
            action="execute_prompt",
            status="error",
            payload={
                "prompt": request.prompt,
                "options": request.options,
                "repo_name": request.repo_name
            },
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompt/async")
async def execute_prompt_async(request: PromptRequest):
    """Execute an asynchronous Copilot CLI prompt."""
    try:
        repo_path = resolve_repo_path(request.repo_name) if request.repo_name else None
        result = await copilot_cli.execute_prompt_async(
            prompt=request.prompt,
            options=request.options,
            cwd=repo_path
        )
        
        if result.get("status") == "error":
            activity_log.add(
                action="execute_prompt_async",
                status="error",
                payload={
                    "prompt": request.prompt,
                    "options": request.options,
                    "repo_name": request.repo_name
                },
                result=result
            )
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        # Determine response format based on show_full_output flag
        if request.show_full_output:
            response = result  # Include full_stdout and full_stderr
        else:
            # Return simplified response
            response = {
                "status": result.get("status"),
                "output": result.get("output"),
                "prompt": result.get("prompt"),
                "log_file": result.get("log_file")
            }
        
        activity_log.add(
            action="execute_prompt_async",
            status="success",
            payload={
                "prompt": request.prompt,
                "options": request.options,
                "repo_name": request.repo_name,
                "show_full_output": request.show_full_output
            },
            result=response
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        activity_log.add(
            action="execute_prompt_async",
            status="error",
            payload={
                "prompt": request.prompt,
                "options": request.options,
                "repo_name": request.repo_name
            },
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompt/stream")
async def execute_prompt_streaming(request: PromptRequest):
    """Execute a Copilot CLI prompt with real-time streaming output."""
    
    async def stream_generator():
        """Generator that yields streaming output from Copilot CLI."""
        try:
            repo_path = resolve_repo_path(request.repo_name) if request.repo_name else None
            
            async for chunk in copilot_cli.execute_prompt_streaming(
                prompt=request.prompt,
                options=request.options,
                cwd=repo_path
            ):
                yield f"data: {chunk}\n\n"
            
        except Exception as e:
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/copilot/sessions")
async def list_copilot_sessions():
    """List active Copilot CLI sessions (legacy endpoint)."""
    try:
        result = copilot_cli.list_sessions()
        activity_log.add(
            action="list_copilot_sessions",
            status=result.get("status", "unknown"),
            payload={},
            result=result
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
async def list_logs(limit: Optional[int] = None):
    """List recent activity logs."""
    try:
        logs = activity_log.list(limit)
        return {
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs/copilot")
async def list_copilot_logs(limit: Optional[int] = 20):
    """List detailed Copilot execution logs from log files."""
    try:
        from pathlib import Path
        import json
        
        log_dir = Path(config.copilot_log_dir)
        if not log_dir.exists():
            return {
                "logs": [],
                "count": 0,
                "message": "Log directory does not exist"
            }
        
        # Get all JSON log files
        log_files = sorted(log_dir.glob("copilot_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        logs = []
        for log_file in log_files[:limit]:
            try:
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
                    logs.append({
                        "file": log_file.name,
                        "data": log_data
                    })
            except Exception as e:
                logs.append({
                    "file": log_file.name,
                    "error": f"Failed to read log: {str(e)}"
                })
        
        return {
            "logs": logs,
            "count": len(logs),
            "total_files": len(log_files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/ui")
@app.get("/ui/{full_path:path}")
async def serve_react_app(full_path: str = ""):
    """Serve the React UI application."""
    ui_index_path = Path(__file__).parent / "src" / "ui" / "dist" / "index.html"
    
    if not ui_index_path.exists():
        return HTMLResponse(
            content="""
            <html>
                <head><title>UI Not Built</title></head>
                <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                    <h1>React UI Not Built</h1>
                    <p>The React UI has not been built yet.</p>
                    <p>Please run the following commands:</p>
                    <pre style="background: #f5f5f5; padding: 20px; display: inline-block; text-align: left;">
cd src/ui
npm install
npm run build
                    </pre>
                </body>
            </html>
            """,
            status_code=503
        )
    
    return FileResponse(ui_index_path)



if __name__ == "__main__":
    import uvicorn
    
    # Get server configuration
    server_config = config.get("server", {})
    ssl_enabled = server_config.get("ssl_enabled", False)
    
    # Prepare uvicorn kwargs
    uvicorn_kwargs = {
        "app": app,
        "host": config.server_host,
        "port": config.server_port
    }
    
    # Add SSL/TLS configuration if enabled
    if ssl_enabled:
        ssl_certfile = server_config.get("ssl_certfile")
        ssl_keyfile = server_config.get("ssl_keyfile")
        
        if ssl_certfile and ssl_keyfile:
            if os.path.exists(ssl_certfile) and os.path.exists(ssl_keyfile):
                uvicorn_kwargs["ssl_certfile"] = ssl_certfile
                uvicorn_kwargs["ssl_keyfile"] = ssl_keyfile
                logger.info(f"HTTPS enabled with cert: {ssl_certfile}")
            else:
                logger.warning("SSL enabled but certificate files not found. Starting without SSL.")
        else:
            logger.warning("SSL enabled but certificate paths not configured. Starting without SSL.")
    
    # Start the server
    logger.info(f"Starting server on {config.server_host}:{config.server_port}")
    uvicorn.run(**uvicorn_kwargs)