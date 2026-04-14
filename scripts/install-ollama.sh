#!/usr/bin/env bash
set -euo pipefail

echo "🤖 Installing Ollama..."

if command -v ollama &> /dev/null; then
    echo "✅ Ollama already installed: $(ollama --version)"
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

echo "✅ Ollama: $(ollama --version)"

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &
sleep 3

echo "✅ Ollama service started"
echo ""
echo "Next step: Run ./scripts/pull-models.sh to download AI models"
