# Installation Guide - Agent CLI Orchestrator

This guide provides detailed, step-by-step instructions for installing and setting up the Agent CLI Orchestrator on your system.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installing Python](#installing-python)
3. [Installing Git](#installing-git)
4. [Installing GitHub CLI](#installing-github-cli)
5. [Authenticating GitHub CLI](#authenticating-github-cli)
6. [Installing GitHub Copilot CLI](#installing-github-copilot-cli)
7. [Installing the Application](#installing-the-application)
8. [Verifying Installation](#verifying-installation)
9. [Troubleshooting](#troubleshooting)

## System Requirements

- **Operating System**: macOS, Linux (Ubuntu/Debian), or Windows 10/11
- **RAM**: Minimum 4GB
- **Disk Space**: At least 500MB free
- **Internet Connection**: Required for GitHub CLI and Copilot features
- **GitHub Account**: Required with active Copilot subscription

## Installing Python

### macOS

**Option 1: Using Homebrew (Recommended)**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Verify installation
python3 --version
```

**Option 2: Using Official Installer**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. Verify: `python3 --version`

### Ubuntu/Debian Linux

```bash
# Update package list
sudo apt update

# Install Python 3.11 and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip

# Set Python 3.11 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Verify installation
python3 --version
```

### Windows

**Option 1: Using winget**
```powershell
winget install Python.Python.3.11
```

**Option 2: Using Official Installer**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **Important**: Check "Add Python to PATH"
4. Verify in PowerShell: `python --version`

## Installing Git

### macOS

```bash
# Using Homebrew
brew install git

# Verify
git --version
```

### Ubuntu/Debian Linux

```bash
# Install Git
sudo apt update
sudo apt install -y git

# Verify
git --version
```

### Windows

**Option 1: Using winget**
```powershell
winget install Git.Git
```

**Option 2: Using Official Installer**
1. Download from [git-scm.com](https://git-scm.com/downloads)
2. Run installer with default options
3. Verify in PowerShell: `git --version`

### Configure Git (All Platforms)

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Installing GitHub CLI

### macOS

```bash
# Using Homebrew
brew install gh

# Verify
gh --version
```

### Ubuntu/Debian Linux

```bash
# Add GitHub CLI repository
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
  sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg

sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
  sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

# Install GitHub CLI
sudo apt update
sudo apt install -y gh

# Verify
gh --version
```

### Windows

**Option 1: Using winget**
```powershell
winget install GitHub.cli
```

**Option 2: Using Scoop**
```powershell
scoop install gh
```

**Option 3: Using Official Installer**
1. Download from [GitHub CLI Releases](https://github.com/cli/cli/releases)
2. Run the MSI installer
3. Verify in PowerShell: `gh --version`

## Authenticating GitHub CLI

### Interactive Authentication (Recommended)

```bash
gh auth login
```

Follow these prompts:
```
? What account do you want to log into?
  > GitHub.com

? What is your preferred protocol for Git operations?
  > HTTPS

? Authenticate Git with your GitHub credentials?
  > Yes

? How would you like to authenticate GitHub CLI?
  > Login with a web browser

! First copy your one-time code: XXXX-XXXX
Press Enter to open github.com in your browser...
```

### Using Personal Access Token

If you prefer using a token:

1. Create a token at https://github.com/settings/tokens
   - Select scopes: `repo`, `read:org`, `copilot`
2. Authenticate:
   ```bash
   gh auth login --with-token < token.txt
   # Or paste token when prompted
   ```

### Verify Authentication

```bash
gh auth status
```

Expected output:
```
github.com
  ✓ Logged in to github.com as <username> (/path/to/config)
  ✓ Git operations for github.com configured to use https protocol.
  ✓ Token: *******************
```

## Installing GitHub Copilot CLI

### Install the Extension

```bash
gh extension install github/gh-copilot
```

### Verify Installation

```bash
gh copilot --version
```

Expected output:
```
gh version X.X.X (YYYY-MM-DD)
```

### Test Copilot CLI

Test with a simple command:
```bash
gh copilot suggest "list files in current directory"
```

### Troubleshooting Copilot Installation

**Issue: "extension not found"**
```bash
# Update GitHub CLI
brew upgrade gh  # macOS
sudo apt upgrade gh  # Ubuntu
winget upgrade GitHub.cli  # Windows

# Try installing again
gh extension install github/gh-copilot
```

**Issue: "Copilot subscription required"**
- Ensure you have an active Copilot subscription
- Sign up at [github.com/features/copilot](https://github.com/features/copilot)
- Wait a few minutes after subscribing, then try again

**Issue: Extension installed but not working**
```bash
# Remove and reinstall
gh extension remove gh-copilot
gh extension install github/gh-copilot
```

## Installing the Application

### Clone the Repository

```bash
# Clone the repo
git clone https://github.com/lioncubs/agent-cli-orchestrator.git

# Navigate to directory
cd agent-cli-orchestrator
```

### Create Virtual Environment (Recommended)

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Upgrade pip
python -m pip install --upgrade pip
```

### Install Python Dependencies

```bash
# Install all requirements
pip install -r requirements.txt
```

### Configure the Application

Copy and customize the configuration file:
```bash
# Use default config.yaml or create a custom one
cp config.yaml config.local.yaml  # Optional

# Edit configuration
nano config.yaml  # or use your preferred editor
```

Key configuration options:
```yaml
repository:
  name: "agent-cli-orchestrator"
  default_branch: "main"

server:
  host: "0.0.0.0"  # Use 127.0.0.1 for localhost only
  port: 8000

copilot:
  enabled: true  # Set to false if Copilot not available
  timeout: 300   # Timeout in seconds

worktrees:
  base_path: "./worktrees"
```

## Verifying Installation

### Run the Application

```bash
# Start the server
python main.py
```

Expected output:
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Test the Installation

**1. Open Web Browser**
Navigate to: http://localhost:8000/ui

You should see the Agent CLI Orchestrator web interface.

**2. Test API Endpoint**
```bash
curl http://localhost:8000/repo
```

Expected response:
```json
{
  "repository": "agent-cli-orchestrator",
  "configured_name": "agent-cli-orchestrator"
}
```

**3. Test Copilot Integration**
```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "How do I reverse a string in Python?"}'
```

**4. Run Tests**
```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov

# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Troubleshooting

### Python Version Issues

**Issue: Wrong Python version**
```bash
# Check version
python3 --version

# If incorrect, use full path
/usr/local/bin/python3.11 -m venv venv
```

### Permission Issues

**macOS/Linux:**
```bash
# If permission denied
chmod +x start.sh

# If sudo required for pip
pip install --user -r requirements.txt
```

**Windows:**
```powershell
# Run PowerShell as Administrator if needed
```

### GitHub CLI Authentication Issues

**Issue: Authentication expired**
```bash
# Re-authenticate
gh auth logout
gh auth login
```

**Issue: Token permissions**
- Ensure token has `repo`, `read:org`, and `copilot` scopes
- Regenerate token if necessary

### Copilot CLI Not Working

**Issue: "copilot: command not found"**
```bash
# Verify extension is installed
gh extension list

# Should show: github/gh-copilot

# If not, install:
gh extension install github/gh-copilot
```

**Issue: "Copilot request failed"**
- Check subscription status at github.com/settings/copilot
- Verify authentication: `gh auth status`
- Check internet connection
- Try: `gh extension upgrade gh-copilot`

### Port Already in Use

**Issue: Port 8000 already in use**

Edit `config.yaml`:
```yaml
server:
  port: 8080  # Use different port
```

Or set environment variable:
```bash
PORT=8080 python main.py
```

### Import Errors

**Issue: ModuleNotFoundError**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Docker Installation (Alternative)

If you prefer using Docker:

```bash
# Build and run
docker-compose up --build

# Access at http://localhost:8000
```

## Getting Help

If you encounter issues not covered here:

1. Check the [README.md](README.md) for additional documentation
2. Review [API.md](API.md) for API details
3. Check [GitHub Issues](https://github.com/lioncubs/agent-cli-orchestrator/issues)
4. Create a new issue with:
   - Your operating system
   - Python version (`python3 --version`)
   - Error messages
   - Steps to reproduce

## Next Steps

After successful installation:

1. Explore the web interface at http://localhost:8000/ui
2. Read the API documentation at http://localhost:8000/docs
3. Review sample prompts in README.md
4. Check out the project roadmap in `docs/planning/project-plan.md`

Happy orchestrating! 🚀