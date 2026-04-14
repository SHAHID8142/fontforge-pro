from __future__ import annotations

"""
Duplicate detector — multi-tier duplicate identification.
"""

import logging
from collections import defaultdict

from models.font_entry import FontEntry

logger = logging.getLogger(__name__)


class Deduplicator:
    """Detects duplicate fonts using multiple strategies."""

    def find_duplicates(
        self, font_entries: list[FontEntry] | list[dict]
    ) -> list[dict]:
        """
        Find duplicate fonts using multi-tier detection.

        Tier 1: Exact hash match (SHA256) → 100% duplicate
        Tier 2: Same family + style + weight → Likely duplicate

        Returns:
            List of duplicate groups. Each group has a 'keep' entry and 'duplicates'.
        """
        if isinstance(font_entries[0], dict) if font_entries else False:
            # Convert dicts back to FontEntry if needed
            pass

        groups = []

        # Tier 1: Hash-based dedup
        hash_groups = self._dedup_by_hash(font_entries)
        groups.extend(hash_groups)

        # Tier 2: Metadata-based dedup (only for non-hash-duplicates)
        already_flagged = {
            f["path"] for g in groups for f in g.get("duplicates", [])
        }
        remaining = [f for f in font_entries if str(f.path) not in already_flagged]
        meta_groups = self._dedup_by_metadata(remaining)
        groups.extend(meta_groups)

        logger.info(f"Found {len(groups)} duplicate groups")
        return groups

    def _dedup_by_hash(
        self, font_entries: list[FontEntry]
    ) -> list[dict]:
        """Group fonts by SHA256 hash."""
        hash_map: dict[str, list[FontEntry]] = defaultdict(list)

        for entry in font_entries:
            if entry.sha256_hash:
                hash_map[entry.sha256_hash].append(entry)

        groups = []
        for hash_val, fonts in hash_map.items():
            if len(fonts) < 2:
                continue

            # Keep the one with the best path (shortest, most descriptive)
            keeper = min(fonts, key=lambda f: len(str(f.path)))
            duplicates = [f for f in fonts if f != keeper]

            groups.append({
                "type": "exact_hash",
                "confidence": 1.0,
                "keep": keeper.to_dict(),
                "duplicates": [d.to_dict() for d in duplicates],
            })

        return groups

    def _dedup_by_metadata(
        self, font_entries: list[FontEntry]
    ) -> list[dict]:
        """Group fonts by family + style + weight."""
        meta_map: dict[tuple, list[FontEntry]] = defaultdict(list)

        for entry in font_entries:
            key = (
                entry.family_name.lower(),
                entry.style_name.lower(),
                entry.weight_class,
            )
            meta_map[key].append(entry)

        groups = []
        for key, fonts in meta_map.items():
            if len(fonts) < 2:
                continue

            # Keep the newest version or highest glyph count
            keeper = max(fonts, key=lambda f: (f.version, f.glyph_count))
            duplicates = [f for f in fonts if f != keeper]

            groups.append({
                "type": "metadata",
                "confidence": 0.85,
                "keep": keeper.to_dict(),
                "duplicates": [d.to_dict() for d in duplicates],
            })

        return groups
