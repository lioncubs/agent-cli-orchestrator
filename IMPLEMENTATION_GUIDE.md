## Main.py Updates - Implementation Guide

This document outlines all the changes needed to complete the repository mapping and full output feature implementation.

### Changes Already Completed:
1. ✅ config.yaml - Updated to repositories list format
2. ✅ config_loader.py - Added repository mapping methods
3. ✅ copilot_cli.py - Added cwd parameter to execute methods
4. ✅ Pydantic models in main.py - Added repo_name and show_full_output fields

### Remaining Changes to main.py:

#### 1. Add resolve_repo_path helper function
**Location:** After Pydantic models, before "# Initialize FastAPI app"

```python
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
```

#### 2. Add /repos endpoint
**Location:** After root endpoint @app.get("/")

```python
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
                "default": repo.get("default", False)
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
```

#### 3. Update @app.get("/repo") endpoint
**Replace existing function with:**

```python
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
```

#### 4. Update @app.get("/branch/current") endpoint
**Replace existing function with:**

```python
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
```

#### 5. Update @app.get("/branches") endpoint
**Replace existing function with:**

```python
@app.get("/branches")
async def list_branches(repo_name: Optional[str] = None):
    """List all branches (local and remote)."""
    try:
        repo_path = resolve_repo_path(repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        branches = temp_git_ops.list_branches()
        activity_log.add(
            action="list_branches",
            status="success",
            payload={"repo_name": repo_name},
            result=branches
        )
        return branches
    except Exception as e:
        activity_log.add(
            action="list_branches",
            status="error",
            payload={"repo_name": repo_name},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))
```

#### 6. Update @app.get("/worktrees") endpoint
**Replace existing function with:**

```python
@app.get("/worktrees")
async def list_worktrees(repo_name: Optional[str] = None):
    """List all worktrees."""
    try:
        repo_path = resolve_repo_path(repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        worktrees = temp_git_ops.list_worktrees()
        activity_log.add(
            action="list_worktrees",
            status="success",
            payload={"repo_name": repo_name},
            result=worktrees
        )
        return worktrees
    except Exception as e:
        activity_log.add(
            action="list_worktrees",
            status="error",
            payload={"repo_name": repo_name},
            result={"message": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))
```

#### 7. Update @app.post("/branch/select") endpoint
**Replace existing function with:**

```python
@app.post("/branch/select")
async def select_branch(request: BranchSelectRequest):
    """Switch to a branch."""
    try:
        repo_path = resolve_repo_path(request.repo_name)
        temp_git_ops = GitOperations(repo_path=repo_path)
        result = temp_git_ops.switch_branch(request.branch)
        
        if result.get("status") == "error":
            activity_log.add(
                action="select_branch",
                status="error",
                payload={"branch": request.branch, "repo_name": request.repo_name},
                result=result
            )
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        activity_log.add(
            action="select_branch",
            status="success",
            payload={"branch": request.branch, "repo_name": request.repo_name},
            result=result
        )
        return result
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
```

#### 8. Update @app.post("/worktree/create") endpoint
**Replace existing function with:**

```python
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
        
        if result.get("status") == "error":
            activity_log.add(
                action="create_worktree",
                status="error",
                payload={
                    "path": request.path,
                    "branch": request.branch,
                    "create_branch": request.create_branch,
                    "repo_name": request.repo_name
                },
                result=result
            )
            raise HTTPException(status_code=400, detail=result.get("message"))
        
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
```

#### 9. Update @app.post("/prompt") endpoint
**Replace existing function with:**

```python
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
```

#### 10. Update @app.post("/prompt/async") endpoint
**Replace existing function with:**

```python
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
```

### UI Updates

The UI section in main.py (around line 700+) needs these additions:

1. Add repository selector dropdown in the HTML form
2. Add "show full output" checkbox
3. Add JavaScript to load repositories on page load
4. Update executePrompt() function to include repo_name and show_full_output

See separate UI_UPDATES.md file for detailed UI changes.

### Testing Commands

After all changes are applied:

```bash
# Test configuration
python3 -c "from config_loader import config; print(config.list_repositories())"

# Test imports
python3 -c "from main import app; print('Main imports OK')"

# Run unit tests
pytest -v

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Validation Checklist

- [ ] All Pydantic models have repo_name field
- [ ] resolve_repo_path() helper function added
- [ ] /repos endpoint returns repository list
- [ ] All GET endpoints accept repo_name query parameter
- [ ] All POST endpoints use request.repo_name
- [ ] /prompt endpoints support show_full_output flag
- [ ] UI has repository dropdown
- [ ] UI has show full output checkbox
- [ ] All tests pass
