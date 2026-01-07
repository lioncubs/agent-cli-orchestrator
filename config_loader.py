"""Configuration loader for the agent-cli-orchestrator."""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


class Config:
    """Configuration management class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
    
    def get(self, key: str, default=None):
        """Get configuration value by key (supports dot notation)."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def repositories(self) -> List[Dict[str, Any]]:
        """Get list of all repositories."""
        return self.get('repositories', [])
    
    def default_repository(self) -> Optional[Dict[str, Any]]:
        """Get the default repository configuration."""
        repos = self.repositories()
        for repo in repos:
            if repo.get('default', False):
                return repo
        # If no default is marked, return the first one
        return repos[0] if repos else None
    
    def get_repository_path(self, repo_name: Optional[str] = None) -> Optional[str]:
        """
        Get the repository path by name.
        If repo_name is None, returns the default repository path.
        """
        if repo_name is None:
            default_repo = self.default_repository()
            return default_repo.get('path') if default_repo else None
        
        repos = self.repositories()
        for repo in repos:
            if repo.get('name') == repo_name:
                return repo.get('path')
        return None
    
    def list_repositories(self) -> List[str]:
        """Get list of repository names."""
        return [repo.get('name', 'unnamed') for repo in self.repositories()]
    
    def get_worktrees_path(self, repo_name: Optional[str] = None) -> Optional[str]:
        """Get the worktrees path for a repository.
        
        Args:
            repo_name: Repository name, or None for default repository
            
        Returns:
            Worktrees base path for the repository, or None if not configured
        """
        if repo_name is None:
            default_repo = self.default_repository()
            return default_repo.get('worktrees_path') if default_repo else None
        
        repos = self.repositories()
        for repo in repos:
            if repo.get('name') == repo_name:
                return repo.get('worktrees_path')
        return None
    
    @property
    def repository_name(self) -> str:
        """Get default repository name."""
        default_repo = self.default_repository()
        return default_repo.get('name', 'unknown') if default_repo else 'unknown'
    
    @property
    def repository_path(self) -> str:
        """Get default repository path."""
        default_repo = self.default_repository()
        return default_repo.get('path', '.') if default_repo else '.'
    
    @property
    def default_branch(self) -> str:
        """Get default branch."""
        return self.get('repository.default_branch', 'main')
    
    @property
    def server_host(self) -> str:
        """Get server host."""
        return self.get('server.host', '0.0.0.0')
    
    @property
    def server_port(self) -> int:
        """Get server port."""
        return self.get('server.port', 8000)
    
    @property
    def copilot_enabled(self) -> bool:
        """Check if Copilot CLI is enabled."""
        return self.get('copilot.enabled', True)
    
    @property
    def copilot_timeout(self) -> int:
        """Get Copilot CLI timeout."""
        return self.get('copilot.timeout', 300)

    @property
    def copilot_log_dir(self) -> str:
        """Get Copilot CLI log directory."""
        return self.get('copilot.log_dir', './logs/copilot')
    
    @property
    def worktrees_base_path(self) -> str:
        """Get worktrees base path for default repository.
        
        Deprecated: Use get_worktrees_path() instead for per-repository paths.
        """
        return self.get_worktrees_path() or './worktrees'
    
    @property
    def metrics_enabled(self) -> bool:
        """Check if metrics collection is enabled."""
        return self.get('metrics.enabled', True)
    
    @property
    def metrics_database_url(self) -> Optional[str]:
        """Get metrics database URL."""
        return self.get('metrics.database_url', None)
    
    @property
    def metrics_collect_system(self) -> bool:
        """Check if system metrics collection is enabled."""
        return self.get('metrics.collect_system_metrics', True)
    
    @property
    def metrics_system_interval(self) -> int:
        """Get system metrics collection interval in seconds."""
        return self.get('metrics.system_metrics_interval', 60)
    
    @property
    def metrics_cache_ttl(self) -> int:
        """Get metrics cache TTL in seconds."""
        return self.get('metrics.cache_ttl_seconds', 300)
    
    @property
    def metrics_retention_days(self) -> int:
        """Get metrics retention period in days."""
        return self.get('metrics.retention_days', 30)


# Global config instance
config = Config()
