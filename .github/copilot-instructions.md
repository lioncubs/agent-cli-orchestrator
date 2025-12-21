# GitHub Copilot Instructions for Agent CLI Orchestrator

## Project Overview
This is a multi-CLI orchestration system that provides a unified HTTP API and web interface for executing commands across different CLI tools, starting with GitHub Copilot CLI integration.

## Core Architecture
- **FastAPI Backend**: RESTful API server with async support
- **Subprocess Management**: Execute CLI commands with timeout and error handling
- **Git Integration**: Branch and worktree management
- **Configuration-driven**: YAML-based settings for flexibility

## Code Style and Conventions

### Python Style
- Follow PEP 8 conventions
- Use type hints for all function parameters and return values
- Use descriptive variable names (e.g., `worktree_path` not `wt_path`)
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

### Documentation
- Add docstrings to all classes and public methods
- Use Google-style docstrings format
- Include examples in docstrings for complex functions
- Keep comments concise and meaningful

### Error Handling
- Always use try-except blocks for external operations (subprocess, file I/O, Git commands)
- Return consistent error response format: `{"status": "error", "message": "..."}`
- Log errors with appropriate context
- Never expose sensitive information in error messages

### API Design
- Use RESTful conventions: GET for retrieval, POST for mutations
- Return JSON for all API responses
- Include status codes in responses
- Use Pydantic models for request/response validation

## File Organization
```
.
├── main.py              # FastAPI application and routes
├── config_loader.py     # Configuration management
├── git_operations.py    # Git-related operations
├── copilot_cli.py      # Copilot CLI wrapper
├── config.yaml         # Application configuration
└── docs/               # Documentation
```

## Key Patterns

### CLI Wrapper Pattern
When adding new CLI integrations:
1. Create a dedicated module (e.g., `aws_cli.py`)
2. Implement both sync and async execution methods
3. Parse output to structured format (preferably JSON)
4. Handle timeouts using configurable values
5. Validate CLI availability before execution

Example:
```python
class NewCLI:
    def __init__(self):
        self.timeout = config.new_cli_timeout
    
    def _validate_cli_available(self) -> bool:
        # Check if CLI is installed
        pass
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        # Sync execution
        pass
    
    async def execute_command_async(self, command: str) -> Dict[str, Any]:
        # Async execution
        pass
```

### Configuration Pattern
- Add new settings to `config.yaml`
- Create properties in `Config` class for easy access
- Use sensible defaults
- Document configuration options

### API Endpoint Pattern
```python
@app.post("/endpoint")
async def endpoint_name(request: RequestModel):
    """
    Brief description.
    
    Args:
        request: Description of request model
    
    Returns:
        Description of response
    """
    try:
        result = await operation()
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing Guidelines
- Test all API endpoints with various inputs
- Mock subprocess calls in unit tests
- Test error handling paths
- Verify timeout behavior
- Test both sync and async code paths

## Security Considerations
- Never commit secrets or API keys
- Validate all user inputs
- Sanitize command arguments to prevent injection
- Use subprocess with list arguments, not shell=True
- Implement rate limiting for production

## Common Tasks

### Adding a New CLI Tool
1. Create `{tool}_cli.py` module
2. Add configuration to `config.yaml`
3. Update `config_loader.py` with new properties
4. Create API endpoints in `main.py`
5. Update web UI to support new tool
6. Document in `API.md` and `README.md`

### Adding a New Endpoint
1. Define Pydantic request/response models
2. Implement handler function with proper error handling
3. Add route decorator with appropriate HTTP method
4. Test with curl or web UI
5. Update API documentation

### Modifying Git Operations
- Always check operation success before returning
- Provide clear error messages
- Support both absolute and relative paths
- Consider worktree context

## Best Practices
- Keep async functions truly async (use asyncio, not blocking calls)
- Use context managers for resource management
- Implement proper cleanup in error cases
- Log important operations for debugging
- Keep configuration separate from code
- Version all API changes
- Maintain backward compatibility when possible

## Dependencies
- Prefer standard library when possible
- Use well-maintained packages
- Pin exact versions in requirements.txt
- Document why each dependency is needed

## UI Development
- Keep UI embedded in main.py for simplicity
- Use vanilla JavaScript (no framework dependencies)
- Ensure responsive design
- Provide clear error messages to users
- Show loading states for async operations

## Git Workflow
- Use feature branches for new functionality
- Keep commits focused and atomic
- Write clear commit messages
- Test before committing
- Update documentation with code changes

## Future Considerations
- WebSocket support for real-time updates
- Authentication/authorization system
- Job queue for long-running operations
- Metrics and monitoring
- Multi-tenancy support
- CLI plugin system