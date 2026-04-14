"""
Tests for the deduplicator module.
"""

from pathlib import Path
from core.deduplicator import Deduplicator
from models.font_entry import FontEntry


class TestDeduplicator:
    """Tests for Deduplicator."""

    def test_no_duplicates(self):
        """Fonts with different hashes should have no duplicates."""
        dedup = Deduplicator()
        fonts = [
            FontEntry(
                path=Path("/fonts/A.ttf"), filename="A.ttf", extension=".ttf",
                file_size=100, sha256_hash="hash1", family_name="FontA",
                style_name="Regular", weight_class=400,
            ),
            FontEntry(
                path=Path("/fonts/B.ttf"), filename="B.ttf", extension=".ttf",
                file_size=100, sha256_hash="hash2", family_name="FontB",
                style_name="Regular", weight_class=400,
            ),
        ]
        groups = dedup.find_duplicates(fonts)
        assert len(groups) == 0

    def test_exact_hash_duplicate(self):
        """Fonts with same hash should be detected as duplicates."""
        dedup = Deduplicator()
        fonts = [
            FontEntry(
                path=Path("/fonts/A.ttf"), filename="A.ttf", extension=".ttf",
                file_size=100, sha256_hash="same_hash", family_name="FontA",
                style_name="Regular", weight_class=400,
            ),
            FontEntry(
                path=Path("/fonts/B.ttf"), filename="B.ttf", extension=".ttf",
                file_size=100, sha256_hash="same_hash", family_name="FontA",
                style_name="Regular", weight_class=400,
            ),
        ]
        groups = dedup.find_duplicates(fonts)
        assert len(groups) == 1
        assert groups[0]["type"] == "exact_hash"
        assert groups[0]["confidence"] == 1.0
