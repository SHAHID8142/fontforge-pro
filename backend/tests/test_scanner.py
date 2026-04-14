"""
Tests for the font scanner module.
"""

import pytest
from pathlib import Path
from core.scanner import FontScanner
from models.font_entry import FontEntry


class TestFontScanner:
    """Tests for FontScanner."""

    def test_scan_nonexistent_folder(self):
        """Scanning a nonexistent folder should raise ValueError."""
        scanner = FontScanner()
        with pytest.raises(ValueError, match="Folder does not exist"):
            scanner.scan("/nonexistent/path/12345")

    def test_scan_empty_folder(self, tmp_path):
        """Scanning an empty folder should return empty list."""
        scanner = FontScanner()
        results = scanner.scan(str(tmp_path))
        assert results == []

    def test_scan_folder_with_non_font_files(self, tmp_path):
        """Non-font files should be ignored."""
        (tmp_path / "document.txt").write_text("hello")
        (tmp_path / "image.png").touch()
        (tmp_path / "data.json").write_text("{}")

        scanner = FontScanner()
        results = scanner.scan(str(tmp_path))
        assert results == []

    def test_scan_with_corrupted_font(self, tmp_path):
        """Corrupted font files should be detected with is_valid=False."""
        from tests.fixtures import FontFactory

        factory = FontFactory(tmp_path)
        path = factory.create_ttf()

        # Corrupt the file by overwriting with invalid bytes
        with open(path, "wb") as f:
            f.write(b"\x00" * 100)

        scanner = FontScanner()
        results = scanner.scan(str(tmp_path))
        assert len(results) == 1
        assert results[0].is_valid is False
        assert results[0].validation_error != ""

    def test_scan_valid_font(self, tmp_path):
        """Valid font should have is_valid=True and metadata."""
        from tests.fixtures import FontFactory

        factory = FontFactory(tmp_path)
        factory.create_ttf(family="Roboto", style="Bold", weight=700, version="1.000")

        scanner = FontScanner()
        results = scanner.scan(str(tmp_path))
        assert len(results) == 1
        font = results[0]
        assert font.is_valid is True
        assert font.family_name == "Roboto"
        assert font.style_name == "Bold"
        assert font.weight_class == 700
        assert font.sha256_hash != ""
        assert font.quick_hash != ""
        assert font.glyph_count >= 1

    def test_scan_recursive(self, tmp_path):
        """Should find fonts in subfolders."""
        from tests.fixtures import FontFactory

        sub = tmp_path / "subfolder" / "nested"
        sub.mkdir(parents=True)

        factory = FontFactory(tmp_path)
        factory.create_ttf(family="FontA", style="Regular", path=str(tmp_path / "A.ttf"))
        factory.create_ttf(family="FontB", style="Regular", path=str(sub / "B.ttf"))

        scanner = FontScanner()
        # Recursive (default)
        results = scanner.scan(str(tmp_path), recursive=True)
        assert len(results) == 2

        # Non-recursive
        results = scanner.scan(str(tmp_path), recursive=False)
        assert len(results) == 1

    def test_scan_multiple_styles(self, tmp_path):
        """Should extract multiple styles from same family."""
        from tests.fixtures import FontFactory

        factory = FontFactory(tmp_path)
        factory.create_family("Roboto", ["Regular", "Bold", "Italic", "Bold Italic"])

        scanner = FontScanner()
        results = scanner.scan(str(tmp_path))
        assert len(results) == 4

        styles = {r.style_name for r in results}
        assert "Regular" in styles
        assert "Bold" in styles
        assert "Italic" in styles
        assert "Bold Italic" in styles

    def test_scan_progress_callback(self, tmp_path):
        """Progress callback should be called for each file."""
        from tests.fixtures import FontFactory

        factory = FontFactory(tmp_path)
        for i in range(5):
            factory.create_ttf(family=f"Font{i}", style="Regular", path=str(tmp_path / f"Font{i}.ttf"))

        progress_calls = []
        scanner = FontScanner(progress_callback=lambda total, found: progress_calls.append((total, found)))
        scanner.scan(str(tmp_path))
        assert len(progress_calls) > 0

    def test_supported_extensions(self):
        """Verify supported extensions."""
        from core.scanner import SUPPORTED_EXTENSIONS
        assert ".ttf" in SUPPORTED_EXTENSIONS
        assert ".otf" in SUPPORTED_EXTENSIONS
        assert ".woff" in SUPPORTED_EXTENSIONS
        assert ".woff2" in SUPPORTED_EXTENSIONS
        assert ".ttc" in SUPPORTED_EXTENSIONS

    def test_font_entry_to_dict(self):
        """Test FontEntry serialization."""
        entry = FontEntry(
            path=Path("/test/Roboto-Bold.ttf"),
            filename="Roboto-Bold.ttf",
            extension=".ttf",
            file_size=12345,
            family_name="Roboto",
            style_name="Bold",
            weight_class=700,
        )
        d = entry.to_dict()
        assert d["family_name"] == "Roboto"
        assert d["style_name"] == "Bold"
        assert d["weight_class"] == 700
        assert d["filename"] == "Roboto-Bold.ttf"

    def test_font_entry_suggested_filename(self):
        """Test suggested filename generation."""
        entry = FontEntry(
            path=Path("/test/abc123.ttf"),
            filename="abc123.ttf",
            extension=".ttf",
            file_size=100,
            family_name="Roboto",
            style_name="Bold",
        )
        assert entry.suggested_filename() == "Roboto-Bold.ttf"

    def test_font_entry_suggested_filename_with_ai(self):
        """Suggested filename should use AI-corrected family/style if available."""
        entry = FontEntry(
            path=Path("/test/abc123.ttf"),
            filename="abc123.ttf",
            extension=".ttf",
            file_size=100,
            family_name="RobotoBd",
            style_name="Bd",
            suggested_family="Roboto",
            suggested_style="Bold",
        )
        assert entry.suggested_filename() == "Roboto-Bold.ttf"
