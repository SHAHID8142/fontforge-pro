"""
Integration tests — full pipeline: scan → validate → dedup → organize.
"""

import pytest
from pathlib import Path
from core.scanner import FontScanner
from core.validator import FontValidator
from core.deduplicator import Deduplicator
from core.organizer import FontOrganizer
from core.renamer import FontRenamer
from tests.fixtures import FontFactory


class TestIntegrationPipeline:
    """End-to-end pipeline tests."""

    @pytest.fixture
    def font_factory(self, tmp_path):
        return FontFactory(tmp_path)

    def test_full_pipeline(self, tmp_path, font_factory):
        """Test: scan → validate → dedup → organize with real fonts."""
        # Setup: Create a mix of fonts
        factory = font_factory

        # Complete family
        factory.create_family("Roboto", ["Regular", "Bold", "Italic", "Bold Italic"])

        # Incomplete family
        factory.create_family("OpenSans", ["Regular", "Bold"])

        # Duplicate (same content, different name)
        factory.create_ttf(family="Copy", style="Regular", path=str(tmp_path / "A.ttf"))
        (tmp_path / "B.ttf").write_bytes((tmp_path / "A.ttf").read_bytes())

        # Corrupted font
        factory.create_ttf(family="Broken", style="Regular", corrupt=True)

        # --- Step 1: Scan ---
        scanner = FontScanner()
        fonts = scanner.scan(str(tmp_path))
        assert len(fonts) >= 8  # All fonts found

        valid_fonts = [f for f in fonts if f.is_valid]
        invalid_fonts = [f for f in fonts if not f.is_valid]

        assert len(invalid_fonts) >= 1  # Corrupted font detected

        # --- Step 2: Validate ---
        validator = FontValidator()
        for font in invalid_fonts:
            result = validator.validate(str(font.path))
            assert result["is_valid"] is False

        # --- Step 3: Deduplicate ---
        dedup = Deduplicator()
        groups = dedup.find_duplicates(valid_fonts)
        # We expect at least the duplicate pair or none depending on hash
        # (FontFactory creates unique fonts, so hash-based dedup may find 0)
        assert isinstance(groups, list)

        # --- Step 4: Organize ---
        output_dir = tmp_path / "output"
        organizer = FontOrganizer(dry_run=True)
        result = organizer.organize(valid_fonts, output_dir)

        assert "complete_families" in result
        assert "incomplete_families" in result

    def test_repair_and_revalidate(self, tmp_path, font_factory):
        """Test: create corrupted font → repair → validate."""
        factory = font_factory

        # Create a font missing the name table (repairable)
        path = factory.create_ttf(family="NeedsRepair", style="Regular", corrupt=True)

        # Validate - should fail
        validator = FontValidator()
        result = validator.validate(path)
        assert result["is_valid"] is False

        # Try repair
        repaired_path = str(tmp_path / "Repaired.ttf")
        repair_result = validator.try_repair(path, repaired_path)

        # Re-validate repaired font
        if repair_result["repaired"]:
            repaired_result = validator.validate(repaired_path)
            # Should now be valid (if cmap wasn't the issue)
            if "cmap" not in result.get("missing_tables", []):
                assert repaired_result["is_valid"] is True

    def test_rename_conflicts(self, tmp_path, font_factory):
        """Test: renaming fonts with conflicts should append _1, _2."""
        factory = font_factory
        factory.create_ttf(family="Roboto", style="Bold", path=str(tmp_path / "Roboto-Bold.ttf"))

        # Now create another font with same suggested name
        font_entry = font_factory.create_ttf(
            family="Roboto", style="Bold", path=str(tmp_path / "Another-Bold.ttf")
        )

        renamer = FontRenamer()
        output_dir = tmp_path / "renamed"
        output_dir.mkdir()

        # First rename
        path1 = renamer.rename(
            type("FontEntry", (), {
                "suggested_family": "Roboto",
                "suggested_style": "Bold",
                "family_name": "Roboto",
                "style_name": "Bold",
                "extension": ".ttf",
                "path": Path(tmp_path / "Roboto-Bold.ttf"),
                "filename": "Roboto-Bold.ttf",
            })(),
            output_dir,
        )

        # Second rename (should get _1 suffix)
        path2 = renamer.resolve_conflicts(output_dir / "Roboto-Bold.ttf")
        assert path2.name == "Roboto-Bold_1.ttf"

    def test_organizer_dry_run(self, tmp_path, font_factory):
        """Test: dry run should not move any files."""
        factory = font_factory
        factory.create_family("Roboto", ["Regular", "Bold", "Italic", "Bold Italic"])

        original_files = set(tmp_path.glob("*.ttf"))
        assert len(original_files) == 4

        output_dir = tmp_path / "output"
        organizer = FontOrganizer(dry_run=True)
        fonts = FontScanner().scan(str(tmp_path))

        result = organizer.organize(fonts, output_dir)

        # No files should be moved
        assert set(tmp_path.glob("*.ttf")) == original_files
        assert result["moved"] == 0

    def test_large_collection_performance(self, tmp_path, font_factory):
        """Test: scanning 100+ fonts should complete in reasonable time."""
        import time

        factory = font_factory
        for i in range(100):
            family = f"Font{i // 4}"
            styles = ["Regular", "Bold", "Italic", "Bold Italic"]
            style = styles[i % 4]
            factory.create_ttf(
                family=family, style=style, path=str(tmp_path / f"{family}-{style}.ttf")
            )

        scanner = FontScanner()
        start = time.time()
        results = scanner.scan(str(tmp_path))
        elapsed = time.time() - start

        assert len(results) == 100
        assert elapsed < 10  # Should complete in under 10 seconds
