"""GitHub Copilot SDK integration module.

This module provides a wrapper around the GitHub Copilot SDK to replace
direct CLI subprocess calls with the official SDK. It maintains API compatibility
with the original copilot_cli.py while leveraging SDK features like:
- Built-in session management
- JSON-RPC communication
- Improved error handling
- Better streaming support
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime
from config_loader import config

try:
    from copilot import CopilotClient
    from copilot.types import SessionConfig
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    CopilotClient = None
    SessionConfig = None


class CopilotSDK:
    """Wrapper for GitHub Copilot SDK operations.
    
    Provides a similar interface to CopilotCLI while using the official
    Copilot SDK under the hood for better reliability and features.
    """
    
    def __init__(self):
        """Initialize the Copilot SDK wrapper."""
        self.timeout = config.copilot_timeout
        self.enabled = config.copilot_enabled
        self.log_dir = Path(config.copilot_log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        if not SDK_AVAILABLE:
            raise ImportError(
                "GitHub Copilot SDK is not installed. "
                "Install it with: pip install github-copilot-sdk"
            )
    
    def _validate_sdk_available(self) -> bool:
        """Check if Copilot SDK is available and CLI is installed."""
        if not SDK_AVAILABLE:
            return False
        
        # The SDK will validate CLI availability when starting
        return True
    
    async def _create_client(self, cwd: Optional[str] = None) -> CopilotClient:
        """Create and start a new Copilot client.
        
        Args:
            cwd: Optional working directory for the client
            
        Returns:
            Started CopilotClient instance
            
        Raises:
            Exception: If client fails to start
        """
        client_options = {}
        if cwd:
            client_options["cwd"] = cwd
        
        client = CopilotClient(client_options)
        await client.start()
        return client
    
    def _build_session_config(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build session configuration from options.
        
        Args:
            options: Optional parameters including model, session_id, etc.
            
        Returns:
            Session configuration dict for SDK
        """
        session_config = {}
        
        if not options:
            return session_config
        
        # Map common options to SDK session config
        if options.get("model"):
            session_config["model"] = options["model"]
        
        # System message configuration
        if options.get("system_message"):
            session_config["system_message"] = options["system_message"]
        
        # Tool configuration
        if options.get("available_tools"):
            session_config["available_tools"] = options["available_tools"]
        if options.get("excluded_tools"):
            session_config["excluded_tools"] = options["excluded_tools"]
        
        return session_config
    
    def _log_execution(
        self, 
        log_type: str,
        prompt: str,
        options: Optional[Dict[str, Any]],
        cwd: Optional[str],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Path:
        """Log SDK execution details to file.
        
        Args:
            log_type: Type of execution (e.g., "sdk_execute", "sdk_execute_async")
            prompt: The prompt that was executed
            options: Options used for execution
            cwd: Working directory used
            result: Result data if successful
            error: Error message if failed
            
        Returns:
            Path to the log file
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": log_type,
            "prompt": prompt,
            "options": options,
            "cwd": cwd
        }
        
        if result:
            log_entry["result"] = result
        if error:
            log_entry["error"] = error
        
        log_file = self.log_dir / f"copilot_sdk_{timestamp.replace(':', '-')}.json"
        try:
            with open(log_file, 'w') as f:
                json.dump(log_entry, f, indent=2)
        except Exception as log_error:
            print(f"Warning: Could not write log file: {log_error}")
        
        return log_file
    
    def execute_prompt(
        self, 
        prompt: str, 
        options: Optional[Dict[str, Any]] = None, 
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a synchronous prompt via Copilot SDK.
        
        This is a synchronous wrapper around the async SDK. For better performance,
        use execute_prompt_async directly.
        
        Args:
            prompt: The prompt text to send to Copilot
            options: Optional parameters such as model, session_id, etc.
            cwd: Optional working directory for the command execution
            
        Returns:
            Dict with status, output, and execution details
        """
        # Run async version in new event loop
        return asyncio.run(self.execute_prompt_async(prompt, options, cwd))
    
    async def execute_prompt_async(
        self, 
        prompt: str, 
        options: Optional[Dict[str, Any]] = None, 
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute an asynchronous prompt via Copilot SDK.
        
        Args:
            prompt: The prompt text to send to Copilot
            options: Optional parameters including:
                - model: Model to use (e.g., "gpt-4o", "claude-3.5-sonnet")
                - session_id: Existing session ID to resume
                - system_message: Custom system message
                - available_tools: List of tools to enable
                - excluded_tools: List of tools to disable
            cwd: Optional working directory for the command execution
            
        Returns:
            Dict with status and response from Copilot SDK
        """
        if not self.enabled:
            return {
                "status": "error",
                "message": "Copilot SDK is disabled in configuration"
            }
        
        if not self._validate_sdk_available():
            return {
                "status": "error",
                "message": "Copilot SDK is not available. Install with: pip install github-copilot-sdk"
            }
        
        client = None
        session = None
        log_file = None
        
        try:
            # Create and start client
            client = await self._create_client(cwd)
            
            # Build session configuration
            session_config = self._build_session_config(options)
            
            # Create or resume session
            if options and options.get("session_id"):
                # Resume existing session
                session = client._sessions.get(options["session_id"])
                if not session:
                    await client.stop()
                    return {
                        "status": "error",
                        "message": f"Session '{options['session_id']}' not found"
                    }
            else:
                # Create new session
                session = await client.create_session(session_config)
            
            # Send prompt and wait for response
            response = await session.send_and_wait({"prompt": prompt})
            
            if response and response.data and hasattr(response.data, 'content'):
                output = response.data.content
                
                # Log successful execution
                log_file = self._log_execution(
                    "sdk_execute_async",
                    prompt,
                    options,
                    cwd,
                    result={"output": output, "session_id": session.session_id}
                )
                
                return {
                    "status": "success",
                    "output": output,
                    "prompt": prompt,
                    "session_id": session.session_id,
                    "log_file": str(log_file)
                }
            else:
                error_msg = "No response received from Copilot SDK"
                log_file = self._log_execution(
                    "sdk_execute_async",
                    prompt,
                    options,
                    cwd,
                    error=error_msg
                )
                
                return {
                    "status": "error",
                    "message": error_msg,
                    "log_file": str(log_file)
                }
        
        except asyncio.TimeoutError:
            error_msg = f"Command timed out after {self.timeout} seconds"
            log_file = self._log_execution(
                "sdk_execute_async",
                prompt,
                options,
                cwd,
                error=error_msg
            )
            return {
                "status": "error",
                "message": error_msg,
                "log_file": str(log_file) if log_file else None
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            log_file = self._log_execution(
                "sdk_execute_async",
                prompt,
                options,
                cwd,
                error=error_msg
            )
            return {
                "status": "error",
                "message": error_msg,
                "log_file": str(log_file) if log_file else None
            }
        finally:
            # Clean up resources
            if session and not (options and options.get("session_id")):
                # Only destroy session if we created it (not resumed)
                try:
                    await session.destroy()
                except:
                    pass
            
            if client:
                try:
                    await client.stop()
                except:
                    pass
    
    async def execute_prompt_streaming(
        self, 
        prompt: str, 
        options: Optional[Dict[str, Any]] = None, 
        cwd: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Execute a prompt and stream output in real-time.
        
        Args:
            prompt: The prompt text to send to Copilot
            options: Optional parameters
            cwd: Optional working directory
            
        Yields:
            JSON strings with streaming output data
        """
        if not self.enabled:
            yield json.dumps({"type": "error", "message": "Copilot SDK is disabled"}) + "\n"
            return
        
        if not self._validate_sdk_available():
            yield json.dumps({"type": "error", "message": "Copilot SDK not available"}) + "\n"
            return
        
        client = None
        session = None
        
        try:
            timestamp = datetime.now().isoformat()
            
            # Send start event
            yield json.dumps({
                "type": "start",
                "timestamp": timestamp,
                "cwd": cwd or "."
            }) + "\n"
            
            # Create and start client
            client = await self._create_client(cwd)
            
            # Build session configuration
            session_config = self._build_session_config(options)
            
            # Create session
            session = await client.create_session(session_config)
            
            # Send the prompt and wait for response
            # Note: For true event-by-event streaming, the SDK's on() handler
            # could be used to capture intermediate events. This simplified
            # version returns the complete response which is compatible with
            # the existing streaming API expectations.
            try:
                response = await asyncio.wait_for(
                    session.send_and_wait({"prompt": prompt}),
                    timeout=self.timeout
                )
                
                if response and response.data and hasattr(response.data, 'content'):
                    yield json.dumps({
                        "type": "complete",
                        "data": {"content": response.data.content},
                        "timestamp": datetime.now().isoformat()
                    }) + "\n"
                else:
                    yield json.dumps({
                        "type": "complete",
                        "timestamp": datetime.now().isoformat()
                    }) + "\n"
            
            except asyncio.TimeoutError:
                yield json.dumps({
                    "type": "error",
                    "message": f"Timeout after {self.timeout} seconds"
                }) + "\n"
        
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            }) + "\n"
        
        finally:
            # Clean up
            if session:
                try:
                    await session.destroy()
                except:
                    pass
            
            if client:
                try:
                    await client.stop()
                except:
                    pass
    
    def list_sessions(self) -> Dict[str, Any]:
        """List active Copilot SDK sessions.
        
        Note: Session management in SDK is per-client instance.
        This returns a placeholder response for API compatibility.
        
        Returns:
            Dict with status and session information
        """
        if not self.enabled:
            return {
                "status": "error",
                "message": "Copilot SDK is disabled in configuration"
            }
        
        return {
            "status": "success",
            "sessions": [],
            "count": 0,
            "message": "Session listing requires a running client instance. Use session_id in requests to maintain sessions."
        }


# Global Copilot SDK instance
copilot_sdk = CopilotSDK()
