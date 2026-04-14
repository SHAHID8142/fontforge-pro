"""
Tests for the font validator module.
"""

import pytest
from core.validator import FontValidator


class TestFontValidator:
    """Tests for FontValidator."""

    def test_validate_nonexistent_file(self):
        """Validating a nonexistent file should return invalid."""
        validator = FontValidator()
        result = validator.validate("/nonexistent/font.ttf")
        assert result["is_valid"] is False

    def test_validate_empty_file(self, tmp_path):
        """Validating an empty file should return invalid."""
        empty = tmp_path / "empty.ttf"
        empty.touch()
        validator = FontValidator()
        result = validator.validate(str(empty))
        assert result["is_valid"] is False

    def test_validate_batch(self):
        """Batch validation should return results for all files."""
        validator = FontValidator()
        results = validator.validate_batch(["/fake1.ttf", "/fake2.otf"])
        assert len(results) == 2
        assert all(not r["is_valid"] for r in results)
