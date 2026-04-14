from __future__ import annotations

"""
SQLite database connection manager.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connection."""

    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "fontforge.db"
        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection | None = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Database connected: {self.db_path}")

    def _create_tables(self):
        """Create required tables if they don't exist."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fonts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                extension TEXT NOT NULL,
                file_size INTEGER,
                family_name TEXT DEFAULT '',
                style_name TEXT DEFAULT '',
                full_name TEXT DEFAULT '',
                weight_class INTEGER DEFAULT 400,
                version TEXT DEFAULT '',
                glyph_count INTEGER DEFAULT 0,
                sha256_hash TEXT DEFAULT '',
                quick_hash TEXT DEFAULT '',
                is_valid INTEGER DEFAULT 1,
                validation_error TEXT DEFAULT '',
                suggested_family TEXT DEFAULT '',
                suggested_style TEXT DEFAULT '',
                category TEXT DEFAULT '',
                ai_confidence REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operations_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                source_path TEXT NOT NULL,
                target_path TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                undoable INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT NOT NULL,
                total_fonts INTEGER DEFAULT 0,
                corrupted INTEGER DEFAULT 0,
                duplicates INTEGER DEFAULT 0,
                scan_time TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()
        logger.info("Database tables created")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor."""
        assert self.conn is not None
        return self.conn.execute(query, params)

    def executemany(self, query: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """Execute many queries and return cursor."""
        assert self.conn is not None
        return self.conn.executemany(query, params_list)

    def commit(self):
        """Commit pending transactions."""
        assert self.conn is not None
        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
