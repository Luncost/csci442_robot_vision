#!/bin/bash
# Activate the project venv, creating it first if it doesn't exist.
# Must be SOURCED, not executed:  source venv.sh

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    echo "Run this with: source ${0}"
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Creating venv at $VENV_DIR"
    # --system-site-packages keeps apt packages (opencv, picamera2) visible
    python3 -m venv --system-site-packages "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
cd "$PROJECT_DIR"
echo "venv active: $(python --version) at $VIRTUAL_ENV"
