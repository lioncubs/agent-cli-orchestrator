"""Tests for copilot_cli module."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import subprocess
import asyncio
import json
from copilot_cli import CopilotCLI


class TestCopilotCLI:
    """Test suite for CopilotCLI class."""
    
    def test_init_with_config(self):
        """Test CopilotCLI initialization with config."""
        cli = CopilotCLI()
        assert cli.timeout > 0
        assert isinstance(cli.enabled, bool)
    
    @patch('copilot_cli.subprocess.run')
    def test_validate_cli_available_true(self, mock_run):
        """Test CLI availability check when CLI is installed."""
        mock_run.return_value = Mock(returncode=0)
        
        cli = CopilotCLI()
        result = cli._validate_cli_available()
        
        assert result is True
    
    @patch('copilot_cli.subprocess.run')
    def test_validate_cli_available_false(self, mock_run):
        """Test CLI availability check when CLI is not installed."""
        mock_run.return_value = Mock(returncode=1)
        
        cli = CopilotCLI()
        result = cli._validate_cli_available()
        
        assert result is False
    
    @patch('copilot_cli.subprocess.run')
    def test_validate_cli_available_timeout(self, mock_run):
        """Test CLI availability check with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('which', 5)
        
        cli = CopilotCLI()
        result = cli._validate_cli_available()
        
        assert result is False
    
    @patch('copilot_cli.subprocess.run')
    def test_validate_cli_available_not_found(self, mock_run):
        """Test CLI availability check with file not found."""
        mock_run.side_effect = FileNotFoundError()
        
        cli = CopilotCLI()
        result = cli._validate_cli_available()
        
        assert result is False
    
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_execute_prompt_cli_disabled(self, mock_validate):
        """Test execute prompt when CLI is disabled."""
        with patch('copilot_cli.config') as mock_config:
            mock_config.copilot_enabled = False
            
            cli = CopilotCLI()
            result = cli.execute_prompt("test prompt")
            
            assert result["status"] == "error"
            assert "disabled" in result["message"].lower()
    
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_execute_prompt_cli_not_available(self, mock_validate):
        """Test execute prompt when CLI is not installed."""
        mock_validate.return_value = False
        
        cli = CopilotCLI()
        result = cli.execute_prompt("test prompt")
        
        assert result["status"] == "error"
        assert "not installed" in result["message"].lower()
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_list_sessions_success_json(self, mock_validate, mock_run):
        """Test list sessions with JSON output."""
        mock_validate.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='[{"session_id": "session1", "status": "active"}, {"session_id": "session2", "status": "active"}]',
            stderr=""
        )
        
        cli = CopilotCLI()
        result = cli.list_sessions()
        
        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["sessions"]) == 2
        assert result["sessions"][0]["session_id"] == "session1"
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_list_sessions_success_text(self, mock_validate, mock_run):
        """Test list sessions with plain text output."""
        mock_validate.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='session-abc123\nsession-def456\n',
            stderr=""
        )
        
        cli = CopilotCLI()
        result = cli.list_sessions()
        
        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["sessions"]) == 2
        assert result["sessions"][0]["session_id"] == "session-abc123"
        assert result["sessions"][1]["session_id"] == "session-def456"
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_list_sessions_empty(self, mock_validate, mock_run):
        """Test list sessions with no active sessions."""
        mock_validate.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='[]',
            stderr=""
        )
        
        cli = CopilotCLI()
        result = cli.list_sessions()
        
        assert result["status"] == "success"
        assert result["count"] == 0
        assert result["sessions"] == []
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_list_sessions_failure(self, mock_validate, mock_run):
        """Test list sessions command failure."""
        mock_validate.return_value = True
        mock_run.return_value = Mock(
            returncode=1,
            stdout='',
            stderr='Error: Unable to list sessions'
        )
        
        cli = CopilotCLI()
        result = cli.list_sessions()
        
        assert result["status"] == "error"
        assert result["exit_code"] == 1
        assert "Unable to list sessions" in result["message"]
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_list_sessions_timeout(self, mock_validate, mock_run):
        """Test list sessions with timeout."""
        mock_validate.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('copilot', 30)
        
        cli = CopilotCLI()
        result = cli.list_sessions()
        
        assert result["status"] == "error"
        assert "timed out" in result["message"].lower()
    
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_list_sessions_cli_disabled(self, mock_validate):
        """Test list sessions when CLI is disabled."""
        with patch('copilot_cli.config') as mock_config:
            mock_config.copilot_enabled = False
            
            cli = CopilotCLI()
            result = cli.list_sessions()
            
            assert result["status"] == "error"
            assert "disabled" in result["message"].lower()
    
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_list_sessions_cli_not_available(self, mock_validate):
        """Test list sessions when CLI is not installed."""
        mock_validate.return_value = False
        
        cli = CopilotCLI()
        result = cli.list_sessions()
        
        assert result["status"] == "error"
        assert "not installed" in result["message"].lower()
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_execute_prompt_success_json(self, mock_validate, mock_run):
        """Test execute prompt with JSON response."""
        mock_validate.return_value = True
        mock_json_output = json.dumps({"response": "test answer"})
        mock_run.return_value = Mock(
            returncode=0,
            stdout=mock_json_output,
            stderr=""
        )
        
        cli = CopilotCLI()
        result = cli.execute_prompt("test prompt")
        
        assert result["status"] == "success"
        assert "output" in result
        assert result["output"]["response"] == "test answer"
        assert result["prompt"] == "test prompt"
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_execute_prompt_success_raw_text(self, mock_validate, mock_run):
        """Test execute prompt with non-JSON response."""
        mock_validate.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Plain text response",
            stderr=""
        )
        
        cli = CopilotCLI()
        result = cli.execute_prompt("test prompt")
        
        assert result["status"] == "success"
        assert result["output"] == "Plain text response"
        assert result.get("raw") is True
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_execute_prompt_failure(self, mock_validate, mock_run):
        """Test execute prompt with command failure."""
        mock_validate.return_value = True
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: command failed"
        )
        
        cli = CopilotCLI()
        result = cli.execute_prompt("test prompt")
        
        assert result["status"] == "error"
        assert result["exit_code"] == 1
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_execute_prompt_timeout(self, mock_validate, mock_run):
        """Test execute prompt with timeout."""
        mock_validate.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('copilot', 60)
        
        cli = CopilotCLI()
        result = cli.execute_prompt("test prompt")
        
        assert result["status"] == "error"
        assert "timed out" in result["message"].lower()
    
    @patch('copilot_cli.subprocess.run')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    def test_execute_prompt_with_options(self, mock_validate, mock_run):
        """Test execute prompt with branch, worktree, and session_id options."""
        mock_validate.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"result": "ok"}',
            stderr=""
        )
        
        cli = CopilotCLI()
        result = cli.execute_prompt(
            "test prompt",
            options={"branch": "main", "worktree": "./worktrees/test", "session_id": "abc123"}
        )
        
        assert result["status"] == "success"
        # Verify options were passed to command
        call_args = mock_run.call_args[0][0]
        assert '--branch' in call_args
        assert '--worktree' in call_args
        assert '--session' in call_args
        assert 'abc123' in call_args
    
    @patch('copilot_cli.asyncio.create_subprocess_exec')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    async def test_execute_prompt_async_success(self, mock_validate, mock_subprocess):
        """Test async execute prompt with success."""
        mock_validate.return_value = True
        
        # Create mock process
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(b'{"result": "async test"}', b'')
        )
        mock_subprocess.return_value = mock_process
        
        cli = CopilotCLI()
        result = await cli.execute_prompt_async("test prompt")
        
        assert result["status"] == "success"
        assert result["output"]["result"] == "async test"
    
    @patch('copilot_cli.asyncio.create_subprocess_exec')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    async def test_execute_prompt_async_timeout(self, mock_validate, mock_subprocess):
        """Test async execute prompt with timeout."""
        mock_validate.return_value = True
        
        # Create mock process that times out
        mock_process = AsyncMock()
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock()
        mock_process.communicate = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        mock_subprocess.return_value = mock_process
        
        cli = CopilotCLI()
        result = await cli.execute_prompt_async("test prompt")
        
        assert result["status"] == "error"
        assert "timed out" in result["message"].lower()
        mock_process.kill.assert_called_once()
    
    @patch('copilot_cli.asyncio.create_subprocess_exec')
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    async def test_execute_prompt_async_failure(self, mock_validate, mock_subprocess):
        """Test async execute prompt with command failure."""
        mock_validate.return_value = True
        
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(
            return_value=(b'', b'Error occurred')
        )
        mock_subprocess.return_value = mock_process
        
        cli = CopilotCLI()
        result = await cli.execute_prompt_async("test prompt")
        
        assert result["status"] == "error"
        assert result["exit_code"] == 1
    
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    async def test_execute_prompt_async_cli_disabled(self, mock_validate):
        """Test async execute prompt when CLI is disabled."""
        with patch('copilot_cli.config') as mock_config:
            mock_config.copilot_enabled = False
            
            cli = CopilotCLI()
            result = await cli.execute_prompt_async("test prompt")
            
            assert result["status"] == "error"
            assert "disabled" in result["message"].lower()
    
    @patch('copilot_cli.CopilotCLI._validate_cli_available')
    async def test_execute_prompt_async_cli_not_available(self, mock_validate):
        """Test async execute prompt when CLI is not installed."""
        mock_validate.return_value = False
        
        cli = CopilotCLI()
        result = await cli.execute_prompt_async("test prompt")
        
        assert result["status"] == "error"
        assert "not installed" in result["message"].lower()