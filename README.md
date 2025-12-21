# 🤖 Agent CLI Orchestrator

A multi-CLI orchestration system with GitHub Copilot CLI support. This project provides an HTTP API and web interface for managing Git operations and executing AI-powered prompts through the GitHub Copilot CLI.

## 🌟 Features

- **HTTP REST API** - FastAPI-based server with comprehensive endpoints
- **GitHub Copilot CLI Integration** - Execute prompts synchronously and asynchronously
- **Git Management** - Branch switching and worktree management
- **Web Interface** - Interactive UI for testing all features
- **Docker Support** - Containerized deployment with pre-installed dependencies
- **YAML Configuration** - Flexible configuration system

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
     host: "0.0.0.0"
     port: 8000
   
   copilot:
     enabled: true
     timeout: 300
   
   worktrees:
     base_path: "./worktrees"
   ```

4. **Run the server**
   ```bash
   python main.py
   ```

5. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Web Interface: http://localhost:8000/ui
   - API Root: http://localhost:8000/

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

### Web Interface

- **GET `/ui`** - Interactive web interface for testing all features

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
- **server.host** - Server host address (default: 0.0.0.0)
- **server.port** - Server port (default: 8000)
- **copilot.enabled** - Enable/disable Copilot CLI features
- **copilot.timeout** - Timeout for Copilot CLI commands (seconds)
- **worktrees.base_path** - Base directory for worktrees

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
- **Web UI**: http://localhost:8000/ui
- **API Endpoint**: `POST http://localhost:8000/prompt`
- **Async Endpoint**: `POST http://localhost:8000/prompt/async`

For detailed API documentation, see [API.md](API.md).

### Testing via Web Interface

1. Navigate to http://localhost:8000/ui
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
