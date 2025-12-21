"""Tests for config_loader module."""

import pytest
import os
import tempfile
from pathlib import Path
from config_loader import Config


class TestConfig:
    """Test suite for Config class."""
    
    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid configuration file."""
        config = Config(temp_config_file)
        
        assert config.repository_name == "test-repo"
        assert config.default_branch == "main"
        assert config.server_host == "127.0.0.1"
        assert config.server_port == 8000
    
    def test_missing_config_file(self):
        """Test error handling when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            Config("nonexistent_config.yaml")
    
    def test_malformed_yaml(self, invalid_config_file):
        """Test error handling for malformed YAML."""
        with pytest.raises(Exception):
            Config(invalid_config_file)
    
    def test_get_nested_value_with_dot_notation(self, temp_config_file):
        """Test getting nested configuration values with dot notation."""
        config = Config(temp_config_file)
        
        # Test new repositories format
        repos = config.get('repositories')
        assert repos is not None
        assert len(repos) > 0
        assert repos[0]['name'] == "test-repo"
        
        # Test other dot notation
        assert config.get('server.port') == 8000
        assert config.get('copilot.enabled') is True
    
    def test_get_with_default_value(self, temp_config_file):
        """Test getting nonexistent key returns default value."""
        config = Config(temp_config_file)
        
        assert config.get('nonexistent.key', 'default') == 'default'
        assert config.get('nonexistent.key') is None
    
    def test_repository_name_property(self, temp_config_file):
        """Test repository_name property accessor."""
        config = Config(temp_config_file)
        assert config.repository_name == "test-repo"
    
    def test_default_branch_property(self, temp_config_file):
        """Test default_branch property accessor."""
        config = Config(temp_config_file)
        assert config.default_branch == "main"
    
    def test_server_host_property(self, temp_config_file):
        """Test server_host property accessor."""
        config = Config(temp_config_file)
        assert config.server_host == "127.0.0.1"
    
    def test_server_port_property(self, temp_config_file):
        """Test server_port property accessor."""
        config = Config(temp_config_file)
        assert config.server_port == 8000
    
    def test_copilot_enabled_property(self, temp_config_file):
        """Test copilot_enabled property accessor."""
        config = Config(temp_config_file)
        assert config.copilot_enabled is True
    
    def test_copilot_timeout_property(self, temp_config_file):
        """Test copilot_timeout property accessor."""
        config = Config(temp_config_file)
        assert config.copilot_timeout == 60
    
    def test_worktrees_base_path_property(self, temp_config_file):
        """Test worktrees_base_path property accessor."""
        config = Config(temp_config_file)
        assert config.worktrees_base_path == "./test-worktrees"
    
    def test_get_with_missing_nested_key(self, temp_config_file):
        """Test getting deeply nested missing key returns default."""
        config = Config(temp_config_file)
        
        assert config.get('deep.nested.missing.key', 'fallback') == 'fallback'
    
    def test_default_values_for_missing_config(self):
        """Test that missing config file with defaults still works."""
        # Create empty config
        content = "{}"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            
            # Test defaults
            assert config.repository_name == "unknown"
            assert config.default_branch == "main"
            assert config.server_host == "0.0.0.0"
            assert config.server_port == 8000
            assert config.copilot_enabled is True
            assert config.copilot_timeout == 300
            assert config.worktrees_base_path == "./worktrees"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)