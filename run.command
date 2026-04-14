#!/bin/bash
# FontForge Pro — Double-click to run
# This script starts the backend + frontend and opens the app in your browser.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 FontForge Pro — Starting..."
echo "================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install Python first."
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install Node.js first."
    exit 1
fi

# Check venv exists
if [ ! -d "backend/venv" ]; then
    echo "📦 First run — setting up Python dependencies..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Check node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 First run — installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "▶️  Starting Backend on http://127.0.0.1:8765"
echo "▶️  Starting Frontend on http://127.0.0.1:1420"
echo ""
echo "🌐 Opening app in your browser..."
echo "   (Press Ctrl+C to stop)"
echo "================================"

# Start backend in background
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
sleep 2

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment then open browser
sleep 3
open http://localhost:1420 2>/dev/null || xdg-open http://localhost:1420 2>/dev/null || echo "👉 Open http://localhost:1420 in your browser"

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Stopped."
    exit 0
}

trap cleanup INT TERM

# Wait for either process to exit
wait
