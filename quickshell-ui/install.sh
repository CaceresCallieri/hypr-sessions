#!/usr/bin/env bash
# Install sessions-ui as a standalone QuickShell configuration.
# Idempotent — safe to run multiple times.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$HOME/.config/quickshell/sessions-ui"

echo "Installing sessions-ui in standalone mode..."
echo "  Project: $PROJECT_DIR"
echo "  Target:  $TARGET_DIR"
echo

ln -sfn "$PROJECT_DIR" "$TARGET_DIR"
echo "  Linked $TARGET_DIR -> $PROJECT_DIR"

echo
echo "Done. Run with:"
echo "  qs -c sessions-ui"
echo
echo "Or for development (clears QML cache):"
echo "  ./quickshell-ui/run.sh"
