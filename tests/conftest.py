"""Shared fixtures for tests."""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    content = """
repository:
  name: "test-repo"
  default_branch: "main"

server:
  host: "127.0.0.1"
  port: 8000

copilot:
  enabled: true
  timeout: 60

worktrees:
  base_path: "./test-worktrees"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def invalid_config_file():
    """Create an invalid YAML config file for testing."""
    content = """
repository:
  name: "test-repo"
  invalid: [unclosed
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository for testing."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    return str(repo_dir)