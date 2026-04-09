#!/usr/bin/env bash
# EOW Quant Engine — Start Script
# Usage: bash start.sh [paper|live]

set -e
cd "$(dirname "$0")"

MODE=${1:-paper}
MODE_UPPER=$(echo "$MODE" | tr '[:lower:]' '[:upper:]')

echo "╔══════════════════════════════════════════╗"
echo "║   EOW QUANT ENGINE  —  v1.0              ║"
echo "║   Mode: $MODE_UPPER                           ║"
echo "╚══════════════════════════════════════════╝"

# Activate venv if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set env
export TRADE_MODE=$MODE_UPPER

# Check Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis not detected. Starting local Redis..."
    redis-server --daemonize yes --port 6379
fi

echo "🚀 Starting FastAPI backend on http://0.0.0.0:8000"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
