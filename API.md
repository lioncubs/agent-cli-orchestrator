# API Documentation

This document provides detailed information about the Agent CLI Orchestrator API endpoints.

## Base URL

```
http://localhost:8000
```

## Endpoints

### Root

#### GET `/`

Get API information and available endpoints.

**Response:**
```json
{
  "message": "Welcome to Agent CLI Orchestrator",
  "version": "0.1.0",
  "endpoints": {
    "GET /repo": "Get repository name",
    "GET /branch/current": "Get current branch",
    "GET /branches": "List all branches (local and remote)",
    "GET /worktrees": "List all worktrees",
    "GET /sessions": "List active Copilot CLI sessions",
    "POST /branch/select": "Switch to a branch",
    "POST /worktree/create": "Create a new worktree",
    "POST /prompt": "Execute synchronous Copilot CLI prompt",
    "POST /prompt/async": "Execute asynchronous Copilot CLI prompt",
    "GET /ui": "Web interface for testing"
  }
}
```

---

### Repository Information

#### GET `/repo`

Get the repository name from Git configuration.

**Response:**
```json
{
  "repository": "agent-cli-orchestrator",
  "configured_name": "agent-cli-orchestrator"
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Failed to retrieve repository information

---

### Branch Management

#### GET `/branch/current`

Get the current Git branch.

**Response:**
```json
{
  "branch": "main"
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Failed to retrieve current branch

---

#### POST `/branch/select`

Switch to a different Git branch.

**Request Body:**
```json
{
  "branch": "feature/new-feature"
}
```

**Response:**
```json
{
  "status": "success",
  "branch": "feature/new-feature",
  "message": "Switched to branch 'feature/new-feature'"
}
```

**Status Codes:**
- `200 OK`: Branch switch successful
- `400 Bad Request`: Invalid branch name or branch doesn't exist
- `500 Internal Server Error`: Git command failed

---

#### GET `/branches`

List all Git branches (both local and remote).

**Response:**
```json
{
  "branches": [
    {
      "name": "main",
      "current": true,
      "type": "local"
    },
    {
      "name": "feature/test",
      "current": false,
      "type": "local"
    },
    {
      "name": "origin/main",
      "current": false,
      "type": "remote"
    },
    {
      "name": "origin/develop",
      "current": false,
      "type": "remote"
    }
  ],
  "count": {
    "total": 4,
    "local": 2,
    "remote": 2
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Failed to list branches

---

### Worktree Management

#### GET `/worktrees`

List all Git worktrees.

**Response:**
```json
{
  "worktrees": [
    {
      "path": "/path/to/repo",
      "branch": "main",
      "HEAD": "abc123..."
    },
    {
      "path": "/path/to/worktrees/feature",
      "branch": "feature/new-feature",
      "HEAD": "def456..."
    }
  ],
  "count": 2
}
```

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Failed to list worktrees

---

#### POST `/worktree/create`

Create a new Git worktree.

**Request Body:**
```json
{
  "path": "./worktrees/feature-branch",
  "branch": "feature/new-feature",
  "create_branch": false
}
```

**Parameters:**
- `path` (string, required): Path where the worktree will be created
- `branch` (string, required): Branch name for the worktree
- `create_branch` (boolean, optional): If true, creates a new branch; defaults to false

**Response:**
```json
{
  "status": "success",
  "path": "./worktrees/feature-branch",
  "branch": "feature/new-feature",
  "message": "Worktree created at './worktrees/feature-branch' for branch 'feature/new-feature'"
}
```

**Status Codes:**
- `200 OK`: Worktree created successfully
- `400 Bad Request`: Invalid parameters or worktree creation failed
- `500 Internal Server Error`: Git operation failed

---

### Copilot CLI Integration

#### POST `/prompt`

Execute a synchronous Copilot CLI prompt.

**Request Body:**
```json
{
  "prompt": "How do I create a Python function to reverse a string?",
  "options": {
    "branch": "main",
    "worktree": "./worktrees/feature",
    "session_id": "abc123-session-id"
  }
}
```

**Parameters:**
- `prompt` (string, required): The prompt to send to Copilot CLI
- `options` (object, optional): Additional options
  - `branch` (string, optional): Specify a Git branch context
  - `worktree` (string, optional): Specify a Git worktree for Copilot's background agent
  - `session_id` (string, optional): Continue an existing Copilot agent session

**Response (Success):**
```json
{
  "status": "success",
  "output": "The response from Copilot CLI",
  "prompt": "How do I create a Python function to reverse a string?",
  "full_stdout": "Complete stdout from copilot CLI execution",
  "full_stderr": "",
  "command": "copilot -p How do I create a Python function to reverse a string? --silent --allow-all-tools",
  "log_file": "logs/copilot/copilot_2025-12-21T19-22-30.737080.json"
}
```

**Response (CLI Not Available):**
```json
{
  "status": "error",
  "message": "Copilot CLI is not installed or not in PATH"
}
```

**Response (Timeout):**
```json
{
  "status": "error",
  "message": "Command timed out after 300 seconds"
}
```

**Status Codes:**
- `200 OK`: Prompt executed successfully
- `400 Bad Request`: Invalid prompt or execution error
- `500 Internal Server Error`: Unexpected error

---

#### POST `/prompt/async`

Execute an asynchronous Copilot CLI prompt.

**Request/Response:** Same as `/prompt` endpoint, but runs asynchronously.

This endpoint is useful for long-running prompts that may take significant time to process.

**Supported options:** `branch`, `worktree`, `session_id` (same as `/prompt` endpoint)

---

#### POST `/prompt/stream`

Execute a Copilot CLI prompt with **real-time streaming output** using Server-Sent Events (SSE).

This endpoint provides line-by-line output as the Copilot CLI executes, allowing you to see what's happening in real-time instead of waiting for the entire command to complete.

**Request Body:**
```json
{
  "prompt": "what files are in this directory?",
  "repo_name": "lioncubs",  // optional
  "options": {}              // optional
}
```

**Response:** Server-Sent Events (SSE) stream with `Content-Type: text/event-stream`

Each event is a JSON object prefixed with `data: `:

```
data: {"type": "start", "timestamp": "2025-12-21T...", "command": "copilot -p ...", "cwd": "/path"}

data: {"type": "stdout", "data": "Files in directory:"}

data: {"type": "stdout", "data": "  main.py"}

data: {"type": "stderr", "data": "Warning: some warning message"}

data: {"type": "complete", "exit_code": 0, "timestamp": "2025-12-21T..."}
```

**Event Types:**

| Type | Description | Fields |
|------|-------------|--------|
| `start` | Command execution started | `timestamp`, `command`, `cwd` |
| `stdout` | Line from standard output | `data` (string) |
| `stderr` | Line from standard error | `data` (string) |
| `complete` | Command finished | `exit_code`, `timestamp` |
| `error` | Error occurred | `message` |

**Use Cases:**
- Interactive development and debugging
- Monitoring long-running commands
- Real-time progress visibility
- Teaching/demonstration purposes

**See also:** [STREAMING.md](STREAMING.md) for detailed documentation and examples.

**JavaScript Example:**
```javascript
const response = await fetch('/prompt/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({prompt: 'list files'})
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    // Parse SSE format and handle events
    console.log(chunk);
}
```

**Test Page:** Visit `/streaming-test` for an interactive demonstration.

---

### Activity Logs

#### GET `/logs`

Get recent activity logs from the orchestrator.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of log entries to return

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2025-12-21T19:22:30.737080",
      "action": "prompt_sync",
      "status": "success",
      "payload": {
        "prompt": "list files in current directory",
        "options": null
      },
      "result": {
        "status": "success"
      }
    }
  ],
  "count": 1
}
```

**Status Codes:**
- `200 OK`: Logs retrieved successfully
- `500 Internal Server Error`: Error retrieving logs

---

#### GET `/logs/copilot`

Get detailed Copilot CLI execution logs with full input/output.

This endpoint provides access to the complete execution logs stored in JSON files,
including the full prompt, command executed, stdout, stderr, and exit code.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of log files to return (default: 20)

**Response:**
```json
{
  "logs": [
    {
      "file": "copilot_2025-12-21T19-22-30.737080.json",
      "data": {
        "timestamp": "2025-12-21T19:22:30.737080",
        "type": "copilot_execute",
        "prompt": "list files in current directory",
        "options": null,
        "command": [
          "copilot",
          "-p",
          "list files in current directory",
          "--silent",
          "--allow-all-tools"
        ],
        "exit_code": 0,
        "stdout": "Complete output from Copilot CLI...",
        "stderr": ""
      }
    }
  ],
  "count": 1,
  "total_files": 4
}
```

**Status Codes:**
- `200 OK`: Logs retrieved successfully
- `500 Internal Server Error`: Error retrieving logs

**Notes:**
- Logs are stored in the directory specified by `copilot_log_dir` config (default: `logs/copilot/`)
- Each log file contains the complete execution details for one Copilot CLI invocation
- Logs are sorted by modification time (newest first)
- The `total_files` field indicates how many log files exist in total

---

### Web Interface

#### GET `/ui`

Serve the interactive web interface for testing all API features.

**Response:** HTML page with interactive forms for:
- Viewing repository information
- Executing Copilot CLI prompts (sync/async)
- Managing Git branches
- Managing Git worktrees

---

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common error status codes:
- `400 Bad Request`: Invalid input or operation failed due to client error
- `500 Internal Server Error`: Server-side error or unexpected exception

---

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- View all available endpoints
- See request/response schemas
- Test endpoints directly from the browser
- Download OpenAPI specification

---

## Authentication

**⚠️ CRITICAL SECURITY WARNING**

**This API currently has NO authentication by default.** Running without authentication is **ONLY acceptable** in a strictly trusted, localhost-only development environment.

### Security Risk

Without authentication, **anyone** with network access to the API can:
- Execute arbitrary prompts via Copilot CLI (potential data exfiltration)
- Switch Git branches in your repository
- Create or modify Git worktrees  
- Access repository information and metadata
- Trigger potentially expensive or long-running operations

### Default Configuration (Safe for Development)

The default `config.yaml` binds the server to `127.0.0.1` (localhost only), which restricts access to your local machine:

```yaml
server:
  host: "127.0.0.1"  # Localhost only - safe for development
  port: 8000
```

### Production Requirements

**Before** exposing this API on a network (setting `host: "0.0.0.0"` or deploying to production), you **MUST** implement:

#### Required Security Measures

1. **Authentication** - Choose at least one:
   - **API Key**: Add `X-API-Key` header validation
   - **JWT Tokens**: Implement `Authorization: Bearer <token>` header validation
   - **OAuth 2.0**: For user-based access control

2. **HTTPS/TLS** - Use a reverse proxy with SSL certificates:
   ```nginx
   # nginx example
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
       }
   }
   ```

3. **Rate Limiting** - Prevent abuse and DoS attacks

4. **Network Controls** - Implement at least one:
   - Firewall rules restricting source IPs
   - VPN requirement for API access
   - IP whitelisting

#### Example: API Key Authentication

Here's a minimal example of adding API key authentication to the FastAPI app:

```python
from fastapi import FastAPI, Header, HTTPException
from typing import Optional

API_KEY = "your-secret-api-key"  # Use environment variable in production

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

app = FastAPI(dependencies=[Depends(verify_api_key)])  # Apply globally
```

**Usage with authentication:**
```bash
curl -H "X-API-Key: your-secret-api-key" http://localhost:8000/repo
```

### Additional Recommendations

- **Audit Logging**: Log all API requests with timestamps and source IPs
- **Input Validation**: Already implemented, but review for your use case
- **Least Privilege**: Run the service with minimal system permissions
- **Regular Updates**: Keep all dependencies up to date
- **Security Monitoring**: Monitor for suspicious activity

### Network Exposure Warning

**DO NOT** set `server.host: "0.0.0.0"` without implementing the security measures above. If the server is accessible via Docker port mapping or cloud deployment, the same security requirements apply.

---

### Copilot CLI Sessions

#### GET `/sessions`

List active GitHub Copilot CLI agent sessions.

**Response:**
```json
{
  "status": "success",
  "sessions": [
    {
      "session_id": "abc123-session-id",
      "status": "active"
    },
    {
      "session_id": "def456-session-id",
      "status": "active"
    }
  ],
  "count": 2
}
```

**Empty Sessions Response:**
```json
{
  "status": "success",
  "sessions": [],
  "count": 0
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Copilot CLI not available or error listing sessions
- `500 Internal Server Error`: Unexpected error

**Notes:**
- Requires GitHub Copilot CLI to be installed and authenticated
- Sessions represent active agent conversations that can be continued
- Session IDs can be used with the `session_id` option in prompt endpoints

---

## Rate Limiting

No rate limiting is currently implemented. Consider adding rate limiting for production deployments to prevent abuse.

---

## CORS

Cross-Origin Resource Sharing (CORS) is not configured by default. If you need to access the API from a different origin, you'll need to configure CORS middleware in the FastAPI application.

---

## Examples

### Using cURL

**Get repository info:**
```bash
curl http://localhost:8000/repo
```

**Get current branch:**
```bash
curl http://localhost:8000/branch/current
```

**Switch branch:**
```bash
curl -X POST http://localhost:8000/branch/select \
  -H "Content-Type: application/json" \
  -d '{"branch": "develop"}'
```

**List worktrees:**
```bash
curl http://localhost:8000/worktrees
```

**List branches:**
```bash
curl http://localhost:8000/branches
```

**List active Copilot sessions:**
```bash
curl http://localhost:8000/sessions
```

**Create worktree:**
```bash
curl -X POST http://localhost:8000/worktree/create \
  -H "Content-Type: application/json" \
  -d '{
    "path": "./worktrees/feature-xyz",
    "branch": "feature/xyz",
    "create_branch": true
  }'
```

**Execute Copilot prompt:**
```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How do I implement a binary search in Python?"
  }'
```

### Using Python

```python
import requests

# Get repository info
response = requests.get('http://localhost:8000/repo')
print(response.json())

# List all branches
response = requests.get('http://localhost:8000/branches')
print(response.json())

# List active Copilot sessions
response = requests.get('http://localhost:8000/sessions')
print(response.json())

# Execute a Copilot prompt
response = requests.post(
    'http://localhost:8000/prompt',
    json={'prompt': 'How to read a CSV file in Python?'}
)
print(response.json())

# Continue an existing session
response = requests.post(
    'http://localhost:8000/prompt',
    json={
        'prompt': 'Can you add error handling to that code?',
        'options': {'session_id': 'abc123-session-id'}
    }
)
print(response.json())

# Create a worktree
response = requests.post(
    'http://localhost:8000/worktree/create',
    json={
        'path': './worktrees/feature-abc',
        'branch': 'feature/abc',
        'create_branch': True
    }
)
print(response.json())
```

### Using JavaScript

```javascript
// Get current branch
fetch('http://localhost:8000/branch/current')
  .then(response => response.json())
  .then(data => console.log(data));

// Execute async Copilot prompt
fetch('http://localhost:8000/prompt/async', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    prompt: 'Explain async/await in JavaScript'
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## Query and Research Operations

### Quick Query Execution

#### POST `/query`

Execute read-only query operations on a repository.

**Request Body:**
```json
{
  "repo_name": "test-repo",
  "operation": "read_file",
  "parameters": {
    "file_path": "src/main.py"
  },
  "user_id": "user123"
}
```

**Supported Operations:**
- `read_file`: Read file contents
- `list_files`: List files in a directory
- `search_code`: Search for code patterns
- `get_branch`: Get current branch information
- `list_branches`: List all branches

**Response:**
```json
{
  "status": "success",
  "result": {
    "file_path": "src/main.py",
    "content": "# File contents here...",
    "lines": 42,
    "size": 1024
  }
}
```

---

### Research Sessions

#### POST `/query/sessions/{session_id}/complete`

Complete a research session and generate a research artifact.

**Path Parameters:**
- `session_id` (UUID): The research session to complete

**Request Body:**
```json
{
  "summary": "Research completed successfully",
  "findings": [
    {
      "file": "src/auth.py",
      "lines": "45-67",
      "note": "Authentication logic needs updating",
      "code_snippet": "def authenticate(user):\n    ..."
    }
  ],
  "recommendations": [
    "Update authentication to use JWT",
    "Add rate limiting"
  ],
  "suggested_delegation_prompt": "Implement JWT authentication",
  "cleanup_worktree": true
}
```

**Response:**
```json
{
  "artifact": {
    "research_id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_name": "test-repo",
    "base_branch": "main",
    "base_commit": "abc123",
    "created_at": "2024-01-06T12:00:00Z",
    "user_id": "user123",
    "summary": "Research completed successfully",
    "findings": [...],
    "recommendations": [...],
    "conversation": [...],
    "suggested_delegation_prompt": "Implement JWT authentication",
    "relevant_files": ["src/auth.py"]
  },
  "message": "Research session completed successfully"
}
```

---

### Research Artifacts

#### GET `/query/research`

List all research artifacts with optional filters.

**Query Parameters:**
- `repo_name` (optional): Filter by repository
- `user_id` (optional): Filter by user
- `limit` (optional): Maximum results (1-100)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "artifacts": [
    {
      "research_id": "550e8400-e29b-41d4-a716-446655440000",
      "repo_name": "test-repo",
      "summary": "Authentication research",
      "created_at": "2024-01-06T12:00:00Z",
      ...
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

---

#### GET `/query/research/{research_id}`

Get a specific research artifact by ID.

**Path Parameters:**
- `research_id` (UUID): The research artifact ID

**Response:**
```json
{
  "artifact": {
    "research_id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_name": "test-repo",
    "base_branch": "main",
    "summary": "Research findings...",
    "findings": [...],
    "recommendations": [...],
    ...
  },
  "message": "Success"
}
```

---

#### POST `/query/research/{research_id}/delegate`

Create a delegation session from a research artifact.

**Path Parameters:**
- `research_id` (UUID): The research artifact ID

**Request Body:**
```json
{
  "user_id": "user456",
  "custom_prompt": "Optional custom delegation prompt"
}
```

**Response:**
```json
{
  "status": "success",
  "session_id": "660e8400-e29b-41d4-a716-446655440000",
  "research_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Delegation session created from research artifact"
}
```

---

#### DELETE `/query/research/{research_id}`

Delete a research artifact.

**Path Parameters:**
- `research_id` (UUID): The research artifact ID to delete

**Response:**
```json
{
  "success": true,
  "message": "Research artifact deleted successfully"
}
```

---

## Tool Policy and Permissions

The system enforces operation-level permissions based on session tiers:

### Operation Tiers

**Read-Only Tier:**
- Allows: read_file, list_files, search_code, get_branch, list_branches
- Denies: All write operations, worktree management, admin operations

**Standard Tier:**
- Allows: All read operations, write operations, worktree management
- Denies: Admin operations (force push, delete branch, delete session)

**Admin Tier:**
- Allows: All operations including force push, branch deletion, session deletion

### Setting Session Tier

Session tiers are automatically assigned based on session type:
- Query sessions → Read-Only tier
- Research sessions → Standard tier
- Delegation sessions → Standard tier

---

## WebSocket Support (Future)

WebSocket support for real-time updates is planned for future releases. This will enable:
- Live progress updates for long-running operations
- Real-time notification of repository changes
- Streaming responses from Copilot CLI

---

## Versioning

The current API version is `0.1.0`. Future versions will maintain backward compatibility when possible, and breaking changes will be introduced in new major versions.