import { useState } from "react";
import FontTable from "../DataTable/FontTable";

interface Step5ReportProps {
  state: any;
}

export default function Step5Report({ state }: Step5ReportProps) {
  const [showTable, setShowTable] = useState(false);
  const fonts = state.fonts || [];
  const issues = state.issues || {};

  const report = {
    total_fonts: fonts.length,
    valid: fonts.filter((f: any) => f.is_valid).length,
    corrupted: issues.corrupted ?? fonts.filter((f: any) => !f.is_valid).length,
    duplicates: issues.duplicates ?? 0,
    misnamed: issues.misnamed ?? 0,
    incomplete_families: issues.incomplete_families ?? 0,
    complete_families: issues.complete_families ?? 0,
  };

  const formats = fonts.reduce((acc: Record<string, number>, f: any) => {
    acc[f.extension] = (acc[f.extension] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Report & Export</h2>
        <p className="mt-2 text-dark-300">
          Scan complete. Your font library has been analyzed.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard label="Total Fonts" value={report.total_fonts} color="text-white" />
        <SummaryCard label="Valid" value={report.valid} color="text-green-400" />
        <SummaryCard label="Corrupted" value={report.corrupted} color="text-red-400" />
        <SummaryCard label="Duplicates" value={report.duplicates} color="text-yellow-400" />
        <SummaryCard label="Misnamed" value={report.misnamed} color="text-blue-400" />
        <SummaryCard label="Complete Families" value={report.complete_families} color="text-emerald-400" />
        <SummaryCard label="Incomplete Families" value={report.incomplete_families} color="text-orange-400" />
        <SummaryCard
          label="Formats"
          value={Object.keys(formats).length}
          color="text-purple-400"
          sub={Object.entries(formats)
            .map(([ext, count]) => `${ext}: ${count}`)
            .join(", ")}
        />
      </div>

      {/* Format Distribution */}
      {Object.keys(formats).length > 0 && (
        <div className="card">
          <h3 className="text-sm font-medium text-dark-200 mb-3">Format Distribution</h3>
          <div className="space-y-2">
            {Object.entries(formats)
              .sort((a, b) => (b[1] as number) - (a[1] as number))
              .map(([ext, count]) => (
                <div key={ext} className="flex items-center gap-3">
                  <span className="text-sm text-dark-300 w-16">{ext}</span>
                  <div className="flex-1 h-3 bg-dark-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent-600 rounded-full transition-all"
                      style={{ width: `${((count as number) / report.total_fonts) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-dark-400 w-20 text-right">
                    {(count as number).toLocaleString()} ({Math.round(((count as number) / report.total_fonts) * 100)}%)
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Export Buttons */}
      <div className="card">
        <h3 className="text-sm font-medium text-dark-200 mb-4">Export Report</h3>
        <div className="flex gap-3">
          <button
            onClick={() => exportJSON(report, formats)}
            className="btn-secondary"
          >
            📄 JSON
          </button>
          <button
            onClick={() => exportCSV(report, formats)}
            className="btn-secondary"
          >
            📊 CSV
          </button>
          <button
            onClick={() => exportHTML(report, formats)}
            className="btn-secondary"
          >
            🌐 HTML
          </button>
        </div>
      </div>

      {/* Toggle Font Table */}
      {fonts.length > 0 && (
        <div>
          <button
            onClick={() => setShowTable(!showTable)}
            className="btn-secondary w-full"
          >
            {showTable ? "Hide Font List" : `Show All ${report.total_fonts} Fonts →`}
          </button>

          {showTable && (
            <div className="mt-4">
              <FontTable fonts={fonts} />
            </div>
          )}
        </div>
      )}

      {/* Done */}
      <div className="text-center pt-6">
        <p className="text-sm text-dark-400">
          Ready to organize your fonts? Go to Step 4 to apply changes.
        </p>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  color,
  sub,
}: {
  label: string;
  value: number;
  color: string;
  sub?: string;
}) {
  return (
    <div className="card text-center">
      <p className={`text-3xl font-bold ${color}`}>{value.toLocaleString()}</p>
      <p className="text-sm text-dark-400 mt-1">{label}</p>
      {sub && <p className="text-xs text-dark-500 mt-1 truncate">{sub}</p>}
    </div>
  );
}

function exportJSON(report: any, _formats: Record<string, number>) {
  const data = { report, formats: _formats, generated: new Date().toISOString() };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  downloadBlob(blob, "fontforge-report.json");
}

function exportCSV(report: any, formats: Record<string, number>) {
  const rows = [["Metric", "Value"]];
  for (const [key, value] of Object.entries(report)) {
    rows.push([key.replace(/_/g, " "), String(value)]);
  }
  for (const [ext, count] of Object.entries(formats)) {
    rows.push([`Format: ${ext}`, String(count)]);
  }
  const blob = new Blob([rows.map((r) => r.join(",")).join("\n")], {
    type: "text/csv",
  });
  downloadBlob(blob, "fontforge-report.csv");
}

function exportHTML(report: any, _formats: Record<string, number>) {
  const html = `<!DOCTYPE html>
<html><head><title>FontForge Pro Report</title>
<style>body{font-family:system-ui;max-width:800px;margin:2rem auto;padding:1rem}
h1{color:#333}.card{background:#f5f5f5;padding:1rem;border-radius:8px;margin:1rem 0}
.metric{display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid #eee}
.value{font-weight:bold;color:#2563eb}</style></head>
<body><h1>FontForge Pro Report</h1>
<div class="card">${Object.entries(report)
    .map(
      ([k, v]) =>
        `<div class="metric"><span>${k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</span><span class="value">${v}</span></div>`
    )
    .join("")}</div></body></html>`;
  const blob = new Blob([html], { type: "text/html" });
  downloadBlob(blob, "fontforge-report.html");
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
