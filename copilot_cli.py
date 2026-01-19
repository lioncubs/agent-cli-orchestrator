"""GitHub Copilot CLI integration module."""

import subprocess
import json
import asyncio
from typing import Dict, Any, Optional
from config_loader import config


class CopilotCLI:
    """Wrapper for GitHub Copilot CLI operations."""
    
    def __init__(self):
        self.timeout = config.copilot_timeout
        self.enabled = config.copilot_enabled
    
    def _validate_cli_available(self) -> bool:
        """Check if Copilot CLI is available."""
        try:
            result = subprocess.run(
                ['which', 'copilot'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def execute_prompt(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a synchronous prompt via Copilot CLI.
        
        Args:
            prompt: The prompt text to send to Copilot
            options: Optional parameters including:
                - branch: Git branch to use
                - worktree: Worktree path for background agent
                - session_id: Existing session ID to continue
        
        Returns:
            Dict with status and response from Copilot CLI
        """
        if not self.enabled:
            return {
                "status": "error",
                "message": "Copilot CLI is disabled in configuration"
            }
        
        if not self._validate_cli_available():
            return {
                "status": "error",
                "message": "Copilot CLI is not installed or not in PATH"
            }
        
        try:
            # Build command - using -p flag for prompt
            command = ['copilot', '-p', prompt]
            
            # Add optional parameters if provided
            if options:
                if 'branch' in options:
                    command.extend(['--branch', options['branch']])
                if 'worktree' in options:
                    command.extend(['--worktree', options['worktree']])
                if 'session_id' in options:
                    command.extend(['--session', options['session_id']])
            
            # Execute command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                # Return raw output (copilot CLI outputs text, not JSON)
                return {
                    "status": "success",
                    "output": result.stdout.strip(),
                    "prompt": prompt
                }
            else:
                return {
                    "status": "error",
                    "message": result.stderr or result.stdout or "Command failed",
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
                "message": f"Unexpected error: {str(e)}"
            }
    
    async def execute_prompt_async(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute an asynchronous prompt via Copilot CLI.
        
        Args:
            prompt: The prompt text to send to Copilot
            options: Optional parameters including:
                - branch: Git branch to use
                - worktree: Worktree path for background agent
                - session_id: Existing session ID to continue
        
        Returns:
            Dict with status and response from Copilot CLI
        """
        if not self.enabled:
            return {
                "status": "error",
                "message": "Copilot CLI is disabled in configuration"
            }
        
        if not self._validate_cli_available():
            return {
                "status": "error",
                "message": "Copilot CLI is not installed or not in PATH"
            }
        
        try:
            # Build command - using -p flag for prompt
            command = ['copilot', '-p', prompt]
            
            # Add optional parameters if provided
            if options:
                if 'branch' in options:
                    command.extend(['--branch', options['branch']])
                if 'worktree' in options:
                    command.extend(['--worktree', options['worktree']])
                if 'session_id' in options:
                    command.extend(['--session', options['session_id']])
            
            # Execute command asynchronously
            process = await asyncio.create_subprocess_exec(
                *command,
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
                # Return raw output (copilot CLI outputs text, not JSON)
                return {
                    "status": "success",
                    "output": stdout.decode().strip(),
                    "prompt": prompt
                }
            else:
                return {
                    "status": "error",
                    "message": stderr.decode() or stdout.decode() or "Command failed",
                    "exit_code": process.returncode
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def list_sessions(self) -> Dict[str, Any]:
        """List active Copilot CLI sessions.
        
        Returns:
            Dict with status and list of sessions
        """
        if not self.enabled:
            return {
                "status": "error",
                "message": "Copilot CLI is disabled in configuration"
            }
        
        if not self._validate_cli_available():
            return {
                "status": "error",
                "message": "Copilot CLI is not installed or not in PATH"
            }
        
        try:
            # Execute copilot session list command
            result = subprocess.run(
                ['copilot', 'session', 'list', '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                try:
                    # Parse JSON output
                    sessions = json.loads(result.stdout)
                    # Ensure sessions is a list
                    if not isinstance(sessions, list):
                        # If single session object, wrap in list
                        sessions = [sessions] if sessions else []
                    return {
                        "status": "success",
                        "sessions": sessions,
                        "count": len(sessions)
                    }
                except json.JSONDecodeError:
                    # If not valid JSON, parse line by line
                    lines = result.stdout.strip().split('\n')
                    sessions = [{"session_id": line.strip()} for line in lines if line.strip()]
                    return {
                        "status": "success",
                        "sessions": sessions,
                        "count": len(sessions)
                    }
            else:
                return {
                    "status": "error",
                    "message": result.stderr or "Failed to list sessions",
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
                "message": f"Unexpected error: {str(e)}"
            }


# Global Copilot CLI instance
copilot_cli = CopilotCLI()