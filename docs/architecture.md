# Agent CLI Orchestrator - Architecture

## System Overview

The Agent CLI Orchestrator is a web-based system that provides a unified interface for executing commands across multiple CLI tools, with initial support for GitHub Copilot CLI and Git operations.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser          │  cURL/HTTP Client  │  Future CLI Client  │
└────────────┬──────────┴────────────────────┴─────────────────────┘
             │
             │ HTTP/HTTPS
             │
┌────────────▼─────────────────────────────────────────────────────┐
│                      API Gateway Layer                            │
├──────────────────────────────────────────────────────────────────┤
│                      FastAPI Application                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Routes & Endpoints                                        │  │
│  │  - Repository endpoints                                    │  │
│  │  - Branch management endpoints                             │  │
│  │  - Worktree management endpoints                           │  │
│  │  - Copilot CLI endpoints                                   │  │
│  │  - Web UI endpoint                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Middleware                                                │  │
│  │  - Request validation (Pydantic)                           │  │
│  │  - Error handling                                          │  │
│  │  - Logging                                                 │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────┬─────────────────────────────────────────────────────┘
             │
             │ Internal Calls
             │
┌────────────▼─────────────────────────────────────────────────────┐
│                     Business Logic Layer                          │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Git Operations   │  │  Copilot CLI     │  │ Future CLIs   │  │
│  │                  │  │  Integration     │  │ (AWS, Azure)  │  │
│  │ - Branch ops     │  │                  │  │               │  │
│  │ - Worktree ops   │  │ - Sync exec      │  │               │  │
│  │ - Repo info      │  │ - Async exec     │  │               │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘  │
│           │                     │                     │           │
└───────────┼─────────────────────┼─────────────────────┼───────────┘
            │                     │                     │
            │                     │                     │
┌───────────▼─────────────────────▼─────────────────────▼───────────┐
│                    Infrastructure Layer                            │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Subprocess Mgmt  │  │  Configuration   │  │  File System  │  │
│  │                  │  │                  │  │               │  │
│  │ - Process spawn  │  │ - YAML loader    │  │ - Git repos   │  │
│  │ - Timeout mgmt   │  │ - Settings       │  │ - Worktrees   │  │
│  │ - Output capture │  │ - Validation     │  │               │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Client Layer

#### Web Browser
- **Purpose**: Primary user interface
- **Technology**: HTML5, CSS3, Vanilla JavaScript
- **Features**: 
  - Interactive forms for all operations
  - Real-time API communication
  - Response visualization
  - Error display

#### HTTP Clients
- **Purpose**: Programmatic API access
- **Examples**: cURL, Python requests, JavaScript fetch
- **Use Cases**: Automation, integration, testing

### 2. API Gateway Layer

#### FastAPI Application
- **Framework**: FastAPI 0.104.1
- **Features**:
  - Automatic OpenAPI documentation
  - Async request handling
  - Type validation via Pydantic
  - Error handling middleware

#### Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | API information |
| GET | `/repo` | Repository details |
| GET | `/branch/current` | Current branch |
| POST | `/branch/select` | Switch branch |
| GET | `/worktrees` | List worktrees |
| POST | `/worktree/create` | Create worktree |
| POST | `/prompt` | Sync Copilot prompt |
| POST | `/prompt/async` | Async Copilot prompt |
| GET | `/ui` | Web interface |
| GET | `/docs` | API documentation |

### 3. Business Logic Layer

#### Git Operations Module (`git_operations.py`)
**Responsibilities**:
- Execute Git commands via subprocess
- Parse Git output
- Manage branches and worktrees
- Extract repository information

**Key Methods**:
```python
get_current_branch() -> str
switch_branch(branch: str) -> dict
list_worktrees() -> list
create_worktree(path: str, branch: str, create_branch: bool) -> dict
get_repository_name() -> str
```

#### Copilot CLI Module (`copilot_cli.py`)
**Responsibilities**:
- Execute Copilot CLI commands
- Parse JSON output
- Handle timeouts and errors
- Support sync and async execution

**Key Methods**:
```python
execute_prompt(prompt: str, options: dict) -> dict
execute_prompt_async(prompt: str, options: dict) -> dict
_validate_cli_available() -> bool
```

#### Configuration Module (`config_loader.py`)
**Responsibilities**:
- Load YAML configuration
- Provide configuration access
- Support dot notation
- Supply default values

**Key Properties**:
```python
repository_name: str
default_branch: str
server_host: str
server_port: int
copilot_enabled: bool
copilot_timeout: int
worktrees_base_path: str
```

### 4. Infrastructure Layer

#### Subprocess Management
- **Library**: Python `subprocess` module
- **Features**:
  - Timeout control
  - Output capture (stdout/stderr)
  - Return code handling
  - Async execution via `asyncio`

#### Configuration Storage
- **Format**: YAML
- **File**: `config.yaml`
- **Validation**: Runtime type checking
- **Defaults**: Built into config loader

#### File System
- **Git Repository**: Working directory
- **Worktrees**: Configurable base path
- **Logs**: stdout/stderr (future: file-based)

## Data Flow

### Example: Execute Copilot Prompt (Async)

```
1. Client sends POST request to /prompt/async
   ↓
2. FastAPI validates request (Pydantic model)
   ↓
3. Route handler calls copilot_cli.execute_prompt_async()
   ↓
4. Copilot CLI validates CLI availability
   ↓
5. Create async subprocess with timeout
   ↓
6. Wait for command completion (with timeout)
   ↓
7. Parse JSON output (or return raw)
   ↓
8. Format response dict
   ↓
9. FastAPI serializes to JSON
   ↓
10. Client receives response
```

### Example: Create Worktree

```
1. Client sends POST request to /worktree/create
   ↓
2. FastAPI validates request body
   ↓
3. Route handler calls git_ops.create_worktree()
   ↓
4. Build git worktree add command
   ↓
5. Execute subprocess synchronously
   ↓
6. Check return code
   ↓
7. Format success/error response
   ↓
8. Return to client
```

## Configuration Management

### Configuration Hierarchy
1. **Default values** (in code)
2. **config.yaml** (file-based)
3. **Environment variables** (future)
4. **Runtime overrides** (future)

### Configuration Schema
```yaml
repository:
  name: string
  default_branch: string

server:
  host: string (IP address)
  port: integer (1-65535)

copilot:
  enabled: boolean
  timeout: integer (seconds)

worktrees:
  base_path: string (path)
```

## Security Architecture

### Current Security Measures
1. **Input Validation**: Pydantic models
2. **Subprocess Safety**: List arguments (not shell)
3. **Timeout Protection**: Prevents hung processes
4. **Error Sanitization**: No sensitive data in errors

### Future Security Enhancements
1. **Authentication**: JWT/API Key/OAuth
2. **Authorization**: Role-based access control
3. **Rate Limiting**: Prevent abuse
4. **Input Sanitization**: Advanced validation
5. **Audit Logging**: Track all operations
6. **HTTPS**: TLS encryption
7. **CORS**: Controlled cross-origin access

## Scalability Considerations

### Current Limitations
- Single-process server
- No horizontal scaling
- In-memory only
- Synchronous Git operations

### Future Scalability
1. **Horizontal Scaling**: Multiple server instances
2. **Load Balancing**: Distribute requests
3. **Caching**: Redis for shared state
4. **Queue System**: Background job processing
5. **Database**: Persistent storage
6. **WebSocket**: Long-lived connections

## Error Handling Strategy

### Error Response Format
```json
{
  "status": "error",
  "message": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Error Categories
1. **Validation Errors** (400): Invalid input
2. **Not Found** (404): Resource doesn't exist
3. **Server Errors** (500): Internal failures
4. **Timeout Errors**: Operation exceeded limit
5. **CLI Errors**: External tool failures

### Error Propagation
```
External Error (CLI/Git)
  ↓
Business Logic catches and formats
  ↓
Route handler receives formatted error
  ↓
HTTPException raised
  ↓
FastAPI error handler
  ↓
JSON error response to client
```

## Logging Strategy

### Current Logging
- **Level**: INFO
- **Output**: Console (stdout)
- **Format**: Text

### Future Logging
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Output**: File + Console + Aggregation service
- **Format**: Structured JSON
- **Rotation**: Size/time-based
- **Retention**: Configurable

### Logged Events
- API requests/responses
- CLI executions
- Git operations
- Errors and exceptions
- Performance metrics

## Deployment Architecture

### Development
```
Local Machine
  ↓
Python 3.11+
  ↓
Virtual Environment
  ↓
FastAPI + Uvicorn
  ↓
Port 8000
```

### Docker
```
Docker Host
  ↓
Docker Image (Python + Git + GitHub CLI)
  ↓
Container
  ↓
Port 8000 (exposed)
```

### Future Production
```
Load Balancer (HTTPS)
  ↓
Multiple API Servers
  ↓
Redis Cache (shared state)
  ↓
PostgreSQL (persistent data)
  ↓
Background Workers (job queue)
```

## Extension Points

### Adding New CLI Tool
1. Create module: `{tool}_cli.py`
2. Implement class with sync/async methods
3. Add configuration in `config.yaml`
4. Create endpoints in `main.py`
5. Update web UI
6. Document in `API.md`

### Adding New Endpoint
1. Define Pydantic models
2. Implement handler function
3. Add route decorator
4. Add error handling
5. Update documentation

### Adding Middleware
1. Create middleware function
2. Register with FastAPI app
3. Handle request/response
4. Update documentation

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn 0.24.0
- **Validation**: Pydantic 2.5.0
- **Config**: PyYAML 6.0.1
- **Git**: GitPython 3.1.40

### Frontend
- **HTML5**: Structure
- **CSS3**: Styling (gradients, flexbox, grid)
- **JavaScript**: Vanilla JS (async/await, fetch API)

### Infrastructure
- **Container**: Docker
- **Orchestration**: Docker Compose
- **CLI Tools**: Git, GitHub CLI

### Development
- **Package Manager**: pip
- **Version Control**: Git
- **Documentation**: Markdown

## Performance Characteristics

### Current Performance
- **API Response Time**: < 100ms (simple endpoints)
- **CLI Execution**: Variable (depends on command)
- **Git Operations**: < 500ms (local)
- **Concurrent Requests**: ~100 (single process)

### Performance Goals (Future)
- **API Response Time**: < 50ms (p95)
- **Concurrent Requests**: > 1000
- **Cache Hit Rate**: > 80%
- **Error Rate**: < 1%

## Monitoring & Observability (Future)

### Metrics
- Request count/rate
- Response times (p50, p95, p99)
- Error rates
- CLI execution times
- Resource usage (CPU, memory)

### Health Checks
- API availability
- CLI tool availability
- Git repository access
- Configuration validity

### Alerts
- High error rate
- Slow response times
- Resource exhaustion
- CLI failures

---

**Document Version**: 1.0
**Last Updated**: December 21, 2024
**Status**: Phase 1 Architecture