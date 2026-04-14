"""
Report data models.
"""

from dataclasses import dataclass, field


@dataclass
class ScanSummary:
    total_fonts: int = 0
    formats: dict[str, int] = field(default_factory=dict)
    scan_time: str = ""


@dataclass
class IssuesFound:
    corrupted: int = 0
    duplicates: int = 0
    misnamed: int = 0
    incomplete_families: int = 0


@dataclass
class ActionsTaken:
    quarantined: int = 0
    duplicates_moved: int = 0
    renamed: int = 0
    organized: int = 0


@dataclass
class Report:
    scan_summary: ScanSummary = field(default_factory=ScanSummary)
    issues_found: IssuesFound = field(default_factory=IssuesFound)
    actions_taken: ActionsTaken = field(default_factory=ActionsTaken)

    def to_dict(self) -> dict:
        return {
            "scan_summary": {
                "total_fonts": self.scan_summary.total_fonts,
                "formats": self.scan_summary.formats,
                "scan_time": self.scan_summary.scan_time,
            },
            "issues_found": {
                "corrupted": self.issues_found.corrupted,
                "duplicates": self.issues_found.duplicates,
                "misnamed": self.issues_found.misnamed,
                "incomplete_families": self.issues_found.incomplete_families,
            },
            "actions_taken": {
                "quarantined": self.actions_taken.quarantined,
                "duplicates_moved": self.actions_taken.duplicates_moved,
                "renamed": self.actions_taken.renamed,
                "organized": self.actions_taken.organized,
            },
        }
