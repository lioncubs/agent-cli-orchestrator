"""Configuration loader for the agent-cli-orchestrator."""

import yaml
from pathlib import Path
from typing import Dict, Any


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
    
    @property
    def repository_name(self) -> str:
        """Get repository name."""
        return self.get('repository.name', 'unknown')
    
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
    def worktrees_base_path(self) -> str:
        """Get worktrees base path."""
        return self.get('worktrees.base_path', './worktrees')


# Global config instance
config = Config()
