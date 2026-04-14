import { useState } from "react";
import { organizeFonts } from "../../lib/api";

interface Step4OrganizeProps {
  state: any;
  setState: (fn: (s: any) => any) => void;
  onNext: () => void;
}

export default function Step4Organize({ state, onNext }: Step4OrganizeProps) {
  const [organizing, setOrganizing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [outputDir, setOutputDir] = useState("");
  const [options, setOptions] = useState({
    groupByFamily: true,
    separateComplete: true,
    aiClassification: false,
    dryRun: true,
  });
  const [result, setResult] = useState<any>(null);

  const handleOrganize = async () => {
    setOrganizing(true);
    setProgress(0);
    setResult(null);

    const fonts = state.fonts || [];
    const output = outputDir || `${state.folderPath}/organized`;

    try {
      // Organize fonts
      const orgResult = await organizeFonts(fonts, output);
      setProgress(100);
      setResult(orgResult);

      // Auto-advance after a brief delay
      setTimeout(() => onNext(), 1500);
    } catch (err: any) {
      setResult({ error: err.message });
      setOrganizing(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Organize Fonts</h2>
        <p className="mt-2 text-dark-300">
          Choose how to organize your cleaned font collection.
        </p>
      </div>

      {/* Output Directory */}
      <div className="card space-y-3">
        <label className="text-sm font-medium text-dark-200">Output Directory</label>
        <input
          type="text"
          className="input w-full"
          placeholder={`${state.folderPath}/organized`}
          value={outputDir}
          onChange={(e) => setOutputDir(e.target.value)}
        />
        <p className="text-xs text-dark-500">Leave empty to use the default: <code className="text-accent-400">{state.folderPath}/organized</code></p>
      </div>

      {/* Options */}
      <div className="card space-y-4">
        <label className="flex items-center justify-between cursor-pointer">
          <div>
            <p className="font-medium text-white">Group by family</p>
            <p className="text-sm text-dark-400">
              Create one folder per font family (e.g., Roboto/, OpenSans/)
            </p>
          </div>
          <input
            type="checkbox"
            checked={options.groupByFamily}
            onChange={(e) => setOptions((o) => ({ ...o, groupByFamily: e.target.checked }))}
            className="w-5 h-5 accent-accent-500"
          />
        </label>

        <div className="border-t border-dark-700" />

        <label className="flex items-center justify-between cursor-pointer">
          <div>
            <p className="font-medium text-white">Separate complete/incomplete</p>
            <p className="text-sm text-dark-400">
              Split families with all 4+ styles vs. those missing styles
            </p>
          </div>
          <input
            type="checkbox"
            checked={options.separateComplete}
            onChange={(e) => setOptions((o) => ({ ...o, separateComplete: e.target.checked }))}
            className="w-5 h-5 accent-accent-500"
          />
        </label>

        <div className="border-t border-dark-700" />

        <label className="flex items-center justify-between cursor-pointer">
          <div>
            <p className="font-medium text-white">AI-powered classification</p>
            <p className="text-sm text-dark-400">
              Use Ollama to categorize fonts (serif, sans-serif, display, etc.)
            </p>
          </div>
          <input
            type="checkbox"
            checked={options.aiClassification}
            onChange={(e) => setOptions((o) => ({ ...o, aiClassification: e.target.checked }))}
            className="w-5 h-5 accent-accent-500"
          />
        </label>

        <div className="border-t border-dark-700" />

        <label className="flex items-center justify-between cursor-pointer">
          <div>
            <p className="font-medium text-white">Dry-run mode</p>
            <p className="text-sm text-dark-400">
              Preview changes without moving files (safe)
            </p>
          </div>
          <input
            type="checkbox"
            checked={options.dryRun}
            onChange={(e) => setOptions((o) => ({ ...o, dryRun: e.target.checked }))}
            className="w-5 h-5 accent-accent-500"
          />
        </label>
      </div>

      {/* Preview */}
      <div className="card">
        <h3 className="text-sm font-medium text-dark-200 mb-3">Output Structure Preview</h3>
        <pre className="text-xs text-dark-300 bg-dark-900 p-3 rounded font-mono">
{`organized/
├── complete_families/
│   ├── Roboto/
│   │   ├── Roboto-Regular.ttf
│   │   ├── Roboto-Bold.ttf
│   │   ├── Roboto-Italic.ttf
│   │   └── Roboto-BoldItalic.ttf
│   └── OpenSans/
└── incomplete_families/
    └── CustomFont/
        └── CustomFont-Bold.ttf (missing Regular, Italic)`}
        </pre>
      </div>

      {/* Progress / Result */}
      {organizing && (
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-dark-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent-600 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-sm text-dark-300">{progress}%</span>
          </div>
        </div>
      )}

      {result && result.error && (
        <div className="card border-red-500">
          <p className="text-red-400 text-sm">❌ {result.error}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-center gap-4">
        <button
          onClick={handleOrganize}
          disabled={organizing || !state.folderPath}
          className="btn-primary text-lg px-8"
        >
          {organizing ? "Organizing..." : options.dryRun ? "Preview Changes" : "Execute"}
        </button>
      </div>
    </div>
  );
}
