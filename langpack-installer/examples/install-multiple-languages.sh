#!/bin/bash
# Example: Install multiple language packs
# Usage: ./install-multiple-languages.sh /opt/pentaho/pentaho-server

PENTAHO_HOME="${1:-/opt/pentaho/pentaho-server}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$SCRIPT_DIR/../pentaho-langpack"

# Languages to install
LANGUAGES=(
    "ru"      # Russian
    "pt_BR"   # Portuguese (Brazil)
    "es"      # Spanish
    "fr"      # French
    "de"      # German
    "zh_CN"   # Chinese (Simplified)
)

echo "=========================================="
echo "Pentaho Multi-Language Pack Installer"
echo "=========================================="
echo ""
echo "Pentaho Home: $PENTAHO_HOME"
echo "Languages: ${LANGUAGES[*]}"
echo ""

# Check if Pentaho directory exists
if [ ! -d "$PENTAHO_HOME" ]; then
    echo "Error: Pentaho directory not found: $PENTAHO_HOME"
    echo "Usage: $0 <pentaho-home>"
    exit 1
fi

# Install each language
SUCCESS_COUNT=0
FAIL_COUNT=0

for lang in "${LANGUAGES[@]}"; do
    echo "→ Installing $lang..."

    if "$INSTALLER" install "$lang" --pentaho "$PENTAHO_HOME"; then
        echo "  ✓ $lang installed successfully"
        ((SUCCESS_COUNT++))
    else
        echo "  ✗ $lang installation failed"
        ((FAIL_COUNT++))
    fi
    echo ""
done

# Summary
echo "=========================================="
echo "Installation Summary"
echo "=========================================="
echo "Successful: $SUCCESS_COUNT"
echo "Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✓ All language packs installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Restart Pentaho server:"
    echo "   $PENTAHO_HOME/stop-pentaho.sh"
    echo "   $PENTAHO_HOME/start-pentaho.sh"
    echo ""
    echo "2. Log in to Pentaho and check language options"
    exit 0
else
    echo "⚠ Some language packs failed to install"
    echo "Check the output above for errors"
    exit 1
fi
