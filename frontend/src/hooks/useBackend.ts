import { useState, useEffect } from "react";

const BACKEND_URL = "http://127.0.0.1:8765";

export interface BackendState {
  connected: boolean;
  loading: boolean;
  error: string | null;
}

export function useBackend() {
  const [state, setState] = useState<BackendState>({
    connected: false,
    loading: true,
    error: null,
  });

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (res.ok) {
        setState({ connected: true, loading: false, error: null });
      } else {
        throw new Error(`Health check failed: ${res.status}`);
      }
    } catch (err) {
      setState({
        connected: false,
        loading: false,
        error: `Cannot connect to backend: ${err instanceof Error ? err.message : "unknown error"}`,
      });
    }
  };

  const scanFonts = async (folderPath: string, includeSubfolders: boolean = true) => {
    const res = await fetch(`${BACKEND_URL}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder_path: folderPath, include_subfolders: includeSubfolders }),
    });
    if (!res.ok) throw new Error(`Scan failed: ${res.status}`);
    return res.json();
  };

  const validateFonts = async (fontPaths: string[]) => {
    const res = await fetch(`${BACKEND_URL}/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ font_paths: fontPaths }),
    });
    if (!res.ok) throw new Error(`Validation failed: ${res.status}`);
    return res.json();
  };

  const findDuplicates = async (fontPaths: string[]) => {
    const res = await fetch(`${BACKEND_URL}/deduplicate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ font_paths: fontPaths }),
    });
    if (!res.ok) throw new Error(`Dedup failed: ${res.status}`);
    return res.json();
  };

  return {
    state,
    scanFonts,
    validateFonts,
    findDuplicates,
    retry: checkHealth,
  };
}
