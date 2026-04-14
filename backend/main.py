from __future__ import annotations

"""
FontForge Pro — AI-Assisted Font Manager
FastAPI backend entry point.
"""

import logging
import asyncio
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.scanner import FontScanner
from core.processor import ProcessingEngine, ProgressInfo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Initializing FontForge Pro backend...")
    app.state.db = None  # Initialize on first use
    app.state.scanner = FontScanner()
    app.state.processor = ProcessingEngine(batch_size=50, max_retries=2)
    app.state.ws_clients: list[WebSocket] = []
    logger.info("Backend ready.")
    yield
    logger.info("Shutting down...")
    app.state.processor.stop()


app = FastAPI(
    title="FontForge Pro API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tauri localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def broadcast_progress(data: dict):
    """Send progress update to all connected WebSocket clients."""
    dead = []
    for ws in app.state.ws_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        app.state.ws_clients.remove(ws)


# --- Request Models ---

class ScanRequest(BaseModel):
    folder_path: str
    include_subfolders: bool = True


class ValidateRequest(BaseModel):
    font_paths: list[str]


class RepairRequest(BaseModel):
    font_path: str
    output_path: Optional[str] = None


class DedupRequest(BaseModel):
    font_entries: list[dict]


class OrganizeRequest(BaseModel):
    font_entries: list[dict]
    output_dir: str


class ClassifyRequest(BaseModel):
    font_entries: list[dict]


# --- Routes ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await websocket.accept()
    app.state.ws_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        if websocket in app.state.ws_clients:
            app.state.ws_clients.remove(websocket)


@app.post("/scan")
async def scan_fonts(req: ScanRequest):
    """Scan a folder for font files."""
    scanner: FontScanner = app.state.scanner

    def progress_callback(total: int, found: int):
        asyncio.create_task(broadcast_progress({
            "type": "scan_progress",
            "total": total,
            "found": found,
            "percentage": round((total / max(total, 1)) * 100, 1),
        }))

    scanner.progress_callback = progress_callback
    results = scanner.scan(req.folder_path, recursive=req.include_subfolders)

    await broadcast_progress({
        "type": "scan_complete",
        "total": len(results),
        "valid": len([f for f in results if f.is_valid]),
        "invalid": len([f for f in results if not f.is_valid]),
    })

    return {
        "total": len(results),
        "fonts": [f.to_dict() for f in results],
    }


@app.post("/validate")
async def validate_fonts(req: ValidateRequest):
    """Validate font files for corruption."""
    from core.validator import FontValidator

    validator = FontValidator()
    results = validator.validate_batch(req.font_paths)
    return {"results": results}


@app.post("/repair")
async def repair_font(req: RepairRequest):
    """Attempt to repair a corrupted font file."""
    from core.validator import FontValidator

    validator = FontValidator()
    return validator.try_repair(req.font_path, req.output_path)


@app.post("/deduplicate")
async def find_duplicates(req: DedupRequest):
    """Find duplicate fonts."""
    from core.deduplicator import Deduplicator
    from models.font_entry import FontEntry
    dedup = Deduplicator()
    # Convert dicts to FontEntry objects
    fonts = [
        FontEntry(
            path=Path(f["path"]),
            filename=f["filename"],
            extension=f["extension"],
            file_size=f["file_size"],
            family_name=f.get("family_name", ""),
            style_name=f.get("style_name", ""),
            weight_class=f.get("weight_class", 400),
            sha256_hash=f.get("sha256_hash", ""),
            glyph_count=f.get("glyph_count", 0),
            version=f.get("version", ""),
        )
        for f in req.font_entries
    ]
    groups = dedup.find_duplicates(fonts)
    return {"duplicate_groups": groups}


@app.post("/organize")
async def organize_fonts(req: OrganizeRequest):
    """Organize fonts into family groups."""
    from core.organizer import FontOrganizer
    from models.font_entry import FontEntry
    from pathlib import Path

    organizer = FontOrganizer()
    fonts = [
        FontEntry(
            path=Path(f["path"]),
            filename=f["filename"],
            extension=f["extension"],
            file_size=f["file_size"],
            family_name=f.get("family_name", ""),
            style_name=f.get("style_name", ""),
            suggested_family=f.get("suggested_family", ""),
            suggested_style=f.get("suggested_style", ""),
        )
        for f in req.font_entries
    ]
    result = organizer.organize(fonts, req.output_dir)
    return result


@app.post("/classify")
async def classify_fonts(req: ClassifyRequest):
    """Classify fonts using AI (Ollama)."""
    from core.ai_classifier import AIClassifier
    from models.font_entry import FontEntry
    from pathlib import Path

    classifier = AIClassifier()
    fonts = [
        FontEntry(
            path=Path(f["path"]),
            filename=f["filename"],
            extension=f["extension"],
            file_size=f["file_size"],
            family_name=f.get("family_name", ""),
            style_name=f.get("style_name", ""),
            weight_class=f.get("weight_class", 400),
            glyph_count=f.get("glyph_count", 0),
        )
        for f in req.font_entries
    ]

    results = classifier.classify_batch(
        fonts,
        progress_callback=lambda done, total: asyncio.create_task(broadcast_progress({
            "type": "ai_progress",
            "done": done,
            "total": total,
            "percentage": round((done / total) * 100, 1),
        })),
    )
    return {"classifications": results}


@app.get("/report")
async def generate_report():
    """Generate scan/organization report."""
    from core.reporter import ReportGenerator

    reporter = ReportGenerator(app.state.db)
    return reporter.generate()


@app.post("/undo")
async def undo_last_operation():
    """Undo the last file operation."""
    from database.operations import OperationsLog

    if app.state.db:
        ops = OperationsLog(app.state.db)
        return ops.undo_last()
    return {"success": False, "message": "Database not initialized"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8765, reload=True)
