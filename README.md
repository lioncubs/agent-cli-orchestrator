# 🤖 Agent CLI Orchestrator

A multi-CLI orchestration system with GitHub Copilot CLI support. This project provides an HTTP API and modern React dashboard for managing Git operations and executing AI-powered prompts through the GitHub Copilot CLI.

## 🌟 Features

- **Modern React Dashboard** - Beautiful, responsive web interface at `/dashboard`
- **HTTP REST API** - FastAPI-based server with comprehensive endpoints
- **GitHub Copilot CLI Integration** - Execute prompts synchronously and asynchronously
- **Memory Management** - Store and retrieve personal memories with tags and metadata
- **Git Management** - Branch switching and worktree management
- **Real-time Streaming** - Server-Sent Events (SSE) for live Copilot output
- **Web Interface** - Legacy interactive UI for testing all features at `/ui`
- **Docker Support** - Containerized deployment with pre-installed dependencies
- **YAML Configuration** - Flexible configuration system
- **Security Hardening** - Authentication, rate limiting, audit logging

## 📋 Prerequisites

- Python 3.11+
- Git
- GitHub CLI (`gh`) with Copilot extension (for Copilot features)
- Docker and Docker Compose (optional, for containerized deployment)

## 📦 Installation

### Step 1: Install Python 3.11+

**macOS (using Homebrew):**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/) or use:
```powershell
winget install Python.Python.3.11
```

Verify installation:
```bash
python3 --version  # Should show 3.11 or higher
```

### Step 2: Install Git

**macOS:**
```bash
brew install git
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install git
```

**Windows:**
```bash
winget install Git.Git
```

Verify installation:
```bash
git --version
```

### Step 3: Install GitHub CLI (gh)

**macOS:**
```bash
brew install gh
```

**Ubuntu/Debian:**
```bash
# Add GitHub CLI repository
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

# Install
sudo apt update
sudo apt install gh
```

**Windows:**
```bash
winget install GitHub.cli
```

**Alternative (all platforms):**
Download from [GitHub CLI Releases](https://github.com/cli/cli/releases)

Verify installation:
```bash
gh --version
```

### Step 4: Authenticate GitHub CLI

```bash
gh auth login
```

Follow the interactive prompts:
1. Choose "GitHub.com"
2. Choose "HTTPS" (recommended) or "SSH"
3. Choose "Login with a web browser"
4. Copy the one-time code and press Enter
5. Complete authentication in your browser

Verify authentication:
```bash
gh auth status
```

### Step 5: Install GitHub Copilot CLI Extension

```bash
gh extension install github/gh-copilot
```

Verify installation:
```bash
gh copilot --version
```

**Note:** You need an active GitHub Copilot subscription to use the CLI. Sign up at [github.com/features/copilot](https://github.com/features/copilot)

### Step 6: Test Copilot CLI (Optional)

Test the CLI directly before using the orchestrator:
```bash
gh copilot suggest "How do I list all files in a directory recursively?"
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/lioncubs/agent-cli-orchestrator.git
   cd agent-cli-orchestrator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application**
   
   Edit `config.yaml` to customize settings:
   ```yaml
   repository:
     name: "agent-cli-orchestrator"
     default_branch: "main"
   
   server:
     # Use 127.0.0.1 for local development (recommended)
     # Use 0.0.0.0 only in secure environments with authentication
     host: "127.0.0.1"
     port: 8000
   
   copilot:
     enabled: true
     timeout: 300
   
   worktrees:
     base_path: "./worktrees"
   ```

   > ⚠️ **Security Note**: The default configuration binds to `127.0.0.1` (localhost only) for security. If you need to expose the API on your network, change `host` to `0.0.0.0` and implement proper authentication (see [API.md](API.md) for details).

4. **Run the server**
   ```bash
   python main.py
   ```

5. **Access the application**
   - Modern Dashboard: http://localhost:8000/dashboard
   - API Documentation: http://localhost:8000/docs
   - Legacy Web Interface: http://localhost:8000/ui
   - API Root: http://localhost:8000/
   
   **Note**: The React UI requires a build step. If not built, you'll see instructions and a link to the legacy UI. The legacy UI works without any build step.

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Same URLs as local development

## 📚 API Endpoints

### Repository Information

- **GET `/repo`** - Get repository name
  ```json
  {
    "repository": "agent-cli-orchestrator",
    "configured_name": "agent-cli-orchestrator"
  }
  ```

### Branch Management

- **GET `/branch/current`** - Get current branch
  ```json
  {
    "branch": "main"
  }
  ```

- **POST `/branch/select`** - Switch to a different branch
  ```json
  Request: {"branch": "feature/new-feature"}
  Response: {
    "status": "success",
    "branch": "feature/new-feature",
    "message": "Switched to branch 'feature/new-feature'"
  }
  ```

### Worktree Management

- **GET `/worktrees`** - List all Git worktrees
  ```json
  {
    "worktrees": [
      {
        "path": "/path/to/repo",
        "branch": "main"
      }
    ],
    "count": 1
  }
  ```

- **POST `/worktree/create`** - Create a new worktree
  ```json
  Request: {
    "path": "./worktrees/feature-branch",
    "branch": "feature/new-feature",
    "create_branch": false
  }
  Response: {
    "status": "success",
    "path": "./worktrees/feature-branch",
    "branch": "feature/new-feature",
    "message": "Worktree created at './worktrees/feature-branch' for branch 'feature/new-feature'"
  }
  ```

### Copilot CLI Integration

- **POST `/prompt`** - Execute synchronous Copilot CLI prompt
  ```json
  Request: {
    "prompt": "How do I create a Python function to reverse a string?",
    "options": {
      "branch": "main",
      "worktree": "./worktrees/feature",
      "session_id": "abc123"
    }
  }
  Response: {
    "status": "success",
    "output": {...},
    "prompt": "How do I create a Python function to reverse a string?"
  }
  ```

  **Options parameters:**
  - `branch` (optional): Git branch to use as context
  - `worktree` (optional): Worktree path for Copilot's background agent execution
  - `session_id` (optional): Continue an existing Copilot agent session

- **POST `/prompt/async`** - Execute asynchronous Copilot CLI prompt
  - Same request/response format as `/prompt`
  - Supports all the same options: `branch`, `worktree`, `session_id`

### Web Interfaces

The orchestrator provides **two web interfaces** for different use cases:

#### Modern React Dashboard (`/ui`)
- Full-featured SPA with authentication, session management, and delegation
- Built with React, TypeScript, and Tailwind CSS
- **Requires build step**: `cd src/ui && npm install && npm run build`
- See [DUAL_UI_SETUP.md](DUAL_UI_SETUP.md) for details

#### Legacy HTML Interface (`/legacy-ui`)
- Simple, embedded HTML UI - works immediately without build
- Core features: Copilot prompts, branch/worktree management, activity logs
- Perfect for quick testing and simple deployments
- **No build required** - always available

## 🏗️ Project Structure

```
agent-cli-orchestrator/
├── main.py              # FastAPI application with all endpoints
├── config_loader.py     # Configuration management
├── git_operations.py    # Git operations (branches, worktrees)
├── copilot_cli.py       # Copilot CLI integration
├── config.yaml          # Configuration file
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container definition
├── docker-compose.yml   # Docker Compose configuration
├── .gitignore           # Git ignore patterns
└── README.md            # This file
```

## 🔧 Configuration

The `config.yaml` file contains all configurable settings:

- **repository.name** - Repository identifier
- **repository.default_branch** - Default branch name
- **server.host** - Server host address (default: 127.0.0.1 for localhost-only access)
- **server.port** - Server port (default: 8000)
- **copilot.enabled** - Enable/disable Copilot CLI features
- **copilot.timeout** - Timeout for Copilot CLI commands (seconds)
- **worktrees.base_path** - Base directory for worktrees

> ⚠️ **Security**: By default, the server binds to `127.0.0.1` (localhost only). To expose on a network, set `server.host` to `0.0.0.0` but **only** in combination with proper authentication and network security controls. See the [Security](#-security) section below.

## 🔒 Security

**⚠️ IMPORTANT: This application currently has NO authentication by default.**

### Development vs Production

#### Development (Default - Localhost Only)
The default configuration (`server.host: 127.0.0.1`) binds the API to localhost only, which is safe for development on your local machine.

#### Production or Network Access
**DO NOT** bind to `0.0.0.0` or expose this service on a network without implementing proper security measures:

**Required Security Measures:**
1. **Authentication**: Implement API key authentication, JWT tokens, or OAuth 2.0
2. **HTTPS/TLS**: Use a reverse proxy (nginx, Apache) with SSL/TLS certificates
3. **Rate Limiting**: Prevent abuse with request rate limiting
4. **Network Controls**: Use firewall rules, VPN, or IP whitelisting
5. **Input Validation**: Already implemented, but always verify

**Why This Matters:**
Without authentication, anyone with network access can:
- Execute arbitrary Copilot CLI prompts (potential data exfiltration)
- Switch Git branches in your repository
- Create or modify Git worktrees
- Access repository information

### Recommended Production Setup

```yaml
# config.yaml for production with reverse proxy
server:
  host: "127.0.0.1"  # Keep localhost, use reverse proxy
  port: 8000

# nginx reverse proxy with SSL/TLS and authentication
# See API.md for detailed production deployment guide
```

For detailed security recommendations and authentication implementation examples, see [API.md](API.md#authentication).

## 📖 Documentation

### Core Documentation
- **[README.md](README.md)** - This file, project overview and getting started
- **[API.md](API.md)** - Complete API reference and endpoint documentation
- **[INSTALL.md](INSTALL.md)** - Detailed installation instructions
- **[MULTI_REPO_FEATURES.md](MULTI_REPO_FEATURES.md)** - Multi-repository support guide
- **[STREAMING.md](STREAMING.md)** - Server-Sent Events (SSE) streaming guide

### Planning & Development
The `docs/planning/` directory contains comprehensive planning documentation:

- **[action-plan.md](docs/planning/project-plan/action-plan.md)** - Detailed development roadmap with task breakdown
- **[plan-summary.md](docs/planning/project-plan/plan-summary.md)** - High-level project plan overview
- **[security-hardening-addendum.md](docs/planning/security-hardening-addendum.md)** - Security hardening guide and checklist
- **[completion-summary.md](docs/planning/project-plan/completion-summary.md)** - Work completion summaries
- **[coverage-improvement.md](docs/planning/project-plan/coverage-improvement.md)** - Test coverage improvement plan
- **[implementation-guide.md](docs/planning/project-plan/implementation-guide.md)** - Implementation guidelines
- **[implementation-summary.md](docs/planning/project-plan/implementation-summary.md)** - Implementation notes
- **[plan.md](docs/planning/project-plan/plan.md)** - Original project plan
- **[project-plan.md](docs/planning/project-plan.md)** - Comprehensive project planning
- **[testing-plan.md](docs/planning/testing-plan.md)** - Testing strategy and plan

### Architecture
- **[docs/architecture.md](docs/architecture.md)** - System architecture and design decisions

For a complete index of planning documentation, see [docs/planning/README.md](docs/planning/README.md).

## 🧪 Testing

### Sample Copilot CLI Prompts

Here are some example prompts that should work with the Copilot CLI integration:

**General Programming Questions:**
```json
{
  "prompt": "How do I reverse a string in Python?"
}
```

**Code Generation:**
```json
{
  "prompt": "Write a Python function that reads a CSV file and returns a list of dictionaries"
}
```

**Debugging Help:**
```json
{
  "prompt": "Explain why I'm getting a 'KeyError' in Python and how to fix it"
}
```

**Best Practices:**
```json
{
  "prompt": "What are best practices for error handling in Python?"
}
```

**Git Commands:**
```json
{
  "prompt": "How do I merge a branch and resolve conflicts in Git?"
}
```

**Docker Questions:**
```json
{
  "prompt": "How do I create a multi-stage Dockerfile for a Python application?"
}
```

**Testing Questions:**
```json
{
  "prompt": "How do I write unit tests for a FastAPI endpoint using pytest?"
}
```

### Session Management

**List active Copilot sessions:**
```bash
curl http://localhost:8000/sessions
```

**Continue an existing session:**
```json
{
  "prompt": "Can you add error handling to that code?",
  "options": {
    "session_id": "abc123-session-id"
  }
}
```

**List all Git branches:**
```bash
curl http://localhost:8000/branches
```

### API Endpoint Examples

All prompts can be tested via:
- **Legacy HTML UI**: http://localhost:8000/legacy-ui (works immediately)
- **Modern React UI**: http://localhost:8000/ui (after build)
- **API Endpoint**: `POST http://localhost:8000/prompt`
- **Async Endpoint**: `POST http://localhost:8000/prompt/async`

For detailed API documentation, see [API.md](API.md).

### Testing via Web Interface

1. Navigate to http://localhost:8000/legacy-ui (or /ui if React build is available)
2. Test repository information retrieval
3. Test branch switching
4. Test worktree creation and listing
5. Test Copilot prompts (both sync and async)

### Testing with cURL

**Get repository info:**
```bash
curl http://localhost:8000/repo
```

**Get current branch:**
```bash
curl http://localhost:8000/branch/current
```

**Execute a Copilot prompt:**
```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "How do I reverse a string in Python?"}'
```

**List worktrees:**
```bash
curl http://localhost:8000/worktrees
```

**Create a memory:**
```bash
curl -X POST http://localhost:8000/memories/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your_user_id",
    "content": "I learned about FastAPI today",
    "tags": ["learning", "python"]
  }'
```

**Get your last memory:**
```bash
curl "http://localhost:8000/memories/last?user_id=your_user_id"
```

For more memory management examples, see [docs/MEMORY.md](docs/MEMORY.md).

## 🐳 Docker Notes

The Docker image includes:
- Python 3.11
- Git
- GitHub CLI (gh) with Copilot extension support
- All Python dependencies

To use Copilot CLI features in Docker, you'll need to:
1. Authenticate GitHub CLI: `gh auth login`
2. Install Copilot extension: `gh extension install github/gh-copilot`

## 🔮 Future Enhancements

- Support for additional CLI tools (Azure CLI, AWS CLI, etc.)
- WebSocket support for real-time updates
- Job queue for long-running operations
- Authentication and authorization
- Metrics and monitoring
- Unit and integration tests
- CI/CD pipeline

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please use the GitHub Issues page.
