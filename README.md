# FontForge Pro

> AI-assisted desktop font manager — accuracy over speed.

## Overview

FontForge Pro is a local-first, offline desktop application that cleans, organizes, and optimizes font collections using lightweight local AI (Ollama, ≤4B parameters).

### Features

- 🔍 **Recursive font scanning** — Detects TTF, OTF, WOFF, WOFF2, TTC files
- 🛡️ **Corrupted font detection** — Validates font structure, quarantines broken files
- 🔄 **Duplicate detection** — Multi-tier: hash → metadata → AI-assisted
- ✏️ **Smart renaming** — `{Family}-{Style}.ttf` from internal metadata
- 📁 **Family grouping** — Complete vs incomplete font families
- 🤖 **AI classification** — Ollama-powered (Qwen3-4B) for naming, categorization
- 📊 **Detailed reports** — JSON, CSV, HTML export
- 🔒 **Safe operations** — Never deletes, only moves; full undo support

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI + fontTools |
| Frontend | Tauri v2 + React + TypeScript |
| AI Engine | Ollama (Qwen3-4B) |
| Database | SQLite |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Rust (for Tauri)
- Ollama (for AI features)

### One-Command Setup

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Run the App

```bash
cargo tauri dev
```

### Run Backend Only

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python main.py
```

### Run Frontend Only

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
font-manager-pro/
├── backend/               # Python backend (FastAPI + fontTools)
│   ├── core/              # Scanner, validator, deduplicator, organizer
│   ├── models/            # Data models (FontEntry, Report, etc.)
│   ├── database/          # SQLite connection + CRUD
│   ├── utils/             # Hashing, file ops, weight mapping
│   └── tests/             # Unit tests
├── frontend/              # Tauri + React frontend
│   └── src/
│       ├── components/    # Wizard, FontPreview, DataTable
│       ├── hooks/         # useBackend, useFonts, useClipboard
│       └── lib/           # API client, utilities
├── src-tauri/             # Tauri Rust core
│   └── src/               # Main.rs, Python subprocess manager
├── scripts/               # Setup, Ollama install, model pull
├── PLAN.md                # Full project plan
└── TODO.md                # Progress tracker
```

## How It Works

1. **Select Folder** — Choose your font collection root
2. **Scan & Analyze** — Recursively find and parse all font files
3. **Review Issues** — See corrupted, duplicates, misnamed fonts
4. **Organize** — Group into complete/incomplete families
5. **Report & Export** — Get detailed summary in JSON/CSV/HTML

## Safety

- ✅ Fonts are **never deleted** — only moved to safe locations
- ✅ **Dry-run mode** — preview all changes before applying
- ✅ **Undo system** — every operation logged for rollback
- ✅ **Quarantine** — corrupted fonts preserved for analysis

## AI Models

The app uses local Ollama models (≤4B parameters):

| Model | Size | Purpose |
|-------|------|---------|
| Qwen3-4B | 4B | Primary classifier (structured output) |
| Qwen2.5-3B | 3B | Fallback classifier |

Install with:
```bash
ollama pull qwen3:4b
ollama pull qwen2.5:3b
```

## License

MIT
