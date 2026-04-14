from __future__ import annotations

"""
Font organizer — groups fonts into family folders.
"""

import logging
import re
import shutil
from pathlib import Path

from models.font_entry import FontEntry
from core.renamer import FontRenamer

logger = logging.getLogger(__name__)

# Minimum styles for a "complete" family
COMPLETE_FAMILY_MIN = {"Regular", "Bold", "Italic", "Bold Italic", "BoldItalic"}


class FontOrganizer:
    """Organizes fonts into family-based directory structure."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.renamer = FontRenamer()

    def organize(
        self,
        font_entries: list[FontEntry],
        output_dir: str | Path,
    ) -> dict:
        """
        Organize fonts into complete/incomplete family directories.

        Structure:
            output_dir/
            ├── complete_families/
            │   ├── Roboto/
            │   │   ├── Roboto-Regular.ttf
            │   │   └── ...
            │   └── OpenSans/
            └── incomplete_families/
                ├── CustomFont/
                └── ...

        Returns:
            Summary dict with counts and details.
        """
        output = Path(output_dir)
        complete_dir = output / "complete_families"
        incomplete_dir = output / "incomplete_families"

        # Group by family name
        families: dict[str, list[FontEntry]] = {}
        for entry in font_entries:
            family = entry.suggested_family or entry.family_name or "Unknown"
            families.setdefault(family, []).append(entry)

        result = {
            "complete_families": [],
            "incomplete_families": [],
            "orphans": [],
            "moved": 0,
            "skipped": 0,
        }

        for family, fonts in families.items():
            styles = {f.style_name.lower() for f in fonts}

            # Determine if family is complete
            is_complete = self._is_complete_family(styles)

            target_base = complete_dir if is_complete else incomplete_dir
            family_dir = target_base / self._safe_folder_name(family)

            for font in fonts:
                try:
                    new_path = self.renamer.rename(font, family_dir)
                    if not self.dry_run:
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(font.path), str(new_path))
                    result["moved"] += 1
                except Exception as e:
                    logger.error(f"Failed to organize {font.filename}: {e}")
                    result["skipped"] += 1

            group_info = {
                "family": family,
                "is_complete": is_complete,
                "styles_found": sorted(styles),
                "count": len(fonts),
            }

            if is_complete:
                result["complete_families"].append(group_info)
            else:
                missing = COMPLETE_FAMILY_MIN - styles
                group_info["missing_styles"] = sorted(missing)
                result["incomplete_families"].append(group_info)

        logger.info(
            f"Organized: {result['complete_families'].__len__()} complete, "
            f"{result['incomplete_families'].__len__()} incomplete, "
            f"{result['moved']} moved"
        )
        return result

    def _is_complete_family(self, styles: set[str]) -> bool:
        """Check if a family has the minimum required styles."""
        normalized = {self._normalize_style(s) for s in styles}
        return COMPLETE_FAMILY_MIN.issubset(normalized)

    @staticmethod
    def _normalize_style(style: str) -> str:
        """Normalize style names (Bold → Bold, Regular → Regular, etc.)."""
        s = style.lower().replace(" ", "").replace("-", "")
        style_map = {
            "regular": "Regular",
            "bold": "Bold",
            "italic": "Italic",
            "bolditalic": "BoldItalic",
        }
        return style_map.get(s, style)

    @staticmethod
    def _safe_folder_name(name: str) -> str:
        """Create a safe folder name from a family name."""
        import re

        safe = re.sub(r'[<>:"/\\|?*]', "", name)
        return safe.strip() or "Unknown"
