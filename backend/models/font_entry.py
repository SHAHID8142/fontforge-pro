"""
FontEntry dataclass — holds all extracted font metadata.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FontEntry:
    """Represents a single font file with its metadata."""

    path: Path
    filename: str
    extension: str
    file_size: int  # bytes

    # Internal font metadata (from fontTools)
    family_name: str = ""
    style_name: str = ""
    full_name: str = ""
    weight_class: int = 400  # OS/2 usWeightClass
    version: str = ""
    glyph_count: int = 0

    # Computed fields
    sha256_hash: str = ""
    quick_hash: str = ""  # First 1MB hash for fast dedup

    # Validation
    is_valid: bool = True
    validation_error: str = ""

    # Organization
    suggested_family: str = ""
    suggested_style: str = ""
    category: str = ""  # serif, sans-serif, display, etc.
    ai_confidence: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON/API."""
        return {
            "path": str(self.path),
            "filename": self.filename,
            "extension": self.extension,
            "file_size": self.file_size,
            "family_name": self.family_name,
            "style_name": self.style_name,
            "full_name": self.full_name,
            "weight_class": self.weight_class,
            "version": self.version,
            "glyph_count": self.glyph_count,
            "sha256_hash": self.sha256_hash,
            "quick_hash": self.quick_hash,
            "is_valid": self.is_valid,
            "validation_error": self.validation_error,
            "suggested_family": self.suggested_family,
            "suggested_style": self.suggested_style,
            "category": self.category,
            "ai_confidence": self.ai_confidence,
        }

    def suggested_filename(self) -> str:
        """Generate suggested filename: {Family}-{Style}.{ext}."""
        family = self.suggested_family or self.family_name or "Unknown"
        style = self.suggested_style or self.style_name or "Regular"
        return f"{family}-{style}{self.extension}"
