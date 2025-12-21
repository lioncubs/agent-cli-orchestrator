"""GitHub Copilot CLI integration module."""

import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from config_loader import config


class CopilotCLI:
    """Wrapper for GitHub Copilot CLI operations."""
    
    def __init__(self):
        self.timeout = config.copilot_timeout
        self.enabled = config.copilot_enabled
        self.log_dir = Path(config.copilot_log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    def _build_command(self, prompt: str, options: Optional[Dict[str, Any]]) -> List[str]:
        """Build the copilot CLI command for a prompt.

        Args:
            prompt: Prompt text.
            options: Optional CLI overrides.

        Returns:
            Command list suitable for subprocess execution.
        """
        # Check if this is an interactive mode request
        if options and options.get('interactive_mode'):
            # For interactive mode, use -i flag
            command = ['copilot', '-i', prompt]
        else:
            # For non-interactive mode, use -p flag with --silent and --allow-all-tools
            command = ['copilot', '-p', prompt, '--silent', '--allow-all-tools']

        if options:
            if options.get('session_id'):
                command.extend(['--resume', options['session_id']])

        return command

    def execute_prompt(self, prompt: str, options: Optional[Dict[str, Any]] = None, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute a synchronous prompt via Copilot CLI.

        Args:
            prompt: The prompt text to send to Copilot.
            options: Optional CLI overrides such as model, session_id, and allow_all_tools.
            cwd: Optional working directory for the command execution.

        Returns:
            Dict with status, stdout, stderr, and exit code.
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
            command = self._build_command(prompt, options)
            
            # Log the full input
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "type": "copilot_execute",
                "prompt": prompt,
                "options": options,
                "command": command,
                "cwd": cwd
            }
            
            # Execute command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd
            )
            
            # Log the full output
            log_entry["exit_code"] = result.returncode
            log_entry["stdout"] = result.stdout
            log_entry["stderr"] = result.stderr
            
            # Write detailed log to file
            log_file = self.log_dir / f"copilot_{timestamp.replace(':', '-')}.json"
            try:
                import json as json_module
                with open(log_file, 'w') as f:
                    json_module.dump(log_entry, f, indent=2)
            except Exception as log_error:
                print(f"Warning: Could not write log file: {log_error}")
            
            parsed = self._parse_output(result.stdout)
            if result.returncode == 0:
                return {
                    "status": "success",
                    "output": parsed,
                    "prompt": prompt,
                    "full_stdout": result.stdout,
                    "full_stderr": result.stderr,
                    "command": ' '.join(command),
                    "log_file": str(log_file)
                }

            return {
                "status": "error",
                "message": result.stderr or "Command failed",
                "exit_code": result.returncode,
                "full_stdout": result.stdout,
                "full_stderr": result.stderr,
                "command": ' '.join(command),
                "log_file": str(log_file)
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
    
    async def execute_prompt_async(self, prompt: str, options: Optional[Dict[str, Any]] = None, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute an asynchronous prompt via Copilot CLI.
        
        Args:
            prompt: The prompt text to send to Copilot
            options: Optional parameters including:
                - branch: Git branch to use
                - worktree: Worktree path for background agent
                - session_id: Existing session ID to continue
            cwd: Optional working directory for the command execution.
        
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
            command = self._build_command(prompt, options)
            
            # Log the full input
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "type": "copilot_execute_async",
                "prompt": prompt,
                "options": options,
                "command": command,
                "cwd": cwd
            }
            
            # Execute command asynchronously
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
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
            
            # Log the full output
            log_entry["exit_code"] = process.returncode
            log_entry["stdout"] = stdout.decode()
            log_entry["stderr"] = stderr.decode()
            
            # Write detailed log to file
            log_file = self.log_dir / f"copilot_async_{timestamp.replace(':', '-')}.json"
            try:
                import json as json_module
                with open(log_file, 'w') as f:
                    json_module.dump(log_entry, f, indent=2)
            except Exception as log_error:
                print(f"Warning: Could not write log file: {log_error}")
            
            parsed = self._parse_output(stdout.decode())
            if process.returncode == 0:
                return {
                    "status": "success",
                    "output": parsed,
                    "prompt": prompt,
                    "full_stdout": stdout.decode(),
                    "full_stderr": stderr.decode(),
                    "command": ' '.join(command),
                    "log_file": str(log_file)
                }

            return {
                "status": "error",
                "message": stderr.decode() or "Command failed",
                "exit_code": process.returncode,
                "full_stdout": stdout.decode(),
                "full_stderr": stderr.decode(),
                "command": ' '.join(command),
                "log_file": str(log_file)
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

        return {
            "status": "success",
            "sessions": [],
            "count": 0,
            "message": "Session listing is not supported by this Copilot CLI version"
        }

    @staticmethod
    def _parse_output(raw_output: str) -> Any:
        """Parse CLI output, returning JSON when possible."""
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            return raw_output


# Global Copilot CLI instance
copilot_cli = CopilotCLI()
