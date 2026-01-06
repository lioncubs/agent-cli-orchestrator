"""Tests for query service."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

from src.query.service import QueryService
from src.permissions.tool_policy import ToolPolicy, Operation, OperationTier


@pytest.fixture
def query_service():
    """Create a query service with default policy."""
    return QueryService()


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository structure for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    # Create some test files
    (repo_path / "test.py").write_text("def test():\n    pass\n")
    (repo_path / "README.md").write_text("# Test Repo\n")
    
    # Create a subdirectory
    subdir = repo_path / "src"
    subdir.mkdir()
    (subdir / "module.py").write_text("class TestClass:\n    pass\n")
    
    return str(repo_path)


class TestQueryService:
    """Test QueryService class."""
    
    def test_initialization(self):
        """Test query service initialization."""
        service = QueryService()
        assert service.tool_policy is not None
        assert service.tool_policy.default_tier == OperationTier.READ_ONLY
    
    def test_initialization_with_custom_policy(self):
        """Test initialization with custom policy."""
        policy = ToolPolicy(default_tier=OperationTier.STANDARD)
        service = QueryService(tool_policy=policy)
        assert service.tool_policy == policy
    
    def test_read_file_success(self, query_service, temp_repo):
        """Test reading a file successfully."""
        result = query_service.read_file(temp_repo, "test.py")
        
        assert result["status"] == "success"
        assert result["file_path"] == "test.py"
        assert "def test():" in result["content"]
        assert result["lines"] == 2
        assert result["size"] > 0
    
    def test_read_file_not_found(self, query_service, temp_repo):
        """Test reading a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            query_service.read_file(temp_repo, "nonexistent.py")
    
    def test_read_file_not_a_file(self, query_service, temp_repo):
        """Test reading a directory as file."""
        with pytest.raises(ValueError):
            query_service.read_file(temp_repo, "src")
    
    def test_read_file_permission_check(self, temp_repo):
        """Test that read_file checks permissions."""
        policy = ToolPolicy(default_tier=OperationTier.STANDARD)
        policy.set_session_tier("test-session", OperationTier.READ_ONLY)
        service = QueryService(tool_policy=policy)
        
        # Should work with read-only tier
        result = service.read_file(temp_repo, "test.py", session_id="test-session")
        assert result["status"] == "success"
    
    def test_list_files_success(self, query_service, temp_repo):
        """Test listing files in a directory."""
        result = query_service.list_files(temp_repo, ".")
        
        assert result["status"] == "success"
        assert result["directory"] == "."
        assert result["total_files"] >= 2
        assert result["total_directories"] >= 1
        
        # Check for expected files
        file_names = [f["name"] for f in result["files"]]
        assert "test.py" in file_names
        assert "README.md" in file_names
    
    def test_list_files_subdirectory(self, query_service, temp_repo):
        """Test listing files in a subdirectory."""
        result = query_service.list_files(temp_repo, "src")
        
        assert result["status"] == "success"
        assert result["total_files"] == 1
        file_names = [f["name"] for f in result["files"]]
        assert "module.py" in file_names
    
    def test_list_files_not_found(self, query_service, temp_repo):
        """Test listing nonexistent directory."""
        result = query_service.list_files(temp_repo, "nonexistent")
        
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()
    
    def test_list_files_not_directory(self, query_service, temp_repo):
        """Test listing a file as directory."""
        result = query_service.list_files(temp_repo, "test.py")
        
        assert result["status"] == "error"
        assert "not a directory" in result["message"].lower()
    
    def test_list_files_with_pattern(self, query_service, temp_repo):
        """Test listing files with glob pattern."""
        result = query_service.list_files(temp_repo, ".", pattern="*.py")
        
        assert result["status"] == "success"
        file_names = [f["name"] for f in result["files"]]
        assert "test.py" in file_names
        assert "README.md" not in file_names
    
    def test_list_files_skips_hidden(self, query_service, temp_repo):
        """Test that hidden files are skipped."""
        # Create a hidden file
        Path(temp_repo).joinpath(".hidden").write_text("hidden content")
        
        result = query_service.list_files(temp_repo, ".")
        
        file_names = [f["name"] for f in result["files"]]
        assert ".hidden" not in file_names
    
    @patch('subprocess.run')
    def test_search_code_success(self, mock_run, query_service, temp_repo):
        """Test searching code successfully."""
        # Mock git grep output
        mock_result = MagicMock()
        mock_result.stdout = "test.py:1:def test():\ntest.py:2:    pass\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = query_service.search_code(temp_repo, "def")
        
        assert result["status"] == "success"
        assert result["pattern"] == "def"
        assert len(result["matches"]) == 2
        assert result["matches"][0]["file"] == "test.py"
        assert result["matches"][0]["line"] == 1
    
    @patch('subprocess.run')
    def test_search_code_no_matches(self, mock_run, query_service, temp_repo):
        """Test searching with no matches."""
        # Mock git grep with no matches (exit code 1)
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['git', 'grep'], stderr=""
        )
        
        result = query_service.search_code(temp_repo, "nonexistent")
        
        assert result["status"] == "success"
        assert len(result["matches"]) == 0
        assert result["total_matches"] == 0
    
    @patch('subprocess.run')
    def test_search_code_with_file_pattern(self, mock_run, query_service, temp_repo):
        """Test searching with file pattern."""
        mock_result = MagicMock()
        mock_result.stdout = "test.py:1:def test():\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = query_service.search_code(temp_repo, "def", file_pattern="*.py")
        
        assert result["status"] == "success"
        # Verify git grep was called with file pattern
        call_args = mock_run.call_args[0][0]
        assert '--' in call_args
        assert '*.py' in call_args
    
    @patch('subprocess.run')
    def test_search_code_max_results(self, mock_run, query_service, temp_repo):
        """Test search respects max_results limit."""
        # Create output with many results
        lines = [f"file{i}.py:{i}:match\n" for i in range(150)]
        mock_result = MagicMock()
        mock_result.stdout = "".join(lines)
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = query_service.search_code(temp_repo, "match", max_results=50)
        
        assert result["status"] == "success"
        assert len(result["matches"]) == 50
        assert result["truncated"] is True
    
    @patch('subprocess.run')
    def test_get_branch_info_success(self, mock_run, query_service, temp_repo):
        """Test getting branch information."""
        # Mock git commands
        def side_effect(*args, **kwargs):
            cmd = args[0]
            result = MagicMock()
            result.returncode = 0
            
            if 'rev-parse' in cmd and '--abbrev-ref' in cmd:
                result.stdout = "main\n"
            elif 'rev-parse' in cmd and 'HEAD' in cmd:
                result.stdout = "abc123def456\n"
            elif 'log' in cmd:
                result.stdout = "Initial commit\n"
            
            return result
        
        mock_run.side_effect = side_effect
        
        result = query_service.get_branch_info(temp_repo)
        
        assert result["status"] == "success"
        assert result["branch"] == "main"
        assert result["commit"] == "abc123def456"
        assert result["commit_message"] == "Initial commit"
    
    @patch('subprocess.run')
    def test_get_branch_info_error(self, mock_run, query_service, temp_repo):
        """Test getting branch info with error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['git'], stderr="Not a git repository"
        )
        
        result = query_service.get_branch_info(temp_repo)
        
        assert result["status"] == "error"
        assert "failed" in result["message"].lower()
    
    @patch('subprocess.run')
    def test_list_branches_success(self, mock_run, query_service, temp_repo):
        """Test listing branches."""
        mock_result = MagicMock()
        mock_result.stdout = "* main\n  develop\n  feature/test\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = query_service.list_branches(temp_repo)
        
        assert result["status"] == "success"
        assert result["current_branch"] == "main"
        assert result["total"] == 3
        
        # Check branches
        branch_names = [b["name"] for b in result["branches"]]
        assert "main" in branch_names
        assert "develop" in branch_names
        assert "feature/test" in branch_names
        
        # Check current flag
        current_branches = [b for b in result["branches"] if b["current"]]
        assert len(current_branches) == 1
        assert current_branches[0]["name"] == "main"
    
    @patch('subprocess.run')
    def test_list_branches_error(self, mock_run, query_service, temp_repo):
        """Test listing branches with error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            128, ['git'], stderr="fatal: not a git repository"
        )
        
        result = query_service.list_branches(temp_repo)
        
        assert result["status"] == "error"
        assert "failed" in result["message"].lower()
    
    def test_operations_respect_policy(self, temp_repo):
        """Test that all operations check policy."""
        policy = ToolPolicy(default_tier=OperationTier.READ_ONLY)
        session_id = "test-session"
        
        # Set up a session that denies operations
        # (We'll use a mock to track calls)
        with patch.object(policy, 'check_operation') as mock_check:
            service = QueryService(tool_policy=policy)
            
            # Each operation should call check_operation
            try:
                service.read_file(temp_repo, "test.py", session_id=session_id)
            except:
                pass
            mock_check.assert_called_with(Operation.READ_FILE, session_id)
            
            mock_check.reset_mock()
            try:
                service.list_files(temp_repo, ".", session_id=session_id)
            except:
                pass
            mock_check.assert_called_with(Operation.LIST_FILES, session_id)
