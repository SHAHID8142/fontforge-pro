from __future__ import annotations

"""
Report generator — generates JSON, CSV, and HTML reports.
"""

import csv
import json
import logging
from io import StringIO
from pathlib import Path
from typing import Optional

from models.report import Report

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates scan/organization reports."""

    def __init__(self, db_manager=None):
        self.db = db_manager
        self.report = Report()

    def generate(self, data: dict | None = None) -> dict:
        """Generate and return report as dict."""
        if data:
            self._update_from_data(data)
        return self.report.to_dict()

    def export_json(self, output_path: str | Path) -> Path:
        """Export report as JSON."""
        path = Path(output_path)
        with open(path, "w") as f:
            json.dump(self.report.to_dict(), f, indent=2)
        logger.info(f"JSON report exported to {path}")
        return path

    def export_csv(self, output_path: str | Path) -> Path:
        """Export report as CSV."""
        path = Path(output_path)
        report = self.report.to_dict()

        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            for section, metrics in report.items():
                writer.writerow([section, ""])
                for key, value in metrics.items():
                    if isinstance(value, dict):
                        for k, v in value.items():
                            writer.writerow([f"{key}.{k}", v])
                    else:
                        writer.writerow([key, value])

        logger.info(f"CSV report exported to {path}")
        return path

    def export_html(self, output_path: str | Path) -> Path:
        """Export report as HTML."""
        path = Path(output_path)
        report = self.report.to_dict()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>FontForge Pro Report</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
        h1 {{ color: #333; }}
        .section {{ margin: 1.5rem 0; padding: 1rem; background: #f5f5f5; border-radius: 8px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #eee; }}
        .metric:last-child {{ border-bottom: none; }}
        .value {{ font-weight: bold; color: #2563eb; }}
        .warning {{ color: #dc2626; }}
    </style>
</head>
<body>
    <h1>FontForge Pro Report</h1>
"""

        for section, metrics in report.items():
            html += f'<div class="section"><h2>{section.replace("_", " ").title()}</h2>'
            for key, value in metrics.items():
                label = key.replace("_", " ").title()
                css_class = 'class="warning"' if isinstance(value, int) and value > 0 else ""
                html += f'<div class="metric"><span>{label}</span> <span {css_class}>{value}</span></div>'
            html += "</div>"

        html += """</body>
</html>"""

        with open(path, "w") as f:
            f.write(html)

        logger.info(f"HTML report exported to {path}")
        return path

    def _update_from_data(self, data: dict):
        """Update report from scan/organization data."""
        if "total_fonts" in data:
            self.report.scan_summary.total_fonts = data["total_fonts"]
        if "formats" in data:
            self.report.scan_summary.formats = data["formats"]
        if "corrupted" in data:
            self.report.issues_found.corrupted = data["corrupted"]
        if "duplicates" in data:
            self.report.issues_found.duplicates = data["duplicates"]
