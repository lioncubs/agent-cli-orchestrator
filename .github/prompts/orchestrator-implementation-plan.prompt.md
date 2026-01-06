# Agent CLI Orchestrator - Implementation Plan

> **Complete Implementation Plan**

---

## Project Overview

**Purpose:** Bring GitHub Copilot CLI's agent delegation capabilities to **non-GitHub repositories** (Bitbucket, GitLab, Azure DevOps, self-hosted Git) where GitHub's cloud Coding Agent doesn't work.

**We ARE the "cloud agent" for non-GitHub repos.**

---

## Table of Contents

1. [Golden Rule](#-golden-rule)
2. [Session Types](#session-types)
3. [Implementation Strategy](#implementation-strategy)
4. [Final Directory Structure](#final-directory-structure)
5. [Phase 0: Plan Documentation](#phase-0-plan-documentation)
6. [Phase 1: Code Reorganization](#phase-1-code-reorganization)
7. [Phase 2: Session Management](#phase-2-session-management)
8. [Phase 3: Query & Research Modes](#phase-3-query--research-modes)
9. [Phase 4: Delegation Mode](#phase-4-delegation-mode)
10. [Phase 5: MCP Server](#phase-5-mcp-server)
11. [Phase 6: Platform Integrations](#phase-6-platform-integrations)
12. [Phase 7: Authentication & Storage](#phase-7-authentication--storage)
13. [Phase 8: Security Hardening](#phase-8-security-hardening)
14. [Phase 9: Modern Dashboard UI](#phase-9-modern-dashboard-ui)
15. [Phase 10: Documentation](#phase-10-documentation)
16. [Configuration Schema](#configuration-schema-final)
17. [Deferred Items](#deferred-items-post-v1)
18. [Test Coverage Requirements](#test-coverage-requirements)
19. [Mermaid Diagram Specifications](#mermaid-diagram-specifications)

---

## 🏆 Golden Rule

**All delegations MUST:**

1. Create isolated worktree with new branch off current branch
2. Work only in that worktree — never touch source branch
3. Commit only delegation-produced changes
4. Require Pull Request to merge — human review mandatory

---

## Session Types

| Type | Worktree | Branch | Commits | Cleanup | Use Case |
|------|----------|--------|---------|---------|----------|
| **Query** | ❌ None | Direct repo | ❌ Never | Immediate | Quick Q&A, simple lookups |
| **Research** | ✅ Temporary | Detached HEAD | ❌ Never | Auto on complete | Long analysis, multi-file review |
| **Delegation** | ✅ Persistent | Named branch | ✅ Required | After PR merge/abandon | Code changes, feature work |

---

## Implementation Strategy

- **Branching:** Each phase branches from previous
- **Full implementation:** No stubs, complete working code
- **Test coverage:** Minimum 80% enforced
- **Commit & push:** Each phase ends with push to origin
- **Reviewable:** Each phase can be reverted independently

```
main
 └──▶ phase-0-plan-docs
        └──▶ phase-1-reorganization
               └──▶ phase-2-sessions
                      └──▶ phase-3-query-research
                             └──▶ phase-4-delegation
                                    └──▶ phase-5-mcp
                                           └──▶ phase-6-platforms
                                                  └──▶ phase-7-auth-storage
                                                         └──▶ phase-8-security
                                                                └──▶ phase-9-modern-ui
                                                                       └──▶ phase-10-documentation
                                                                              └──▶ main (final merge)
```

---

## Final Directory Structure

```
agent-cli-orchestrator/
├── main.py                              # Entry point
├── config.yaml                          # Configuration
├── requirements.txt                     # Python dependencies
├── .github/
│   └── prompts/
│       ├── orchestrator-implementation-plan.prompt.md
│       └── mermaid-color-palette.md
├── scripts/
│   ├── export-diagrams.sh              # Mermaid → PNG export
│   └── generate-dev-cert.sh            # TLS cert generation
├── deploy/
│   ├── orchestrator.service            # Systemd service
│   └── Caddyfile                       # Reverse proxy config
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                   # Config loading
│   │   ├── activity.py                 # Activity logging
│   │   └── security.py                 # Encryption, hashing
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── models.py                   # User, APIKey, Session
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   └── api_key.py              # API key auth
│   │   └── service.py                  # Auth business logic
│   ├── identity/
│   │   ├── __init__.py
│   │   ├── models.py                   # GitIdentity, GitCredential
│   │   └── git_config.py               # Git identity injection
│   ├── permissions/
│   │   ├── __init__.py
│   │   ├── models.py                   # PermissionTier
│   │   └── tool_policy.py              # Copilot tool allow/deny
│   ├── session/
│   │   ├── __init__.py
│   │   ├── models.py                   # Session, Turn, SessionType
│   │   ├── manager.py                  # Session lifecycle
│   │   └── store.py                    # Session persistence
│   ├── query/
│   │   ├── __init__.py
│   │   ├── service.py                  # Quick query execution
│   │   └── research_service.py         # Research with temp worktree
│   ├── delegation/
│   │   ├── __init__.py
│   │   ├── service.py                  # Delegation lifecycle
│   │   ├── worktree_manager.py         # Worktree creation/cleanup
│   │   ├── commit_manager.py           # Selective commits
│   │   └── pr_manager.py               # PR creation orchestration
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── copilot.py                  # Copilot CLI wrapper
│   │   ├── git.py                      # Git operations
│   │   └── platforms/
│   │       ├── __init__.py
│   │       ├── base.py                 # GitPlatform ABC
│   │       ├── bitbucket.py            # Bitbucket Cloud + Server
│   │       ├── gitlab.py               # GitLab.com + self-hosted
│   │       ├── azure_devops.py         # Azure DevOps
│   │       └── generic.py              # Manual PR fallback
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py                     # StorageBackend ABC
│   │   ├── yaml_backend.py             # YAML file storage
│   │   └── encrypted.py                # Fernet encryption
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── repo_registry.py            # Repository CRUD
│   │   ├── user_registry.py            # User CRUD
│   │   ├── session_registry.py         # Session persistence
│   │   └── research_store.py           # Research artifacts
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                      # FastAPI app creation
│   │   ├── models.py                   # Pydantic models
│   │   ├── dependencies.py             # DI, auth deps
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # Auth middleware
│   │   │   ├── rate_limit.py           # Rate limiting
│   │   │   └── security_headers.py     # CORS, CSP, HSTS
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # /auth/* endpoints
│   │   │   ├── sessions.py             # /sessions/* endpoints
│   │   │   ├── query.py                # /query endpoint
│   │   │   ├── delegation.py           # Delegation endpoints
│   │   │   ├── repositories.py         # /repos/* endpoints
│   │   │   └── monitoring.py           # /activity, /logs
│   │   └── web/
│   │       └── legacy_ui.py            # Existing simple UI
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py                   # FastMCP setup
│   │   ├── models.py                   # Tool I/O models
│   │   ├── context_manager.py          # History injection
│   │   ├── resources.py                # MCP resources
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── query.py                # query, research tools
│   │       ├── session.py              # Session management tools
│   │       ├── delegation.py           # Delegation tools
│   │       └── repository.py           # Repository tools
│   └── ui/                             # Modern React dashboard
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── index.html
│       ├── src/
│       │   ├── main.tsx
│       │   ├── App.tsx
│       │   ├── api/                    # API client
│       │   ├── components/             # Reusable components
│       │   ├── pages/                  # Page components
│       │   ├── hooks/                  # Custom hooks
│       │   └── store/                  # State management
│       └── public/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # Shared fixtures
│   ├── core/
│   │   ├── test_config.py
│   │   └── test_activity.py
│   ├── auth/
│   │   ├── test_api_key.py
│   │   └── test_service.py
│   ├── identity/
│   │   └── test_git_config.py
│   ├── permissions/
│   │   └── test_tool_policy.py
│   ├── session/
│   │   ├── test_models.py
│   │   ├── test_manager.py
│   │   ├── test_store.py
│   │   └── test_context_manager.py
│   ├── query/
│   │   ├── test_service.py
│   │   └── test_research_service.py
│   ├── delegation/
│   │   ├── test_service.py
│   │   ├── test_worktree_manager.py
│   │   ├── test_commit_manager.py
│   │   └── test_pr_manager.py
│   ├── integrations/
│   │   ├── test_copilot.py
│   │   └── test_git.py
│   ├── platforms/
│   │   ├── test_base.py
│   │   ├── test_bitbucket.py
│   │   ├── test_gitlab.py
│   │   ├── test_azure_devops.py
│   │   └── test_generic.py
│   ├── storage/
│   │   ├── test_yaml_backend.py
│   │   └── test_encrypted.py
│   ├── registry/
│   │   ├── test_repo_registry.py
│   │   ├── test_user_registry.py
│   │   └── test_research_store.py
│   ├── api/
│   │   ├── test_auth_routes.py
│   │   ├── test_session_routes.py
│   │   ├── test_query_routes.py
│   │   ├── test_delegation_routes.py
│   │   └── test_repo_routes.py
│   ├── mcp/
│   │   ├── test_server.py
│   │   ├── test_tools_query.py
│   │   ├── test_tools_session.py
│   │   └── test_tools_delegation.py
│   ├── middleware/
│   │   ├── test_auth.py
│   │   ├── test_rate_limit.py
│   │   └── test_security_headers.py
│   └── ui/
│       └── test_api_integration.py
├── docs/
│   ├── diagrams/
│   │   ├── mermaid/                    # Source .mmd files
│   │   │   ├── architecture-overview.mmd
│   │   │   ├── session-lifecycle.mmd
│   │   │   ├── delegation-flow.mmd
│   │   │   ├── golden-rule-isolation.mmd
│   │   │   ├── query-research-flow.mmd
│   │   │   ├── mcp-tool-flow.mmd
│   │   │   ├── auth-flow.mmd
│   │   │   ├── platform-pr-flow.mmd
│   │   │   └── context-injection.mmd
│   │   └── png/                        # Exported hi-res PNGs
│   ├── installation/
│   │   ├── local.md
│   │   ├── server.md
│   │   └── devcontainer.md
│   ├── mcp/
│   │   ├── README.md
│   │   ├── installation.md
│   │   ├── authentication.md
│   │   ├── tools/
│   │   │   ├── README.md
│   │   │   ├── query.md
│   │   │   ├── session.md
│   │   │   ├── delegation.md
│   │   │   └── repository.md
│   │   ├── resources.md
│   │   ├── client-setup/
│   │   │   ├── claude-desktop.md
│   │   │   ├── vscode.md
│   │   │   └── custom-client.md
│   │   ├── examples/
│   │   │   ├── research-workflow.md
│   │   │   ├── delegation-workflow.md
│   │   │   └── multi-repo.md
│   │   └── troubleshooting.md
│   ├── api/
│   │   └── README.md                   # OpenAPI reference
│   ├── user-guide/
│   │   └── README.md
│   └── architecture.md
└── .devcontainer/
    └── devcontainer.json
```

---

## Phase 0: Plan Documentation

**Branch:** `phase-0-plan-docs` (from `main`)

### Deliverables

| File | Description |
|------|-------------|
| `.github/prompts/orchestrator-implementation-plan.prompt.md` | Complete implementation plan as reusable prompt |
| `.github/prompts/mermaid-color-palette.md` | Standardized color palette reference |
| `docs/diagrams/mermaid/*.mmd` | All 9 Mermaid diagram source files |
| `docs/diagrams/png/*.png` | Exported hi-res PNG diagrams |
| `scripts/export-diagrams.sh` | Diagram export script |

### Diagrams Required

| Diagram | File | Description |
|---------|------|-------------|
| Architecture Overview | `architecture-overview.mmd` | Clients → API/MCP → Services → Integrations |
| Session Lifecycle | `session-lifecycle.mmd` | Query/Research/Delegation states |
| Delegation Flow | `delegation-flow.mmd` | Create worktree → Execute → Commit → PR |
| Golden Rule Isolation | `golden-rule-isolation.mmd` | Branch isolation visualization |
| Query & Research Flow | `query-research-flow.mmd` | Direct vs temp worktree paths |
| MCP Tool Flow | `mcp-tool-flow.mmd` | Tool invocation → Service → Response |
| Auth Flow | `auth-flow.mmd` | API key validation → User context |
| Platform PR Flow | `platform-pr-flow.mmd` | Bitbucket/GitLab/Azure paths |
| Context Injection | `context-injection.mmd` | Session history → Prompt building |

### Acceptance Criteria

- [ ] Prompt file contains all phase details
- [ ] Color palette documented
- [ ] All 9 Mermaid diagrams created
- [ ] All diagrams exported to PNG (2x scale)
- [ ] Export script functional
- [ ] Committed and pushed

---

## Phase 1: Code Reorganization

**Branch:** `phase-1-reorganization` (from `phase-0-plan-docs`)

### Deliverables

| Task | Files |
|------|-------|
| Create src/ package structure | All `__init__.py` files |
| Move config loader | `config_loader.py` → `src/core/config.py` |
| Move activity log | `activity_log.py` → `src/core/activity.py` |
| Move Copilot CLI | `copilot_cli.py` → `src/integrations/copilot.py` |
| Move Git operations | `git_operations.py` → `src/integrations/git.py` |
| Split main.py | Extract to `src/api/` modules |
| Create thin entry point | `main.py` imports from `src/` |
| Update all imports | Fix import paths throughout |

### Files to Create

```
src/__init__.py
src/core/__init__.py
src/core/config.py              # From config_loader.py
src/core/activity.py            # From activity_log.py
src/integrations/__init__.py
src/integrations/copilot.py     # From copilot_cli.py
src/integrations/git.py         # From git_operations.py
src/api/__init__.py
src/api/app.py                  # FastAPI app setup
src/api/models.py               # Pydantic models from main.py
src/api/routes/__init__.py
src/api/routes/repositories.py  # Repo endpoints from main.py
src/api/routes/copilot.py       # Copilot endpoints from main.py
src/api/routes/worktrees.py     # Worktree endpoints from main.py
src/api/routes/monitoring.py    # Activity/logs from main.py
src/api/web/__init__.py
src/api/web/legacy_ui.py        # UI HTML from main.py
```

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/core/test_config.py` | Config loading, repo resolution |
| `tests/core/test_activity.py` | Activity log operations |
| `tests/integrations/test_copilot.py` | Copilot CLI wrapper |
| `tests/integrations/test_git.py` | Git operations |
| `tests/api/test_routes.py` | All API endpoints |

### Acceptance Criteria

- [ ] All code moved to `src/` structure
- [ ] `main.py` is thin entry point only
- [ ] All existing tests pass with new imports
- [ ] New test files created for each module
- [ ] Test coverage ≥ 80%
- [ ] Application starts and functions identically
- [ ] Committed and pushed

---

## Phase 2: Session Management

**Branch:** `phase-2-sessions` (from `phase-1-reorganization`)

### Deliverables

| Component | File | Description |
|-----------|------|-------------|
| Session Models | `src/session/models.py` | Session, Turn, SessionType, SessionStatus |
| Session Manager | `src/session/manager.py` | Full session lifecycle |
| Session Store | `src/session/store.py` | In-memory with interface for DB |
| Context Manager | `src/mcp/context_manager.py` | History injection for prompts |
| API Routes | `src/api/routes/sessions.py` | Session endpoints |

### Models

```python
# src/session/models.py

class SessionType(str, Enum):
    QUERY = "query"
    RESEARCH = "research"
    DELEGATION = "delegation"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    COMMITTED = "committed"
    PR_CREATED = "pr_created"
    MERGED = "merged"
    ABANDONED = "abandoned"
    CLOSED = "closed"

class Turn(BaseModel):
    id: int
    prompt: str
    response: str
    response_summary: str
    files_analyzed: List[str] = []
    files_changed: List[str] = []
    timestamp: datetime

class Session(BaseModel):
    id: UUID
    type: SessionType
    status: SessionStatus
    repo_name: str
    user_id: str
    user_identity: Optional[GitIdentity] = None
    created_at: datetime
    last_activity_at: datetime
    expires_at: Optional[datetime] = None
    
    # Copilot session tracking
    copilot_session_id: Optional[str] = None
    
    # Research/Delegation fields
    base_branch: Optional[str] = None
    base_commit: Optional[str] = None
    session_branch: Optional[str] = None
    worktree_path: Optional[str] = None
    is_temporary: bool = False
    
    # Conversation
    turns: List[Turn] = []
    
    # Delegation results
    commit_sha: Optional[str] = None
    files_changed: List[str] = []
    pr_url: Optional[str] = None
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` | Create new session |
| GET | `/sessions` | List sessions (filter by type, status, repo) |
| GET | `/sessions/{id}` | Get session details |
| POST | `/sessions/{id}/continue` | Send follow-up prompt |
| DELETE | `/sessions/{id}` | Close/abandon session |

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/session/test_models.py` | Model validation, serialization |
| `tests/session/test_manager.py` | Create, continue, close lifecycle |
| `tests/session/test_store.py` | CRUD operations, expiry |
| `tests/session/test_context_manager.py` | History injection, truncation |
| `tests/api/test_session_routes.py` | All session endpoints |

### Acceptance Criteria

- [ ] Session models fully defined
- [ ] Session manager handles full lifecycle
- [ ] Context injection working for multi-turn
- [ ] API endpoints functional
- [ ] Test coverage ≥ 80%
- [ ] Committed and pushed

---

## Phase 3: Query & Research Modes

**Branch:** `phase-3-query-research` (from `phase-2-sessions`)

### Deliverables

| Component | File | Description |
|-----------|------|-------------|
| Query Service | `src/query/service.py` | Quick read-only execution |
| Research Service | `src/query/research_service.py` | Temp worktree research |
| Research Store | `src/registry/research_store.py` | Artifact persistence |
| Tool Policy | `src/permissions/tool_policy.py` | Read-only restrictions |
| API Routes | `src/api/routes/query.py` | Query/research endpoints |

### Research Artifact Model

```python
# src/session/models.py (extended)

class ResearchFinding(BaseModel):
    file: str
    lines: Optional[str] = None
    note: str
    code_snippet: Optional[str] = None

class ResearchArtifact(BaseModel):
    research_id: UUID
    repo_name: str
    base_branch: str
    base_commit: str
    created_at: datetime
    user_id: str
    
    summary: str
    findings: List[ResearchFinding]
    recommendations: List[str]
    conversation: List[TurnSummary]
    
    suggested_delegation_prompt: str
    relevant_files: List[str]
```

### Tool Policy

```python
# src/permissions/tool_policy.py

class PermissionTier(str, Enum):
    READ_ONLY = "read-only"
    RESTRICTED = "restricted"
    FULL = "full"

TIER_POLICIES = {
    PermissionTier.READ_ONLY: {
        "deny": ["write", "shell(rm)", "shell(git commit)", "shell(git push)",
                 "shell(git checkout)", "shell(git reset)", "shell(mv)"]
    },
    PermissionTier.RESTRICTED: {
        "allow": ["shell(git add)", "shell(git commit)"],
        "deny": ["shell(git push)", "shell(rm -rf)"]
    },
    PermissionTier.FULL: {
        "require_scope": "admin"
    }
}

def build_tool_flags(tier: PermissionTier) -> List[str]:
    """Build Copilot CLI --allow-tool/--deny-tool flags."""
    ...
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | Execute read-only query |
| POST | `/sessions` (type=research) | Start research session |
| POST | `/sessions/{id}/complete` | End research, generate artifact |
| GET | `/research` | List research artifacts |
| GET | `/research/{id}` | Get artifact details |
| POST | `/research/{id}/delegate` | Start delegation from research |
| DELETE | `/research/{id}` | Delete artifact |

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/query/test_service.py` | Query execution, tool restrictions |
| `tests/query/test_research_service.py` | Research lifecycle, worktree |
| `tests/registry/test_research_store.py` | Artifact CRUD |
| `tests/permissions/test_tool_policy.py` | Policy building, flag generation |
| `tests/api/test_query_routes.py` | All query/research endpoints |

### Acceptance Criteria

- [ ] Query executes with read-only restrictions
- [ ] Research creates temp worktree
- [ ] Research artifacts saved and retrievable
- [ ] Branch selection prefers main
- [ ] Worktree cleanup on research complete
- [ ] Test coverage ≥ 80%
- [ ] Committed and pushed

---

## Phase 4: Delegation Mode

**Branch:** `phase-4-delegation` (from `phase-3-query-research`)

### Deliverables

| Component | File | Description |
|-----------|------|-------------|
| Delegation Service | `src/delegation/service.py` | Full delegation lifecycle |
| Worktree Manager | `src/delegation/worktree_manager.py` | Create/cleanup worktrees |
| Commit Manager | `src/delegation/commit_manager.py` | Selective commits |
| PR Manager | `src/delegation/pr_manager.py` | PR creation orchestration |
| API Routes | `src/api/routes/delegation.py` | Delegation endpoints |

### Worktree Manager

```python
# src/delegation/worktree_manager.py

class WorktreeManager:
    def create_delegation_worktree(
        self,
        repo_path: str,
        base_branch: str,
        session_id: UUID,
        user_id: str,
        task_slug: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Create worktree for delegation.
        
        Returns: (worktree_path, branch_name)
        Branch format: agent/<user_id>/<session_uuid_short>-<slug>
        """
        ...
    
    def create_temp_worktree(
        self,
        repo_path: str,
        commit_sha: str,
        session_id: UUID
    ) -> str:
        """Create temporary worktree for research (detached HEAD)."""
        ...
    
    def cleanup_worktree(
        self,
        worktree_path: str,
        delete_branch: bool = False
    ) -> None:
        """Remove worktree and optionally delete branch."""
        ...
```

### Commit Manager

```python
# src/delegation/commit_manager.py

class CommitManager:
    def get_changed_files(self, worktree_path: str) -> List[str]:
        """Get files modified/added/deleted in worktree."""
        ...
    
    def commit_delegation_changes(
        self,
        worktree_path: str,
        user_identity: GitIdentity,
        agent_identity: GitIdentity,
        message: Optional[str] = None
    ) -> Optional[str]:
        """
        Commit only changed files.
        
        - Sets GIT_AUTHOR_* from user_identity
        - Sets GIT_COMMITTER_* from agent_identity
        - Returns commit SHA or None if no changes
        """
        ...
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` (type=delegation) | Start delegation |
| POST | `/sessions/{id}/continue` | Continue delegation |
| POST | `/sessions/{id}/commit` | Commit changes |
| POST | `/sessions/{id}/pr` | Create PR |
| DELETE | `/sessions/{id}` | Abandon delegation |

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/delegation/test_service.py` | Full delegation lifecycle |
| `tests/delegation/test_worktree_manager.py` | Worktree CRUD |
| `tests/delegation/test_commit_manager.py` | Selective commits, identity |
| `tests/delegation/test_pr_manager.py` | PR creation |
| `tests/api/test_delegation_routes.py` | All delegation endpoints |
| Integration test | Full flow: delegate → commit → PR |

### Acceptance Criteria

- [ ] Delegation creates isolated worktree + branch
- [ ] Branch naming follows pattern `agent/<user>/<id>-<slug>`
- [ ] Only changed files are committed
- [ ] Git identity correctly set (author = user, committer = agent)
- [ ] Worktree cleanup works
- [ ] **Golden Rule enforced**
- [ ] Test coverage ≥ 80%
- [ ] Committed and pushed

---

## Phase 5: MCP Server

**Branch:** `phase-5-mcp` (from `phase-4-delegation`)

### Deliverables

| Component | File | Description |
|-----------|------|-------------|
| MCP Server | `src/mcp/server.py` | FastMCP setup |
| MCP Models | `src/mcp/models.py` | Tool I/O models |
| Query Tools | `src/mcp/tools/query.py` | query, start_research, complete_research |
| Session Tools | `src/mcp/tools/session.py` | continue_session, list_sessions, close_session |
| Delegation Tools | `src/mcp/tools/delegation.py` | start_delegation, commit_changes, create_pr |
| Repository Tools | `src/mcp/tools/repository.py` | list_repos, get_repo |
| Resources | `src/mcp/resources.py` | MCP resources |

### Dependencies

Add to `requirements.txt`:

```
mcp[cli]>=1.25.0
```

### MCP Tools

| Tool | Parameters | Returns | Description |
|------|------------|---------|-------------|
| `query` | repo_name, prompt, session_id? | TurnResult | Read-only query |
| `start_research` | repo_name, prompt, base_branch? | SessionResult | Start research |
| `complete_research` | session_id | ResearchArtifactResult | End research |
| `continue_session` | session_id, prompt | TurnResult | Follow-up prompt |
| `list_sessions` | filters | List[SessionResult] | List sessions |
| `get_session` | session_id | SessionResult | Get details |
| `close_session` | session_id, abandon? | str | Close session |
| `start_delegation` | repo_name, prompt, base_branch?, research_id? | SessionResult | Start delegation |
| `commit_changes` | session_id, message? | CommitResult | Commit changes |
| `create_pr` | session_id, title?, body?, draft? | PRResult | Create PR |
| `list_repos` | - | List[RepoInfo] | List repos |
| `get_repo` | repo_name | RepoInfo | Get repo details |

### MCP Server Setup

```python
# src/mcp/server.py

from mcp.server.fastmcp import FastMCP
from src.mcp.tools import query, session, delegation, repository

mcp = FastMCP(
    "Agent CLI Orchestrator",
    version="1.0.0",
    json_response=True,
    stateless_http=True,
)

# Register tool routers
mcp.include_router(query.router)
mcp.include_router(session.router)
mcp.include_router(delegation.router)
mcp.include_router(repository.router)

def get_mcp_app():
    """Get MCP app for mounting."""
    return mcp.streamable_http_app()
```

### Mounting with FastAPI

```python
# src/api/app.py

from starlette.applications import Starlette
from starlette.routing import Mount
from src.api.routes import create_api_app
from src.mcp.server import get_mcp_app

def create_app():
    api_app = create_api_app()
    
    return Starlette(routes=[
        Mount("/api", app=api_app),
        Mount("/mcp", app=get_mcp_app()),
    ])
```

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/mcp/test_server.py` | Server initialization, mounting |
| `tests/mcp/test_tools_query.py` | Query tools |
| `tests/mcp/test_tools_session.py` | Session tools |
| `tests/mcp/test_tools_delegation.py` | Delegation tools |
| `tests/mcp/test_context_manager.py` | Context injection |
| Integration test | MCP client → tool → response |

### Acceptance Criteria

- [ ] MCP server starts and responds
- [ ] All tools implemented and functional
- [ ] Tools call underlying services correctly
- [ ] Context injection works for multi-turn
- [ ] MCP mounted alongside FastAPI
- [ ] Stdio transport works for local clients
- [ ] Test coverage ≥ 80%
- [ ] Committed and pushed

---

## Phase 6: Platform Integrations

**Branch:** `phase-6-platforms` (from `phase-5-mcp`)

### Deliverables

| Component | File | Description |
|-----------|------|-------------|
| Base Platform | `src/integrations/platforms/base.py` | GitPlatform ABC |
| Bitbucket | `src/integrations/platforms/bitbucket.py` | Cloud + Server |
| GitLab | `src/integrations/platforms/gitlab.py` | .com + self-hosted |
| Azure DevOps | `src/integrations/platforms/azure_devops.py` | Services + Server |
| Generic | `src/integrations/platforms/generic.py` | Manual fallback |
| Platform Detection | `src/integrations/platforms/__init__.py` | Auto-detection |

### Platform ABC

```python
# src/integrations/platforms/base.py

from abc import ABC, abstractmethod

class GitPlatform(ABC):
    @abstractmethod
    async def create_pull_request(
        self,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = False
    ) -> PRResult:
        ...
    
    @abstractmethod
    async def get_pull_request(self, repo: str, pr_id: str) -> PRInfo:
        ...
    
    @abstractmethod
    async def list_pull_requests(
        self, 
        repo: str, 
        state: str = "open"
    ) -> List[PRInfo]:
        ...
    
    @abstractmethod
    async def add_pr_comment(
        self, 
        repo: str, 
        pr_id: str, 
        body: str
    ) -> None:
        ...
    
    @classmethod
    @abstractmethod
    def detect_from_url(cls, remote_url: str) -> bool:
        """Check if this platform handles the given remote URL."""
        ...
```

### Platform Detection

```python
# src/integrations/platforms/__init__.py

def detect_platform(remote_url: str) -> GitPlatform:
    """Auto-detect platform from remote URL."""
    if "bitbucket.org" in remote_url:
        return BitbucketCloud(...)
    elif "gitlab.com" in remote_url:
        return GitLab(...)
    elif "dev.azure.com" in remote_url:
        return AzureDevOps(...)
    else:
        return GenericPlatform(...)
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions/{id}/pr` | Create PR (uses detected platform) |
| GET | `/repos/{name}/prs` | List PRs for repo |
| GET | `/repos/{name}/prs/{pr_id}` | Get PR details |

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/platforms/test_base.py` | Interface contracts |
| `tests/platforms/test_bitbucket.py` | Bitbucket API (mocked) |
| `tests/platforms/test_gitlab.py` | GitLab API (mocked) |
| `tests/platforms/test_azure_devops.py` | Azure API (mocked) |
| `tests/platforms/test_generic.py` | Manual fallback |
| `tests/platforms/test_detection.py` | Platform auto-detection |

### Acceptance Criteria

- [ ] All platform classes implemented
- [ ] PR creation works for each platform
- [ ] Platform auto-detection works
- [ ] Generic fallback returns manual instructions
- [ ] API endpoints use platform abstraction
- [ ] Test coverage ≥ 80%
- [ ] Committed and pushed

---

## Phase 7: Authentication & Storage

**Branch:** `phase-7-auth-storage` (from `phase-6-platforms`)

### Deliverables

| Component | File | Description |
|-----------|------|-------------|
| Storage Base | `src/storage/base.py` | StorageBackend ABC |
| YAML Backend | `src/storage/yaml_backend.py` | File-based storage |
| Encryption | `src/storage/encrypted.py` | Fernet encryption |
| Auth Models | `src/auth/models.py` | User, APIKey |
| API Key Provider | `src/auth/providers/api_key.py` | API key auth |
| Auth Service | `src/auth/service.py` | Business logic |
| User Registry | `src/registry/user_registry.py` | User CRUD |
| Identity Models | `src/identity/models.py` | GitIdentity, GitCredential |
| Git Config | `src/identity/git_config.py` | Identity injection |
| Auth Routes | `src/api/routes/auth.py` | Auth endpoints |

### Auth Models

```python
# src/auth/models.py

class User(BaseModel):
    id: UUID
    email: str
    display_name: str
    password_hash: str
    git_identity: GitIdentity
    default_model: str = "gpt-4o"
    permission_tier: str = "restricted"
    created_at: datetime
    updated_at: datetime

class APIKey(BaseModel):
    id: UUID
    key_hash: str  # SHA-256, never store plaintext
    user_id: UUID
    name: str
    scopes: List[str]  # ["read", "write", "admin"]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
```

### Storage Interface

```python
# src/storage/base.py

class StorageBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        ...
    
    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        ...
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        ...
    
    @abstractmethod
    async def list(self, prefix: str) -> List[str]:
        ...
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

class SecretStore(StorageBackend):
    """Storage with encryption for sensitive data."""
    ...
```

### Encryption

```python
# src/storage/encrypted.py

from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self, key: Optional[str] = None):
        # Key from env: ORCHESTRATOR_ENCRYPTION_KEY
        self.key = key or os.environ.get("ORCHESTRATOR_ENCRYPTION_KEY")
        self.fernet = Fernet(self.key.encode())
    
    def encrypt(self, data: str) -> str:
        ...
    
    def decrypt(self, encrypted: str) -> str:
        ...
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create user |
| POST | `/auth/login` | Login, get session |
| POST | `/auth/api-keys` | Generate API key |
| GET | `/auth/api-keys` | List user's API keys |
| DELETE | `/auth/api-keys/{id}` | Revoke API key |
| GET | `/auth/me` | Get current user |
| PUT | `/auth/me` | Update user settings |
| POST | `/auth/credentials` | Add git credentials |
| GET | `/auth/credentials` | List credentials (masked) |
| DELETE | `/auth/credentials/{id}` | Remove credentials |

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/storage/test_yaml_backend.py` | YAML operations |
| `tests/storage/test_encrypted.py` | Encryption/decryption |
| `tests/auth/test_api_key.py` | API key validation |
| `tests/auth/test_service.py` | Auth flows |
| `tests/registry/test_user_registry.py` | User CRUD |
| `tests/identity/test_git_config.py` | Identity injection |
| `tests/api/test_auth_routes.py` | Auth endpoints |

### Acceptance Criteria

- [ ] YAML storage backend works
- [ ] Encryption/decryption works
- [ ] User registration and login work
- [ ] API key generation and validation work
- [ ] Git credentials stored encrypted
- [ ] User settings persist
- [ ] Test coverage ≥ 80%
- [ ] Committed and pushed

---

## Phase 8: Security Hardening

**Branch:** `phase-8-security` (from `phase-7-auth-storage`)

### Deliverables

| Component | File | Description |
|-----------|------|-------------|
| Auth Middleware | `src/api/middleware/auth.py` | Token validation |
| Rate Limiting | `src/api/middleware/rate_limit.py` | Request throttling |
| Security Headers | `src/api/middleware/security_headers.py` | CORS, CSP, HSTS |
| Input Validation | `src/core/security.py` | Sanitization |
| TLS Config | `main.py` | HTTPS support |
| Audit Logging | `src/core/activity.py` | Security events |

### Auth Middleware

```python
# src/api/middleware/auth.py

class AuthMiddleware:
    def __init__(
        self,
        app,
        exclude_paths: List[str] = None,
        require_auth: bool = True
    ):
        ...
    
    async def __call__(self, scope, receive, send):
        # Extract token from Authorization header
        # Validate and load user
        # Inject user into request state
        ...
```

### Rate Limiting

```python
# src/api/middleware/rate_limit.py

class RateLimitMiddleware:
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst: int = 10
    ):
        # Sliding window algorithm
        ...
```

### Security Headers

```python
# src/api/middleware/security_headers.py

class SecurityHeadersMiddleware:
    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }
```

### TLS Configuration

```yaml
# config.yaml
server:
  ssl_enabled: true
  ssl_certfile: "/etc/certs/server.crt"
  ssl_keyfile: "/etc/certs/server.key"
```

### Permission Enforcement

```python
# src/api/dependencies.py

def require_permission(tier: PermissionTier):
    async def dependency(user: User = Depends(get_current_user)):
        if not user.has_permission(tier):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dependency
```

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/middleware/test_auth.py` | Auth enforcement |
| `tests/middleware/test_rate_limit.py` | Rate limiting |
| `tests/middleware/test_security_headers.py` | Header validation |
| `tests/security/test_input_validation.py` | Sanitization |
| `tests/security/test_audit_log.py` | Audit events |
| Integration test | Unauthorized access blocked |

### Acceptance Criteria

- [ ] Auth middleware blocks unauthenticated requests
- [ ] Rate limiting works per API key
- [ ] Security headers present on responses
- [ ] TLS configuration works
- [ ] Input validation prevents injection
- [ ] Audit log captures security events
- [ ] MCP respects auth
- [ ] Test coverage ≥ 80%
- [ ] Committed and pushed

---

## Phase 9: Modern Dashboard UI

**Branch:** `phase-9-modern-ui` (from `phase-8-security`)

### Deliverables

| Component | Location | Description |
|-----------|----------|-------------|
| React App | `src/ui/` | Modern SPA |
| Login Page | `src/ui/src/pages/Login.tsx` | User authentication |
| Dashboard | `src/ui/src/pages/Dashboard.tsx` | Home with activity |
| Sessions | `src/ui/src/pages/Sessions.tsx` | Session management |
| Settings | `src/ui/src/pages/Settings.tsx` | User settings |
| Delegation | `src/ui/src/pages/Delegation.tsx` | Delegation wizard |
| Research | `src/ui/src/pages/Research.tsx` | Research browser |
| Repositories | `src/ui/src/pages/Repositories.tsx` | Repo management |

### Technology Stack

| Layer | Technology |
|-------|------------|
| Framework | React 18 + TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| State | React Query + Zustand |
| Routing | React Router v6 |
| Build | Vite |
| Serving | FastAPI static files |

### Pages

| Page | Route | Features |
|------|-------|----------|
| Login | `/login` | Email/password, API key option |
| Register | `/register` | Create account |
| Dashboard | `/` | Active sessions, quick actions, activity |
| Sessions | `/sessions` | List, filter, search |
| Session Detail | `/sessions/:id` | Conversation, files, actions |
| Delegation | `/delegate` | Start wizard |
| Research | `/research` | Artifacts browser |
| Repositories | `/repos` | Manage repos, platforms |
| Settings | `/settings` | Profile, model, PATs, identity |

### Component Library

| Component | Description |
|-----------|-------------|
| SessionCard | Session summary card |
| ConversationView | Chat-style message display |
| FileChangesView | Modified files list |
| StreamingOutput | Real-time Copilot output |
| RepoSelector | Repository dropdown |
| BranchSelector | Branch dropdown |
| PATManager | Credential management |
| ModelSelector | Model dropdown |

### API Integration

```typescript
// src/ui/src/api/client.ts

import { createClient } from '@tanstack/react-query';

const api = {
  sessions: {
    list: (filters) => fetch('/api/sessions', ...),
    get: (id) => fetch(`/api/sessions/${id}`),
    create: (data) => fetch('/api/sessions', { method: 'POST', ... }),
    continue: (id, prompt) => fetch(`/api/sessions/${id}/continue`, ...),
    commit: (id) => fetch(`/api/sessions/${id}/commit`, ...),
    createPR: (id) => fetch(`/api/sessions/${id}/pr`, ...),
  },
  // ... other endpoints
};
```

### Tests

| Test Type | Description |
|-----------|-------------|
| `tests/ui/test_api_integration.py` | API calls from UI |
| Jest unit tests | Component logic |
| E2E (Playwright) | Login flow, delegation flow |

### Acceptance Criteria

- [ ] All pages implemented
- [ ] Login/register flow works
- [ ] Session management functional
- [ ] Real-time streaming works (SSE)
- [ ] User settings persist
- [ ] Responsive design (mobile)
- [ ] Dark mode support
- [ ] Served by FastAPI
- [ ] Test coverage ≥ 80%
- [ ] Committed and pushed

---

## Phase 10: Documentation

**Branch:** `phase-10-documentation` (from `phase-9-modern-ui`)

### Deliverables

| Document | Location |
|----------|----------|
| Local Installation | `docs/installation/local.md` |
| Server Installation | `docs/installation/server.md` |
| DevContainer Setup | `docs/installation/devcontainer.md` |
| MCP Overview | `docs/mcp/README.md` |
| MCP Installation | `docs/mcp/installation.md` |
| MCP Authentication | `docs/mcp/authentication.md` |
| MCP Tool Reference | `docs/mcp/tools/*.md` |
| MCP Resources | `docs/mcp/resources.md` |
| Claude Desktop Setup | `docs/mcp/client-setup/claude-desktop.md` |
| VS Code Setup | `docs/mcp/client-setup/vscode.md` |
| Custom Client | `docs/mcp/client-setup/custom-client.md` |
| Workflow Examples | `docs/mcp/examples/*.md` |
| Troubleshooting | `docs/mcp/troubleshooting.md` |
| API Reference | `docs/api/README.md` |
| User Guide | `docs/user-guide/README.md` |
| Architecture | `architecture.md` |

### Documentation Standards

- All code examples tested
- All diagrams reference PNG exports
- All links validated
- Version numbers current

### Acceptance Criteria

- [ ] All installation guides complete
- [ ] All MCP documentation complete
- [ ] All diagrams included
- [ ] API reference generated from OpenAPI
- [ ] User guide covers all workflows
- [ ] All links work
- [ ] Committed and pushed

---

## Configuration Schema (Final)

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  ssl_enabled: false
  ssl_certfile: null
  ssl_keyfile: null

mcp:
  enabled: true
  transport: "streamable-http"
  path: "/mcp"
  auth_required: true

storage:
  backend: "yaml"
  path: "./data"
  # ORCHESTRATOR_ENCRYPTION_KEY env var required

auth:
  enabled: true
  session_expiry_hours: 24
  api_key_expiry_days: 90

identity:
  agent_name: "Agent CLI Orchestrator"
  agent_email: "agent@orchestrator.local"

session:
  max_active_per_user:
    query: 20
    research: 3
    delegation: 10
  expiry_minutes:
    query: 30
    research: 120
    delegation: 1440
  context:
    max_history_turns: 5
    max_context_tokens: 4000

research:
  default_base_branch: null
  artifact_retention_days: 90

delegation:
  branch_prefix: "agent"
  worktrees_suffix: ".worktrees"

permissions:
  default_tier: "read-only"
  tiers:
    read-only:
      deny: ["write", "shell(rm)", "shell(git commit)", "shell(git push)"]
    restricted:
      allow: ["shell(git add)", "shell(git commit)"]
      deny: ["shell(git push)", "shell(rm -rf)"]
    full:
      require_scope: "admin"

platforms:
  bitbucket_cloud:
    enabled: true
  bitbucket_server:
    enabled: false
    base_url: null
  gitlab:
    enabled: true
    base_url: null
  azure_devops:
    enabled: false
    organization: null
  generic:
    enabled: true

repositories: []

copilot:
  enabled: true
  timeout: 300
  log_dir: "./logs/copilot"

defaults:
  model: "gpt-4o"

ui:
  serve_frontend: true
```

---

## Deferred Items (Post-v1)

| Item | Description |
|------|-------------|
| Separate frontend deployment | CDN hosting for UI |
| OAuth login | Google, Microsoft, SAML SSO |
| WebSocket streaming | Real-time output display |
| Mobile app | React Native |
| SQLite/Vault storage | Secure database backends |
| GitHub platform | Air-gapped GitHub Enterprise |
| CI/CD pipeline | Bitbucket/Jenkins automation |

---

## Test Coverage Requirements

- **Minimum:** 80% enforced per phase
- **Per module:** Unit tests for all public functions
- **Integration:** Full workflow tests
- **E2E:** UI flows with Playwright

---

## Mermaid Diagram Specifications

### Color Palette

```markdown
# Mermaid Color Palette

## Primary Colors
- Primary Blue: #2563eb
- Primary Green: #16a34a
- Primary Orange: #ea580c
- Primary Purple: #9333ea

## Background Colors
- Light Blue: #dbeafe
- Light Green: #dcfce7
- Light Orange: #ffedd5
- Light Purple: #f3e8ff

## Neutral Colors
- Dark Gray: #1f2937
- Medium Gray: #6b7280
- Light Gray: #f3f4f6
- White: #ffffff

## Status Colors
- Success: #22c55e
- Warning: #eab308
- Error: #ef4444
- Info: #3b82f6

## Usage
- Use Primary colors for main elements
- Use Light colors for backgrounds
- Use Status colors for states
- Use Neutral colors for text and borders
```

### Diagrams to Create

1. **architecture-overview.mmd** - Clients → API/MCP → Services → Integrations
2. **session-lifecycle.mmd** - Query/Research/Delegation states
3. **delegation-flow.mmd** - Create worktree → Execute → Commit → PR
4. **golden-rule-isolation.mmd** - Branch isolation visualization
5. **query-research-flow.mmd** - Direct vs temp worktree paths
6. **mcp-tool-flow.mmd** - Tool invocation → Service → Response
7. **auth-flow.mmd** - API key validation → User context
8. **platform-pr-flow.mmd** - Bitbucket/GitLab/Azure paths
9. **context-injection.mmd** - Session history → Prompt building

### Export Script

```bash
#!/bin/bash
# scripts/export-diagrams.sh

# Requires: npm install -g @mermaid-js/mermaid-cli

MERMAID_DIR="docs/diagrams/mermaid"
PNG_DIR="docs/diagrams/png"

mkdir -p "$PNG_DIR"

for file in "$MERMAID_DIR"/*.mmd; do
    filename=$(basename "$file" .mmd)
    mmdc -i "$file" -o "$PNG_DIR/$filename.png" -s 2 -b transparent
    echo "Exported: $filename.png"
done
```

---

## Implementation Checklist

### Phase 0: Plan Documentation
- [ ] Create `.github/prompts/` directory
- [ ] Save this plan file
- [ ] Create mermaid color palette doc
- [ ] Create 9 Mermaid diagrams
- [ ] Export diagrams to PNG
- [ ] Create export script
- [ ] Commit to `phase-0-plan-docs` branch

### Phase 1: Code Reorganization
- [ ] Create `src/` package structure
- [ ] Move existing modules
- [ ] Update imports
- [ ] Update tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-1-reorganization` branch

### Phase 2: Session Management
- [ ] Create session models
- [ ] Implement session manager
- [ ] Implement session store
- [ ] Add context manager
- [ ] Create API routes
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-2-sessions` branch

### Phase 3: Query & Research Modes
- [ ] Create query service
- [ ] Create research service
- [ ] Create research store
- [ ] Implement tool policy
- [ ] Create API routes
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-3-query-research` branch

### Phase 4: Delegation Mode
- [ ] Create delegation service
- [ ] Create worktree manager
- [ ] Create commit manager
- [ ] Create PR manager
- [ ] Enforce Golden Rule
- [ ] Create API routes
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-4-delegation` branch

### Phase 5: MCP Server
- [ ] Set up FastMCP
- [ ] Implement query tools
- [ ] Implement session tools
- [ ] Implement delegation tools
- [ ] Implement repository tools
- [ ] Implement resources
- [ ] Mount with FastAPI
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-5-mcp` branch

### Phase 6: Platform Integrations
- [ ] Create platform interface
- [ ] Implement Bitbucket
- [ ] Implement GitLab
- [ ] Implement Azure DevOps
- [ ] Implement Generic fallback
- [ ] Implement auto-detection
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-6-platforms` branch

### Phase 7: Authentication & Storage
- [ ] Create storage interface
- [ ] Implement YAML backend
- [ ] Implement encryption
- [ ] Create auth models
- [ ] Implement API key auth
- [ ] Create user registry
- [ ] Create identity models
- [ ] Implement git config injection
- [ ] Create API routes
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-7-auth-storage` branch

### Phase 8: Security Hardening
- [ ] Implement auth middleware
- [ ] Implement rate limiting
- [ ] Implement security headers
- [ ] Add input validation
- [ ] Configure TLS
- [ ] Add audit logging
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-8-security` branch

### Phase 9: Modern Dashboard UI
- [ ] Set up React project
- [ ] Implement login/register
- [ ] Build dashboard
- [ ] Build sessions page
- [ ] Build delegation wizard
- [ ] Build research browser
- [ ] Build repo management
- [ ] Build settings
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-9-modern-ui` branch

### Phase 10: Documentation
- [ ] Write installation guides
- [ ] Write MCP documentation
- [ ] Write API reference
- [ ] Write user guide
- [ ] Update architecture doc
- [ ] Validate all links
- [ ] Commit to `phase-10-documentation` branch

---

## Next Steps

1. **Review this plan** - Make any adjustments before starting
2. **Start Phase 0** - Create diagrams and documentation
3. **Follow the branching strategy** - Each phase on its own branch
4. **Maintain test coverage** - 80% minimum per phase
5. **Document as you go** - Update docs with implementation

---

*Document Version: 2.0*  
*Created: January 2026*  
*Last Updated: January 2026*
