# GitHub Copilot SDK Integration

This document describes the integration of the GitHub Copilot SDK into the Agent CLI Orchestrator.

## Overview

The orchestrator now uses the official **GitHub Copilot SDK** (Python) instead of making direct subprocess calls to the Copilot CLI. This provides better reliability, session management, and access to advanced SDK features.

## Architecture

```
API Request
     ↓
FastAPI Endpoint (main.py)
     ↓
Backend Selector (get_copilot_backend)
     ↓
┌─────────────┬──────────────┐
│  SDK Mode   │   CLI Mode   │
│ (copilot_sdk│ (copilot_cli │
│      .py)   │       .py)   │
└─────────────┴──────────────┘
     ↓              ↓
Copilot SDK    subprocess
     ↓              ↓
Copilot CLI ←──────┘
```

## Key Components

### 1. `copilot_sdk.py`
Main SDK wrapper that provides:
- **CopilotSDK class**: Wraps GitHub Copilot SDK with a compatible interface
- **Session management**: Leverages SDK's built-in session handling
- **Async execution**: Native async support via SDK
- **Streaming**: Real-time output streaming
- **Error handling**: Improved error recovery and reporting

### 2. `main.py` - Backend Selection
```python
def get_copilot_backend():
    """Get the appropriate Copilot backend (SDK or CLI)."""
    if config.copilot_use_sdk:
        return copilot_sdk
    else:
        return copilot_cli
```

This allows seamless switching between SDK and CLI modes via configuration.

### 3. Configuration (`config.yaml`)
```yaml
copilot:
  enabled: true
  timeout: 300
  use_sdk: true  # Toggle SDK vs CLI mode
  
  # SDK-specific settings
  sdk:
    model: "gpt-4o"  # Default model
    cli_path: null  # Auto-detect CLI path
    use_stdio: true  # Use stdio transport (recommended)
    log_level: "info"  # Logging level
```

## API Compatibility

All existing API endpoints remain unchanged:

### Execute Prompt (Sync)
```bash
POST /prompt
{
  "prompt": "What is 2+2?",
  "options": {
    "model": "gpt-4o",
    "session_id": "optional-session-id"
  }
}
```

### Execute Prompt (Async)
```bash
POST /prompt/async
{
  "prompt": "Write a Python function...",
  "options": {}
}
```

### Streaming
```bash
POST /prompt/stream
{
  "prompt": "Explain recursion",
  "options": {}
}
```

## SDK Features

### Session Management
The SDK provides built-in session management:

```python
# Create session with specific model
session_config = {
    "model": "gpt-4o",
    "system_message": {"mode": "append", "content": "Be concise"}
}

# Sessions are automatically managed by the SDK
session = await client.create_session(session_config)
```

### Tool Configuration
```python
# Specify available tools
options = {
    "available_tools": ["view", "edit", "bash"],
    "excluded_tools": ["web_search"]
}
```

### Model Selection
Supported models (via SDK):
- `gpt-4o` - GPT-4 Optimized
- `gpt-4.1` - GPT-4 Turbo
- `claude-3.5-sonnet` - Claude 3.5 Sonnet
- Other models supported by Copilot CLI

## Implementation Details

### Async Execution Flow

```python
async def execute_prompt_async(prompt: str, options: dict, cwd: str):
    # 1. Create and start client
    client = CopilotClient({"cwd": cwd})
    await client.start()
    
    # 2. Build session config
    session_config = build_session_config(options)
    
    # 3. Create session
    session = await client.create_session(session_config)
    
    # 4. Send prompt and wait for response
    response = await session.send_and_wait({"prompt": prompt})
    
    # 5. Extract result
    output = response.data.content
    
    # 6. Cleanup
    await session.destroy()
    await client.stop()
    
    return {"status": "success", "output": output}
```

### Streaming Implementation

The SDK provides event-based streaming:

```python
async def execute_prompt_streaming(prompt: str, options: dict, cwd: str):
    client = await create_client(cwd)
    session = await client.create_session(session_config)
    
    # Set up event handler
    def on_event(event):
        # Stream event data to client
        yield json.dumps({
            "type": event.type,
            "data": event.data
        })
    
    session.on(on_event)
    await session.send({"prompt": prompt})
    
    # Events are streamed as they occur
```

## Migration Guide

### For Existing Code

No changes required! The backend selector automatically uses SDK mode when configured:

```python
# This code works with both SDK and CLI modes
backend = get_copilot_backend()
result = await backend.execute_prompt_async(prompt, options, cwd)
```

### Switching Modes

**Enable SDK mode (recommended):**
```yaml
copilot:
  use_sdk: true
```

**Fallback to CLI mode:**
```yaml
copilot:
  use_sdk: false
```

## Testing

Tests verify both SDK wrapper and backend selection:

```bash
# Run SDK-specific tests
pytest tests/test_copilot_sdk.py -v

# Run all tests
pytest tests/ -v
```

Test coverage includes:
- ✅ SDK initialization
- ✅ Configuration building
- ✅ Session config generation
- ✅ Async execution (mocked)
- ✅ Backend selection
- ✅ Error handling

## Benefits of SDK Integration

1. **Better Session Management**: SDK handles session lifecycle, persistence, and resumption
2. **Improved Reliability**: JSON-RPC protocol more robust than subprocess pipes
3. **Native Async**: Built on async/await, no event loop juggling
4. **Advanced Features**: Access to SDK-only features (custom tools, agents, skills)
5. **Better Errors**: Structured error responses with context
6. **Resource Management**: Automatic cleanup and connection pooling
7. **Performance**: Reduced overhead compared to subprocess spawning

## Troubleshooting

### SDK Import Error
```
ImportError: github-copilot-sdk is not installed
```
**Solution:** Install SDK
```bash
pip install github-copilot-sdk>=0.1.18
```

### CLI Not Found
```
Copilot CLI is not installed or not in PATH
```
**Solution:** Install and authenticate Copilot CLI
```bash
gh extension install github/gh-copilot
gh auth login
```

### Fallback to CLI Mode
If SDK has issues, temporarily use CLI mode:
```yaml
copilot:
  use_sdk: false  # Fallback to legacy subprocess mode
```

## Future Enhancements

Potential SDK features to leverage:
- [ ] Custom agent definitions
- [ ] Custom tool implementation
- [ ] Skill management
- [ ] Provider configuration (BYOK)
- [ ] Advanced streaming modes
- [ ] Multi-session management
- [ ] Session persistence across restarts

## References

- [GitHub Copilot SDK Repository](https://github.com/github/copilot-sdk)
- [SDK Python Documentation](https://github.com/github/copilot-sdk/tree/main/cookbook/python)
- [Getting Started Guide](https://github.com/github/copilot-sdk/blob/main/docs/getting-started.md)
- [Copilot CLI Documentation](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line)
