"""
Recursive font scanner — finds and extracts metadata from font files.
Supports scan result caching for fast re-scans.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Callable, Optional

from fontTools import ttLib

from models.font_entry import FontEntry
from utils.hash_utils import compute_sha256, compute_quick_hash
from utils.weight_mapper import weight_class_to_name

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2", ".ttc"}


class FontScanner:
    """Scans directories for font files and extracts metadata."""

    def __init__(
        self,
        progress_callback: Callable | None = None,
        scan_cache=None,  # ScanCache instance (optional)
    ):
        self.progress_callback = progress_callback
        self.scan_cache = scan_cache

    def scan(self, folder_path: str | Path, recursive: bool = True) -> list[FontEntry]:
        """
        Scan a folder for font files and extract metadata.

        Args:
            folder_path: Root folder to scan.
            recursive: Whether to scan subfolders.

        Returns:
            List of FontEntry objects for valid font files.
        """
        folder = Path(folder_path)
        if not folder.is_dir():
            raise ValueError(f"Folder does not exist: {folder}")

        pattern = "**/*" if recursive else "*"
        font_entries: list[FontEntry] = []
        total_files = 0
        cache_hits = 0
        cache_misses = 0

        for file_path in folder.glob(pattern):
            if not file_path.is_file():
                continue

            total_files += 1

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            # Try cache first
            if self.scan_cache:
                cached = self.scan_cache.get_cached(file_path)
                if cached:
                    font_entries.append(cached)
                    cache_hits += 1
                    if self.progress_callback:
                        self.progress_callback(total_files, len(font_entries))
                    continue

            # Scan the file
            cache_misses += 1
            entry = self._extract_metadata(file_path)
            if entry:
                font_entries.append(entry)
                if self.scan_cache and entry.is_valid:
                    self.scan_cache.put(entry)

            if self.progress_callback:
                self.progress_callback(total_files, len(font_entries))

        if self.scan_cache:
            logger.info(
                f"Scan complete: {len(font_entries)} fonts "
                f"({cache_hits} cache hits, {cache_misses} new) "
                f"in {total_files} files"
            )
        else:
            logger.info(
                f"Scan complete: found {len(font_entries)} fonts in {total_files} files"
            )
        return font_entries

    def _extract_metadata(self, file_path: Path) -> FontEntry | None:
        """Extract metadata from a single font file."""
        try:
            font = ttLib.TTFont(str(file_path))
        except Exception as e:
            logger.warning(f"Could not parse {file_path.name}: {e}")
            entry = FontEntry(
                path=file_path,
                filename=file_path.name,
                extension=file_path.suffix,
                file_size=file_path.stat().st_size,
                is_valid=False,
                validation_error=str(e),
            )
            entry.quick_hash = compute_quick_hash(file_path)
            return entry

        try:
            entry = FontEntry(
                path=file_path,
                filename=file_path.name,
                extension=file_path.suffix,
                file_size=file_path.stat().st_size,
                family_name=self._get_name(font, 1),
                style_name=self._get_name(font, 2),
                full_name=self._get_name(font, 4),
                weight_class=self._get_weight_class(font),
                version=self._get_name(font, 5),
                glyph_count=self._get_glyph_count(font),
                quick_hash=compute_quick_hash(file_path),
                sha256_hash=compute_sha256(file_path),
                is_valid=True,
            )
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path.name}: {e}")
            entry = FontEntry(
                path=file_path,
                filename=file_path.name,
                extension=file_path.suffix,
                file_size=file_path.stat().st_size,
                is_valid=False,
                validation_error=str(e),
            )
        finally:
            font.close()

        return entry

    @staticmethod
    def _get_name(font: ttLib.TTFont, name_id: int) -> str:
        """Extract a name record from the font's name table."""
        for record in font["name"].names:
            if record.nameID == name_id:
                try:
                    if record.isUnicode():
                        return record.toUnicode()
                    return record.string.decode("utf-8", errors="replace")
                except Exception:
                    pass
        return ""

    @staticmethod
    def _get_weight_class(font: ttLib.TTFont) -> int:
        """Get the OS/2 weight class."""
        try:
            return font["OS/2"].usWeightClass
        except Exception:
            return 400  # Default: Regular

    @staticmethod
    def _get_glyph_count(font: ttLib.TTFont) -> int:
        """Get the number of glyphs in the font."""
        try:
            return font["maxp"].numGlyphs
        except Exception:
            return 0
