#!/usr/bin/env bash
set -euo pipefail

echo "🤖 Pulling required Ollama models..."

echo ""
echo "📥 Pulling Qwen3-4B (primary model)..."
ollama pull qwen3:4b

echo ""
echo "📥 Pulling Qwen2.5-3B (fallback model)..."
ollama pull qwen2.5:3b

echo ""
echo "✅ Models downloaded:"
ollama list

echo ""
echo "You're ready to use AI-powered font classification!"
