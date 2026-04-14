const BACKEND_URL = "http://127.0.0.1:8765";

export async function healthCheck() {
  const res = await fetch(`${BACKEND_URL}/health`);
  return res.json();
}

export async function scanFonts(folderPath: string, includeSubfolders: boolean = true) {
  const res = await fetch(`${BACKEND_URL}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder_path: folderPath, include_subfolders: includeSubfolders }),
  });
  if (!res.ok) throw new Error(`Scan failed: ${res.status}`);
  return res.json();
}

export async function validateFonts(fontPaths: string[]) {
  const res = await fetch(`${BACKEND_URL}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ font_paths: fontPaths }),
  });
  if (!res.ok) throw new Error(`Validation failed: ${res.status}`);
  return res.json();
}

export async function findDuplicates(fontPaths: string[]) {
  const res = await fetch(`${BACKEND_URL}/deduplicate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ font_paths: fontPaths }),
  });
  if (!res.ok) throw new Error(`Dedup failed: ${res.status}`);
  return res.json();
}

export async function organizeFonts(fontPaths: string[], outputDir: string) {
  const res = await fetch(`${BACKEND_URL}/organize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ font_paths: fontPaths, output_dir: outputDir }),
  });
  if (!res.ok) throw new Error(`Organize failed: ${res.status}`);
  return res.json();
}

export async function getReport() {
  const res = await fetch(`${BACKEND_URL}/report`);
  if (!res.ok) throw new Error(`Report failed: ${res.status}`);
  return res.json();
}

export async function undoLast() {
  const res = await fetch(`${BACKEND_URL}/undo`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Undo failed: ${res.status}`);
  return res.json();
}
