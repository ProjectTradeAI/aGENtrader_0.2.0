#!/bin/bash

# Script to prepare for GitHub repository separation
# This script prepares the aGENtrader_v2 directory for migration to a new GitHub repository

echo "Preparing aGENtrader_v2 for GitHub separation..."

# Create a temporary directory for the v2 files
mkdir -p temp_v2_repo

# Copy the v2 directory contents
echo "Copying aGENtrader_v2 files..."
cp -r aGENtrader_v2/* temp_v2_repo/

# Copy essential docs
echo "Copying documentation files..."
cp aGENtrader_v2/README.md temp_v2_repo/
cp aGENtrader_v2/requirements.txt temp_v2_repo/

# Create a .gitignore file
cat > temp_v2_repo/.gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
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
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# OS specific files
.DS_Store
Thumbs.db

# Project specific
data/simulated/*.json
logs/decisions/*.json
EOF

# Create a basic GitHub Actions workflow for CI
mkdir -p temp_v2_repo/.github/workflows
cat > temp_v2_repo/.github/workflows/python-tests.yml << EOF
name: Python Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        pip install pytest
    - name: Run tests
      run: |
        pytest
EOF

echo "Files prepared in temp_v2_repo/"
echo ""
echo "Next steps for GitHub separation:"
echo "1. Create a new repository on GitHub named 'aGENtrader-v2'"
echo "2. Initialize the repository locally:"
echo "   cd temp_v2_repo"
echo "   git init"
echo "   git add ."
echo "   git commit -m \"Initial commit of aGENtrader v2\""
echo "3. Link to your GitHub repository:"
echo "   git remote add origin https://github.com/yourusername/aGENtrader-v2.git"
echo "4. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "See GITHUB_SEPARATION_GUIDE.md for more detailed instructions."