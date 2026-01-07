"""Main FastAPI application for agent-cli-orchestrator."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import asyncio

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


# Initialize FastAPI app
app = FastAPI(
    title="Agent CLI Orchestrator",
    description="Multi-CLI orchestration system with GitHub Copilot CLI support",
    version="0.1.0"
)

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
            "GET /ui": "Web interface for testing",
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


@app.get("/ui", response_class=HTMLResponse)
async def web_interface():
    """Serve the web interface."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agent CLI Orchestrator</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            header {
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }
            
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .subtitle {
                font-size: 1.1em;
                opacity: 0.9;
            }
            
            .main-content {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            }
            
            .section {
                margin-bottom: 30px;
            }
            
            .section h2 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 1.5em;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #333;
            }
            
            input, textarea, select {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            
            input:focus, textarea:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            
            textarea {
                min-height: 120px;
                resize: vertical;
            }
            
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            button:active {
                transform: translateY(0);
            }
            
            .button-group {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            .output {
                background: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                min-height: 100px;
                max-height: 400px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }
            
            .output pre {
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .loading {
                color: #667eea;
                font-style: italic;
            }
            
            .error {
                color: #e74c3c;
            }
            
            .success {
                color: #27ae60;
            }
            
            .stream-line {
                margin: 2px 0;
                line-height: 1.4;
            }
            
            .stream-stdout {
                color: #2c3e50;
            }
            
            .stream-stderr {
                color: #e74c3c;
                font-weight: 500;
            }
            
            .stream-start {
                color: #27ae60;
                font-weight: bold;
                border-bottom: 1px solid #27ae60;
                padding-bottom: 5px;
                margin-bottom: 5px;
            }
            
            .stream-complete {
                color: #27ae60;
                font-weight: bold;
                border-top: 1px solid #27ae60;
                padding-top: 5px;
                margin-top: 5px;
            }
            
            .stream-error {
                color: #e74c3c;
                font-weight: bold;
                background: #fee;
                padding: 5px;
                border-radius: 4px;
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .info-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            
            .info-card h3 {
                color: #667eea;
                margin-bottom: 10px;
                font-size: 1.1em;
            }
            
            .info-card p {
                color: #666;
                font-size: 0.95em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🤖 Agent CLI Orchestrator</h1>
                <p class="subtitle">Multi-CLI orchestration with GitHub Copilot CLI</p>
            </header>
            
            <div class="main-content">
                <!-- Repository Info Section -->
                <div class="section">
                    <h2>📊 Repository Information</h2>
                    <div class="info-grid" id="repoInfo">
                        <div class="info-card">
                            <h3>Repository</h3>
                            <p id="repoName">Loading...</p>
                        </div>
                        <div class="info-card">
                            <h3>Current Branch</h3>
                            <p id="currentBranch">Loading...</p>
                        </div>
                    </div>
                </div>
                
                <!-- Copilot Prompt Section -->
                <div class="section">
                    <h2>💬 Copilot CLI Prompt</h2>
                    <div class="form-group">
                        <label for="promptInput">Enter your prompt:</label>
                        <textarea id="promptInput" placeholder="e.g., How do I create a Python function to reverse a string?"></textarea>
                    </div>
                    <div class="form-group">
                        <label for="sessionId">Session ID (optional - to continue existing session):</label>
                        <input type="text" id="sessionId" placeholder="e.g., abc123-session-id">
                    </div>
                    <div class="button-group">
                        <button onclick="executePrompt(false)">Execute Synchronous</button>
                        <button onclick="executePrompt(true)">Execute Async</button>
                        <button onclick="executePromptStreaming()" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">🔴 Execute with Live Streaming</button>
                    </div>
                    <div id="promptOutput" class="output" style="display: none;"></div>
                </div>
                
                <!-- Branch Management Section -->
                <div class="section">
                    <h2>🌿 Branch Management</h2>
                    <div class="button-group" style="margin-bottom: 12px;">
                        <button onclick="listBranches()">List Branches</button>
                    </div>
                    <div id="branchesOutput" class="output" style="display: none;"></div>
                    <div class="form-group">
                        <label for="branchInput">Branch name:</label>
                        <input type="text" id="branchInput" placeholder="e.g., feature/new-feature">
                    </div>
                    <button onclick="switchBranch()">Switch Branch</button>
                    <div id="branchOutput" class="output" style="display: none;"></div>
                </div>
                
                <!-- Worktree Management Section -->
                <div class="section">
                    <h2>📁 Worktree Management</h2>
                    <div class="button-group">
                        <button onclick="listWorktrees()">List Worktrees</button>
                    </div>
                    <div class="form-group" style="margin-top: 15px;">
                        <label for="worktreePath">Worktree path:</label>
                        <input type="text" id="worktreePath" placeholder="e.g., ./worktrees/feature-branch">
                    </div>
                    <div class="form-group">
                        <label for="worktreeBranch">Branch name:</label>
                        <input type="text" id="worktreeBranch" placeholder="e.g., feature/new-feature">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="createBranch"> Create new branch
                        </label>
                    </div>
                    <button onclick="createWorktree()">Create Worktree</button>
                    <div id="worktreeOutput" class="output" style="display: none;"></div>
                </div>

                <!-- Activity Logs Section -->
                <div class="section">
                    <h2>📜 Activity Logs</h2>
                    <div class="form-group">
                        <label for="logLimit">Entries to fetch (latest):</label>
                        <input type="number" id="logLimit" value="50" min="1" max="200">
                    </div>
                    <div class="button-group">
                        <button onclick="loadLogs()">Load Activity Logs</button>
                        <button onclick="loadCopilotLogs()">Load Copilot Full Logs</button>
                    </div>
                    <div id="logsOutput" class="output" style="display: none;"></div>
                </div>
            </div>
        </div>
        
        <script>
            // Load repository information on page load
            window.addEventListener('DOMContentLoaded', async () => {
                await loadRepoInfo();
            });
            
            async function loadRepoInfo() {
                try {
                    const repoResponse = await fetch('/repo');
                    const repoData = await repoResponse.json();
                    document.getElementById('repoName').textContent = repoData.repository || 'Unknown';
                    
                    const branchResponse = await fetch('/branch/current');
                    const branchData = await branchResponse.json();
                    document.getElementById('currentBranch').textContent = branchData.branch || 'Unknown';
                } catch (error) {
                    document.getElementById('repoName').textContent = 'Error loading';
                    document.getElementById('currentBranch').textContent = 'Error loading';
                }
            }
            
            async function executePrompt(isAsync) {
                const prompt = document.getElementById('promptInput').value.trim();
                const sessionId = document.getElementById('sessionId').value.trim();
                const output = document.getElementById('promptOutput');
                
                if (!prompt) {
                    alert('Please enter a prompt');
                    return;
                }
                
                output.style.display = 'block';
                output.innerHTML = '<p class="loading">Executing prompt...</p>';
                
                try {
                    const endpoint = isAsync ? '/prompt/async' : '/prompt';
                    const requestBody = { prompt: prompt };
                    
                    // Add session_id to options if provided
                    if (sessionId) {
                        requestBody.options = { session_id: sessionId };
                    }
                    
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestBody)
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        output.innerHTML = '<p class="success">✓ Success</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    } else {
                        output.innerHTML = '<p class="error">✗ Error</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    }
                } catch (error) {
                    output.innerHTML = '<p class="error">✗ Error: ' + error.message + '</p>';
                }
            }
            
            async function executePromptStreaming() {
                const prompt = document.getElementById('promptInput').value.trim();
                const sessionId = document.getElementById('sessionId').value.trim();
                const output = document.getElementById('promptOutput');
                
                if (!prompt) {
                    alert('Please enter a prompt');
                    return;
                }
                
                output.style.display = 'block';
                output.innerHTML = '<div class="stream-start">🔴 Streaming output - live...</div>';
                
                try {
                    const requestBody = { prompt: prompt };
                    
                    if (sessionId) {
                        requestBody.options = { session_id: sessionId };
                    }
                    
                    const response = await fetch('/prompt/stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestBody)
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    while (true) {
                        const {done, value} = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.substring(6).trim();
                                if (data) {
                                    try {
                                        const event = JSON.parse(data);
                                        handleStreamEvent(event, output);
                                    } catch (e) {
                                        console.error('Failed to parse event:', data);
                                    }
                                }
                            }
                        }
                    }
                    
                } catch (error) {
                    output.innerHTML += '<div class="stream-error">✗ Error: ' + error.message + '</div>';
                }
            }
            
            function handleStreamEvent(event, output) {
                let lineDiv = document.createElement('div');
                lineDiv.className = 'stream-line';
                
                switch (event.type) {
                    case 'start':
                        lineDiv.className += ' stream-start';
                        lineDiv.textContent = `Command: ${event.command}`;
                        output.appendChild(lineDiv);
                        
                        let cwdDiv = document.createElement('div');
                        cwdDiv.className = 'stream-line stream-start';
                        cwdDiv.textContent = `Working directory: ${event.cwd}`;
                        output.appendChild(cwdDiv);
                        break;
                    
                    case 'stdout':
                        lineDiv.className += ' stream-stdout';
                        lineDiv.textContent = event.data;
                        output.appendChild(lineDiv);
                        break;
                    
                    case 'stderr':
                        lineDiv.className += ' stream-stderr';
                        lineDiv.textContent = `[stderr] ${event.data}`;
                        output.appendChild(lineDiv);
                        break;
                    
                    case 'complete':
                        lineDiv.className += ' stream-complete';
                        const status = event.exit_code === 0 ? '✓ Completed successfully' : `⚠ Exited with code ${event.exit_code}`;
                        lineDiv.textContent = status;
                        output.appendChild(lineDiv);
                        break;
                    
                    case 'error':
                        lineDiv.className += ' stream-error';
                        lineDiv.textContent = `ERROR: ${event.message}`;
                        output.appendChild(lineDiv);
                        break;
                }
                
                // Auto-scroll to bottom
                output.scrollTop = output.scrollHeight;
            }
            
            async function switchBranch() {
                const branch = document.getElementById('branchInput').value.trim();
                const output = document.getElementById('branchOutput');
                
                if (!branch) {
                    alert('Please enter a branch name');
                    return;
                }
                
                output.style.display = 'block';
                output.innerHTML = '<p class="loading">Switching branch...</p>';
                
                try {
                    const response = await fetch('/branch/select', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ branch: branch })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        output.innerHTML = '<p class="success">✓ Success</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                        await loadRepoInfo(); // Refresh branch info
                    } else {
                        output.innerHTML = '<p class="error">✗ Error</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    }
                } catch (error) {
                    output.innerHTML = '<p class="error">✗ Error: ' + error.message + '</p>';
                }
            }

            async function listBranches() {
                const output = document.getElementById('branchesOutput');
                output.style.display = 'block';
                output.innerHTML = '<p class="loading">Loading branches...</p>';
                
                try {
                    const response = await fetch('/branches');
                    const data = await response.json();
                    
                    if (response.ok) {
                        output.innerHTML = '<p class="success">✓ Branches</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    } else {
                        output.innerHTML = '<p class="error">✗ Error</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    }
                } catch (error) {
                    output.innerHTML = '<p class="error">✗ Error: ' + error.message + '</p>';
                }
            }
            
            async function listWorktrees() {
                const output = document.getElementById('worktreeOutput');
                output.style.display = 'block';
                output.innerHTML = '<p class="loading">Loading worktrees...</p>';
                
                try {
                    const response = await fetch('/worktrees');
                    const data = await response.json();
                    
                    if (response.ok) {
                        output.innerHTML = '<p class="success">✓ Worktrees</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    } else {
                        output.innerHTML = '<p class="error">✗ Error</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    }
                } catch (error) {
                    output.innerHTML = '<p class="error">✗ Error: ' + error.message + '</p>';
                }
            }
            
            async function createWorktree() {
                const path = document.getElementById('worktreePath').value.trim();
                const branch = document.getElementById('worktreeBranch').value.trim();
                const createBranch = document.getElementById('createBranch').checked;
                const output = document.getElementById('worktreeOutput');
                
                if (!path || !branch) {
                    alert('Please enter both path and branch name');
                    return;
                }
                
                output.style.display = 'block';
                output.innerHTML = '<p class="loading">Creating worktree...</p>';
                
                try {
                    const response = await fetch('/worktree/create', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            path: path,
                            branch: branch,
                            create_branch: createBranch
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        output.innerHTML = '<p class="success">✓ Success</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    } else {
                        output.innerHTML = '<p class="error">✗ Error</p><pre>' + 
                            JSON.stringify(data, null, 2) + '</pre>';
                    }
                } catch (error) {
                    output.innerHTML = '<p class="error">✗ Error: ' + error.message + '</p>';
                }
            }

            async function loadLogs() {
                const limitInput = document.getElementById('logLimit');
                const limit = parseInt(limitInput.value, 10) || 50;
                const output = document.getElementById('logsOutput');
                output.style.display = 'block';
                output.innerHTML = '<p class="loading">Loading logs...</p>';

                try {
                    const response = await fetch(`/logs?limit=${encodeURIComponent(limit)}`);
                    const data = await response.json();

                    if (response.ok) {
                        output.innerHTML = '<p class="success">✓ Activity Logs</p><pre>' +
                            JSON.stringify(data, null, 2) + '</pre>';
                    } else {
                        output.innerHTML = '<p class="error">✗ Error</p><pre>' +
                            JSON.stringify(data, null, 2) + '</pre>';
                    }
                } catch (error) {
                    output.innerHTML = '<p class="error">✗ Error: ' + error.message + '</p>';
                }
            }

            async function loadCopilotLogs() {
                const limitInput = document.getElementById('logLimit');
                const limit = parseInt(limitInput.value, 10) || 20;
                const output = document.getElementById('logsOutput');
                output.style.display = 'block';
                output.innerHTML = '<p class="loading">Loading Copilot detailed logs...</p>';

                try {
                    const response = await fetch(`/logs/copilot?limit=${encodeURIComponent(limit)}`);
                    const data = await response.json();

                    if (response.ok) {
                        let logHtml = '<p class="success">✓ Copilot Full Logs (' + data.count + ' of ' + data.total_files + ' total)</p>';
                        
                        if (data.logs && data.logs.length > 0) {
                            data.logs.forEach((log, index) => {
                                logHtml += '<div style="border-top: 2px solid #667eea; margin-top: 15px; padding-top: 10px;">';
                                logHtml += '<strong style="color: #667eea;">Log #' + (index + 1) + ': ' + log.file + '</strong>';
                                if (log.error) {
                                    logHtml += '<p class="error">' + log.error + '</p>';
                                } else if (log.data) {
                                    logHtml += '<pre>' + JSON.stringify(log.data, null, 2) + '</pre>';
                                }
                                logHtml += '</div>';
                            });
                        } else {
                            logHtml += '<p>No Copilot logs found.</p>';
                        }
                        
                        output.innerHTML = logHtml;
                    } else {
                        output.innerHTML = '<p class="error">✗ Error</p><pre>' +
                            JSON.stringify(data, null, 2) + '</pre>';
                    }
                } catch (error) {
                    output.innerHTML = '<p class="error">✗ Error: ' + error.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.server_host,
        port=config.server_port
    )