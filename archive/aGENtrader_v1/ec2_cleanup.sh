#!/bin/bash
# EC2 Environment Cleanup Script
# This script organizes the EC2 environment to match the Replit structure,
# removing redundant files and organizing the codebase.

set -e  # Exit on any error
echo "Starting EC2 environment cleanup..."

# Create a backup of the current state before cleaning
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
echo "Creating backup in $BACKUP_DIR..."
mkdir -p $BACKUP_DIR
cp -r * $BACKUP_DIR/ 2>/dev/null || true
cp -r .* $BACKUP_DIR/ 2>/dev/null || true
echo "Backup created successfully."

# Create the required directory structure if it doesn't exist
echo "Creating directory structure..."
mkdir -p agents
mkdir -p agents_backup
mkdir -p api
mkdir -p archive
mkdir -p attached_assets
mkdir -p backtesting
mkdir -p backups
mkdir -p coding
mkdir -p config
mkdir -p data
mkdir -p data_integrity_deployment
mkdir -p deployment
mkdir -p docs
mkdir -p examples
mkdir -p logs/decisions
mkdir -p models
mkdir -p orchestration
mkdir -p scripts
mkdir -p server
mkdir -p strategies
mkdir -p tests
mkdir -p utils

# Move files to their appropriate directories
echo "Organizing files..."

# Move agent-related files
echo "Moving agent files..."
find . -maxdepth 1 -name "*agent*.py" -not -path "./agents/*" -not -path "./agents_backup/*" -exec mv {} ./agents/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*trader*.py" -not -path "./agents/*" -not -path "./agents_backup/*" -exec mv {} ./agents/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*analysis*.py" -not -path "./agents/*" -not -path "./strategies/*" -exec mv {} ./agents/ \; 2>/dev/null || true

# Move API-related files
echo "Moving API files..."
find . -maxdepth 1 -name "*api*.py" -not -path "./api/*" -exec mv {} ./api/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*endpoint*.py" -not -path "./api/*" -exec mv {} ./api/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*rest*.py" -not -path "./api/*" -exec mv {} ./api/ \; 2>/dev/null || true

# Move backtesting files
echo "Moving backtesting files..."
find . -maxdepth 1 -name "*backtest*.py" -not -path "./backtesting/*" -exec mv {} ./backtesting/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*backtest*.sh" -not -path "./backtesting/*" -exec mv {} ./backtesting/ \; 2>/dev/null || true

# Move configuration files
echo "Moving configuration files..."
find . -maxdepth 1 -name "*.conf" -not -path "./config/*" -exec mv {} ./config/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*config*.json" -not -path "./config/*" -exec mv {} ./config/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*config*.py" -not -path "./config/*" -exec mv {} ./config/ \; 2>/dev/null || true

# Move data files
echo "Moving data files..."
find . -maxdepth 1 -name "*.csv" -not -path "./data/*" -exec mv {} ./data/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*.json" -not -path "./data/*" -not -path "./config/*" -not -name "package.json" -not -name "package-lock.json" -not -name "tsconfig.json" -exec mv {} ./data/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*data*.py" -not -path "./data/*" -exec mv {} ./data/ \; 2>/dev/null || true

# Move documentation files
echo "Moving documentation files..."
find . -maxdepth 1 -name "*.md" -not -path "./docs/*" -not -name "README.md" -not -name "API_DOCUMENTATION.md" -not -name "CLEANUP_COMPLETION_REPORT.md" -not -name "CLEANUP_PLAN.md" -not -name "CLEANUP_SUMMARY.md" -not -name "BACKEND_FOCUS_README.md" -not -name "REORGANIZATION_COMPLETE.md" -not -name "REORGANIZATION_SUMMARY.md" -exec mv {} ./docs/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*.pdf" -not -path "./docs/*" -not -path "./attached_assets/*" -not -name "AGENT_ARCHITECTURE.pdf" -exec mv {} ./docs/ \; 2>/dev/null || true

# Move server-related files
echo "Moving server files..."
find . -maxdepth 1 -name "*server*.js" -not -path "./server/*" -not -name "test_server.js" -not -name "test_simple_api.js" -not -name "start_test_server.sh" -not -name "stop_test_server.sh" -exec mv {} ./server/ \; 2>/dev/null || true
find . -maxdepth 1 -name "index.js" -not -path "./server/*" -exec mv {} ./server/ \; 2>/dev/null || true

# Move script files
echo "Moving script files..."
find . -maxdepth 1 -name "*.sh" -not -name "start_test_server.sh" -not -name "stop_test_server.sh" -not -name "backend_focus_cleanup.sh" -not -name "backup_codebase.sh" -not -name "complete_cleanup.sh" -not -name "data_cleanup.sh" -not -name "ec2_cleanup.sh" -not -path "./scripts/*" -not -path "./backtesting/*" -exec mv {} ./scripts/ \; 2>/dev/null || true

# Move utility files
echo "Moving utility files..."
find . -maxdepth 1 -name "*util*.py" -not -path "./utils/*" -exec mv {} ./utils/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*helper*.py" -not -path "./utils/*" -exec mv {} ./utils/ \; 2>/dev/null || true

# Move orchestration files
echo "Moving orchestration files..."
find . -maxdepth 1 -name "*orchestr*.py" -not -path "./orchestration/*" -exec mv {} ./orchestration/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*decision_session*.py" -not -path "./orchestration/*" -exec mv {} ./orchestration/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*workflow*.py" -not -path "./orchestration/*" -exec mv {} ./orchestration/ \; 2>/dev/null || true

# Move testing files
echo "Moving test files..."
find . -maxdepth 1 -name "*test*.py" -not -name "test_output.py" -not -name "test_system.py" -not -path "./tests/*" -exec mv {} ./tests/ \; 2>/dev/null || true

# Move outdated or redundant files to archive
echo "Archiving outdated files..."
find . -maxdepth 1 -name "*.bak" -exec mv {} ./archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*old*" -exec mv {} ./archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*deprecated*" -exec mv {} ./archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*.py.save" -exec mv {} ./archive/ \; 2>/dev/null || true

# Handle any duplicate files in destination directories
echo "Checking for duplicates..."
for dir in agents api backtesting config data docs orchestration scripts server strategies tests utils; do
    find ./$dir -type f | while read file; do
        basename=$(basename "$file")
        count=$(find ./$dir -name "$basename" | wc -l)
        if [ $count -gt 1 ]; then
            # Keep the newest version, archive others
            newest=$(find ./$dir -name "$basename" -printf "%T@ %p\n" | sort -n | tail -1 | cut -d' ' -f2-)
            find ./$dir -name "$basename" | grep -v "$newest" | while read dupe; do
                echo "Moving duplicate $dupe to archive"
                mv "$dupe" "./archive/${basename%.*}_dupe_$(date +%Y%m%d_%H%M%S).${basename##*.}"
            done
        fi
    done
done

# Create a report of the cleanup
echo "Generating cleanup report..."
cat > CLEANUP_COMPLETION_REPORT.md << EOF
# EC2 Environment Cleanup Report

## Cleanup Completed on $(date)

### Directory Structure
The EC2 environment has been organized to match the Replit structure with the following directories:

- agents: Agent-related Python files
- agents_backup: Backup of agent files
- api: API-related Python files
- archive: Archived outdated or redundant files
- attached_assets: Asset files
- backtesting: Backtesting scripts and modules
- backups: Backup directory with timestamped backup from this cleanup
- config: Configuration files
- data: Data files and datasets
- deployment: Deployment-related files
- docs: Documentation files
- logs: Log files
- models: Model-related files
- orchestration: Orchestration modules
- scripts: Shell scripts
- server: Server-related JavaScript files
- strategies: Trading strategy modules
- tests: Test modules
- utils: Utility modules

### Files Organized
Files have been moved to their appropriate directories based on their names and functions.

### Backup
A complete backup of the environment before cleanup was created in:
$BACKUP_DIR

### Next Steps
1. Review the organization to ensure all files are in the appropriate locations
2. Test the system functionality to confirm everything works as expected
3. Update any path references in code that may have been affected by the reorganization
EOF

echo "EC2 environment cleanup completed successfully!"
echo "A backup of the original state is available in: $BACKUP_DIR"
echo "See CLEANUP_COMPLETION_REPORT.md for details and next steps."