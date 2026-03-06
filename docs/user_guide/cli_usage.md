LI Usage Guide
Overview
The Command Line Interface (CLI) provides powerful tools for managing projects, tasks, and automation directly from your terminal. Perfect for developers and power users who prefer command-line workflows.

Installation
macOS
Using Homebrew:
bashbrew tap example/cli
brew install example-cli
Using installer:
bashcurl -fsSL https://cli.example.com/install.sh | sh
Linux
Using package manager:
bash# Ubuntu/Debian
curl -sL https://cli.example.com/deb | sudo bash
sudo apt-get install example-cli

# CentOS/RHEL
curl -sL https://cli.example.com/rpm | sudo bash
sudo yum install example-cli

# Arch Linux
yay -S example-cli
Manual installation:
bashwget https://github.com/example/cli/releases/latest/download/example-cli-linux-amd64.tar.gz
tar -xzf example-cli-linux-amd64.tar.gz
sudo mv example /usr/local/bin/
Windows
Using Chocolatey:
powershellchoco install example-cli
Using Scoop:
powershellscoop bucket add example https://github.com/example/scoop-bucket
scoop install example-cli
Using installer:
powershell# Run in PowerShell as Administrator
iwr https://cli.example.com/install.ps1 | iex
Verify Installation
bashexample --version
# Output: example-cli version 2.5.0

Authentication
Login
bash# Interactive login
example login

# Login with API key
example login --api-key sk_live_abc123xyz789

# Login with OAuth
example login --oauth

# Login with specific organization
example login --org acme-corp
Interactive Login Flow:
$ example login
? Enter your email: john@example.com
? Enter your password: ********
✓ Authentication successful!
✓ Logged in as John Doe (john@example.com)
✓ Default organization: Acme Corp

You can now use the CLI. Try:
  example projects list
Logout
bashexample logout

# Logout from all sessions
example logout --all
Check Authentication Status
bashexample whoami

# Output:
# User: John Doe (john@example.com)
# Organization: Acme Corp (org_abc123)
# Plan: Pro
# API Key: sk_live_***xyz789