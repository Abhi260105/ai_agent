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

Update Task
bash# Update task status
example tasks update tsk_abc123 --status done

# Update assignee
example tasks update tsk_abc123 --assignee jane@example.com

# Update priority
example tasks update tsk_abc123 --priority high

# Update due date
example tasks update tsk_abc123 --due +3d  # 3 days from now
example tasks update tsk_abc123 --due 2026-02-20

# Add comment
example tasks comment tsk_abc123 "This is looking good!"

# Bulk update
example tasks update tsk_abc123 tsk_def456 --status done
Task Actions
bash# Assign to yourself
example tasks assign tsk_abc123

# Start task (change to in-progress)
example tasks start tsk_abc123

# Complete task
example tasks complete tsk_abc123

# Move task to different project
example tasks move tsk_abc123 --project prj_def456

# Clone task
example tasks clone tsk_abc123 --title "Similar task"
Task Templates
bash# Create from template
example tasks create --template bug-report

# List available templates
example tasks templates list

# Create custom template
example tasks templates create bug-report \
  --title "Bug: {{title}}" \
  --description "Steps to reproduce:\n1. \n2. \n3. " \
  --priority high \
  --tags bug

File Management
Upload Files
bash# Upload single file
example files upload design.png --project prj_abc123

# Upload with metadata
example files upload design.png \
  --project prj_abc123 \
  --folder designs/v2 \
  --description "Homepage mockup v2"

# Upload multiple files
example files upload *.png --project prj_abc123

# Upload directory
example files upload ./assets/* \
  --project prj_abc123 \
  --folder project-assets \
  --recursive

# Upload and attach to task
example files upload screenshot.png \
  --task tsk_abc123
List Files
bash# List all files in project
example files list --project prj_abc123

# Filter by folder
example files list --project prj_abc123 --folder designs

# Filter by type
example files list --project prj_abc123 --type image

# Search files
example files list --search mockup
Download Files
bash# Download single file
example files download fil_abc123

# Download to specific location
example files download fil_abc123 --output ~/Downloads/design.png

# Download all files from project
example files download --project prj_abc123 --all

# Download folder
example files download --project prj_abc123 --folder designs
Delete Files
bash# Delete file
example files delete fil_abc123

# Delete multiple files
example files delete fil_abc123 fil_def456

# Delete all files in folder
example files delete --project prj_abc123 --folder old-designs

Team Management
List Team Members
bash# List all members
example team list

# List with roles
example team list --show-roles

# Filter by role
example team list --role admin
Invite Member
bash# Interactive invite
example team invite

# Direct invite
example team invite jane.doe@example.com \
  --role member \
  --projects prj_abc123,prj_def456

# Invite multiple members
example team invite \
  alice@example.com \
  bob@example.com \
  charlie@example.com \
  --role member
Remove Member
bash# Remove member
example team remove jane@example.com

# Remove with confirmation
example team remove jane@example.com --confirm
Update Member Role
bash# Change role
example team update jane@example.com --role admin

# Add to projects
example team update jane@example.com \
  --add-projects prj_ghi789

Automation & Scripting
Batch Operations
bash# Complete all tasks assigned to you
example tasks list --assignee me --status in-progress \
  --format json | \
  jq -r '.data[].id' | \
  xargs -I {} example tasks complete {}

# Archive old projects
example projects list --status inactive --format json | \
  jq -r '.data[].id' | \
  xargs -I {} example projects archive {}
Scripting Examples
Daily Standup Report:
bash#!/bin/bash
# daily-standup.sh

echo "📊 Daily Standup Report"
echo "======================="
echo ""

echo "✅ Completed Yesterday:"
example tasks list \
  --assignee me \
  --status done \
  --completed-after yesterday \
  --format json | \
  jq -r '.data[] | "  - \(.title)"'

echo ""
echo "🏃 Working On Today:"
example tasks list \
  --assignee me \
  --status in-progress \
  --format json | \
  jq -r '.data[] | "  - \(.title)"'

echo ""
echo "⚠️ Blockers:"
example tasks list \
  --assignee me \
  --priority urgent \
  --status blocked \
  --format json | \
  jq -r '.data[] | "  - \(.title)"'
Automated Task Creation:
bash#!/bin/bash
# create-weekly-tasks.sh

TASKS=(
  "Weekly team meeting"
  "Review pull requests"
  "Update documentation"
  "Sprint planning"
)

for task in "${TASKS[@]}"; do
  example tasks create "$task" \
    --project prj_abc123 \
    --assignee me \
    --due +7d \
    --tags recurring
done
Backup Script:
bash#!/bin/bash
# backup-projects.sh

BACKUP_DIR="$HOME/backups/example/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Export projects
example projects list --format json > "$BACKUP_DIR/projects.json"

# Export tasks
example tasks list --format json > "$BACKUP_DIR/tasks.json"

# Download files
example files download --all --output "$BACKUP_DIR/files/"

echo "✓ Backup completed: $BACKUP_DIR"
Webhooks from CLI
bash# List webhooks
example webhooks list

# Create webhook
example webhooks create \
  --url https://your-app.com/webhooks \
  --events user.created,task.completed \
  --secret your_webhook_secret

# Test webhook
example webhooks test whk_abc123

# Delete webhook
example webhooks delete whk_abc123

Watch Mode
Monitor changes in real-time:
bash# Watch task list
example tasks list --watch

# Watch specific project
example projects get prj_abc123 --watch

# Watch with custom interval
example tasks list --watch --interval 5s

Output Formatting
Format Options
bash# Table (default)
example tasks list --output table

# JSON
example tasks list --output json

# JSON (pretty)
example tasks list --output json --pretty

# YAML
example tasks list --output yaml

# CSV
example tasks list --output csv

# Custom template
example tasks list --template "{{.id}}: {{.title}}"
Filter Output with JQ
bash# Get task IDs only
example tasks list --output json | jq -r '.data[].id'

# Get high priority tasks
example tasks list --output json | \
  jq '.data[] | select(.priority == "high")'

# Count tasks by status
example tasks list --output json | \
  jq -r '.data | group_by(.status) | 
  map({status: .[0].status, count: length})'
Color Output
bash# Enable colors
example tasks list --color

# Disable colors
example tasks list --no-color

# Auto-detect (default)
example tasks list

Advanced Features
Shell Completion
Bash:
bashexample completion bash > /etc/bash_completion.d/example
Zsh:
bashexample completion zsh > "${fpath[1]}/_example"
Fish:
bashexample completion fish > ~/.config/fish/completions/example.fish
Aliases
Create shortcuts in your shell:
bash# Add to ~/.bashrc or ~/.zshrc
alias et='example tasks'
alias ep='example projects'
alias ec='example tasks create'
alias el='example tasks list'