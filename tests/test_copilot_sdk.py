"""Tests for Copilot SDK integration module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from copilot_sdk import CopilotSDK


class TestCopilotSDK:
    """Test CopilotSDK wrapper class."""
    
    def test_initialization(self):
        """Test that CopilotSDK initializes correctly."""
        sdk = CopilotSDK()
        assert sdk.enabled is True
        assert sdk.timeout > 0
        assert sdk.log_dir.exists()
    
    def test_validate_sdk_available(self):
        """Test SDK availability check."""
        sdk = CopilotSDK()
        # SDK is imported successfully, so it should be available
        assert sdk._validate_sdk_available() is True
    
    def test_build_session_config_empty(self):
        """Test session config building with no options."""
        sdk = CopilotSDK()
        config = sdk._build_session_config(None)
        assert isinstance(config, dict)
        assert len(config) == 0
    
    def test_build_session_config_with_model(self):
        """Test session config building with model option."""
        sdk = CopilotSDK()
        options = {"model": "gpt-4o"}
        config = sdk._build_session_config(options)
        assert config["model"] == "gpt-4o"
    
    def test_build_session_config_with_tools(self):
        """Test session config building with tool options."""
        sdk = CopilotSDK()
        options = {
            "available_tools": ["view", "edit"],
            "excluded_tools": ["bash"]
        }
        config = sdk._build_session_config(options)
        assert config["available_tools"] == ["view", "edit"]
        assert config["excluded_tools"] == ["bash"]
    
    @pytest.mark.asyncio
    async def test_execute_prompt_disabled(self):
        """Test that execution fails when SDK is disabled."""
        sdk = CopilotSDK()
        sdk.enabled = False
        
        result = await sdk.execute_prompt_async("test prompt")
        assert result["status"] == "error"
        assert "disabled" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_prompt_async_basic(self):
        """Test basic async execution (mocked)."""
        sdk = CopilotSDK()
        
        # Mock the CopilotClient
        with patch('copilot_sdk.CopilotClient') as MockClient:
            mock_client = AsyncMock()
            mock_session = AsyncMock()
            mock_response = MagicMock()
            mock_response.data.content = "Test response"
            
            MockClient.return_value = mock_client
            mock_client.start = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_session)
            mock_session.send_and_wait = AsyncMock(return_value=mock_response)
            mock_session.destroy = AsyncMock()
            mock_session.session_id = "test-session-id"
            mock_client.stop = AsyncMock()
            
            result = await sdk.execute_prompt_async("What is 2+2?")
            
            assert result["status"] == "success"
            assert result["output"] == "Test response"
            assert result["prompt"] == "What is 2+2?"
            assert "session_id" in result
    
    def test_list_sessions(self):
        """Test session listing."""
        sdk = CopilotSDK()
        result = sdk.list_sessions()
        
        assert result["status"] == "success"
        assert "sessions" in result
        assert isinstance(result["sessions"], list)


class TestBackendSelection:
    """Test backend selection logic in main.py."""
    
    def test_get_copilot_backend_sdk(self):
        """Test that SDK backend is selected when configured."""
        from main import get_copilot_backend
        from config_loader import config
        
        # Verify config is set to use SDK
        assert config.copilot_use_sdk is True
        
        # Get backend
        backend = get_copilot_backend()
        
        # Should be copilot_sdk, not copilot_cli
        from copilot_sdk import copilot_sdk
        assert backend is copilot_sdk


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
