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
        """Execute a synchronous prompt via Copilot CLI."""
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
            # Build command
            command = ['copilot', 'prompt', '-i', prompt, '-o', 'json']
            
            # Add optional parameters if provided
            if options:
                if 'branch' in options:
                    command.extend(['--branch', options['branch']])
                if 'worktree' in options:
                    command.extend(['--worktree', options['worktree']])
            
            # Execute command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                try:
                    # Parse JSON output
                    output = json.loads(result.stdout)
                    return {
                        "status": "success",
                        "output": output,
                        "prompt": prompt
                    }
                except json.JSONDecodeError:
                    # If not valid JSON, return raw output
                    return {
                        "status": "success",
                        "output": result.stdout,
                        "prompt": prompt,
                        "raw": True
                    }
            else:
                return {
                    "status": "error",
                    "message": result.stderr or "Command failed",
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
        """Execute an asynchronous prompt via Copilot CLI."""
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
            # Build command
            command = ['copilot', 'prompt', '-i', prompt, '-o', 'json']
            
            # Add optional parameters if provided
            if options:
                if 'branch' in options:
                    command.extend(['--branch', options['branch']])
                if 'worktree' in options:
                    command.extend(['--worktree', options['worktree']])
            
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
                try:
                    # Parse JSON output
                    output = json.loads(stdout.decode())
                    return {
                        "status": "success",
                        "output": output,
                        "prompt": prompt
                    }
                except json.JSONDecodeError:
                    # If not valid JSON, return raw output
                    return {
                        "status": "success",
                        "output": stdout.decode(),
                        "prompt": prompt,
                        "raw": True
                    }
            else:
                return {
                    "status": "error",
                    "message": stderr.decode() or "Command failed",
                    "exit_code": process.returncode
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }


# Global Copilot CLI instance
copilot_cli = CopilotCLI()
