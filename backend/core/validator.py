from __future__ import annotations

"""
Font validator — detects corrupted or broken font files.
Supports basic auto-repair for minor issues.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

from fontTools import ttLib

logger = logging.getLogger(__name__)

# Critical tables that every font must have
CRITICAL_TABLES = {"head", "hhea", "maxp", "cmap"}


class FontValidator:
    """Validates font files for structural integrity."""

    def validate(self, font_path: str) -> dict:
        """
        Validate a single font file.

        Returns:
            dict with keys: path, is_valid, error, missing_tables
        """
        result = {
            "path": str(font_path),
            "is_valid": True,
            "error": "",
            "missing_tables": [],
            "recoverable": False,
        }

        try:
            font = ttLib.TTFont(str(font_path))

            # Check for critical tables
            missing = CRITICAL_TABLES - set(font.keys())
            if missing:
                result["is_valid"] = False
                result["missing_tables"] = list(missing)
                result["error"] = f"Missing critical tables: {', '.join(missing)}"
                # Can recover if only name table is missing
                result["recoverable"] = missing == {"name"}

            font.close()

        except ttLib.TTLibError as e:
            result["is_valid"] = False
            result["error"] = f"TTLibError: {e}"
            result["recoverable"] = False
        except Exception as e:
            result["is_valid"] = False
            result["error"] = str(e)
            result["recoverable"] = False

        return result

    def validate_batch(self, font_paths: list[str]) -> list[dict]:
        """Validate multiple font files."""
        results = []
        for path in font_paths:
            results.append(self.validate(path))
        return results

    def try_repair(self, font_path: str, output_path: str | None = None) -> dict:
        """
        Attempt basic repair on a font file.

        Repairs:
        - Rebuilds missing name table with minimal records
        - Fixes missing post table defaults

        Args:
            font_path: Path to the broken font.
            output_path: Where to save repaired font (None = overwrite original).

        Returns:
            dict with repair status and details.
        """
        result = {
            "path": font_path,
            "repaired": False,
            "output": output_path or font_path,
            "actions": [],
            "error": "",
        }

        try:
            font = ttLib.TTFont(str(font_path))
            repaired = False

            # Rebuild missing name table
            if "name" not in font:
                name_table = font.newTable("name")
                name_table.names = []

                # Extract filename as family name (best guess)
                filename = Path(font_path).stem
                # Remove common suffixes
                for suffix in ["-Regular", "-Bold", "-Italic", "Regular", "Bold"]:
                    if filename.endswith(suffix):
                        filename = filename[: -len(suffix)].strip("-")
                        break

                def add_name(name_id: int, string: str):
                    from fontTools.ttLib.tables._n_a_m_e import NameRecord
                    record = NameRecord()
                    record.nameID = name_id
                    record.platformID = 3
                    record.platEncID = 1
                    record.langID = 0x409
                    record.string = string.encode("utf-16-be")
                    name_table.names.append(record)

                add_name(1, filename)
                add_name(2, "Regular")
                add_name(4, f"{filename} Regular")

                font["name"] = name_table
                result["actions"].append("Rebuilt name table")
                repaired = True

            # Fix missing post table
            if "post" not in font:
                post = font.newTable("post")
                post.formatType = 3.0  # Minimal format
                post.underlinePosition = -75
                post.underlineThickness = 50
                post.isFixedPitch = 0
                font["post"] = post
                result["actions"].append("Added post table")
                repaired = True

            if repaired:
                target = output_path or font_path
                font.save(target)
                result["repaired"] = True
                logger.info(f"Repaired: {font_path} -> {target}")
            else:
                result["error"] = "No repairs needed or font cannot be repaired"

            font.close()

        except Exception as e:
            result["error"] = f"Repair failed: {e}"
            logger.error(f"Repair failed for {font_path}: {e}")

        return result
