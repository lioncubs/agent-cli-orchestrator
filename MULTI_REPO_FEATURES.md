# New Features: Multi-Repository Support and Full Output Display

## Overview

The agent-cli-orchestrator now supports:
1. **Multi-repository configuration** - Manage multiple Git repositories from config
2. **Dynamic repository switching** - Execute operations in different repositories via API
3. **Full output display** - View complete Copilot CLI session output

## Configuration Changes

### Old Format (Single Repository)
```yaml
repository:
  name: "agent-cli-orchestrator"
  default_branch: "main"
```

### New Format (Multiple Repositories)
```yaml
repositories:
  - name: "agent-cli-orchestrator"
    path: "."
    default: true
    worktrees_path: "../agent-cli-orchestrator.worktrees"
  - name: "lioncubs"
    path: "/workspaces/lioncubs"
    worktrees_path: "/workspaces/lioncubs.worktrees"
  - name: "my-other-project"
    path: "/path/to/project"
    worktrees_path: "/path/to/project.worktrees"
```

**Key Points:**
- Use `default: true` to mark the default repository
- Paths can be relative or absolute
- Repository names must be unique
- At least one repository must be configured
- Each repository has its own `worktrees_path` for organizing worktrees

## New API Endpoints

### List Repositories
```bash
GET /repos
```

**Response:**
```json
{
  "status": "success",
  "repositories": [
    {
      "name": "agent-cli-orchestrator",
      "path": ".",
      "default": true
    },
    {
      "name": "lioncubs",
      "path": "/workspaces/lioncubs",
      "default": false
    }
  ],
  "count": 2
}
```

## Updated API Endpoints

All Git-related endpoints now accept an optional `repo_name` parameter:

### Query Parameter (GET Requests)
```bash
# Use default repository
GET /repo

# Use specific repository
GET /repo?repo_name=lioncubs
```

### Request Body (POST Requests)
```bash
# Switch branch in default repository
POST /branch/select
{
  "branch": "main"
}

# Switch branch in specific repository
POST /branch/select
{
  "branch": "main",
  "repo_name": "lioncubs"
}
```

## Affected Endpoints

All these endpoints now support `repo_name`:
- `GET /repo?repo_name=<name>`
- `GET /branch/current?repo_name=<name>`
- `GET /branches?repo_name=<name>`
- `GET /worktrees?repo_name=<name>`
- `POST /branch/select` (in request body)
- `POST /worktree/create` (in request body)
- `POST /prompt` (in request body)
- `POST /prompt/async` (in request body)

## Full Output Display

### New Parameter: show_full_output

The Copilot CLI endpoints (`/prompt` and `/prompt/async`) now support viewing complete session output.

**Default Behavior (show_full_output=false):**
```bash
POST /prompt
{
  "prompt": "what files are in this directory?"
}
```

**Response (Simplified):**
```json
{
  "status": "success",
  "output": "Files:\n- main.py\n- config.yaml\n- README.md",
  "prompt": "what files are in this directory?",
  "log_file": "/path/to/logs/copilot/copilot_2025-01-15T10-30-45.json"
}
```

**Full Output (show_full_output=true):**
```bash
POST /prompt
{
  "prompt": "what files are in this directory?",
  "show_full_output": true
}
```

**Response (Complete):**
```json
{
  "status": "success",
  "output": "Files:\n- main.py\n- config.yaml\n- README.md",
  "prompt": "what files are in this directory?",
  "full_stdout": "[COMPLETE AGENT SESSION OUTPUT WITH ALL INTERACTIONS]",
  "full_stderr": "",
  "command": "copilot -p 'what files are in this directory?' --silent --allow-all-tools",
  "log_file": "/path/to/logs/copilot/copilot_2025-01-15T10-30-45.json"
}
```

### Benefits of Full Output

- **Debugging** - See exactly what the agent did
- **Auditing** - Track complete execution history
- **Learning** - Understand agent decision-making process
- **Verification** - Confirm tool usage and file modifications

### Log Files

Regardless of `show_full_output` setting, complete logs are always saved to:
```
logs/copilot/copilot_<timestamp>.json
```

Log files include:
- Timestamp
- Full command executed
- Complete stdout and stderr
- Exit code
- Input prompt and options

## Complete Examples

### Example 1: Execute Copilot in Different Repository
```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "list all Python files in this project",
    "repo_name": "lioncubs",
    "show_full_output": false
  }'
```

### Example 2: View Complete Agent Session
```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "create a function to calculate fibonacci numbers",
    "show_full_output": true
  }'
```

### Example 3: List Branches in Specific Repository
```bash
curl "http://localhost:8000/branches?repo_name=lioncubs"
```

**Response:**
```json
{
  "branches": [
    {"name": "main", "current": true, "type": "local"},
    {"name": "feature/updates", "current": false, "type": "local"},
    {"name": "origin/main", "current": false, "type": "remote"}
  ],
  "count": {
    "total": 3,
    "local": 2,
    "remote": 1
  }
}
```

### Example 4: Create Worktree in Specific Repository
```bash
curl -X POST http://localhost:8000/worktree/create \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/tmp/feature-worktree",
    "branch": "feature/new",
    "create_branch": true,
    "repo_name": "agent-cli-orchestrator"
  }'
```

## Migration Guide

If you're upgrading from the single-repository version:

### Step 1: Backup Current Config
```bash
cp config.yaml config.yaml.backup
```

### Step 2: Update config.yaml
Replace:
```yaml
repository:
  name: "my-repo"
  default_branch: "main"
```

With:
```yaml
repositories:
  - name: "my-repo"
    path: "."
    default: true
    worktrees_path: "./worktrees"
```

### Step 3: Add Additional Repositories (Optional)
```yaml
repositories:
  - name: "my-repo"
    path: "."
    default: true
    worktrees_path: "./worktrees"
  - name: "other-repo"
    path: "/path/to/other/repo"
    worktrees_path: "/path/to/other/repo.worktrees"
```

### Step 4: Restart Server
```bash
# If using uvicorn directly
pkill uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# If using Docker
docker-compose restart
```

### Step 5: Test
```bash
# Verify configuration
curl http://localhost:8000/repos

# Test default repository
curl http://localhost:8000/repo

# Test specific repository (if configured)
curl http://localhost:8000/repo?repo_name=other-repo
```

## Backward Compatibility

All existing API calls without `repo_name` parameter will use the default repository, ensuring backward compatibility with existing clients.

## Error Handling

### Repository Not Found
```bash
curl "http://localhost:8000/repo?repo_name=nonexistent"
```

**Response (404):**
```json
{
  "detail": "Repository 'nonexistent' not found in configuration"
}
```

### No Default Repository
If no repository is marked as default and no `repo_name` is provided:

**Response (500):**
```json
{
  "detail": "No default repository configured"
}
```

## Best Practices

1. **Always specify a default repository** - Mark one repository with `default: true`
2. **Use absolute paths for clarity** - While relative paths work, absolute paths are more explicit
3. **Enable full output for debugging** - Use `show_full_output: true` when troubleshooting
4. **Review log files regularly** - Check `logs/copilot/` for complete execution history
5. **Test repository switching** - Verify `repo_name` parameter works before production use

## See Also

- [docs/planning/implementation-summary.md](docs/planning/implementation-summary.md) - Detailed implementation notes
- [docs/planning/implementation-guide.md](docs/planning/implementation-guide.md) - Step-by-step implementation guide
- [API.md](API.md) - Complete API documentation
- [README.md](README.md) - Main project documentation
