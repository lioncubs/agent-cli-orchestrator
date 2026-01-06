# Agent CLI Orchestrator - Action Plan

## Executive Summary
This document outlines the concrete action plan for the next development phase of the Agent CLI Orchestrator project. The project currently has a solid foundation with 98 passing tests and 76.27% code coverage.

## Current Status (as of January 2, 2026)

### ✅ Completed
- **Core Infrastructure**: FastAPI application with async support
- **Configuration System**: YAML-based, multi-repository support
- **Git Operations**: Branch management, worktree creation and management
- **Copilot CLI Integration**: Sync/async execution with session management
- **Web Interface**: Full-featured UI for testing all capabilities
- **Testing Infrastructure**: 98 tests passing with 76.27% coverage
- **Documentation**: Comprehensive README, API docs, and planning documents
- **Docker Support**: Full containerization with Docker Compose

### 📊 Current Metrics
- **Total Tests**: 98 (all passing)
- **Coverage**: 76.27% overall
  - `config_loader.py`: 100% ✅
  - `git_operations.py`: 93.41% ✅
  - `activity_log.py`: 88.24% ✅
  - `main.py`: 71.30% ⚠️
  - `copilot_cli.py`: 59.87% ⚠️

### 🎯 Immediate Goals
1. Improve test coverage to 80%+ overall
2. Fix deprecation warnings (datetime.utcnow)
3. Add missing test coverage for streaming and logging features
4. Update documentation with latest features
5. Prepare for Phase 2 enhancements

---

## Phase 1: Coverage & Quality Improvements (Priority: HIGH)

### Task 1.1: Fix Deprecation Warnings ⏰ Estimated: 30 minutes
**File**: `activity_log.py`

**Issue**: Using deprecated `datetime.utcnow()`

**Action**:
```python
# Replace line 32 in activity_log.py:
# OLD: "timestamp": datetime.utcnow().isoformat() + "Z",
# NEW: "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
```

**Testing**: 
- Verify all tests still pass
- Check that timestamp format is preserved

---

### Task 1.2: Improve copilot_cli.py Coverage ⏰ Estimated: 3-4 hours
**Current**: 59.87% | **Target**: 80%+

**Missing Coverage Areas** (lines 291-362, 369-390):
- Streaming functionality (`execute_prompt_stream`, `_stream_copilot_output`)
- Full output logging paths
- Error handling in streaming mode
- Session ID handling edge cases

**Actions**:
1. Add tests for streaming prompt execution
2. Test full output flag behavior
3. Test log file creation and writing
4. Test error scenarios in streaming
5. Test session management edge cases

**New Test Cases**:
```python
# tests/test_copilot_cli.py
def test_execute_prompt_with_full_output()
def test_execute_prompt_stream_success()
def test_execute_prompt_stream_error()
def test_log_file_creation()
def test_session_id_handling()
```

---

### Task 1.3: Improve main.py Coverage ⏰ Estimated: 2-3 hours
**Current**: 71.30% | **Target**: 80%+

**Missing Coverage Areas**:
- Lines 108-109: Repository list endpoint edge cases
- Lines 115-145: Error handling in repo operations
- Lines 261-270: Worktree management errors
- Lines 339-353: Streaming endpoint
- Lines 406-417: Copilot logs endpoint
- Lines 470-481, 488-504: UI rendering
- Lines 553-589: Streaming test page

**Actions**:
1. Add tests for `/repos` endpoint
2. Add tests for `/prompt/stream` endpoint
3. Add tests for `/logs/copilot` endpoint
4. Add UI endpoint tests (basic smoke tests)
5. Test error scenarios in all new endpoints

**New Test Cases**:
```python
# tests/test_api.py
def test_list_repos_endpoint()
def test_execute_prompt_stream_endpoint()
def test_copilot_logs_endpoint()
def test_streaming_test_ui()
def test_repo_name_parameter_handling()
def test_show_full_output_flag()
```

---

### Task 1.4: Add Integration Tests for New Features ⏰ Estimated: 2 hours
**Features to Test**:
- Repository mapping (repo_name parameter)
- Full output flag (show_full_output)
- Streaming endpoints
- Copilot log retrieval

**New Test Cases**:
```python
# tests/test_api.py
def test_prompt_with_repo_name()
def test_prompt_with_show_full_output()
def test_branch_operations_with_repo_name()
def test_worktree_operations_with_repo_name()
```

---

## Phase 2: Documentation Updates (Priority: HIGH)

### Task 2.1: Update README.md ⏰ Estimated: 1 hour
**Sections to Update**:
- Add streaming feature documentation
- Document repository mapping feature
- Add examples of show_full_output flag
- Update API endpoint list with new endpoints

**Changes**:
```markdown
## New Features
- **Multi-Repository Support**: Switch between configured repositories
- **Streaming Output**: Real-time SSE streaming for Copilot responses
- **Full Output Mode**: Get complete stdout/stderr from Copilot sessions
- **Activity Logging**: Track all API operations
```

---

### Task 2.2: Update API.md ⏰ Estimated: 1.5 hours
**New Endpoints to Document**:
- `GET /repos` - List configured repositories
- `POST /prompt/stream` - Streaming Copilot execution
- `GET /logs/copilot` - Detailed Copilot logs
- `GET /streaming-test` - Streaming test UI

**Parameter Updates**:
- Document `repo_name` parameter on all endpoints
- Document `show_full_output` flag
- Add SSE response format examples

---

### Task 2.3: Create CHANGELOG.md ⏰ Estimated: 30 minutes
**Purpose**: Track version history and changes

**Initial Entries**:
```markdown
# Changelog

## [0.2.0] - 2026-01-XX
### Added
- Multi-repository support with repo_name parameter
- Streaming output via SSE (Server-Sent Events)
- Full output mode for Copilot responses
- Activity logging for all operations
- Detailed Copilot execution logs

### Changed
- Configuration format updated to support multiple repositories
- API endpoints now accept optional repo_name parameter

### Fixed
- Deprecated datetime.utcnow() usage

## [0.1.0] - 2024-12-21
### Added
- Initial release
- GitHub Copilot CLI integration
- Git operations (branches, worktrees)
- Web interface
- Docker support
```

---

## Phase 3: Code Quality Improvements (Priority: MEDIUM)

### Task 3.1: Add Type Hints ⏰ Estimated: 2 hours
**Files to Update**:
- `activity_log.py` - Add return type hints
- `main.py` - Complete type hints for all functions
- `copilot_cli.py` - Add type hints for internal methods

**Example**:
```python
from typing import Dict, List, Optional, Any

def add(action: str, status: str, payload: Dict[str, Any], 
        result: Dict[str, Any]) -> None:
    """Add activity log entry."""
    ...
```

---

### Task 3.2: Code Refactoring ⏰ Estimated: 2 hours
**Opportunities**:
1. Extract common error handling patterns into decorator
2. Create response model classes for consistency
3. Refactor large functions in `main.py` (UI generation)
4. Extract log file path generation to helper function

**Example Decorator**:
```python
def handle_git_errors(func):
    """Decorator to handle git operation errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            if result.get("status") == "error":
                raise HTTPException(status_code=400, detail=result.get("message"))
            return result
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return wrapper
```

---

## Phase 4: CI/CD Setup (Priority: MEDIUM)

### Task 4.1: Create GitHub Actions Workflow ⏰ Estimated: 2 hours
**File**: `.github/workflows/test.yml`

**Workflow**:
```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

### Task 4.2: Add Code Quality Checks ⏰ Estimated: 1.5 hours
**Tools to Add**:
- **Black**: Code formatting
- **Flake8**: Linting
- **mypy**: Type checking
- **isort**: Import sorting

**Configuration Files**:

`.github/workflows/lint.yml`:
```yaml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        pip install black flake8 mypy isort
    - name: Run formatters and linters
      run: |
        black --check .
        isort --check-only .
        flake8 .
        mypy .
```

---

## Phase 5: Feature Enhancements (Priority: LOW)

### Task 5.1: WebSocket Support ⏰ Estimated: 1 week
**Purpose**: Real-time bidirectional communication

**Implementation**:
- Add WebSocket endpoint for live updates
- Push git operation notifications
- Stream Copilot output over WebSocket
- Send progress updates for long operations

---

### Task 5.2: AWS CLI Integration ⏰ Estimated: 1 week
**New Module**: `aws_cli.py`

**Features**:
- Execute AWS CLI commands
- Profile management
- Region selection
- Output format handling

---

### Task 5.3: Authentication System ⏰ Estimated: 2 weeks
**Methods**:
- API Key authentication
- JWT tokens
- Optional OAuth 2.0

**Security Features**:
- Rate limiting
- Request validation
- Audit logging

---

## Timeline & Milestones

### Week 1: Quality & Testing
- **Days 1-2**: Fix deprecation warnings, improve copilot_cli.py coverage
- **Days 3-4**: Improve main.py coverage, add integration tests
- **Day 5**: Documentation updates (README, API.md, CHANGELOG)

**Milestone**: 80%+ test coverage achieved

### Week 2: CI/CD & Code Quality
- **Days 1-2**: Set up GitHub Actions workflows
- **Days 3-4**: Add linting and type checking
- **Day 5**: Code refactoring and cleanup

**Milestone**: Automated testing and quality checks in place

### Week 3-4: Feature Planning
- **Week 3**: Research and design for WebSocket support
- **Week 4**: Research and design for AWS CLI integration

**Milestone**: Detailed specifications ready for Phase 2 features

---

## Success Criteria

### Phase 1 Completion
- ✅ All tests passing (98+)
- ✅ Overall coverage ≥ 80%
- ✅ No deprecation warnings
- ✅ All modules ≥ 75% coverage
- ✅ Documentation up to date

### Phase 2 Completion
- ✅ CI/CD pipeline operational
- ✅ Automated tests on all PRs
- ✅ Code quality checks passing
- ✅ Coverage reporting integrated

### Long-term Goals
- 🎯 3+ CLI tools integrated
- 🎯 Authentication implemented
- 🎯 WebSocket support operational
- 🎯 Production deployment ready

---

## Risk Management

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking API changes | High | API versioning, deprecation warnings |
| Test flakiness | Medium | Proper mocking, isolated tests |
| Coverage gaps in edge cases | Medium | Systematic review of uncovered lines |
| Dependency updates | Medium | Automated dependency checking |

### Resource Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Time constraints | Medium | Prioritize critical tasks, incremental delivery |
| Complexity creep | Medium | Stick to defined scope, defer non-critical items |

---

## Next Immediate Actions (Today)

1. ✅ **Create this action plan** - DONE
2. 🔄 **Fix datetime deprecation warning** - 30 minutes
3. 🔄 **Add tests for streaming functionality** - 2 hours
4. 🔄 **Commit and push progress** - Report with updated plan

## Commands to Execute

```bash
# Fix deprecation warning
# Edit activity_log.py line 32

# Run tests to verify
pytest -v

# Add new tests for streaming
# Edit tests/test_copilot_cli.py and tests/test_api.py

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Commit changes
git add -A
git commit -m "Improve test coverage and fix deprecation warnings"
git push
```

---

## Notes
- This plan is living document - update as priorities change
- Focus on incremental progress with frequent commits
- Keep tests passing at all times
- Document decisions and rationale
- Celebrate small wins along the way

---

**Last Updated**: January 2, 2026  
**Status**: Phase 1 - Coverage & Quality Improvements  
**Next Review**: January 9, 2026
