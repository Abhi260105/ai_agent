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

Configuration
View Configuration
bash# Show all configuration
example config list

# Show specific value
example config get api_key
example config get default_org
Set Configuration
bash# Set default organization
example config set default_org acme-corp

# Set output format
example config set output json

# Set default project
example config set default_project prj_abc123
Configuration File
Location: ~/.example/config.yml
yaml# Example configuration file
api_key: sk_live_abc123xyz789
default_org: acme-corp
default_project: prj_abc123
output_format: table  # table, json, yaml, csv
editor: vim
timezone: America/New_York
color: true
Environment Variables
Override config with environment variables:
bashexport EXAMPLE_API_KEY=sk_live_abc123xyz789
export EXAMPLE_ORG=acme-corp
export EXAMPLE_OUTPUT=json

Project Management
List Projects
bash# List all projects
example projects list

# List with filters
example projects list --status active
example projects list --owner john@example.com
example projects list --limit 10

# Output formats
example projects list --output json
example projects list --output csv > projects.csv
Example Output:
┌──────────────┬─────────────────────┬────────┬────────────┬────────────┐
│ ID           │ NAME                │ STATUS │ OWNER      │ TASKS      │
├──────────────┼─────────────────────┼────────┼────────────┼────────────┤
│ prj_abc123   │ Website Redesign    │ Active │ John Doe   │ 45/100     │
│ prj_def456   │ Mobile App v2       │ Active │ Jane Smith │ 23/50      │
│ prj_ghi789   │ Marketing Campaign  │ Paused │ Bob Wilson │ 10/30      │
└──────────────┴─────────────────────┴────────┴────────────┴────────────┘
Get Project Details
bash# Get project by ID
example projects get prj_abc123

# Get with statistics
example projects get prj_abc123 --stats

# Get and open in browser
example projects get prj_abc123 --web