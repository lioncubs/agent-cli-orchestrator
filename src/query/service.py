"""Query service for quick read-only repository queries."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.permissions.tool_policy import ToolPolicy, Operation, OperationTier


class QueryService:
    """
    Handle quick read-only query execution.
    
    Targets minimal repository access for fast, non-invasive queries.
    """
    
    def __init__(self, tool_policy: Optional[ToolPolicy] = None):
        """
        Initialize query service.
        
        Args:
            tool_policy: Tool policy for operation validation (optional)
        """
        self.tool_policy = tool_policy or ToolPolicy(default_tier=OperationTier.READ_ONLY)
    
    def read_file(
        self,
        repo_path: str,
        file_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Read a file from the repository.
        
        Args:
            repo_path: Path to repository
            file_path: Relative path to file within repo
            session_id: Optional session ID for policy check
            
        Returns:
            Dict containing file content and metadata
            
        Raises:
            PermissionError: If operation not allowed
            FileNotFoundError: If file doesn't exist
        """
        self.tool_policy.check_operation(Operation.READ_FILE, session_id)
        
        full_path = Path(repo_path) / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not full_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "status": "success",
                "file_path": file_path,
                "content": content,
                "size": len(content),
                "lines": len(content.splitlines())
            }
        except UnicodeDecodeError:
            return {
                "status": "error",
                "message": f"File is not a text file: {file_path}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error reading file: {str(e)}"
            }
    
    def list_files(
        self,
        repo_path: str,
        directory: str = ".",
        pattern: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files in a directory.
        
        Args:
            repo_path: Path to repository
            directory: Directory to list (relative to repo)
            pattern: Optional glob pattern to filter files
            session_id: Optional session ID for policy check
            
        Returns:
            Dict containing list of files and directories
            
        Raises:
            PermissionError: If operation not allowed
        """
        self.tool_policy.check_operation(Operation.LIST_FILES, session_id)
        
        full_path = Path(repo_path) / directory
        
        if not full_path.exists():
            return {
                "status": "error",
                "message": f"Directory not found: {directory}"
            }
        
        if not full_path.is_dir():
            return {
                "status": "error",
                "message": f"Path is not a directory: {directory}"
            }
        
        try:
            files = []
            dirs = []
            
            if pattern:
                items = full_path.glob(pattern)
            else:
                items = full_path.iterdir()
            
            for item in items:
                # Skip hidden files and .git directory
                if item.name.startswith('.'):
                    continue
                
                relative_path = str(item.relative_to(repo_path))
                
                if item.is_file():
                    files.append({
                        "path": relative_path,
                        "name": item.name,
                        "size": item.stat().st_size
                    })
                elif item.is_dir():
                    dirs.append({
                        "path": relative_path,
                        "name": item.name
                    })
            
            return {
                "status": "success",
                "directory": directory,
                "files": sorted(files, key=lambda x: x["name"]),
                "directories": sorted(dirs, key=lambda x: x["name"]),
                "total_files": len(files),
                "total_directories": len(dirs)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error listing directory: {str(e)}"
            }
    
    def search_code(
        self,
        repo_path: str,
        pattern: str,
        file_pattern: Optional[str] = None,
        max_results: int = 100,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for code patterns in the repository.
        
        Args:
            repo_path: Path to repository
            pattern: Search pattern (regex)
            file_pattern: Optional file pattern to limit search
            max_results: Maximum number of results to return
            session_id: Optional session ID for policy check
            
        Returns:
            Dict containing search results
            
        Raises:
            PermissionError: If operation not allowed
        """
        self.tool_policy.check_operation(Operation.SEARCH_CODE, session_id)
        
        try:
            # Use git grep for efficient searching
            cmd = ['git', 'grep', '-n', '-i', pattern]
            
            if file_pattern:
                cmd.extend(['--', file_pattern])
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            matches = []
            output_lines = result.stdout.splitlines()
            for line in output_lines[:max_results]:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    matches.append({
                        "file": parts[0],
                        "line": int(parts[1]),
                        "content": parts[2].strip()
                    })
            
            return {
                "status": "success",
                "pattern": pattern,
                "matches": matches,
                "total_matches": len(matches),
                "truncated": len(output_lines) > max_results
            }
        except subprocess.CalledProcessError as e:
            # git grep returns 1 when no matches found
            if e.returncode == 1:
                return {
                    "status": "success",
                    "pattern": pattern,
                    "matches": [],
                    "total_matches": 0,
                    "truncated": False
                }
            return {
                "status": "error",
                "message": f"Search failed: {e.stderr}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Search error: {str(e)}"
            }
    
    def get_branch_info(
        self,
        repo_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current branch information.
        
        Args:
            repo_path: Path to repository
            session_id: Optional session ID for policy check
            
        Returns:
            Dict containing branch information
            
        Raises:
            PermissionError: If operation not allowed
        """
        self.tool_policy.check_operation(Operation.GET_BRANCH, session_id)
        
        try:
            # Get current branch
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            
            # Get current commit
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commit = result.stdout.strip()
            
            # Get commit message
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            message = result.stdout.strip()
            
            return {
                "status": "success",
                "branch": branch,
                "commit": commit,
                "commit_message": message
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Failed to get branch info: {e.stderr}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def list_branches(
        self,
        repo_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all branches in the repository.
        
        Args:
            repo_path: Path to repository
            session_id: Optional session ID for policy check
            
        Returns:
            Dict containing branch list
            
        Raises:
            PermissionError: If operation not allowed
        """
        self.tool_policy.check_operation(Operation.LIST_BRANCHES, session_id)
        
        try:
            result = subprocess.run(
                ['git', 'branch', '-a'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            branches = []
            current_branch = None
            
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith('* '):
                    current_branch = line[2:]
                    branches.append({"name": current_branch, "current": True})
                elif line:
                    branches.append({"name": line, "current": False})
            
            return {
                "status": "success",
                "branches": branches,
                "current_branch": current_branch,
                "total": len(branches)
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Failed to list branches: {e.stderr}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
