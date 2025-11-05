#!/bin/bash
# Example: Deploy language packs with automatic Pentaho restart
# Usage: ./deploy-with-restart.sh ru pt_BR es

PENTAHO_HOME="${PENTAHO_HOME:-/opt/pentaho/pentaho-server}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$SCRIPT_DIR/../pentaho-langpack"

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <language1> [language2] [language3] ..."
    echo ""
    echo "Examples:"
    echo "  $0 ru"
    echo "  $0 ru pt_BR es"
    echo "  PENTAHO_HOME=/opt/pentaho/pentaho-server $0 ru"
    echo ""
    echo "Available languages:"
    "$INSTALLER" list
    exit 1
fi

LANGUAGES=("$@")

echo "=========================================="
echo "Pentaho Language Pack Deployment"
echo "=========================================="
echo ""
echo "Pentaho Home: $PENTAHO_HOME"
echo "Languages: ${LANGUAGES[*]}"
echo ""

# Confirm
read -p "Continue with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Backup
BACKUP_FILE="/tmp/pentaho-system-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "Creating backup: $BACKUP_FILE"
tar -czf "$BACKUP_FILE" \
    "$PENTAHO_HOME/pentaho-solutions/system" \
    2>/dev/null
echo "✓ Backup created"
echo ""

# Install languages
echo "Installing language packs..."
SUCCESS_COUNT=0
FAIL_COUNT=0

for lang in "${LANGUAGES[@]}"; do
    echo "→ Installing $lang..."

    if "$INSTALLER" install "$lang" --pentaho "$PENTAHO_HOME"; then
        echo "  ✓ $lang installed"
        ((SUCCESS_COUNT++))
    else
        echo "  ✗ $lang failed"
        ((FAIL_COUNT++))
    fi
done

echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    echo "⚠ Some installations failed"
    echo "Backup saved at: $BACKUP_FILE"
    exit 1
fi

echo "✓ All language packs installed successfully"
echo ""

# Restart Pentaho
echo "Restarting Pentaho server..."

if [ -f "$PENTAHO_HOME/stop-pentaho.sh" ]; then
    echo "→ Stopping Pentaho..."
    "$PENTAHO_HOME/stop-pentaho.sh"

    echo "→ Waiting 10 seconds..."
    sleep 10

    echo "→ Starting Pentaho..."
    "$PENTAHO_HOME/start-pentaho.sh"

    echo ""
    echo "=========================================="
    echo "✓ Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Installed languages: ${LANGUAGES[*]}"
    echo "Backup saved at: $BACKUP_FILE"
    echo ""
    echo "Pentaho server is starting up..."
    echo "Wait a few minutes, then log in and check language options."
else
    echo "⚠ Could not find Pentaho start/stop scripts"
    echo "Please restart Pentaho manually:"
    echo "  $PENTAHO_HOME/stop-pentaho.sh"
    echo "  $PENTAHO_HOME/start-pentaho.sh"
fi
