#!/bin/bash
# Setup script for Multi-Agent Intelligence System
# This creates the project structure and placeholder files

set -e

PROJECT_NAME="agentSquad"

echo "Creating Multi-Agent Intelligence System project..."

# Create project directory
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Create directory structure
echo "Creating directory structure..."
mkdir -p .claude
mkdir -p data/drone_telemetry
mkdir -p data/intel_reports
mkdir -p src/agents
mkdir -p tests

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Environment
.env
.env.local

# Claude Code
.claude/settings.local.json
EOF

echo ""
echo "✅ Project structure created!"
echo ""
echo "Next steps:"
echo "1. Copy the artifacts from Claude chat into these files:"
echo "   - .claude/CLAUDE.md"
echo "   - .claude/settings.json"
echo "   - PROJECT_SPEC.md"
echo "   - requirements.txt"
echo "   - README.md"
echo "   - SETUP_GUIDE.md"
echo "   - data/drone_telemetry/sample_trigger_event.json"
echo ""
echo "2. Set your API key:"
echo "   export ANTHROPIC_API_KEY='your-key-here'"
echo ""
echo "3. Start Claude Code:"
echo "   cd $PROJECT_NAME"
echo "   claude"
echo ""
echo "4. Tell Claude Code to implement the system (see SETUP_GUIDE.md)"
echo ""
echo "Project ready at: $PROJECT_NAME/"
