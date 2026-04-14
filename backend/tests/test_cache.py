"""
Tests for scan cache — caching, cache hits, invalidation.
"""

import pytest
from pathlib import Path
from database.db import DatabaseManager
from database.cache import ScanCache
from models.font_entry import FontEntry


class TestScanCache:
    """Tests for ScanCache."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a scan cache with temporary database."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(db_path)
        yield ScanCache(db)
        db.close()

    def test_put_and_get(self, cache, tmp_path):
        """Should cache and retrieve font entry."""
        font_file = tmp_path / "test.ttf"
        font_file.touch()

        import time
        entry = FontEntry(
            path=font_file,
            filename="test.ttf",
            extension=".ttf",
            file_size=100,
            family_name="TestFont",
            style_name="Regular",
            quick_hash="abc123",
        )
        cache.put(entry)

        # Small delay to ensure mtime is stable
        time.sleep(0.05)

        cached = cache.get_cached(font_file)
        assert cached is not None
        assert cached.family_name == "TestFont"

    def test_cache_miss_modified_file(self, cache, tmp_path):
        """Should return None if file was modified."""
        font_file = tmp_path / "test.ttf"
        font_file.touch()

        entry = FontEntry(
            path=font_file,
            filename="test.ttf",
            extension=".ttf",
            file_size=100,
            family_name="TestFont",
            style_name="Regular",
            quick_hash="abc123",
        )
        cache.put(entry)

        # Modify the file (changes mtime)
        import time
        time.sleep(0.1)
        font_file.write_text("modified")

        cached = cache.get_cached(font_file)
        assert cached is None

    def test_cache_miss_nonexistent_file(self, cache):
        """Should return None for nonexistent file."""
        cached = cache.get_cached(Path("/nonexistent/file.ttf"))
        assert cached is None

    def test_invalidate(self, cache, tmp_path):
        """Should remove entry from cache."""
        font_file = tmp_path / "test.ttf"
        font_file.touch()

        entry = FontEntry(
            path=font_file,
            filename="test.ttf",
            extension=".ttf",
            file_size=100,
            family_name="TestFont",
            style_name="Regular",
            quick_hash="abc123",
        )
        cache.put(entry)

        stats = cache.get_stats()
        assert stats["total_cached"] == 1

        cache.invalidate(font_file)
        stats = cache.get_stats()
        assert stats["total_cached"] == 0

    def test_invalidate_all(self, cache, tmp_path):
        """Should clear entire cache."""
        for i in range(5):
            font_file = tmp_path / f"font{i}.ttf"
            font_file.touch()
            cache.put(FontEntry(
                path=font_file,
                filename=f"font{i}.ttf",
                extension=".ttf",
                file_size=100,
                family_name=f"Font{i}",
                style_name="Regular",
                quick_hash=f"hash{i}",
            ))

        stats = cache.get_stats()
        assert stats["total_cached"] == 5

        cache.invalidate_all()
        stats = cache.get_stats()
        assert stats["total_cached"] == 0

    def test_put_many(self, cache, tmp_path):
        """Should cache multiple entries."""
        entries = []
        for i in range(10):
            font_file = tmp_path / f"font{i}.ttf"
            font_file.touch()
            entries.append(FontEntry(
                path=font_file,
                filename=f"font{i}.ttf",
                extension=".ttf",
                file_size=100,
                family_name=f"Font{i}",
                style_name="Regular",
                quick_hash=f"hash{i}",
            ))

        cache.put_many(entries)
        stats = cache.get_stats()
        assert stats["total_cached"] == 10
