# Agent CLI Orchestrator - Useful Prompts

This file contains common prompts and examples for working with the Agent CLI Orchestrator project.

## Development Prompts

### Adding New CLI Integration
```
Add support for [CLI_NAME] to the orchestrator:
- Create a new module [cli_name]_cli.py
- Implement sync and async execution methods
- Add configuration options to config.yaml
- Create API endpoints in main.py
- Update the web UI to support the new CLI
- Add documentation and examples
```

### API Endpoint Creation
```
Create a new API endpoint that:
- Route: [METHOD] /[path]
- Purpose: [description]
- Request: [JSON schema]
- Response: [JSON schema]
- Error handling: [cases to handle]
```

### Bug Investigation
```
Investigate and fix the following issue:
- Description: [what's happening]
- Expected behavior: [what should happen]
- Steps to reproduce: [how to trigger]
- Error messages: [any errors]
- Affected files: [which files might be involved]
```

### Performance Optimization
```
Optimize the performance of [feature/endpoint]:
- Current behavior: [description]
- Performance issue: [what's slow]
- Expected improvement: [target metrics]
- Consider: caching, async operations, database queries
```

### Testing
```
Create comprehensive tests for [module/feature]:
- Unit tests for core logic
- Integration tests for API endpoints
- Mock external dependencies
- Test error handling
- Test edge cases
```

## Copilot CLI Integration Prompts

### Execute Basic Prompt
```python
# POST /prompt
{
  "prompt": "How do I implement error handling in Python?",
  "options": {}
}
```

### Execute with Context
```python
# POST /prompt
{
  "prompt": "Review this code for security issues",
  "options": {
    "branch": "feature/security-audit",
    "worktree": "./worktrees/security"
  }
}
```

### Async Long-Running Prompt
```python
# POST /prompt/async
{
  "prompt": "Generate comprehensive API documentation for all endpoints",
  "options": {}
}
```

## Git Operations Prompts

### Create Worktree for Feature
```python
# POST /worktree/create
{
  "path": "./worktrees/feature-new-cli",
  "branch": "feature/new-cli-support",
  "create_branch": true
}
```

### Switch Branch
```python
# POST /branch/select
{
  "branch": "develop"
}
```

## Configuration Prompts

### Add New Configuration Section
```
Add configuration support for [feature]:
- Add section to config.yaml
- Create properties in Config class
- Document the new options
- Provide sensible defaults
- Add validation if needed
```

### Modify Existing Configuration
```
Update configuration for [setting]:
- Current: [current value/structure]
- New: [desired value/structure]
- Reason: [why the change is needed]
- Impact: [what will be affected]
```

## Documentation Prompts

### Update README
```
Update README.md to include:
- New feature: [description]
- Installation steps: [if changed]
- Usage examples: [code samples]
- Configuration: [new options]
```

### API Documentation
```
Document the following API endpoint in API.md:
- Endpoint: [METHOD] /[path]
- Description: [what it does]
- Parameters: [request schema]
- Response: [response schema]
- Examples: [curl, Python, JavaScript]
- Error codes: [possible errors]
```

## Docker Prompts

### Update Dockerfile
```
Modify Dockerfile to:
- Add [new dependency]
- Change base image to [image]
- Optimize build layers
- Add health check
- Reduce image size
```

### Docker Compose Changes
```
Update docker-compose.yml to:
- Add new service: [service name]
- Configure networking: [requirements]
- Add volume mounts: [paths]
- Set environment variables: [variables]
```

## Troubleshooting Prompts

### Debug Subprocess Execution
```
Debug subprocess execution issues:
- Command: [the command being run]
- Error: [error message]
- Expected output: [what should happen]
- Check: timeout, PATH, permissions, command format
```

### Fix Import Errors
```
Resolve import errors:
- Error message: [the error]
- Missing module: [module name]
- Check: requirements.txt, virtual environment, Python path
```

### Git Operation Failures
```
Fix Git operation failures:
- Operation: [branch/worktree operation]
- Error: [Git error message]
- Repository state: [current state]
- Desired state: [target state]
```

## Code Review Prompts

### Security Review
```
Review the code for security vulnerabilities:
- Check for command injection risks
- Verify input validation
- Check for exposed secrets
- Review error message content
- Validate subprocess usage
```

### Code Quality Review
```
Review code quality:
- Check for PEP 8 compliance
- Verify type hints usage
- Review error handling
- Check for code duplication
- Assess function complexity
```

## Refactoring Prompts

### Extract Common Logic
```
Refactor to extract common logic:
- Duplicate code in: [files/functions]
- Create utility function: [name]
- Location: [where to put it]
- Update callers: [which functions]
```

### Improve Error Handling
```
Improve error handling in [module]:
- Add try-except blocks where needed
- Standardize error response format
- Add logging for errors
- Improve error messages
- Handle edge cases
```

## Feature Enhancement Prompts

### Add Authentication
```
Add authentication to the API:
- Method: [JWT/API Key/OAuth]
- Endpoints to protect: [list]
- Configuration: [auth settings]
- Documentation: [update docs]
```

### Implement Caching
```
Add caching for [feature]:
- Cache type: [in-memory/Redis/file]
- Cache key: [what to cache on]
- TTL: [time to live]
- Invalidation: [when to clear]
```

### WebSocket Support
```
Add WebSocket support for real-time updates:
- Events to stream: [event types]
- Connection handling: [authentication, errors]
- Client library: [JavaScript example]
- Documentation: [usage guide]
```