from __future__ import annotations

"""
Scan result caching — skips unchanged files on re-scan.
"""

import logging
import time
from pathlib import Path
from typing import Optional

from database.db import DatabaseManager
from database.operations import FontRepository
from models.font_entry import FontEntry

logger = logging.getLogger(__name__)


class ScanCache:
    """
    Caches scan results in SQLite to avoid re-processing unchanged files.

    Strategy:
    - Store file path + mtime + quick_hash
    - On re-scan, compare mtime and quick_hash
    - If unchanged, reuse cached FontEntry
    - If changed, re-scan and update cache
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.repo = FontRepository(db)
        self._ensure_cache_table()

    def _ensure_cache_table(self):
        """Create cache metadata table if not exists."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS scan_cache (
                path TEXT PRIMARY KEY,
                mtime REAL NOT NULL,
                quick_hash TEXT NOT NULL,
                font_data TEXT,
                last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    def get_cached(self, file_path: Path) -> FontEntry | None:
        """
        Get cached font entry if file hasn't changed.

        Returns:
            Cached FontEntry or None if file changed or not cached.
        """
        try:
            stat = file_path.stat()
            current_mtime = stat.st_mtime
        except OSError:
            return None

        row = self.db.execute(
            "SELECT mtime, quick_hash FROM scan_cache WHERE path = ?",
            (str(file_path),),
        ).fetchone()

        if row is None:
            return None  # Not cached

        # Check if file changed
        if row["mtime"] != current_mtime:
            return None  # File modified

        # Return cached entry — need full data from fonts table
        cached_entry = self.repo.get_by_path(str(file_path))
        if cached_entry:
            logger.debug(f"Cache hit: {file_path.name}")
            return cached_entry

        return None

    def put(self, entry: FontEntry):
        """Cache a font entry."""
        try:
            mtime = entry.path.stat().st_mtime
        except OSError:
            mtime = time.time()

        # Upsert into cache
        self.db.execute(
            """
            INSERT INTO scan_cache (path, mtime, quick_hash, last_scanned)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(path) DO UPDATE SET
                mtime = excluded.mtime,
                quick_hash = excluded.quick_hash,
                last_scanned = CURRENT_TIMESTAMP
            """,
            (str(entry.path), mtime, entry.quick_hash),
        )
        self.db.commit()
        logger.debug(f"Cache put: {entry.filename}")

    def put_many(self, entries: list[FontEntry]):
        """Cache multiple font entries."""
        for entry in entries:
            self.put(entry)
        logger.info(f"Cached {len(entries)} font entries")

    def invalidate(self, file_path: Path):
        """Remove a specific entry from cache."""
        self.db.execute(
            "DELETE FROM scan_cache WHERE path = ?",
            (str(file_path),),
        )
        self.db.commit()

    def invalidate_all(self):
        """Clear entire cache."""
        self.db.execute("DELETE FROM scan_cache")
        self.db.commit()
        logger.info("Scan cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.db.execute("SELECT COUNT(*) as cnt FROM scan_cache").fetchone()["cnt"]
        return {
            "total_cached": total,
        }
