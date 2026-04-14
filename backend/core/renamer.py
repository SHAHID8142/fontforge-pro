"""
Smart renaming engine — renames font files based on internal metadata.
"""

import logging
import re
from pathlib import Path

from models.font_entry import FontEntry

logger = logging.getLogger(__name__)


class FontRenamer:
    """Renames font files to match internal metadata: {Family}-{Style}.{ext}"""

    # Characters to remove from filenames
    INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    # Normalize whitespace and common abbreviations
    STYLE_ABBREVS = {
        "reg": "Regular",
        "bld": "Bold",
        "it": "Italic",
        "itl": "Italic",
        "bdit": "BoldItalic",
        "bdi": "BoldItalic",
        "med": "Medium",
        "sb": "SemiBold",
        "semibold": "SemiBold",
        "eb": "ExtraBold",
        "extrabold": "ExtraBold",
        "blk": "Black",
        "black": "Black",
        "thn": "Thin",
        "lt": "Light",
        "light": "Light",
    }

    def generate_new_name(self, entry: FontEntry) -> str:
        """Generate a safe, normalized filename from font metadata."""
        family = entry.suggested_family or entry.family_name or "Unknown"
        style = entry.suggested_style or entry.style_name or "Regular"

        # Expand common abbreviations
        style_lower = style.lower().strip()
        if style_lower in self.STYLE_ABBREVS:
            style = self.STYLE_ABBREVS[style_lower]

        # Clean invalid characters
        family = self.INVALID_CHARS.sub("", family).strip()
        style = self.INVALID_CHARS.sub("", style).strip()

        # Normalize spaces to hyphens
        family = re.sub(r"\s+", "-", family)
        style = re.sub(r"\s+", "-", style)

        return f"{family}-{style}{entry.extension}"

    def resolve_conflicts(self, target_path: Path) -> Path:
        """If target exists, append _1, _2, etc."""
        if not target_path.exists():
            return target_path

        counter = 1
        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent

        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    def rename(self, entry: FontEntry, output_dir: Path) -> Path:
        """
        Rename and move a font file to the output directory.

        Returns:
            The new file path.
        """
        new_name = self.generate_new_name(entry)
        target = output_dir / new_name
        target = self.resolve_conflicts(target)

        logger.info(f"Rename: {entry.path.name} → {target.name}")
        return target
