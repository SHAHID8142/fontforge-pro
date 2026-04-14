#!/usr/bin/env bash
set -euo pipefail

echo "🔧 FontForge Pro — Setup Script"
echo "================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install it first."
    exit 1
fi

echo "✅ Python: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Install it first."
    exit 1
fi

echo "✅ Node.js: $(node --version)"

# Check Rust (for Tauri)
if ! command -v rustc &> /dev/null; then
    echo "❌ Rust is required. Install it from https://rustup.rs"
    exit 1
fi

echo "✅ Rust: $(rustc --version)"

# Setup Python backend
echo ""
echo "📦 Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup Frontend
echo ""
echo "📦 Setting up frontend..."
cd frontend
npm install
cd ..

# Check Tauri
echo ""
echo "📦 Checking Tauri dependencies..."
if ! cargo tauri --version &> /dev/null; then
    echo "Installing Tauri CLI..."
    cargo install tauri-cli --version "^2.0.0"
fi

echo ""
echo "================================="
echo "✅ Setup complete!"
echo ""
echo "To run the app:"
echo "  cargo tauri dev"
echo ""
echo "To run just the backend:"
echo "  cd backend && source venv/bin/activate && python main.py"
echo ""
echo "To run just the frontend:"
echo "  cd frontend && npm run dev"
