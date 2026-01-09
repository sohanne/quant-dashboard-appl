#!/bin/bash
set -e

# Go to repository root
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# Activate virtual environment if present (Linux)
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

# Run daily portfolio report
python -m portfolio.daily_report

