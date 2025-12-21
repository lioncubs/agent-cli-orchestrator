# Reusable Skills for Agent CLI Orchestrator

This file contains reusable skills and code patterns for common tasks in the project.

## Skill: CLI Wrapper Implementation

**Purpose**: Create a wrapper for executing external CLI commands

**Pattern**:
```python
import subprocess
import asyncio
import json
from typing import Dict, Any, Optional

class CLIWrapper:
    """Base class for CLI tool wrappers."""
    
    def __init__(self, cli_name: str, timeout: int = 300):
        self.cli_name = cli_name
        self.timeout = timeout
    
    def _validate_cli_available(self) -> bool:
        """Check if CLI tool is installed."""
        import shutil
        try:
            return shutil.which(self.cli_name) is not None
        except Exception:
            return False
    
    def execute(self, args: list) -> Dict[str, Any]:
        """Execute CLI command synchronously."""
        if not self._validate_cli_available():
            return {
                "status": "error",
                "message": f"{self.cli_name} is not installed"
            }
        
        try:
            result = subprocess.run(
                [self.cli_name] + args,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "output": result.stdout,
                    "command": ' '.join([self.cli_name] + args)
                }
            else:
                return {
                    "status": "error",
                    "message": result.stderr,
                    "exit_code": result.returncode
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"Command timed out after {self.timeout} seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def execute_async(self, args: list) -> Dict[str, Any]:
        """Execute CLI command asynchronously."""
        if not self._validate_cli_available():
            return {
                "status": "error",
                "message": f"{self.cli_name} is not installed"
            }
        
        try:
            process = await asyncio.create_subprocess_exec(
                self.cli_name, *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "status": "error",
                    "message": f"Command timed out after {self.timeout} seconds"
                }
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "output": stdout.decode(),
                    "command": ' '.join([self.cli_name] + args)
                }
            else:
                return {
                    "status": "error",
                    "message": stderr.decode(),
                    "exit_code": process.returncode
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
```

**Usage**:
```python
# Create wrapper instance
aws_cli = CLIWrapper('aws', timeout=120)

# Sync execution
result = aws_cli.execute(['s3', 'ls'])

# Async execution
result = await aws_cli.execute_async(['s3', 'ls'])
```

## Skill: API Endpoint Pattern

**Purpose**: Standardized pattern for creating API endpoints

**Pattern**:
```python
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

class RequestModel(BaseModel):
    """Request model with validation."""
    param1: str
    param2: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class ResponseModel(BaseModel):
    """Response model."""
    status: str
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

@app.post("/endpoint", response_model=ResponseModel)
async def endpoint_handler(request: RequestModel):
    """
    Endpoint description.
    
    Args:
        request: Request parameters
    
    Returns:
        Response with status and data
    
    Raises:
        HTTPException: On validation or processing errors
    """
    try:
        # Validate input
        if not request.param1:
            raise HTTPException(
                status_code=400,
                detail="param1 is required"
            )
        
        # Execute operation
        result = await some_operation(request.param1, request.options)
        
        # Check for operation errors
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("message")
            )
        
        # Return success response
        return ResponseModel(
            status="success",
            data=result,
            message="Operation completed successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
```

## Skill: Configuration Management

**Purpose**: Add new configuration options

**Pattern**:

1. **Update config.yaml**:
```yaml
new_feature:
  enabled: true
  timeout: 300
  option1: "value1"
  option2: 100
```

2. **Update config_loader.py**:
```python
@property
def new_feature_enabled(self) -> bool:
    """Check if new feature is enabled."""
    return self.get('new_feature.enabled', False)

@property
def new_feature_timeout(self) -> int:
    """Get new feature timeout."""
    return self.get('new_feature.timeout', 300)

@property
def new_feature_option1(self) -> str:
    """Get new feature option1."""
    return self.get('new_feature.option1', 'default')
```

3. **Usage**:
```python
from config_loader import config

if config.new_feature_enabled:
    result = execute_with_timeout(config.new_feature_timeout)
```

## Skill: Error Response Formatting

**Purpose**: Standardized error response format

**Pattern**:
```python
def format_error(message: str, code: Optional[str] = None) -> Dict[str, Any]:
    """
    Format error response.
    
    Args:
        message: Error message
        code: Optional error code
    
    Returns:
        Formatted error dictionary
    """
    error = {
        "status": "error",
        "message": message
    }
    if code:
        error["code"] = code
    return error

def format_success(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Format success response.
    
    Args:
        data: Response data
        message: Optional success message
    
    Returns:
        Formatted success dictionary
    """
    response = {
        "status": "success",
        "data": data
    }
    if message:
        response["message"] = message
    return response
```

**Usage**:
```python
# Error case
if not valid:
    return format_error("Invalid input", code="INVALID_INPUT")

# Success case
return format_success({"result": value}, message="Operation completed")
```

## Skill: Input Validation

**Purpose**: Validate and sanitize user inputs

**Pattern**:
```python
import re
from typing import Optional

def validate_branch_name(branch: str) -> Optional[str]:
    """
    Validate Git branch name.
    
    Args:
        branch: Branch name to validate
    
    Returns:
        Error message if invalid, None if valid
    """
    if not branch:
        return "Branch name is required"
    
    if len(branch) > 255:
        return "Branch name too long"
    
    # Check for invalid characters
    invalid_chars = ['~', '^', ':', '?', '*', '[', '\\', ' ']
    for char in invalid_chars:
        if char in branch:
            return f"Branch name contains invalid character: {char}"
    
    # Check for invalid patterns
    if branch.startswith('.') or branch.endswith('.'):
        return "Branch name cannot start or end with '.'"
    
    if '..' in branch:
        return "Branch name cannot contain '..'"
    
    return None

def sanitize_path(path: str) -> str:
    """
    Sanitize file path.
    
    Args:
        path: Path to sanitize
    
    Returns:
        Sanitized path
    """
    import os
    from pathlib import Path
    
    # Remove null bytes
    path = path.replace('\0', '')
    
    # Remove leading/trailing whitespace
    path = path.strip()
    
    # Normalize path (handles separators cross-platform)
    path = os.path.normpath(path)
    
    return path

def validate_command_args(args: list) -> Optional[str]:
    """
    Validate command arguments for safety.
    
    Args:
        args: List of command arguments
    
    Returns:
        Error message if unsafe, None if safe
    """
    dangerous_patterns = [
        ';', '|', '&', '$', '`', '>', '<', '\n',
        '(', ')', '{', '}', '*', '?', '[', ']'
    ]
    
    for arg in args:
        for pattern in dangerous_patterns:
            if pattern in str(arg):
                return f"Argument contains dangerous pattern: {pattern}"
    
    return None
```

**Usage**:
```python
# Validate branch name
error = validate_branch_name(request.branch)
if error:
    raise HTTPException(status_code=400, detail=error)

# Sanitize path
safe_path = sanitize_path(user_input_path)

# Validate command args
error = validate_command_args(command_args)
if error:
    raise HTTPException(status_code=400, detail=error)
```

## Skill: Async Timeout Handling

**Purpose**: Handle async operations with timeout

**Pattern**:
```python
import asyncio
from typing import Any, Callable

async def execute_with_timeout(
    operation: Callable,
    timeout: int,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute async operation with timeout.
    
    Args:
        operation: Async function to execute
        timeout: Timeout in seconds
        *args: Positional arguments for operation
        **kwargs: Keyword arguments for operation
    
    Returns:
        Operation result or timeout error
    """
    try:
        result = await asyncio.wait_for(
            operation(*args, **kwargs),
            timeout=timeout
        )
        return {
            "status": "success",
            "result": result
        }
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": f"Operation timed out after {timeout} seconds"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
```

**Usage**:
```python
async def long_operation():
    await asyncio.sleep(5)
    return "completed"

result = await execute_with_timeout(long_operation, timeout=10)
```

## Skill: JSON Output Parsing

**Purpose**: Parse and validate JSON output from CLI tools

**Pattern**:
```python
import json
from typing import Any, Dict, Optional

def parse_json_output(output: str, strict: bool = False) -> Dict[str, Any]:
    """
    Parse JSON output with fallback.
    
    Args:
        output: String output to parse
        strict: If True, raise error on parse failure
    
    Returns:
        Parsed JSON or error dict
    """
    try:
        return {
            "status": "success",
            "data": json.loads(output),
            "format": "json"
        }
    except json.JSONDecodeError as e:
        if strict:
            return {
                "status": "error",
                "message": f"Invalid JSON: {str(e)}"
            }
        else:
            # Return raw output if not strict
            return {
                "status": "success",
                "data": output,
                "format": "raw",
                "warning": "Output is not valid JSON"
            }

def extract_json_from_output(output: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from mixed output.
    
    Args:
        output: Output that may contain JSON
    
    Returns:
        Extracted JSON or None
    """
    # Try to find JSON in output
    start = output.find('{')
    end = output.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(output[start:end+1])
        except json.JSONDecodeError:
            pass
    
    return None
```

**Usage**:
```python
# Parse strict JSON
result = parse_json_output(cli_output, strict=True)

# Parse with fallback
result = parse_json_output(cli_output, strict=False)

# Extract JSON from mixed output
json_data = extract_json_from_output(mixed_output)
```

## Skill: Logging Pattern

**Purpose**: Standardized logging for operations

**Pattern**:
```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_operation(operation: str, **kwargs):
    """
    Log operation with context.
    
    Args:
        operation: Operation name
        **kwargs: Additional context
    """
    context = {
        "operation": operation,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    logger.info(f"Operation: {operation}", extra=context)

def log_error(operation: str, error: Exception, **kwargs):
    """
    Log error with context.
    
    Args:
        operation: Operation that failed
        error: Exception that occurred
        **kwargs: Additional context
    """
    context = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    logger.error(f"Operation failed: {operation}", extra=context, exc_info=True)
```

**Usage**:
```python
# Log successful operation
log_operation("execute_cli", command="aws s3 ls", duration=1.5)

# Log error
try:
    result = execute_operation()
except Exception as e:
    log_error("execute_operation", e, user_id="123", request_id="abc")
    raise
```