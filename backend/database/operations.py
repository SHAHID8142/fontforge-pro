from __future__ import annotations

"""
Database CRUD operations for font records.
"""

import logging
from typing import Optional

from models.font_entry import FontEntry

logger = logging.getLogger(__name__)


class FontRepository:
    """CRUD operations for font records in SQLite."""

    def __init__(self, db):
        self.db = db

    def insert(self, entry: FontEntry) -> int:
        """Insert a font entry. Returns the font ID."""
        cursor = self.db.execute(
            """
            INSERT INTO fonts (
                path, filename, extension, file_size,
                family_name, style_name, full_name, weight_class,
                version, glyph_count, sha256_hash, quick_hash,
                is_valid, validation_error,
                suggested_family, suggested_style, category, ai_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(entry.path),
                entry.filename,
                entry.extension,
                entry.file_size,
                entry.family_name,
                entry.style_name,
                entry.full_name,
                entry.weight_class,
                entry.version,
                entry.glyph_count,
                entry.sha256_hash,
                entry.quick_hash,
                int(entry.is_valid),
                entry.validation_error,
                entry.suggested_family,
                entry.suggested_style,
                entry.category,
                entry.ai_confidence,
            ),
        )
        self.db.commit()
        return cursor.lastrowid

    def insert_many(self, entries: list[FontEntry]) -> int:
        """Insert multiple font entries. Returns count inserted."""
        data = [
            (
                str(e.path), e.filename, e.extension, e.file_size,
                e.family_name, e.style_name, e.full_name, e.weight_class,
                e.version, e.glyph_count, e.sha256_hash, e.quick_hash,
                int(e.is_valid), e.validation_error,
                e.suggested_family, e.suggested_style, e.category, e.ai_confidence,
            )
            for e in entries
        ]
        cursor = self.db.executemany(
            """
            INSERT OR IGNORE INTO fonts (
                path, filename, extension, file_size,
                family_name, style_name, full_name, weight_class,
                version, glyph_count, sha256_hash, quick_hash,
                is_valid, validation_error,
                suggested_family, suggested_style, category, ai_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )
        self.db.commit()
        return cursor.rowcount

    def get_by_path(self, path: str) -> FontEntry | None:
        """Get a font entry by its file path."""
        row = self.db.execute(
            "SELECT * FROM fonts WHERE path = ?", (path,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_entry(dict(row))

    def get_all(self) -> list[FontEntry]:
        """Get all font entries."""
        rows = self.db.execute("SELECT * FROM fonts ORDER BY family_name").fetchall()
        return [self._row_to_entry(dict(r)) for r in rows]

    def get_invalid(self) -> list[FontEntry]:
        """Get all invalid/corrupted font entries."""
        rows = self.db.execute(
            "SELECT * FROM fonts WHERE is_valid = 0"
        ).fetchall()
        return [self._row_to_entry(dict(r)) for r in rows]

    def update(self, entry_id: int, **kwargs):
        """Update fields of a font entry."""
        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [entry_id]
        self.db.execute(
            f"UPDATE fonts SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values),
        )
        self.db.commit()

    def delete(self, entry_id: int):
        """Delete a font entry (note: does NOT delete the file)."""
        self.db.execute("DELETE FROM fonts WHERE id = ?", (entry_id,))
        self.db.commit()

    @staticmethod
    def _row_to_entry(row: dict) -> FontEntry:
        """Convert a database row to a FontEntry."""
        from pathlib import Path

        return FontEntry(
            path=Path(row["path"]),
            filename=row["filename"],
            extension=row["extension"],
            file_size=row["file_size"],
            family_name=row["family_name"],
            style_name=row["style_name"],
            full_name=row["full_name"],
            weight_class=row["weight_class"],
            version=row["version"],
            glyph_count=row["glyph_count"],
            sha256_hash=row["sha256_hash"],
            quick_hash=row["quick_hash"],
            is_valid=bool(row["is_valid"]),
            validation_error=row["validation_error"],
            suggested_family=row["suggested_family"],
            suggested_style=row["suggested_style"],
            category=row["category"],
            ai_confidence=row["ai_confidence"],
        )


class OperationsLog:
    """Manages the undo/redo operation log."""

    def __init__(self, db):
        self.db = db

    def log(self, operation: str, source_path: str, target_path: str, undoable: bool = True):
        """Log a file operation."""
        self.db.execute(
            """
            INSERT INTO operations_log (operation, source_path, target_path, undoable)
            VALUES (?, ?, ?, ?)
            """,
            (operation, source_path, target_path, int(undoable)),
        )
        self.db.commit()

    def undo_last(self) -> dict:
        """Undo the last logged operation."""
        row = self.db.execute(
            "SELECT * FROM operations_log WHERE undoable = 1 ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()

        if row is None:
            return {"success": False, "message": "No operations to undo"}

        import shutil

        try:
            # Move file back to original location
            shutil.move(row["target_path"], row["source_path"])
            # Remove the log entry
            self.db.execute("DELETE FROM operations_log WHERE id = ?", (row["id"],))
            self.db.commit()
            return {"success": True, "message": f"Undid: {row['operation']}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_all(self) -> list[dict]:
        """Get all logged operations."""
        rows = self.db.execute(
            "SELECT * FROM operations_log ORDER BY timestamp DESC"
        ).fetchall()
        return [dict(r) for r in rows]
