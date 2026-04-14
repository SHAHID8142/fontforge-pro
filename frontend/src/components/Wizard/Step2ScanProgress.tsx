import { useState, useEffect } from "react";
import ProgressBar from "../common/ProgressBar";

interface Step2ScanProgressProps {
  state: any;
  setState: (fn: (s: any) => any) => void;
  onNext: () => void;
}

export default function Step2ScanProgress({
  state,
  setState,
  onNext,
}: Step2ScanProgressProps) {
  const [scanning, setScanning] = useState(true);
  const [progress, setProgress] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket connection for real-time progress
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket("ws://127.0.0.1:8765/ws/progress");
      ws.onopen = () => setWsConnected(true);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "scan_progress") {
            setProgress(data.percentage || 0);
          } else if (data.type === "scan_complete") {
            setProgress(100);
            setScanning(false);
          }
        } catch {
          // Ignore parse errors
        }
      };
      ws.onclose = () => {
        setWsConnected(false);
      };
      ws.onerror = () => {
        // Silently fail — use polling fallback
      };
    } catch {
      // WebSocket unavailable — use polling fallback
    }

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  // Polling fallback if WebSocket not available
  useEffect(() => {
    if (wsConnected) return;
    if (state.scanComplete) {
      setProgress(100);
      setScanning(false);
      return;
    }

    // Simulate progress if no real data
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 95) return p;
        return p + 2;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [wsConnected, state.scanComplete]);

  // Auto-advance when scan completes
  useEffect(() => {
    if (state.scanComplete && !scanning) {
      setState((s: any) => ({
        ...s,
        issues: {
          corrupted: state.fonts?.filter((f: any) => !f.is_valid)?.length || 0,
          duplicates: 0,  // Will be calculated in step 3
          misnamed: 0,    // Will be calculated in step 3
          incomplete_families: 0,
        },
      }));
    }
  }, [state.scanComplete, scanning]);

  const totalFonts = state.scanTotal || state.fonts?.length || 0;
  const validFonts = state.fonts?.filter((f: any) => f.is_valid)?.length || 0;
  const invalidFonts = state.fonts?.filter((f: any) => !f.is_valid)?.length || 0;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Scan & Analyze</h2>
        <p className="mt-2 text-dark-300">
          {scanning ? "Scanning for font files..." : "Scan complete!"}
        </p>
        {wsConnected && (
          <span className="badge badge-success mt-2">Live Progress</span>
        )}
      </div>

      {/* Progress Bar */}
      <div className="card">
        <ProgressBar
          value={progress}
          max={100}
          label={scanning ? "Scanning..." : "Complete"}
        />

        <div className="mt-6 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-3xl font-bold text-white">{totalFonts.toLocaleString()}</p>
            <p className="text-sm text-dark-400">Total Fonts</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-green-400">{validFonts.toLocaleString()}</p>
            <p className="text-sm text-dark-400">Valid</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-red-400">{invalidFonts.toLocaleString()}</p>
            <p className="text-sm text-dark-400">Corrupted</p>
          </div>
        </div>
      </div>

      {/* Scan Error */}
      {state.scanError && (
        <div className="card border-red-500">
          <p className="text-red-400 text-sm">⚠️ {state.scanError}</p>
          <p className="text-dark-400 text-xs mt-1">
            Start the backend with: <code className="text-accent-400">cd backend && python main.py</code>
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-center gap-4">
        {!scanning && progress === 100 && (
          <button onClick={onNext} className="btn-primary text-lg px-8">
            Review Issues →
          </button>
        )}
      </div>
    </div>
  );
}
