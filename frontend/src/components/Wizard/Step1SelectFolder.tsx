import { useState, useCallback } from "react";
import { scanFonts } from "../../lib/api";

interface Step1SelectFolderProps {
  state: any;
  setState: (fn: (s: any) => any) => void;
  onNext: () => void;
}

export default function Step1SelectFolder({
  state,
  setState,
  onNext,
}: Step1SelectFolderProps) {
  const [error, setError] = useState<string | null>(null);

  const handleStartScan = useCallback(async () => {
    if (!state.folderPath) return;
    setError(null);
    onNext();

    try {
      const result = await scanFonts(state.folderPath, state.includeSubfolders);
      setState((s: any) => ({
        ...s,
        fonts: result.fonts || [],
        scanTotal: result.total || 0,
        scanComplete: true,
      }));
    } catch (err: any) {
      setError(err.message);
      setState((s: any) => ({
        ...s,
        fonts: [],
        scanComplete: false,
        scanError: err.message,
      }));
    }
  }, [state.folderPath, state.includeSubfolders, onNext, setState]);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Select Font Folder</h2>
        <p className="mt-2 text-dark-300">
          Enter the path to your font collection folder.
        </p>
      </div>

      <div className="card space-y-4">
        {/* Folder Path Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-dark-200">Folder Path</label>
          <input
            type="text"
            className="input flex-1 w-full"
            placeholder="/Users/yourname/Fonts"
            value={state.folderPath}
            onChange={(e) =>
              setState((s: any) => ({ ...s, folderPath: e.target.value }))
            }
            onKeyDown={(e) => {
              if (e.key === "Enter" && state.folderPath) handleStartScan();
            }}
          />
          <p className="text-xs text-dark-500">
            💡 Tip: Right-click a folder in Finder → <code className="text-dark-300">Get Info</code> → Copy the path
          </p>
        </div>

        {/* Quick Select Buttons */}
        <div className="space-y-2 pt-2 border-t border-dark-700">
          <p className="text-xs text-dark-400">Quick select:</p>
          <div className="flex flex-wrap gap-2">
            {[
              { label: "macOS System Fonts", path: "/System/Library/Fonts" },
              { label: "User Fonts", path: "~/Library/Fonts" },
              { label: "All User Fonts", path: "/Users/maryam/Library/Fonts" },
            ].map((preset) => (
              <button
                key={preset.path}
                onClick={() =>
                  setState((s: any) => ({ ...s, folderPath: preset.path }))
                }
                className="text-xs px-3 py-1.5 rounded bg-dark-700 hover:bg-dark-600 text-dark-300 hover:text-white transition-colors"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Options */}
        <div className="space-y-3 pt-4 border-t border-dark-700">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={state.includeSubfolders}
              onChange={(e) =>
                setState((s: any) => ({ ...s, includeSubfolders: e.target.checked }))
              }
              className="w-4 h-4 accent-accent-500 rounded"
            />
            <span className="text-sm text-dark-200">Include subfolders</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={state.createBackup}
              onChange={(e) =>
                setState((s: any) => ({ ...s, createBackup: e.target.checked }))
              }
              className="w-4 h-4 accent-accent-500 rounded"
            />
            <span className="text-sm text-dark-200">Create backup before processing</span>
          </label>
        </div>
      </div>

      {/* Supported Formats */}
      <div className="card">
        <h3 className="text-sm font-medium text-dark-200 mb-2">Supported Formats</h3>
        <div className="flex flex-wrap gap-2">
          {[".ttf", ".otf", ".woff", ".woff2", ".ttc"].map((ext) => (
            <span key={ext} className="badge badge-info">
              {ext}
            </span>
          ))}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card border border-red-500/50">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
          <p className="text-dark-400 text-xs mt-1">
            Backend not running? Start with:{" "}
            <code className="text-accent-400">cd backend && source venv/bin/activate && python main.py</code>
          </p>
        </div>
      )}

      {/* Start Scan Button */}
      <div className="flex justify-center">
        <button
          onClick={handleStartScan}
          disabled={!state.folderPath}
          className="btn-primary text-lg px-10 py-3"
        >
          🔍 Start Scan
        </button>
      </div>

      {/* Info */}
      <div className="text-center text-sm text-dark-400">
        <p>Fonts will never be deleted — only moved to safe locations.</p>
      </div>
    </div>
  );
}
