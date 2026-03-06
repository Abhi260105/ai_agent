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

Create Project
bash# Interactive mode
example projects create

# With inline arguments
example projects create \
  --name "Q2 Product Launch" \
  --description "Launch new features for Q2 2026" \
  --template software-dev \
  --visibility private

# From JSON file
example projects create --from-file project.json
project.json:
json{
  "name": "Q2 Product Launch",
  "description": "Launch new features for Q2 2026",
  "template": "software-dev",
  "settings": {
    "visibility": "private",
    "enable_notifications": true
  },
  "members": [
    "john@example.com",
    "jane@example.com"
  ]
}
Update Project
bash# Update project details
example projects update prj_abc123 \
  --name "Q2 Product Launch v2" \
  --status active

# Update settings
example projects update prj_abc123 \
  --set-setting visibility=public

# Archive project
example projects archive prj_abc123
Delete Project
bash# Delete with confirmation
example projects delete prj_abc123

# Force delete (skip confirmation)
example projects delete prj_abc123 --force

# Delete multiple
example projects delete prj_abc123 prj_def456 prj_ghi789

Task Management
List Tasks
bash# List all tasks
example tasks list

# List tasks in project
example tasks list --project prj_abc123

# Filter tasks
example tasks list --status todo
example tasks list --assignee john@example.com
example tasks list --priority high
example tasks list --due-before 2026-02-20

# Multiple filters
example tasks list \
  --project prj_abc123 \
  --status "in-progress" \
  --assignee me \
  --priority high

# Sort results
example tasks list --sort created_at:desc
example tasks list --sort priority:asc,due_date:asc
Create Task
bash# Interactive mode
example tasks create

# Quick create
example tasks create "Design homepage mockup"

# With full details
example tasks create \
  --title "Implement user authentication" \
  --description "Add OAuth 2.0 support" \
  --project prj_abc123 \
  --assignee jane@example.com \
  --priority high \
  --due 2026-02-20 \
  --tags backend,security

# Natural language parsing
example tasks create "Fix bug #123 due tomorrow @john !urgent"