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
    "GET /worktrees": "List all worktrees",
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
- `500 Internal Server Error`: Git operation failed

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
  "output": {
    // Copilot CLI JSON output
  },
  "prompt": "How do I create a Python function to reverse a string?"
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

Currently, the API does not require authentication. In production environments, you should implement:
- API key authentication
- OAuth 2.0
- JWT tokens
- Rate limiting

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

# Execute a Copilot prompt
response = requests.post(
    'http://localhost:8000/prompt',
    json={'prompt': 'How to read a CSV file in Python?'}
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

## WebSocket Support (Future)

WebSocket support for real-time updates is planned for future releases. This will enable:
- Live progress updates for long-running operations
- Real-time notification of repository changes
- Streaming responses from Copilot CLI

---

## Versioning

The current API version is `0.1.0`. Future versions will maintain backward compatibility when possible, and breaking changes will be introduced in new major versions.