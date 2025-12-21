# Real-Time Streaming Output for Copilot CLI

## Overview

The streaming feature allows you to see **real-time output** from the GitHub Copilot CLI as it executes, instead of waiting for the entire command to complete.

## Why Streaming?

Previously, when you executed a Copilot prompt:
- The server would run the entire command
- Wait for it to complete
- Then return all output at once

With streaming:
- You see output **line-by-line** as it happens
- Better visibility into what Copilot is doing
- Can see progress for long-running commands
- Easier to debug issues

## How to Use

### 1. Web Interface (Easiest)

Visit the streaming test page:
```
http://localhost:8000/streaming-test
```

This provides a live terminal-like interface where you can:
- Enter prompts
- See command execution details
- Watch real-time stdout/stderr output
- See completion status and exit codes

### 2. API Endpoint

**Endpoint:** `POST /prompt/stream`

**Request:**
```json
{
  "prompt": "what files are in this directory?",
  "repo_name": "lioncubs",  // optional
  "options": {}              // optional
}
```

**Response:** Server-Sent Events (SSE) stream

The response is a stream of JSON events, each prefixed with `data: `:

```
data: {"type": "start", "timestamp": "2025-12-21T...", "command": "copilot -p ...", "cwd": "..."}

data: {"type": "stdout", "data": "Files in directory:"}

data: {"type": "stdout", "data": "  main.py"}

data: {"type": "stdout", "data": "  config.yaml"}

data: {"type": "complete", "exit_code": 0, "timestamp": "2025-12-21T..."}
```

### 3. Event Types

| Type | Description | Fields |
|------|-------------|--------|
| `start` | Command started | `timestamp`, `command`, `cwd` |
| `stdout` | Standard output line | `data` |
| `stderr` | Standard error line | `data` |
| `complete` | Command finished | `exit_code`, `timestamp` |
| `error` | Error occurred | `message` |

### 4. JavaScript Example

```javascript
async function streamPrompt(prompt) {
    const response = await fetch('/prompt/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: prompt})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const event = JSON.parse(line.substring(6));
                console.log(event.type, event);
            }
        }
    }
}
```

### 5. curl Example

```bash
curl -X POST http://localhost:8000/prompt/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "list files in current directory"}' \
  --no-buffer
```

## Comparison: Streaming vs Non-Streaming

### Regular Async Endpoint (`/prompt/async`)
- Returns: Complete JSON response after command finishes
- Best for: Automated workflows, when you only need final result
- Response time: Waits for entire command to complete

### Streaming Endpoint (`/prompt/stream`)
- Returns: Line-by-line output as it happens
- Best for: Interactive use, debugging, progress monitoring
- Response time: Starts immediately, shows real-time progress

## Technical Details

### Server-Sent Events (SSE)
- Protocol: HTTP with `text/event-stream` content type
- Connection: Long-lived HTTP connection
- Format: Each event is `data: {json}\n\n`
- Headers:
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`
  - `X-Accel-Buffering: no`

### Implementation
- Uses Python `asyncio` for concurrent stdout/stderr reading
- Streams both stdout and stderr in real-time
- Merges streams while preserving order
- Properly handles command timeouts and errors

## Use Cases

1. **Interactive Development**
   - See what Copilot is thinking as it works
   - Debug prompts that aren't working as expected
   - Monitor long-running code generation

2. **Debugging**
   - See stderr messages immediately
   - Identify where commands are failing
   - Check command arguments and working directory

3. **Progress Monitoring**
   - Watch file operations in progress
   - See iterative refinement in real-time
   - Better understanding of Copilot's workflow

4. **Teaching/Demos**
   - Show how Copilot works step-by-step
   - Demonstrate command execution flow
   - Explain what's happening at each stage

## Logging

Streaming executions are still logged to:
- Activity log: `/logs` endpoint
- Detailed logs: `/logs/copilot` endpoint
- File logs: `logs/copilot/copilot_async_*.json`

The streaming endpoint captures all output for logging even while streaming it to the client.

## Browser Compatibility

The streaming test page works in all modern browsers:
- Chrome/Edge (Chromium)
- Firefox
- Safari
- Any browser supporting Fetch API and ReadableStream

## Tips

1. **Use streaming for development** - See what's happening in real-time
2. **Use async for automation** - Get structured final result
3. **Check stderr** - Important warnings/errors appear there
4. **Monitor exit codes** - Non-zero means command failed
5. **Watch timing** - See how long each step takes

## Troubleshooting

**No output appearing?**
- Check that Copilot CLI is installed: `which copilot`
- Verify `copilot_enabled: true` in config.yaml
- Check browser console for JavaScript errors

**Connection drops?**
- Check firewall/proxy settings
- Verify server timeout settings
- Look for network issues in browser DevTools

**Garbled output?**
- This is normal for some CLI tools with progress bars
- The streaming shows raw output exactly as received
- Final parsed output is in `/prompt/async` endpoint
