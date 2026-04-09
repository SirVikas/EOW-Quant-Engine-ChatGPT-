#!/usr/bin/env bash
# EOW Quant Engine — Linux/macOS Quick-Install
# Usage: bash install_and_run.sh [paper|live]

set -e
cd "$(dirname "$0")"
MODE=${1:-paper}

echo ""
echo " ╔═══════════════════════════════════════════╗"
echo " ║   EOW QUANT ENGINE  —  Linux/macOS Setup  ║"
echo " ╚═══════════════════════════════════════════╝"
echo ""

# ── Check Python ─────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] Python 3.11+ required. Install via: sudo apt install python3"
    exit 1
fi
PY=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo " [1/5] Python $PY detected ✓"

# ── Virtual Environment ───────────────────────────────────────────────────────
if [ ! -d "venv" ]; then
    echo " [2/5] Creating virtual environment..."
    python3 -m venv venv
else
    echo " [2/5] Virtual environment exists ✓"
fi
source venv/bin/activate

# ── Install Dependencies ──────────────────────────────────────────────────────
echo " [3/5] Installing Python dependencies..."
pip install -r requirements.txt -q --disable-pip-version-check

# ── Directories ───────────────────────────────────────────────────────────────
echo " [4/5] Creating data directories..."
mkdir -p data/exports

# ── .env File ─────────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.template .env
    echo " [5/5] .env created from template."
    echo "       Edit .env with your Binance API keys before going LIVE."
else
    echo " [5/5] .env already exists ✓"
fi

# ── Optional: start Redis ─────────────────────────────────────────────────────
if command -v redis-server &>/dev/null; then
    if ! redis-cli ping &>/dev/null; then
        echo " [+] Starting local Redis..."
        redis-server --daemonize yes --port 6379 --loglevel warning
    fi
fi

echo ""
echo " ════════════════════════════════════════════"
echo " Setup complete! Launching in $(echo $MODE | tr '[:lower:]' '[:upper:]') mode..."
echo " Dashboard opens automatically in your browser."
echo " Press Ctrl+C to stop."
echo " ════════════════════════════════════════════"
echo ""

python run.py "$MODE"
