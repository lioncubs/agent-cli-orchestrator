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

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL CLIENTS                               │
├─────────────────┬─────────────────┬─────────────────┬───────────────────┤
│  React Dashboard │   MCP Clients   │   REST API      │   CLI Tools       │
│  (Browser)       │ (Claude Desktop)│   (curl, etc)   │   (scripts)       │
└────────┬────────┴────────┬────────┴────────┬────────┴─────────┬─────────┘
         │                 │                 │                   │
         ▼                 ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR CORE                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  FastAPI    │  │  MCP Server │  │  Session    │  │  Auth       │    │
│  │  Router     │  │  (FastMCP)  │  │  Manager    │  │  Manager    │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                 │           │
│         ▼                ▼                ▼                 ▼           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      SERVICE LAYER                                │  │
│  ├────────────┬────────────┬────────────┬────────────┬──────────────┤  │
│  │  Query     │  Research  │ Delegation │  Identity  │  Permissions │  │
│  │  Service   │  Service   │  Service   │  Service   │  Service     │  │
│  └─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┴──────┬───────┘  │
│        │            │            │            │             │          │
│        ▼            ▼            ▼            ▼             ▼          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    INFRASTRUCTURE LAYER                           │  │
│  ├────────────┬────────────┬────────────┬────────────┬──────────────┤  │
│  │  Copilot   │    Git     │  Storage   │  Platform  │   Registry   │  │
│  │  CLI       │  Operations│  Backend   │ Integrations│  Manager    │  │
│  └────────────┴────────────┴────────────┴────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────────┐                    ┌─────────────────────────────┐
│   COPILOT CLI       │                    │   EXTERNAL PLATFORMS        │
│   (gh copilot -p)   │                    ├─────────────────────────────┤
└─────────────────────┘                    │  Bitbucket Cloud/Server     │
                                           │  GitLab.com / Self-hosted   │
                                           │  Azure DevOps               │
                                           │  Generic Git (SSH/HTTPS)    │
                                           └─────────────────────────────┘
```

---

## Phase Overview

| Phase | Name | Description | Branch |
|-------|------|-------------|--------|
| 0 | Documentation & Planning | Diagrams, plan docs, color palette | `phase-0-plan-docs` |
| 1 | Code Reorganization | Move to `src/` package structure | `phase-1-reorganization` |
| 2 | Storage Abstraction | Generic backend with YAML implementation | `phase-2-storage` |
| 3 | Identity & Permissions | Git identity injection, role-based access | `phase-3-identity` |
| 4 | Session Management | UUID sessions, multi-turn context | `phase-4-sessions` |
| 5 | Query Service | Direct query execution | `phase-5-query` |
| 6 | Delegation Service | Worktree + branch background tasks | `phase-6-delegation` |
| 7 | Platform Integrations | Bitbucket, GitLab, Azure DevOps | `phase-7-platforms` |
| 8 | MCP Server | FastMCP tool definitions | `phase-8-mcp` |
| 9 | Security Hardening | HTTPS, rate limiting, audit logging | `phase-9-security` |
| 10 | Modern UI | React dashboard with auth | `phase-10-ui` |

---

## Detailed Phases

### Phase 0: Documentation & Planning

**Branch:** `phase-0-plan-docs`

**Deliverables:**
1. `.github/prompts/orchestrator-implementation-plan.prompt.md` (this file)
2. `.github/prompts/mermaid-color-palette.md`
3. `docs/diagrams/mermaid/*.mmd` (9 diagrams)
4. `docs/diagrams/png/*.png` (exported diagrams)
5. `scripts/export-diagrams.sh`

**Diagrams to Create:**
1. `system-architecture.mmd` - High-level system overview
2. `session-flow.mmd` - Session lifecycle (Query/Research/Delegation)
3. `delegation-flow.mmd` - Golden Rule worktree flow
4. `mcp-integration.mmd` - MCP client/server interaction
5. `auth-flow.mmd` - Authentication and authorization
6. `storage-abstraction.mmd` - Storage backend architecture
7. `platform-integrations.mmd` - Multi-platform support
8. `git-identity-flow.mmd` - Identity injection for commits
9. `api-overview.mmd` - API endpoint categories

**Acceptance Criteria:**
- [ ] All 9 Mermaid diagrams render correctly
- [ ] PNG exports generated
- [ ] Color palette documented and consistent

---

### Phase 1: Code Reorganization

**Branch:** `phase-1-reorganization`

**Deliverables:**
1. `src/` package structure
2. Refactored modules with imports
3. Updated `main.py` as thin entry point
4. All existing tests passing

**Tasks:**
1. Create `src/__init__.py`
2. Move `config_loader.py` → `src/core/config.py`
3. Move `copilot_cli.py` → `src/core/copilot.py`
4. Move `git_operations.py` → `src/core/git.py`
5. Move `activity_log.py` → `src/core/activity.py`
6. Extract Pydantic models from `main.py` → `src/api/models.py`
7. Extract routes from `main.py` → `src/api/routes/`
8. Update all imports
9. Update tests to use new paths

**Directory Structure After Phase 1:**
```
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py        # from config_loader.py
│   ├── copilot.py       # from copilot_cli.py
│   ├── git.py           # from git_operations.py
│   └── activity.py      # from activity_log.py
├── api/
│   ├── __init__.py
│   ├── models.py        # Pydantic models from main.py
│   └── routes/
│       ├── __init__.py
│       ├── copilot.py   # /copilot/* endpoints
│       ├── git.py       # /git/* endpoints
│       ├── repos.py     # /repos/* endpoints
│       └── health.py    # /health, /status
main.py                  # Thin entry point
```

**Tests:**
- `tests/test_reorganization.py` - Verify imports work
- Update existing tests for new paths
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] All existing functionality preserved
- [ ] All existing tests pass
- [ ] New import structure works
- [ ] Coverage ≥80%

---

### Phase 2: Storage Abstraction

**Branch:** `phase-2-storage`

**Deliverables:**
1. `src/storage/base.py` - Abstract storage interface
2. `src/storage/yaml_backend.py` - YAML implementation
3. `src/storage/encryption.py` - Fernet encryption utilities
4. Migrated config to use storage layer

**Storage Interface:**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class StorageBackend(ABC):
    """Abstract storage backend interface."""
    
    @abstractmethod
    async def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by key."""
        pass
    
    @abstractmethod
    async def set(self, collection: str, key: str, value: Dict[str, Any]) -> None:
        """Store a document."""
        pass
    
    @abstractmethod
    async def delete(self, collection: str, key: str) -> bool:
        """Delete a document."""
        pass
    
    @abstractmethod
    async def list(self, collection: str, filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """List documents in a collection."""
        pass
    
    @abstractmethod
    async def exists(self, collection: str, key: str) -> bool:
        """Check if a document exists."""
        pass
```

**Collections:**
- `users` - User accounts
- `repos` - Repository configurations
- `pats` - Encrypted PATs
- `sessions` - Active sessions
- `delegations` - Delegation tasks
- `research` - Research artifacts

**Tests:**
- `tests/test_storage_base.py` - Interface contract tests
- `tests/test_yaml_backend.py` - YAML implementation tests
- `tests/test_encryption.py` - Encryption round-trip tests
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] Abstract interface defined
- [ ] YAML backend fully implements interface
- [ ] Encryption working for sensitive fields
- [ ] Coverage ≥80%

---

### Phase 3: Identity & Permissions

**Branch:** `phase-3-identity`

**Deliverables:**
1. `src/identity/models.py` - User, Identity models
2. `src/identity/service.py` - Identity management
3. `src/permissions/models.py` - Role, Permission models
4. `src/permissions/service.py` - RBAC enforcement

**Identity Model:**
```python
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class GitIdentity(BaseModel):
    name: str
    email: EmailStr

class User(BaseModel):
    id: str  # UUID
    username: str
    email: EmailStr
    git_identity: GitIdentity
    roles: List[Role]
    default_model: Optional[str] = "gpt-4"
    created_at: datetime
    updated_at: datetime
```

**Permission Matrix:**

| Action | Admin | Developer | Viewer |
|--------|-------|-----------|--------|
| Query | ✅ | ✅ | ✅ |
| Research | ✅ | ✅ | ❌ |
| Delegation | ✅ | ✅ | ❌ |
| Manage Repos | ✅ | ❌ | ❌ |
| Manage Users | ✅ | ❌ | ❌ |
| View Logs | ✅ | ✅ | ✅ |

**Git Identity Injection:**
```python
async def inject_git_identity(user: User, worktree_path: str) -> Dict[str, str]:
    """Return environment variables for git commits."""
    return {
        "GIT_AUTHOR_NAME": user.git_identity.name,
        "GIT_AUTHOR_EMAIL": user.git_identity.email,
        "GIT_COMMITTER_NAME": user.git_identity.name,
        "GIT_COMMITTER_EMAIL": user.git_identity.email,
    }
```

**Tests:**
- `tests/test_identity_models.py`
- `tests/test_identity_service.py`
- `tests/test_permissions_models.py`
- `tests/test_permissions_service.py`
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] User CRUD operations
- [ ] Role assignment
- [ ] Permission checks on all endpoints
- [ ] Git identity injection working
- [ ] Coverage ≥80%

---

### Phase 4: Session Management

**Branch:** `phase-4-sessions`

**Deliverables:**
1. `src/session/models.py` - Session models
2. `src/session/manager.py` - Session lifecycle
3. `src/session/context.py` - Context injection for multi-turn

**Session Types:**
```python
from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SessionType(str, Enum):
    QUERY = "query"          # Direct question, no worktree
    RESEARCH = "research"    # Temp worktree, save artifacts, cleanup
    DELEGATION = "delegation"  # Persistent worktree + branch

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConversationTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    tool_calls: Optional[List[Dict]] = None

class Session(BaseModel):
    id: str  # UUID
    type: SessionType
    status: SessionStatus
    user_id: str
    repo_id: str
    branch: Optional[str] = None
    worktree_path: Optional[str] = None
    conversation: List[ConversationTurn] = []
    artifacts: List[str] = []  # File paths for research
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
```

**Context Injection:**

Since Copilot CLI `-p` mode is stateless, we inject conversation history:

```python
async def build_context_prompt(session: Session, new_message: str) -> str:
    """Build prompt with conversation history for context continuity."""
    context_parts = []
    
    # Add conversation history
    for turn in session.conversation[-10:]:  # Last 10 turns
        prefix = "User:" if turn.role == "user" else "Assistant:"
        context_parts.append(f"{prefix} {turn.content}")
    
    # Add new message
    context_parts.append(f"User: {new_message}")
    
    return "\n\n".join(context_parts)
```

**Tests:**
- `tests/test_session_models.py`
- `tests/test_session_manager.py`
- `tests/test_context_injection.py`
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] Session CRUD operations
- [ ] Session type enforcement
- [ ] Multi-turn context injection
- [ ] Session timeout/cleanup
- [ ] Coverage ≥80%

---

### Phase 5: Query Service

**Branch:** `phase-5-query`

**Deliverables:**
1. `src/query/service.py` - Query execution
2. `src/query/models.py` - Query request/response models
3. Updated API routes

**Query Flow:**
1. Receive query request with optional session_id
2. If session_id provided, load session and inject context
3. Execute Copilot CLI with query
4. Store response in session (if session exists)
5. Return response

**Query Service:**
```python
class QueryService:
    async def execute(
        self,
        user: User,
        repo: Repository,
        query: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> QueryResponse:
        """Execute a query against Copilot CLI."""
        
        # Load or create session
        session = await self._get_or_create_session(session_id, user, repo)
        
        # Build context-injected prompt
        prompt = await build_context_prompt(session, query)
        
        # Execute Copilot CLI
        result = await self.copilot.execute_async(
            prompt=prompt,
            cwd=repo.local_path,
            model=model or user.default_model,
        )
        
        # Update session
        await self._update_session(session, query, result)
        
        return QueryResponse(
            session_id=session.id,
            response=result.output,
            model=model or user.default_model,
        )
```

**Tests:**
- `tests/test_query_service.py`
- `tests/test_query_models.py`
- `tests/test_query_context.py`
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] Single query execution
- [ ] Multi-turn with context injection
- [ ] Model selection
- [ ] Error handling
- [ ] Coverage ≥80%

---

### Phase 6: Delegation Service

**Branch:** `phase-6-delegation`

**Deliverables:**
1. `src/delegation/service.py` - Delegation execution
2. `src/delegation/models.py` - Delegation models
3. `src/delegation/worker.py` - Background task worker
4. Research mode support

**⚠️ GOLDEN RULE ENFORCEMENT:**

Every delegation MUST:
1. Create a new branch from the specified base
2. Create an isolated worktree
3. Execute Copilot CLI in that worktree
4. Commit changes with user's git identity
5. Push to remote (if configured)

**Delegation Models:**
```python
class DelegationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DelegationType(str, Enum):
    RESEARCH = "research"      # Temp worktree, artifacts saved
    IMPLEMENTATION = "implementation"  # Persistent worktree + branch

class Delegation(BaseModel):
    id: str  # UUID
    type: DelegationType
    status: DelegationStatus
    user_id: str
    repo_id: str
    session_id: str
    
    # Branch info
    base_branch: str
    target_branch: str
    worktree_path: str
    
    # Task info
    prompt: str
    tool_policy: Optional[ToolPolicy] = None
    
    # Results
    commits: List[str] = []
    artifacts: List[str] = []  # For research mode
    error: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ToolPolicy(BaseModel):
    """Control which tools Copilot CLI can use."""
    allowed: List[str] = []   # --allow-tool flags
    denied: List[str] = []    # --deny-tool flags
```

**Delegation Flow:**
```
1. Create Delegation record (PENDING)
2. Create branch: git checkout -b {target_branch} {base_branch}
3. Create worktree: git worktree add {path} {target_branch}
4. Set status RUNNING
5. Execute Copilot CLI in worktree with tool policy
6. Commit changes with user's git identity
7. For RESEARCH: Save artifacts, cleanup worktree
8. For IMPLEMENTATION: Keep worktree, push if configured
9. Set status COMPLETED/FAILED
```

**Research vs Implementation:**

| Aspect | Research | Implementation |
|--------|----------|----------------|
| Worktree | Temporary | Persistent |
| Branch | Auto-deleted | Kept for PR/MR |
| Artifacts | Saved to session | Committed |
| Purpose | Exploration | Code generation |

**Tests:**
- `tests/test_delegation_service.py`
- `tests/test_delegation_models.py`
- `tests/test_delegation_worker.py`
- `tests/test_research_mode.py`
- `tests/test_golden_rule.py` - Verify worktree isolation
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] Golden Rule enforced (worktree + branch)
- [ ] Research mode with artifact saving
- [ ] Implementation mode with commits
- [ ] Tool policy support
- [ ] Background execution
- [ ] Git identity injection
- [ ] Coverage ≥80%

---

### Phase 7: Platform Integrations

**Branch:** `phase-7-platforms`

**Deliverables:**
1. `src/integrations/base.py` - Abstract platform interface
2. `src/integrations/bitbucket.py` - Bitbucket Cloud/Server
3. `src/integrations/gitlab.py` - GitLab.com/self-hosted
4. `src/integrations/azure_devops.py` - Azure DevOps
5. `src/integrations/generic.py` - Generic Git fallback
6. `src/registry/manager.py` - Repository registry

**Platform Interface:**
```python
from abc import ABC, abstractmethod

class PlatformIntegration(ABC):
    """Abstract interface for git platform integrations."""
    
    @abstractmethod
    async def validate_credentials(self, pat: str) -> bool:
        """Validate PAT is valid."""
        pass
    
    @abstractmethod
    async def clone_repository(self, repo_url: str, local_path: str, pat: str) -> bool:
        """Clone a repository."""
        pass
    
    @abstractmethod
    async def create_pull_request(
        self,
        repo: Repository,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
    ) -> PullRequestResult:
        """Create a pull/merge request."""
        pass
    
    @abstractmethod
    async def get_repository_info(self, repo_url: str, pat: str) -> RepositoryInfo:
        """Get repository metadata."""
        pass
```

**Platform-Specific Notes:**

| Platform | PAT Scope | Clone URL Format | PR API |
|----------|-----------|------------------|--------|
| Bitbucket Cloud | repository:write | `https://x-token-auth:{pat}@bitbucket.org/...` | REST 2.0 |
| Bitbucket Server | repo:write | `https://{user}:{pat}@server/...` | REST 1.0 |
| GitLab | write_repository | `https://oauth2:{pat}@gitlab.com/...` | GraphQL/REST |
| Azure DevOps | Code (Read & Write) | `https://{pat}@dev.azure.com/...` | REST |
| Generic | N/A | SSH or HTTPS | N/A |

**Repository Registry:**
```python
class RepositoryRegistry:
    """Manage registered repositories."""
    
    async def register(
        self,
        url: str,
        platform: str,
        pat_id: str,
        local_path: str,
        default_branch: str = "main",
    ) -> Repository:
        """Register a new repository."""
        pass
    
    async def get(self, repo_id: str) -> Optional[Repository]:
        """Get repository by ID."""
        pass
    
    async def list(self, user_id: str) -> List[Repository]:
        """List repositories accessible to user."""
        pass
    
    async def sync(self, repo_id: str) -> SyncResult:
        """Sync repository with remote."""
        pass
```

**Tests:**
- `tests/test_platform_base.py`
- `tests/test_bitbucket.py`
- `tests/test_gitlab.py`
- `tests/test_azure_devops.py`
- `tests/test_generic.py`
- `tests/test_registry.py`
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] All 4 platforms implemented
- [ ] PAT validation per platform
- [ ] Clone with authentication
- [ ] PR/MR creation (where supported)
- [ ] Repository registry CRUD
- [ ] Coverage ≥80%

---

### Phase 8: MCP Server

**Branch:** `phase-8-mcp`

**Deliverables:**
1. `src/mcp/server.py` - FastMCP server
2. `src/mcp/tools.py` - Tool definitions
3. `src/mcp/resources.py` - Resource definitions
4. MCP configuration for clients

**Dependencies:**
```
mcp[cli]>=1.25.0
```

**MCP Server Setup:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("agent-cli-orchestrator")

@mcp.tool()
async def query(
    prompt: str,
    repo_id: str,
    session_id: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Execute a query against Copilot CLI."""
    # Implementation
    pass

@mcp.tool()
async def delegate(
    prompt: str,
    repo_id: str,
    branch_name: str,
    delegation_type: str = "implementation",
    tool_policy: Optional[Dict] = None,
) -> Dict:
    """Create a delegation task (Golden Rule enforced)."""
    # Implementation
    pass

@mcp.tool()
async def get_delegation_status(delegation_id: str) -> Dict:
    """Get status of a delegation task."""
    # Implementation
    pass

@mcp.tool()
async def list_repositories() -> List[Dict]:
    """List registered repositories."""
    # Implementation
    pass

@mcp.tool()
async def research(
    prompt: str,
    repo_id: str,
    session_id: Optional[str] = None,
) -> Dict:
    """Start a research session with temporary worktree."""
    # Implementation
    pass
```

**MCP Resources:**
```python
@mcp.resource("repo://{repo_id}")
async def get_repository(repo_id: str) -> str:
    """Get repository details."""
    pass

@mcp.resource("session://{session_id}")
async def get_session(session_id: str) -> str:
    """Get session details and conversation history."""
    pass

@mcp.resource("delegation://{delegation_id}")
async def get_delegation(delegation_id: str) -> str:
    """Get delegation details and status."""
    pass
```

**Client Configuration (Claude Desktop):**
```json
{
  "mcpServers": {
    "agent-cli-orchestrator": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "/path/to/orchestrator"
    }
  }
}
```

**Tests:**
- `tests/test_mcp_server.py`
- `tests/test_mcp_tools.py`
- `tests/test_mcp_resources.py`
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] FastMCP server running
- [ ] All tools callable from MCP client
- [ ] Resources accessible
- [ ] Authentication integrated
- [ ] Coverage ≥80%

---

### Phase 9: Security Hardening

**Branch:** `phase-9-security`

**Deliverables:**
1. `src/auth/jwt.py` - JWT token management
2. `src/auth/middleware.py` - Auth middleware
3. `src/security/rate_limiter.py` - Rate limiting
4. `src/security/audit.py` - Audit logging
5. HTTPS configuration
6. Security documentation

**JWT Authentication:**
```python
from datetime import datetime, timedelta
from jose import jwt

class JWTManager:
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm
    
    def create_token(self, user_id: str, expires_delta: timedelta = timedelta(hours=8)) -> str:
        """Create a JWT token."""
        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify token and return user_id."""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload.get("sub")
        except jwt.JWTError:
            return None
```

**Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to routes
@app.post("/api/query")
@limiter.limit("60/minute")
async def query_endpoint(request: Request):
    pass

@app.post("/api/delegate")
@limiter.limit("10/minute")
async def delegate_endpoint(request: Request):
    pass
```

**Audit Logging:**
```python
class AuditLogger:
    async def log(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log an auditable action."""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        await self.storage.set("audit", str(uuid4()), entry.dict())
```

**HTTPS Configuration:**
```yaml
# config.yaml
server:
  host: "0.0.0.0"
  port: 8443
  ssl:
    enabled: true
    cert_file: "/path/to/cert.pem"
    key_file: "/path/to/key.pem"
```

**Tests:**
- `tests/test_jwt.py`
- `tests/test_auth_middleware.py`
- `tests/test_rate_limiter.py`
- `tests/test_audit.py`
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] JWT authentication working
- [ ] Rate limiting on all endpoints
- [ ] Audit logging for sensitive actions
- [ ] HTTPS support
- [ ] Security documentation
- [ ] Coverage ≥80%

---

### Phase 10: Modern UI

**Branch:** `phase-10-ui`

**Deliverables:**
1. `ui/` - React application
2. User authentication flow
3. Dashboard with session management
4. Delegation monitoring
5. Repository management UI

**Tech Stack:**
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Vite build
- React Query (TanStack Query)
- Zustand for state
- React Router

**UI Structure:**
```
ui/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn components
│   │   ├── layout/       # Layout components
│   │   ├── auth/         # Auth components
│   │   ├── dashboard/    # Dashboard components
│   │   ├── sessions/     # Session management
│   │   ├── delegations/  # Delegation monitoring
│   │   └── repos/        # Repository management
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Utilities
│   ├── stores/           # Zustand stores
│   ├── api/              # API client
│   ├── types/            # TypeScript types
│   └── App.tsx
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

**Key Pages:**
1. **Login** - Username/password auth
2. **Dashboard** - Overview of sessions, delegations, repos
3. **Query** - Interactive query interface with session history
4. **Delegations** - List and monitor delegations
5. **Repositories** - Manage registered repos
6. **Settings** - User settings, git identity, default model

**Tests:**
- `ui/src/__tests__/` - Component tests
- Playwright E2E tests
- Coverage: ≥80%

**Acceptance Criteria:**
- [ ] Login/logout working
- [ ] Dashboard with real data
- [ ] Query interface with multi-turn
- [ ] Delegation creation and monitoring
- [ ] Repository CRUD
- [ ] Responsive design
- [ ] Coverage ≥80%

---

## Directory Structure

Final directory structure after all phases:

```
agent-cli-orchestrator/
├── .github/
│   └── prompts/
│       ├── orchestrator-implementation-plan.prompt.md
│       └── mermaid-color-palette.md
├── docs/
│   ├── architecture.md
│   ├── API.md
│   ├── INSTALL.md
│   ├── MCP.md
│   ├── SECURITY.md
│   ├── diagrams/
│   │   ├── mermaid/
│   │   │   ├── system-architecture.mmd
│   │   │   ├── session-flow.mmd
│   │   │   ├── delegation-flow.mmd
│   │   │   ├── mcp-integration.mmd
│   │   │   ├── auth-flow.mmd
│   │   │   ├── storage-abstraction.mmd
│   │   │   ├── platform-integrations.mmd
│   │   │   ├── git-identity-flow.mmd
│   │   │   └── api-overview.mmd
│   │   └── png/
│   │       └── *.png
│   └── planning/
│       ├── project-plan.md
│       └── testing-plan.md
├── scripts/
│   ├── export-diagrams.sh
│   └── setup.sh
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── copilot.py
│   │   ├── git.py
│   │   └── activity.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py
│   │   └── middleware.py
│   ├── identity/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── permissions/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── session/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── manager.py
│   │   └── context.py
│   ├── query/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── service.py
│   ├── delegation/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── service.py
│   │   └── worker.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── bitbucket.py
│   │   ├── gitlab.py
│   │   ├── azure_devops.py
│   │   └── generic.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── yaml_backend.py
│   │   └── encryption.py
│   ├── registry/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py
│   │   └── audit.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── copilot.py
│   │       ├── git.py
│   │       ├── repos.py
│   │       ├── sessions.py
│   │       ├── delegations.py
│   │       └── health.py
│   └── mcp/
│       ├── __init__.py
│       ├── server.py
│       ├── tools.py
│       └── resources.py
├── ui/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── stores/
│   │   ├── api/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_*.py
│   └── e2e/
│       └── *.spec.ts
├── main.py
├── config.yaml
├── config.local.yaml
├── requirements.txt
├── pytest.ini
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## Configuration Schema

```yaml
# config.yaml

server:
  host: "0.0.0.0"
  port: 8000
  debug: false
  ssl:
    enabled: false
    cert_file: ""
    key_file: ""

auth:
  jwt_secret: "${JWT_SECRET}"  # Environment variable
  jwt_algorithm: "HS256"
  token_expiry_hours: 8

storage:
  backend: "yaml"  # yaml | sqlite | vault (future)
  yaml:
    data_dir: "./data"
  encryption:
    enabled: true
    key: "${ENCRYPTION_KEY}"  # Environment variable

copilot:
  timeout: 120
  default_model: "gpt-4"
  log_dir: "./logs/copilot"

git:
  default_branch: "main"
  worktree_base: "./worktrees"
  cleanup_on_completion: true

platforms:
  bitbucket:
    cloud_api: "https://api.bitbucket.org/2.0"
    server_api: ""  # Self-hosted URL
  gitlab:
    api: "https://gitlab.com/api/v4"
  azure_devops:
    api: "https://dev.azure.com"

rate_limiting:
  enabled: true
  default_limit: "100/minute"
  query_limit: "60/minute"
  delegation_limit: "10/minute"

logging:
  level: "INFO"
  format: "json"
  audit:
    enabled: true
    retention_days: 90

mcp:
  enabled: true
  transport: "streamable-http"
  port: 8001
```

---

## Models & Interfaces

### Core Models

```python
# src/core/models.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class GitIdentity(BaseModel):
    name: str
    email: EmailStr

class User(BaseEntity):
    username: str
    email: EmailStr
    password_hash: str
    git_identity: GitIdentity
    roles: List[Role] = [Role.DEVELOPER]
    default_model: str = "gpt-4"
    is_active: bool = True

class Platform(str, Enum):
    BITBUCKET_CLOUD = "bitbucket_cloud"
    BITBUCKET_SERVER = "bitbucket_server"
    GITLAB = "gitlab"
    AZURE_DEVOPS = "azure_devops"
    GENERIC = "generic"

class Repository(BaseEntity):
    name: str
    url: str
    platform: Platform
    local_path: str
    default_branch: str = "main"
    pat_id: str  # Reference to encrypted PAT
    owner_id: str  # User who registered it
    is_active: bool = True

class SessionType(str, Enum):
    QUERY = "query"
    RESEARCH = "research"
    DELEGATION = "delegation"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConversationTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[Dict[str, Any]]] = None

class Session(BaseEntity):
    type: SessionType
    status: SessionStatus = SessionStatus.ACTIVE
    user_id: str
    repo_id: str
    branch: Optional[str] = None
    worktree_path: Optional[str] = None
    conversation: List[ConversationTurn] = []
    artifacts: List[str] = []
    completed_at: Optional[datetime] = None

class DelegationType(str, Enum):
    RESEARCH = "research"
    IMPLEMENTATION = "implementation"

class DelegationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ToolPolicy(BaseModel):
    allowed: List[str] = []
    denied: List[str] = []

class Delegation(BaseEntity):
    type: DelegationType
    status: DelegationStatus = DelegationStatus.PENDING
    user_id: str
    repo_id: str
    session_id: str
    base_branch: str
    target_branch: str
    worktree_path: str
    prompt: str
    tool_policy: Optional[ToolPolicy] = None
    commits: List[str] = []
    artifacts: List[str] = []
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

---

## API Endpoints

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/logout` | Logout (invalidate token) |
| POST | `/api/auth/refresh` | Refresh JWT token |
| GET | `/api/auth/me` | Get current user |

### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users` | List users (admin) |
| POST | `/api/users` | Create user (admin) |
| GET | `/api/users/{id}` | Get user |
| PUT | `/api/users/{id}` | Update user |
| DELETE | `/api/users/{id}` | Delete user (admin) |

### Repositories

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/repos` | List repositories |
| POST | `/api/repos` | Register repository |
| GET | `/api/repos/{id}` | Get repository |
| PUT | `/api/repos/{id}` | Update repository |
| DELETE | `/api/repos/{id}` | Unregister repository |
| POST | `/api/repos/{id}/sync` | Sync with remote |

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sessions` | List sessions |
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions/{id}` | Get session |
| DELETE | `/api/sessions/{id}` | End session |
| GET | `/api/sessions/{id}/history` | Get conversation history |

### Query

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/query` | Execute query |
| POST | `/api/query/stream` | Execute query (streaming) |

### Delegations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/delegations` | List delegations |
| POST | `/api/delegations` | Create delegation |
| GET | `/api/delegations/{id}` | Get delegation |
| POST | `/api/delegations/{id}/cancel` | Cancel delegation |
| GET | `/api/delegations/{id}/logs` | Get delegation logs |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Detailed status |

---

## MCP Tools

```python
# Available MCP tools

@mcp.tool()
async def query(
    prompt: str,
    repo_id: str,
    session_id: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Execute a query against Copilot CLI.
    
    Args:
        prompt: The question or request
        repo_id: Repository to query against
        session_id: Optional session for multi-turn
        model: Optional model override
    
    Returns:
        Copilot CLI response
    """

@mcp.tool()
async def delegate(
    prompt: str,
    repo_id: str,
    branch_name: str,
    base_branch: str = "main",
    delegation_type: str = "implementation",
    tool_policy: Optional[Dict] = None,
) -> Dict:
    """
    Create a delegation task.
    
    ⚠️ GOLDEN RULE: This will create an isolated worktree and branch.
    
    Args:
        prompt: Task description
        repo_id: Target repository
        branch_name: Name for the new branch
        base_branch: Branch to base off (default: main)
        delegation_type: "implementation" or "research"
        tool_policy: Optional tool allow/deny lists
    
    Returns:
        Delegation details including ID and status
    """

@mcp.tool()
async def research(
    prompt: str,
    repo_id: str,
    session_id: Optional[str] = None,
) -> Dict:
    """
    Start a research session with temporary worktree.
    
    Args:
        prompt: Research question
        repo_id: Repository to research
        session_id: Optional existing session
    
    Returns:
        Research results and artifacts
    """

@mcp.tool()
async def get_delegation_status(delegation_id: str) -> Dict:
    """Get status of a delegation task."""

@mcp.tool()
async def cancel_delegation(delegation_id: str) -> Dict:
    """Cancel a running delegation."""

@mcp.tool()
async def list_repositories() -> List[Dict]:
    """List all registered repositories."""

@mcp.tool()
async def list_sessions(
    status: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    """List sessions with optional status filter."""

@mcp.tool()
async def get_session_history(session_id: str) -> List[Dict]:
    """Get conversation history for a session."""
```

---

## Testing Strategy

### Coverage Requirements

- **Minimum:** 80% per phase
- **Target:** 90% for core services
- **Tool:** pytest-cov

### Test Categories

1. **Unit Tests** - Individual functions/methods
2. **Integration Tests** - Service interactions
3. **API Tests** - Endpoint testing
4. **E2E Tests** - Full workflow tests

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_config.py
│   ├── test_copilot.py
│   ├── test_git.py
│   ├── test_storage.py
│   ├── test_identity.py
│   ├── test_permissions.py
│   ├── test_session.py
│   ├── test_query.py
│   ├── test_delegation.py
│   └── test_platforms.py
├── integration/
│   ├── test_auth_flow.py
│   ├── test_query_flow.py
│   ├── test_delegation_flow.py
│   └── test_mcp_integration.py
├── api/
│   ├── test_auth_endpoints.py
│   ├── test_user_endpoints.py
│   ├── test_repo_endpoints.py
│   ├── test_session_endpoints.py
│   ├── test_query_endpoints.py
│   └── test_delegation_endpoints.py
└── e2e/
    ├── playwright.config.ts
    └── specs/
        ├── login.spec.ts
        ├── query.spec.ts
        └── delegation.spec.ts
```

### Key Fixtures

```python
# conftest.py

@pytest.fixture
def mock_copilot_cli():
    """Mock Copilot CLI for testing."""
    pass

@pytest.fixture
def test_user():
    """Create a test user."""
    pass

@pytest.fixture
def test_repo():
    """Create a test repository."""
    pass

@pytest.fixture
def test_session():
    """Create a test session."""
    pass

@pytest.fixture
async def storage_backend():
    """In-memory storage for testing."""
    pass
```

---

## Documentation Deliverables

### Required Documents

1. **README.md** - Project overview, quick start
2. **INSTALL.md** - Detailed installation guide
3. **API.md** - API reference
4. **MCP.md** - MCP integration guide
5. **SECURITY.md** - Security considerations
6. **CONTRIBUTING.md** - Contribution guidelines
7. **docs/architecture.md** - Architecture details

### MCP Documentation

Must include:
- Installation for Claude Desktop
- Installation for other MCP clients
- Tool reference with examples
- Resource reference
- Troubleshooting

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

1. **system-architecture.mmd** - Flowchart showing all components
2. **session-flow.mmd** - State diagram for session lifecycle
3. **delegation-flow.mmd** - Sequence diagram for Golden Rule
4. **mcp-integration.mmd** - Flowchart for MCP client/server
5. **auth-flow.mmd** - Sequence diagram for authentication
6. **storage-abstraction.mmd** - Class diagram for storage
7. **platform-integrations.mmd** - Flowchart for platforms
8. **git-identity-flow.mmd** - Sequence diagram for identity
9. **api-overview.mmd** - Flowchart for API categories

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
    mmdc -i "$file" -o "$PNG_DIR/$filename.png" -b transparent
    echo "Exported: $filename.png"
done
```

---

## Implementation Checklist

### Phase 0: Documentation & Planning
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

### Phase 2: Storage Abstraction
- [ ] Create abstract interface
- [ ] Implement YAML backend
- [ ] Add encryption utilities
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-2-storage` branch

### Phase 3: Identity & Permissions
- [ ] Create identity models
- [ ] Create permission models
- [ ] Implement services
- [ ] Add git identity injection
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-3-identity` branch

### Phase 4: Session Management
- [ ] Create session models
- [ ] Implement session manager
- [ ] Add context injection
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-4-sessions` branch

### Phase 5: Query Service
- [ ] Create query models
- [ ] Implement query service
- [ ] Add API routes
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-5-query` branch

### Phase 6: Delegation Service
- [ ] Create delegation models
- [ ] Implement delegation service
- [ ] Add background worker
- [ ] Implement research mode
- [ ] Enforce Golden Rule
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-6-delegation` branch

### Phase 7: Platform Integrations
- [ ] Create platform interface
- [ ] Implement Bitbucket
- [ ] Implement GitLab
- [ ] Implement Azure DevOps
- [ ] Implement Generic
- [ ] Create repository registry
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-7-platforms` branch

### Phase 8: MCP Server
- [ ] Set up FastMCP
- [ ] Implement tools
- [ ] Implement resources
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-8-mcp` branch

### Phase 9: Security Hardening
- [ ] Implement JWT auth
- [ ] Add rate limiting
- [ ] Add audit logging
- [ ] Configure HTTPS
- [ ] Write security docs
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-9-security` branch

### Phase 10: Modern UI
- [ ] Set up React project
- [ ] Implement authentication
- [ ] Build dashboard
- [ ] Build query interface
- [ ] Build delegation UI
- [ ] Build repo management
- [ ] Write tests
- [ ] Verify 80% coverage
- [ ] Commit to `phase-10-ui` branch

---

## Next Steps

1. **Review this plan** - Make any adjustments before starting
2. **Start Phase 0** - Create diagrams and documentation
3. **Follow the branching strategy** - Each phase on its own branch
4. **Maintain test coverage** - 80% minimum per phase
5. **Document as you go** - Update docs with implementation

---

*Document Version: 1.0*
*Created: January 2026*
*Last Updated: January 2026*
