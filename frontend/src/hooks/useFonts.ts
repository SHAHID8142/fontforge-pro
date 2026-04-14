import { useState } from "react";

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

export function useFonts() {
  const [fonts, setFonts] = useState<FontEntry[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState("");
  const [sortField, setSortField] = useState<keyof FontEntry>("family_name");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const filtered = fonts
    .filter((f) => {
      if (!filter) return true;
      const q = filter.toLowerCase();
      return (
        f.family_name.toLowerCase().includes(q) ||
        f.style_name.toLowerCase().includes(q) ||
        f.filename.toLowerCase().includes(q)
      );
    })
    .sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDir === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      return sortDir === "asc" ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });

  const toggleSelect = (path: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const selectAll = () => {
    setSelected(new Set(filtered.map((f) => f.path)));
  };

  const deselectAll = () => setSelected(new Set());

  return {
    fonts,
    setFonts,
    selected,
    filtered,
    filter,
    setFilter,
    sortField,
    setSortField,
    sortDir,
    setSortDir,
    toggleSelect,
    selectAll,
    deselectAll,
  };
}
