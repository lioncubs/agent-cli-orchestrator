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
      "worktree": "./worktrees/feature"
    }
  }
  Response: {
    "status": "success",
    "output": {...},
    "prompt": "How do I create a Python function to reverse a string?"
  }
  ```

- **POST `/prompt/async`** - Execute asynchronous Copilot CLI prompt
  - Same request/response format as `/prompt`

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

### Manual Testing via Web Interface

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
