import { useState } from "react";
import Step1SelectFolder from "./components/Wizard/Step1SelectFolder";
import Step2ScanProgress from "./components/Wizard/Step2ScanProgress";
import Step3ReviewIssues from "./components/Wizard/Step3ReviewIssues";
import Step4Organize from "./components/Wizard/Step4Organize";
import Step5Report from "./components/Wizard/Step5Report";
import { useBackend } from "./hooks/useBackend";

export interface ScanState {
  folderPath: string;
  includeSubfolders: boolean;
  createBackup: boolean;
  fonts: FontEntry[];
  issues: Issues;
  step: number;
  scanTotal: number;
  scanComplete: boolean;
  scanError: string | null;
}

export interface FontEntry {
  path: string;
  filename: string;
  extension: string;
  file_size: number;
  family_name: string;
  style_name: string;
  full_name: string;
  weight_class: number;
  version: string;
  glyph_count: number;
  sha256_hash: string;
  quick_hash: string;
  is_valid: boolean;
  validation_error: string;
  suggested_family: string;
  suggested_style: string;
  category: string;
  ai_confidence: number;
}

export interface Issues {
  corrupted: number;
  duplicates: number;
  misnamed: number;
  incomplete_families: number;
  complete_families: number;
}

const STEPS = [
  "Select Folder",
  "Scan & Analyze",
  "Review Issues",
  "Organize",
  "Report & Export",
];

function App() {
  const { state: backend } = useBackend();
  const [state, setState] = useState<ScanState>({
    folderPath: "",
    includeSubfolders: true,
    createBackup: false,
    fonts: [],
    issues: { corrupted: 0, duplicates: 0, misnamed: 0, incomplete_families: 0, complete_families: 0 },
    step: 1,
    scanTotal: 0,
    scanComplete: false,
    scanError: null,
  });

  const nextStep = () => setState((s) => ({ ...s, step: Math.min(s.step + 1, 5) }));
  const prevStep = () => setState((s) => ({ ...s, step: Math.max(s.step - 1, 1) }));

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-dark-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-white">FontForge Pro</h1>
            <span className="text-xs text-dark-500">v0.1.0</span>
          </div>
          <div className="flex items-center gap-3">
            {/* Backend Connection Status */}
            <span
              className={`badge ${
                backend.connected ? "badge-success" : "badge-danger"
              }`}
            >
              {backend.connected ? "● Backend" : "○ Backend Offline"}
            </span>
          </div>
        </div>
      </header>

      {/* Step Indicator */}
      <nav className="px-6 py-3 bg-dark-900 border-b border-dark-800">
        <div className="flex items-center gap-1 overflow-x-auto">
          {STEPS.map((label, i) => {
            const stepNum = i + 1;
            const isActive = stepNum === state.step;
            const isComplete = stepNum < state.step;
            return (
              <div key={label} className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => {
                    if (stepNum < state.step) {
                      setState((s) => ({ ...s, step: stepNum }));
                    }
                  }}
                  className={`flex items-center gap-2 px-2 py-1 rounded transition-colors ${
                    isActive
                      ? "bg-accent-600/20 text-accent-400"
                      : isComplete
                        ? "text-green-400 hover:bg-dark-700"
                        : "text-dark-500"
                  }`}
                  disabled={stepNum > state.step}
                >
                  <div
                    className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-medium ${
                      isActive
                        ? "bg-accent-600 text-white"
                        : isComplete
                          ? "bg-green-600 text-white"
                          : "bg-dark-700 text-dark-400"
                    }`}
                  >
                    {isComplete ? "✓" : stepNum}
                  </div>
                  <span className="text-sm hidden md:inline">{label}</span>
                </button>
                {i < STEPS.length - 1 && (
                  <div className={`w-6 h-px ${isComplete ? "bg-green-600" : "bg-dark-600"}`} />
                )}
              </div>
            );
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto">
        {state.step === 1 && (
          <Step1SelectFolder state={state} setState={setState} onNext={nextStep} />
        )}
        {state.step === 2 && (
          <Step2ScanProgress state={state} setState={setState} onNext={nextStep} />
        )}
        {state.step === 3 && (
          <Step3ReviewIssues state={state} setState={setState} onNext={nextStep} />
        )}
        {state.step === 4 && (
          <Step4Organize state={state} setState={setState} onNext={nextStep} />
        )}
        {state.step === 5 && <Step5Report state={state} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-700 px-6 py-3">
        <div className="flex items-center justify-between text-sm text-dark-400">
          <span className="text-xs">Accuracy over Speed</span>
          <div className="flex gap-3">
            {state.step > 1 && (
              <button
                onClick={prevStep}
                className="btn-secondary text-sm px-4 py-2"
              >
                ← Back
              </button>
            )}
            {state.step < 5 && (
              <button
                onClick={nextStep}
                disabled={
                  (state.step === 1 && !state.folderPath) ||
                  (state.step === 2 && !state.scanComplete)
                }
                className="btn-primary text-sm px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next →
              </button>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
