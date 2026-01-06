# Project Plan: Agent CLI Orchestrator

## Objective
To build an HTTP-based multi-CLI orchestration system, starting with Copilot CLI integration, while ensuring extensibility to support additional CLIs in the future. This project will allow developers to standardize CLI interactions via an HTTP interface, choose branches, and dynamically interact with Git worktrees.

---

## Features for Phase 1

### 1. HTTP Server
- A lightweight HTTP server to:
  - Accept **POST** requests for prompt submission to the Copilot CLI.
  - Handle **GET** requests for various base functionalities like:
    - `/repo`: Retrieve the name of the repository being worked on.
    - `/branch/current`: Fetch the current branch in use.
    - `/worktrees`: Obtain a list of available Git worktrees.
  - Support both **synchronous** and **asynchronous prompts** using Copilot CLI.

### 2. Copilot CLI Integration
- Adopt `copilot prompt -i "<input_text>" -o json` for prompt handling.
- Use Python's subprocess library to:
    - Execute commands like the above.
    - Parse CLI output.
    - Gracefully handle errors returned from Copilot CLI to avoid runtime failures.

### 3. Repository and Branch Management
- API support for:
  - Fetching and switching branches.
  - Managing Git worktrees with the following endpoints:
    - **GET `/worktrees`**: List all tracked worktrees.
    - **POST `/worktree/create`**: Add a new worktree dynamically for a specific branch.

### 4. YAML Configuration Support
- A simple, centralized `config.yaml` for the agent to load:
    - Default repository location.
    - Default branch.
    - Optional predefined worktree paths.

### 5. Prototype HTTP Landing Page
- Serve an initial web interface to:
    - Test prompt submission via **sync** or **async** flows.
    - Retrieve prompt results for active or completed tasks through polling.

### 6. Documentation
- Detailed setup and run instructions documented in the repository README.
- Explanation of HTTP endpoints and their usage.

---

## Technologies
- **Programming Language**: Python 3.x
- **Framework**: FastAPI or Flask
- **Git Integration**: For branch and worktree actions.
- **Process Management**: Use `subprocess` to interact with Copilot CLI.

---

## Next Steps
1. Set up the repository structure:
   - `app/` for HTTP server logic.
   - `tests/` for automated testing.
   - Add `README.md`.
2. Build basic HTTP routes for Copilot CLI integration.
3. Implement branching and worktree management features.
4. Create the YAML configuration for repo and branch defaults.
5. Test sync/async CLI prompt workflows.
6. Deploy a functional prototype with documentation.

---

## Future Extensions
- Integration with additional CLIs (e.g., Terraform, AWS CLI).
- Environments support for dynamic CLI switching.
- Role-based access and audit logs.
- Container orchestration (e.g., Docker, Kubernetes).

---

Let’s begin by implementing the foundational HTTP services and Copilot CLI integration.