# Testing Infrastructure Plan - Phase 1

## Overview
This document outlines the testing strategy and implementation plan for the Agent CLI Orchestrator project, now prioritized as part of Phase 1.

## Testing Goals
1. Ensure code reliability and correctness
2. Enable confident refactoring
3. Catch regressions early
4. Document expected behavior through tests
5. Achieve >80% code coverage

## Testing Strategy

### 1. Unit Testing
Test individual modules in isolation with mocked dependencies.

**Target Modules:**
- `config_loader.py` - Configuration management
- `git_operations.py` - Git operations
- `copilot_cli.py` - Copilot CLI wrapper
- `main.py` - API endpoint logic

### 2. Integration Testing
Test API endpoints end-to-end with real FastAPI test client.

**Target Endpoints:**
- GET `/` - API information
- GET `/repo` - Repository details
- GET `/branch/current` - Current branch
- POST `/branch/select` - Switch branch
- GET `/worktrees` - List worktrees
- POST `/worktree/create` - Create worktree
- POST `/prompt` - Sync Copilot prompt
- POST `/prompt/async` - Async Copilot prompt

### 3. UI Testing (Optional for Phase 1)
Basic smoke tests to ensure UI loads and renders correctly.

## Testing Stack

### Framework
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities

### API Testing
- **httpx** - Async HTTP client for FastAPI testing
- **TestClient** - FastAPI's built-in test client

### Additional Tools
- **coverage** - Code coverage analysis
- **pytest-xdist** - Parallel test execution

## Implementation Plan

### Phase 1.1: Setup Testing Infrastructure (Day 1)
**Duration:** 2-3 hours

- [ ] Add testing dependencies to `requirements.txt`
- [ ] Create `tests/` directory structure
- [ ] Set up `pytest.ini` configuration
- [ ] Create `conftest.py` with common fixtures
- [ ] Add `.coveragerc` for coverage configuration
- [ ] Update `.gitignore` for test artifacts

**Directory Structure:**
```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_config_loader.py # Config tests
├── test_git_operations.py # Git operations tests
├── test_copilot_cli.py   # Copilot CLI tests
└── test_api.py           # API endpoint tests
```

### Phase 1.2: Unit Tests - Config Loader (Day 1)
**Duration:** 1-2 hours

**Test Cases:**
- [ ] Load valid YAML configuration
- [ ] Handle missing config file
- [ ] Handle malformed YAML
- [ ] Get nested configuration values with dot notation
- [ ] Return default values when keys don't exist
- [ ] Test all property accessors (repository_name, server_host, etc.)

**Coverage Target:** >90%

### Phase 1.3: Unit Tests - Git Operations (Day 2)
**Duration:** 2-3 hours

**Test Cases:**
- [ ] Get current branch (success and failure)
- [ ] Switch branch (success, invalid branch)
- [ ] List worktrees (none, single, multiple)
- [ ] Create worktree (success, already exists, invalid path)
- [ ] Get repository name (from remote URL)
- [ ] Handle subprocess errors gracefully
- [ ] Test timeout scenarios

**Mocking Strategy:**
- Mock `subprocess.run` calls
- Mock Git command outputs
- Test error conditions

**Coverage Target:** >85%

### Phase 1.4: Unit Tests - Copilot CLI (Day 2)
**Duration:** 2-3 hours

**Test Cases:**
- [ ] CLI availability check (installed, not installed)
- [ ] Execute sync prompt (success, error, timeout)
- [ ] Execute async prompt (success, error, timeout)
- [ ] Parse JSON output (valid, invalid, raw text)
- [ ] Handle CLI disabled in config
- [ ] Handle missing CLI binary
- [ ] Test timeout configuration

**Mocking Strategy:**
- Mock `subprocess.run` and `asyncio.create_subprocess_exec`
- Mock CLI command outputs
- Simulate various error conditions

**Coverage Target:** >85%

### Phase 1.5: Integration Tests - API Endpoints (Day 3)
**Duration:** 3-4 hours

**Test Cases:**
- [ ] GET `/` - Returns API information
- [ ] GET `/repo` - Returns repository details
- [ ] GET `/branch/current` - Returns current branch
- [ ] POST `/branch/select` - Switch branch (valid, invalid)
- [ ] GET `/worktrees` - Returns worktree list
- [ ] POST `/worktree/create` - Create worktree (valid, invalid)
- [ ] POST `/prompt` - Execute prompt (CLI available, unavailable)
- [ ] POST `/prompt/async` - Execute async prompt
- [ ] GET `/ui` - Returns HTML page
- [ ] Test error responses (400, 500)
- [ ] Test request validation (Pydantic)

**Testing Approach:**
- Use FastAPI `TestClient`
- Mock underlying service calls (Git, Copilot CLI)
- Test request/response formats
- Verify status codes and error messages

**Coverage Target:** >80%

### Phase 1.6: Coverage Analysis & Reporting (Day 3)
**Duration:** 1 hour

- [ ] Run coverage report
- [ ] Identify uncovered lines
- [ ] Add tests for critical uncovered code
- [ ] Set up coverage reporting in CI/CD (future)
- [ ] Document coverage metrics

**Coverage Goals:**
- Overall: >80%
- Critical modules (config, git_operations, copilot_cli): >85%
- API endpoints: >75%

### Phase 1.7: CI/CD Integration (Day 4 - Optional)
**Duration:** 2-3 hours

- [ ] Create GitHub Actions workflow
- [ ] Run tests on push/PR
- [ ] Upload coverage reports
- [ ] Add status badges to README
- [ ] Configure test environments

## Test File Templates

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestModuleName:
    """Test suite for module_name."""
    
    def test_basic_functionality(self):
        """Test basic functionality description."""
        # Arrange
        expected = "expected_value"
        
        # Act
        result = function_under_test()
        
        # Assert
        assert result == expected
    
    @patch('module.dependency')
    def test_with_mock(self, mock_dependency):
        """Test with mocked dependency."""
        # Arrange
        mock_dependency.return_value = "mocked_value"
        
        # Act
        result = function_under_test()
        
        # Assert
        mock_dependency.assert_called_once()
        assert result == "expected"
```

### API Test Template
```python
import pytest
from fastapi.testclient import TestClient
from main import app

class TestAPIEndpoint:
    """Test suite for API endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_endpoint_success(self, client):
        """Test successful endpoint call."""
        response = client.get("/endpoint")
        
        assert response.status_code == 200
        assert "expected_key" in response.json()
    
    def test_endpoint_error(self, client):
        """Test error handling."""
        response = client.post("/endpoint", json={"invalid": "data"})
        
        assert response.status_code == 400
        assert "detail" in response.json()
```

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_config_loader.py

# Run specific test
pytest tests/test_config_loader.py::TestConfig::test_load_valid_config

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto

# Run and stop on first failure
pytest -x
```

### Coverage Commands
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser

# Generate terminal coverage report
pytest --cov=. --cov-report=term-missing

# Check coverage threshold
pytest --cov=. --cov-fail-under=80
```

## Success Criteria

### Phase 1 Completion
- [ ] All test files created and passing
- [ ] Overall code coverage >80%
- [ ] No critical bugs found
- [ ] All API endpoints tested
- [ ] All core modules tested
- [ ] Tests run in <30 seconds
- [ ] Documentation updated

### Quality Metrics
- **Test Count:** >50 tests
- **Coverage:** >80% overall
- **Execution Time:** <30 seconds
- **Pass Rate:** 100%
- **Flaky Tests:** 0

## Timeline

### Estimated Effort
- **Total Time:** 3-4 days
- **Day 1:** Setup + Config tests (3-5 hours)
- **Day 2:** Git + Copilot tests (4-6 hours)
- **Day 3:** API tests + Coverage (4-5 hours)
- **Day 4:** CI/CD integration (2-3 hours, optional)

### Milestones
1. **Day 1 End:** Testing infrastructure ready, config tests passing
2. **Day 2 End:** All unit tests passing, >85% coverage on modules
3. **Day 3 End:** All integration tests passing, >80% overall coverage
4. **Day 4 End:** CI/CD pipeline operational (optional)

## Future Enhancements (Post Phase 1)

- [ ] UI automated testing (Selenium/Playwright)
- [ ] Load/performance testing
- [ ] Security testing
- [ ] Mutation testing
- [ ] Property-based testing
- [ ] Contract testing for APIs
- [ ] E2E testing with Docker
- [ ] Visual regression testing

## Dependencies

### New Python Packages
```
pytest>=7.4.3
pytest-asyncio>=0.21.1
pytest-cov>=4.1.0
pytest-mock>=3.12.0
httpx>=0.25.2
coverage>=7.3.2
```

### Development Tools
- pytest (test runner)
- coverage (coverage analysis)
- Editor/IDE with pytest integration

## Notes

- All tests should be independent and idempotent
- Use fixtures for common setup/teardown
- Mock external dependencies (Git, Copilot CLI)
- Follow AAA pattern: Arrange, Act, Assert
- Keep tests focused and readable
- Document complex test scenarios
- Use descriptive test names

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Status:** Planning Complete
**Priority:** Phase 1 - High Priority
**Estimated Completion:** 3-4 days