"""Additional tests for config_loader module to improve coverage."""

import pytest
import tempfile
import os
from config_loader import Config


class TestConfigLoaderCoverage:
    """Additional tests for Config class methods."""
    
    def test_repositories_method(self):
        """Test repositories() method."""
        content = """
repositories:
  - name: "repo1"
    path: "/path1"
    default: true
  - name: "repo2"
    path: "/path2"
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            repos = config.repositories()
            assert len(repos) == 2
            assert repos[0]['name'] == "repo1"
            assert repos[1]['name'] == "repo2"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_default_repository_with_explicit_default(self):
        """Test default_repository() when default is explicitly set."""
        content = """
repositories:
  - name: "repo1"
    path: "/path1"
  - name: "repo2"
    path: "/path2"
    default: true
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            default = config.default_repository()
            assert default is not None
            assert default['name'] == "repo2"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_default_repository_first_when_no_default_marked(self):
        """Test default_repository() returns first when none marked default."""
        content = """
repositories:
  - name: "repo1"
    path: "/path1"
  - name: "repo2"
    path: "/path2"
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            default = config.default_repository()
            assert default is not None
            assert default['name'] == "repo1"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_default_repository_when_empty(self):
        """Test default_repository() when no repositories configured."""
        content = """
repositories: []
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            default = config.default_repository()
            assert default is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_repository_path_by_name(self):
        """Test get_repository_path() with specific repo name."""
        content = """
repositories:
  - name: "repo1"
    path: "/path/to/repo1"
    default: true
  - name: "repo2"
    path: "/path/to/repo2"
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            
            # Test getting specific repo
            path1 = config.get_repository_path("repo1")
            assert path1 == "/path/to/repo1"
            
            path2 = config.get_repository_path("repo2")
            assert path2 == "/path/to/repo2"
            
            # Test non-existent repo
            path_none = config.get_repository_path("nonexistent")
            assert path_none is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_repository_path_default(self):
        """Test get_repository_path() with None returns default."""
        content = """
repositories:
  - name: "repo1"
    path: "/default/path"
    default: true
  - name: "repo2"
    path: "/other/path"
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            default_path = config.get_repository_path(None)
            assert default_path == "/default/path"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_repository_path_when_no_default(self):
        """Test get_repository_path(None) when no repos configured."""
        content = """
repositories: []
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            path = config.get_repository_path(None)
            assert path is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_list_repositories(self):
        """Test list_repositories() method."""
        content = """
repositories:
  - name: "alpha"
    path: "/path1"
  - name: "beta"
    path: "/path2"
  - name: "gamma"
    path: "/path3"
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            names = config.list_repositories()
            assert names == ["alpha", "beta", "gamma"]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_worktrees_path_by_name(self):
        """Test get_worktrees_path() with specific repo name."""
        content = """
repositories:
  - name: "repo1"
    path: "/path1"
    worktrees_path: "/worktrees1"
    default: true
  - name: "repo2"
    path: "/path2"
    worktrees_path: "/worktrees2"
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            
            wt1 = config.get_worktrees_path("repo1")
            assert wt1 == "/worktrees1"
            
            wt2 = config.get_worktrees_path("repo2")
            assert wt2 == "/worktrees2"
            
            wt_none = config.get_worktrees_path("nonexistent")
            assert wt_none is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_worktrees_path_default(self):
        """Test get_worktrees_path(None) returns default repo's path."""
        content = """
repositories:
  - name: "repo1"
    path: "/path1"
    worktrees_path: "/default/worktrees"
    default: true
  - name: "repo2"
    path: "/path2"
    worktrees_path: "/other/worktrees"
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            wt_path = config.get_worktrees_path(None)
            assert wt_path == "/default/worktrees"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_worktrees_path_when_no_default_repo(self):
        """Test get_worktrees_path(None) when no default repo."""
        content = """
repositories: []
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            wt_path = config.get_worktrees_path(None)
            assert wt_path is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_repository_path_property(self):
        """Test repository_path property."""
        content = """
repositories:
  - name: "test-repo"
    path: "/my/repo/path"
    default: true
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.repository_path == "/my/repo/path"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_repository_path_property_when_no_default(self):
        """Test repository_path property when no default repo."""
        content = """
repositories: []
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.repository_path == "."
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_non_dict_value(self):
        """Test get() when encountering non-dict value in path."""
        content = """
repositories:
  - name: "test"
    path: "."
    
simple_value: "just a string"
    
server:
  host: "127.0.0.1"
  port: 8000
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            # Try to get nested value from non-dict
            result = config.get('simple_value.nested', 'default')
            assert result == 'default'
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
