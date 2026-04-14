"""
Scan result models.
"""

from dataclasses import dataclass, field
from pathlib import Path

from models.font_entry import FontEntry


@dataclass
class ScanResult:
    """Result of a folder scan."""

    folder_path: Path
    total_files_found: int
    valid_fonts: list[FontEntry] = field(default_factory=list)
    unsupported_files: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    @property
    def total_fonts(self) -> int:
        return len(self.valid_fonts)

    def to_dict(self) -> dict:
        return {
            "folder_path": str(self.folder_path),
            "total_files_found": self.total_files_found,
            "total_fonts": self.total_fonts,
            "valid_fonts": [f.to_dict() for f in self.valid_fonts],
            "unsupported_files": self.unsupported_files,
            "errors": self.errors,
        }
