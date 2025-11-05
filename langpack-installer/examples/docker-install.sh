#!/bin/bash
# Example: Install language packs in a Docker container
# Usage: ./docker-install.sh <container-name-or-id> ru pt_BR

CONTAINER="$1"
shift
LANGUAGES=("$@")

if [ -z "$CONTAINER" ] || [ ${#LANGUAGES[@]} -eq 0 ]; then
    echo "Usage: $0 <container> <language1> [language2] ..."
    echo ""
    echo "Example:"
    echo "  $0 pentaho-server ru pt_BR es"
    echo ""
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Docker Language Pack Installation"
echo "=========================================="
echo ""
echo "Container: $CONTAINER"
echo "Languages: ${LANGUAGES[*]}"
echo ""

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "Error: Container '$CONTAINER' not found"
    exit 1
fi

# Copy installer to container
echo "→ Copying installer to container..."
docker cp "$SCRIPT_DIR/.." "$CONTAINER:/tmp/langpack-installer"

# Copy data directory
echo "→ Copying language pack data..."
docker cp "$SCRIPT_DIR/../../data" "$CONTAINER:/tmp/langpack-installer/"

# Install each language
for lang in "${LANGUAGES[@]}"; do
    echo ""
    echo "→ Installing $lang in container..."

    docker exec "$CONTAINER" python3 \
        /tmp/langpack-installer/pentaho-langpack.py install "$lang" \
        --pentaho /opt/pentaho/pentaho-server \
        --data-dir /tmp/langpack-installer/data

    if [ $? -eq 0 ]; then
        echo "  ✓ $lang installed"
    else
        echo "  ✗ $lang failed"
    fi
done

# Restart container
echo ""
echo "→ Restarting container..."
docker restart "$CONTAINER"

echo ""
echo "✓ Installation complete!"
echo "Container is restarting. Wait a minute then access Pentaho."
