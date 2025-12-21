"""Main FastAPI application for agent-cli-orchestrator."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os

from config_loader import config
from git_operations import GitOperations
from copilot_cli import copilot_cli


# Pydantic models
class PromptRequest(BaseModel):
    prompt: str
    options: Optional[Dict[str, Any]] = None


class BranchSelectRequest(BaseModel):
    branch: str


class WorktreeCreateRequest(BaseModel):
    path: str
    branch: str
    create_branch: Optional[bool] = False


# Initialize FastAPI app
app = FastAPI(
    title="Agent CLI Orchestrator",
    description="Multi-CLI orchestration system with GitHub Copilot CLI support",
    version="0.1.0"
)

# Initialize Git operations
git_ops = GitOperations()


@app.get("/")
async def root():
    """Root endpoint with welcome message."""
    return {
        "message": "Welcome to Agent CLI Orchestrator",
        "version": "0.1.0",
        "endpoints": {
            "GET /repo": "Get repository name",
            "GET /branch/current": "Get current branch",
            "GET /worktrees": "List all worktrees",
            "POST /branch/select": "Switch to a branch",
            "POST /worktree/create": "Create a new worktree",
            "POST /prompt": "Execute synchronous Copilot CLI prompt",
            "POST /prompt/async": "Execute asynchronous Copilot CLI prompt",
            "GET /ui": "Web interface for testing"
        }
    }


@app.get("/repo")
async def get_repository():
    """Get repository name."""
    try:
        repo_name = git_ops.get_repository_name()
        return {
            "repository": repo_name,
            "configured_name": config.repository_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/branch/current")
async def get_current_branch():
    """Get the current branch."""
    try:
        branch = git_ops.get_current_branch()
        return {
            "branch": branch
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/branch/select")
async def select_branch(request: BranchSelectRequest):
    """Switch to a different branch."""
    try:
        result = git_ops.switch_branch(request.branch)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/worktrees")
async def list_worktrees():
    """List all Git worktrees."""
    try:
        worktrees = git_ops.list_worktrees()
        return {
            "worktrees": worktrees,
            "count": len(worktrees)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/worktree/create")
async def create_worktree(request: WorktreeCreateRequest):
    """Create a new Git worktree."""
    try:
        result = git_ops.create_worktree(
            path=request.path,
            branch=request.branch,
            create_branch=request.create_branch
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/prompt")
async def execute_prompt(request: PromptRequest):
    """Execute a synchronous Copilot CLI prompt."""
    try:
        result = copilot_cli.execute_prompt(
            prompt=request.prompt,
            options=request.options
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompt/async")
async def execute_prompt_async(request: PromptRequest):
    """Execute an asynchronous Copilot CLI prompt."""
    try:
        result = await copilot_cli.execute_prompt_async(
            prompt=request.prompt,
            options=request.options
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
    except HTTPException:
        raise
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
                    <div class="button-group">
                        <button onclick="executePrompt(false)">Execute Synchronous</button>
                        <button onclick="executePrompt(true)">Execute Async</button>
                    </div>
                    <div id="promptOutput" class="output" style="display: none;"></div>
                </div>
                
                <!-- Branch Management Section -->
                <div class="section">
                    <h2>🌿 Branch Management</h2>
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
                const output = document.getElementById('promptOutput');
                
                if (!prompt) {
                    alert('Please enter a prompt');
                    return;
                }
                
                output.style.display = 'block';
                output.innerHTML = '<p class="loading">Executing prompt...</p>';
                
                try {
                    const endpoint = isAsync ? '/prompt/async' : '/prompt';
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ prompt: prompt })
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
