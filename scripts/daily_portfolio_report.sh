#!/bin/bash
set -e

# Go to repo root
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# Activate venv if present (Linux path)
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

python -m src.portfolio.daily_report
