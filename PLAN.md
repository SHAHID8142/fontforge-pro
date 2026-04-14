# FontForge Pro — AI-Assisted Font Manager

> **Accuracy > Speed** — Safe, local-first, offline font organization system

---

## 🎯 Core Problem

Font collections over time become messy:
- Corrupted files that crash design tools
- Duplicate fonts wasting disk space
- Misnamed files (`abc123.ttf` = `Roboto Bold`)
- Incomplete families scattered across folders
- System slowdown from thousands of active fonts

---

## 🏗️ Architecture (Revised & Improved)

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | Python | fontTools, freetype-python, rich ecosystem |
| **Frontend** | Tauri v2 + React + TypeScript | 96% smaller than Electron, 50% less RAM, native performance |
| **Font Parsing** | fontTools (Python) | Industry standard, reads TTF/OTF/WOFF/WOFF2/TTC |
| **AI Engine** | Ollama via HTTP API | Local, offline, pluggable models |
| **AI Model** | **Qwen3-4B** (primary), **Qwen2.5-3B** (fallback) | Best structured output, reasoning mode, excellent at classification |
| **Database** | SQLite | Zero-config, ACID, perfect for desktop |
| **File Operations** | Python `pathlib` + `shutil` | Safe move/rename with rollback |

### Why Tauri + Python (not Rust + Python)?

- Tauri's `tauri-plugin-shell` can spawn Python subprocesses
- Alternative: **PyO3** bindings (PyTauri) for direct Python integration
- **Recommended approach**: Python backend as a local service, Tauri frontend communicates via stdin/stdout or TCP socket
- This keeps font parsing in Python (fontTools is mature) while UI stays in Tauri

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Tauri App (Frontend)              │
│  ┌───────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │   React   │  │  Next.js │  │  Font Preview    │  │
│  │    UI     │  │  Router  │  │  (Canvas/WebGL)  │  │
│  └─────┬─────┘  └────┬─────┘  └────────┬────────┘  │
│        │              │                 │            │
│        └──────────────┴─────────────────┘            │
│                         │                            │
│              ┌──────────▼──────────┐                │
│              │   Tauri Commands    │                │
│              │   (Rust ↔ Python)   │                │
│              └──────────┬──────────┘                │
└─────────────────────────┼───────────────────────────┘
                          │ IPC (stdin/stdout or HTTP)
┌─────────────────────────▼───────────────────────────┐
│                  Python Backend                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Scanner │  │Validator │  │  AI Classifier   │  │
│  │ Module   │  │  Module  │  │  (Ollama HTTP)   │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                 │             │
│  ┌────▼──────────────▼─────────────────▼─────────┐  │
│  │           fontTools + FreeType                │  │
│  │         (Font Parsing Engine)                 │  │
│  └────────────────────┬──────────────────────────┘  │
│                       │                              │
│  ┌────────────────────▼──────────────────────────┐  │
│  │          SQLite Database (State)              │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                 File System                          │
│  /organized/  /duplicates/  /quarantine/  /reports/ │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Features (Prioritized & Enhanced)

### Phase 1: Core Engine (MVP)

#### 1. Recursive Font Scanner
- **Formats**: `.ttf`, `.otf`, `.woff`, `.woff2`, `.ttc`
- **Metadata extracted via fontTools**:
  - Family name (nameID 1)
  - SubFamily/Style (nameID 2)
  - Full name (nameID 4)
  - Weight class (OS/2 table `usWeightClass`)
  - Version
  - Glyph count
  - File hash (SHA256 for duplicate detection)
  - File size
  - Last modified date

#### 2. Corrupted Font Detection
- Validate font tables using `fontTools.ttLib.TTFont()`
- Catch exceptions: `ttLib.TTLibError`, structure errors
- Check for missing critical tables (`head`, `hhea`, `maxp`, `cmap`)
- **Actions**:
  - Move to `/quarantine/corrupted_fonts/`
  - Log error details in SQLite
  - Optional: basic auto-repair (rebuild missing name records)

#### 3. Duplicate Detection (Multi-Tier)
```
Tier 1: Exact hash match (SHA256) → 100% duplicate
Tier 2: Same family + style + weight → Likely duplicate
Tier 3: Same family + similar name → Possible duplicate (flag for review)
Tier 4: AI-assisted glyph comparison → Near-duplicate detection
```
- **Action**: Keep newest/highest quality, move others to `/duplicates/`

#### 4. Smart Renaming Engine
- Compare filename vs internal metadata
- Rename pattern: `{Family}-{Style}.ttf`
  - Examples: `Roboto-Bold.ttf`, `OpenSans-Italic.ttf`
- Handles edge cases:
  - Spaces → hyphens
  - Special characters removal
  - Name conflicts (append `_1`, `_2`)
  - Case normalization

#### 5. Family Grouping Engine
```
├── organized/
│   ├── complete_families/
│   │   ├── Roboto/
│   │   │   ├── Roboto-Regular.ttf
│   │   │   ├── Roboto-Bold.ttf
│   │   │   ├── Roboto-Italic.ttf
│   │   │   └── Roboto-BoldItalic.ttf
│   │   └── OpenSans/
│   │       └── ...
│   └── incomplete_families/
│       ├── CustomFont/
│       │   └── CustomFont-Bold.ttf  (missing Regular, Italic)
│       └── ...
```

**Complete family detection**:
- A family is "complete" if it has: Regular, Bold, Italic, BoldItalic (minimum 4)
- Incomplete families flagged with missing styles report

---

### Phase 2: AI-Powered Features

#### 6. Ollama Integration (AI Classification)

**Model Selection**:
| Model | Size | VRAM | Best For |
|-------|------|------|----------|
| **Qwen3-4B** (primary) | 4B | ~3GB | Structured output, reasoning, classification |
| **Qwen2.5-3B** (fallback) | 3B | ~2GB | Fast classification, naming |
| **Phi-4 Mini** (alternative) | 3.8B | ~2.5GB | Instruction following |

**AI Tasks** (only when rule-based logic fails):
1. **Name normalization**: `RobotoBd` → `Roboto Bold`
2. **Category classification**: serif, sans-serif, display, handwriting, monospace, script
3. **Missing style inference**: Detect if "Bd" = "Bold"
4. **Family grouping suggestions**: Detect mismatched families
5. **Font similarity detection**: Find near-duplicates

**Prompt Template** (optimized for Qwen3-4B):
```
You are a font classification expert. Analyze this font metadata and return ONLY valid JSON.

Font Metadata:
- Filename: "abc123.ttf"
- Internal Family: "RobotoBd"
- Internal Style: "Bd"
- Weight Class: 700
- Glyph Count: 876

Return your analysis in this exact JSON format:
{
  "corrected_family": "Roboto",
  "corrected_style": "Bold",
  "category": "sans-serif",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}

Do not include any text outside the JSON object.
```

**Ollama API Integration** (Python):
```python
import requests

def classify_font_with_ai(metadata: dict) -> dict:
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "qwen3:4b",
        "prompt": build_prompt(metadata),
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temp for deterministic output
            "num_predict": 500
        }
    })
    return parse_json_response(response.json()["response"])
```

---

### Phase 3: UX & Polish

#### 7. Background Processing Engine
- **Queue-based system** using Python `queue.Queue`
- **Priority levels**:
  - High: User-triggered actions
  - Normal: Scan & organize
  - Low: Background AI classification
- **Features**:
  - Pause/Resume
  - Progress bar with ETA
  - Low CPU priority mode (`nice` on Unix)
  - Batch processing (50 fonts per batch)
  - Auto-retry on failures

#### 8. Font Preview System
- Render fonts in Tauri webview using CSS `@font-face`
- Custom preview text input
- Clipboard monitoring (copy text → instant preview)
- Adjustable font size slider
- Live character map (optional)

#### 9. Reporting System
```json
{
  "scan_summary": {
    "total_fonts": 12450,
    "formats": {"ttf": 8000, "otf": 4000, "woff2": 450},
    "scan_time": "2m 34s"
  },
  "issues_found": {
    "corrupted": 120,
    "duplicates": 2340,
    "misnamed": 3200,
    "incomplete_families": 310
  },
  "actions_taken": {
    "quarantined": 120,
    "duplicates_moved": 2340,
    "renamed": 3200,
    "organized": 5400
  }
}
```
- **Export formats**: JSON, CSV, HTML report
- **Before/After preview**: Show what will change before executing

#### 10. Safety Features
- ✅ **Never delete** — only move files
- ✅ **Dry-run mode** — preview all changes before applying
- ✅ **Undo system** — maintain operation log for rollback
- ✅ **SQLite operation log** — every file move recorded
- ✅ **Conflict resolution** — user prompts for ambiguous cases
- ✅ **Backup folder** — optional pre-processing backup

---

## 🔄 Workflow (Wizard-Based UX)

```
┌─────────────────────────────────────────────┐
│  Step 1: Select Source Folder               │
│  [Browse...] /Users/maryam/Fonts/           │
│  [ ] Include subfolders (checked)           │
│  [ ] Create backup before processing         │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Step 2: Scan & Analyze                     │
│  ████████████████░░░░  78% (9,712/12,450)   │
│  Found: 8,234 valid | 120 corrupted        │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Step 3: Review Issues                      │
│  ┌─────────────────────────────────────┐   │
│  │ ⚠️  Corrupted (120)                 │   │
│  │ 🔄 Duplicates (2,340)               │   │
│  │ ✏️  Misnamed (3,200)                │   │
│  │ 📁 Incomplete Families (310)        │   │
│  └─────────────────────────────────────┘   │
│  [View Details] [Apply All Fixes]          │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Step 4: Organize                           │
│  [ ] Group by family                         │
│  [ ] Separate complete/incomplete           │
│  [ ] AI-powered classification               │
│  [Preview Changes] [Execute]                │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Step 5: Report & Export                    │
│  Summary + charts                            │
│  [Export JSON] [Export CSV] [Export HTML]   │
│  [View Organized Folder] [Done]             │
└─────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
font-manager-pro/
├── plan.md                      # This file
├── README.md                    # Project documentation
├── .gitignore
│
├── backend/                     # Python backend
│   ├── __init__.py
│   ├── main.py                  # Entry point (FastAPI or HTTP server)
│   ├── requirements.txt
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scanner.py           # Recursive font scanner
│   │   ├── validator.py         # Corruption detection
│   │   ├── deduplicator.py      # Duplicate detection
│   │   ├── renamer.py           # Smart renaming logic
│   │   ├── organizer.py         # Family grouping
│   │   ├── ai_classifier.py     # Ollama integration
│   │   └── reporter.py          # Report generation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── font_entry.py        # Font metadata dataclass
│   │   ├── scan_result.py       # Scan result models
│   │   └── report.py            # Report data models
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                # SQLite connection manager
│   │   ├── operations.py        # CRUD operations
│   │   └── migrations.py        # Schema migrations
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_ops.py          # Safe file operations
│   │   ├── hash_utils.py        # SHA256 hashing
│   │   └── weight_mapper.py     # Weight class → name mapping
│   │
│   └── tests/
│       ├── test_scanner.py
│       ├── test_validator.py
│       ├── test_deduplicator.py
│       └── test_ai_classifier.py
│
├── frontend/                    # Tauri + React frontend
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   │
│   ├── src/
│   │   ├── main.tsx             # Entry point
│   │   ├── App.tsx              # Root component
│   │   │
│   │   ├── components/
│   │   │   ├── Wizard/
│   │   │   │   ├── Step1SelectFolder.tsx
│   │   │   │   ├── Step2ScanProgress.tsx
│   │   │   │   ├── Step3ReviewIssues.tsx
│   │   │   │   ├── Step4Organize.tsx
│   │   │   │   └── Step5Report.tsx
│   │   │   ├── FontPreview/
│   │   │   │   ├── PreviewCard.tsx
│   │   │   │   ├── CharacterMap.tsx
│   │   │   │   └── PreviewControls.tsx
│   │   │   ├── DataTable/
│   │   │   │   ├── FontTable.tsx
│   │   │   │   ├── FilterBar.tsx
│   │   │   │   └── SortHeader.tsx
│   │   │   └── common/
│   │   │       ├── Button.tsx
│   │   │       ├── ProgressBar.tsx
│   │   │       └── Modal.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useBackend.ts    # Python IPC communication
│   │   │   ├── useFonts.ts      # Font data state management
│   │   │   └── useClipboard.ts  # Clipboard monitoring
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts           # Backend API client
│   │   │   └── utils.ts         # Utility functions
│   │   │
│   │   └── styles/
│   │       └── globals.css
│   │
│   └── public/
│       └── ...
│
├── src-tauri/                   # Tauri Rust backend
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── build.rs
│   └── src/
│       ├── main.rs              # Rust entry point
│       ├── lib.rs               # Tauri commands
│       └── python.rs            # Python subprocess management
│
└── scripts/
    ├── setup.sh                 # Initial setup script
    ├── install-ollama.sh        # Ollama installation helper
    └── pull-models.sh           # Pull required Ollama models
```

---

## ⚡ Performance Strategy

| Technique | Implementation |
|-----------|---------------|
| **Multi-threaded scanning** | `concurrent.futures.ThreadPoolExecutor` for I/O bound scanning |
| **Batch processing** | Process 50 fonts per batch, checkpoint after each |
| **Lazy AI classification** | Only call Ollama when rule-based logic fails or user requests |
| **SQLite caching** | Cache scan results, skip unchanged files (compare mtime + hash) |
| **Font preview lazy load** | Load font into CSS only when user selects it |
| **Memory-efficient hashing** | Hash first 1MB of file for quick duplicate detection, full hash only on match |

---

## 🔒 Safety Guarantees

1. **No destructive operations** — files are moved, never deleted
2. **Dry-run mode** — all changes previewed before execution
3. **Operation log** — every file move logged in SQLite for undo
4. **Conflict handling** — user prompted when target name exists
5. **Quarantine, not delete** — corrupted fonts preserved for analysis
6. **Backup option** — optional full backup before major operations

---

## 🚀 Future Enhancements (Post-MVP)

- [ ] Font activation/deactivation system (like Font Book)
- [ ] Live font preview with custom text
- [ ] Font pairing suggestions (AI-powered)
- [ ] Cloud sync for font libraries
- [ ] Plugin system for custom organizers
- [ ] Font similarity search (vector embeddings)
- [ ] Import from Google Fonts, Adobe Fonts catalogs
- [ ] Font license checker (commercial vs free)

---

## 📦 Dependencies

### Python Backend
```txt
fonttools>=4.47.0        # Font parsing
freetype-py>=2.3.0       # Font validation
chardet>=5.2.0           # Encoding detection
fastapi>=0.109.0         # HTTP API (lightweight)
uvicorn>=0.27.0          # ASGI server
pydantic>=2.5.0          # Data validation
requests>=2.31.0         # Ollama HTTP client
```

### Tauri Frontend
```json
{
  "dependencies": {
    "@tauri-apps/api": "^2.0.0",
    "@tauri-apps/plugin-shell": "^2.0.0",
    "@tauri-apps/plugin-dialog": "^2.0.0",
    "@tauri-apps/plugin-fs": "^2.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.3.0"
  }
}
```

---

## 🛠️ Setup & Run

```bash
# 1. Clone repo
git clone <repo-url> && cd font-manager-pro

# 2. Setup Python backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Install Ollama + model
brew install ollama   # or download from https://ollama.com
ollama serve &
ollama pull qwen3:4b

# 4. Setup Tauri frontend
cd ../frontend
npm install

# 5. Run in development
cd ../src-tauri
cargo tauri dev
```

---

## 📊 Metrics & KPIs

| Metric | Target |
|--------|--------|
| Scan speed | ~500 fonts/minute |
| AI classification | ~10 fonts/minute (background) |
| Memory usage | <500MB RAM |
| Binary size | <15MB (Tauri advantage) |
| False duplicate rate | <2% |
| Rename accuracy | >98% |

---

## 🎨 UI Design Principles

1. **Dark mode first** — designers prefer dark UI for font work
2. **Preview-centric** — font preview always visible
3. **Wizard flow** — guide users step by step
4. **Non-destructive by default** — dry-run always shown first
5. **Progressive disclosure** — advanced options hidden by default

---

## 🧪 Testing Strategy

| Layer | Tool | Coverage |
|-------|------|----------|
| Unit | `pytest` | Scanner, validator, deduplicator |
| Integration | `pytest` + test fonts | Full pipeline on sample fonts |
| E2E | Tauri driver | Wizard flow on real fonts |
| AI | Mock Ollama responses | Classifier edge cases |

---

**Next Steps**: Choose what to build first:
1. Backend scanner + validator (core engine)
2. Tauri project scaffold + UI skeleton
3. Wizard step 1-2 (folder selection + scanning)
4. Ollama integration prototype
