import { useState, useMemo } from "react";
import PreviewCard from "../FontPreview/PreviewCard";

interface FontEntry {
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
  is_valid: boolean;
  validation_error: string;
  category: string;
}

interface FontTableProps {
  fonts: FontEntry[];
  pageSize?: number;
}

type SortField = keyof FontEntry;
type SortDir = "asc" | "desc";

const ITEMS_PER_PAGE_OPTIONS = [25, 50, 100, 250];

export default function FontTable({ fonts, pageSize: initialPageSize = 50 }: FontTableProps) {
  const [search, setSearch] = useState("");
  const [sortField, setSortField] = useState<SortField>("family_name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [filterValid, setFilterValid] = useState<"all" | "valid" | "invalid">("all");
  const [selectedFont, setSelectedFont] = useState<FontEntry | null>(null);
  const [filterFormat, setFilterFormat] = useState<string>("all");

  // Filter and sort
  const filtered = useMemo(() => {
    let result = [...fonts];

    // Search
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (f) =>
          f.family_name.toLowerCase().includes(q) ||
          f.style_name.toLowerCase().includes(q) ||
          f.filename.toLowerCase().includes(q)
      );
    }

    // Validity filter
    if (filterValid === "valid") result = result.filter((f) => f.is_valid);
    if (filterValid === "invalid") result = result.filter((f) => !f.is_valid);

    // Format filter
    if (filterFormat !== "all") {
      result = result.filter((f) => f.extension === filterFormat);
    }

    // Sort
    result.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDir === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDir === "asc" ? aVal - bVal : bVal - aVal;
      }
      return 0;
    });

    return result;
  }, [fonts, search, filterValid, filterFormat, sortField, sortDir]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
    setPage(0);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <span className="text-dark-600 ml-1">↕</span>;
    return <span className="text-accent-400 ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>;
  };

  // Available formats
  const formats = useMemo(() => {
    const set = new Set(fonts.map((f) => f.extension));
    return Array.from(set).sort();
  }, [fonts]);

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          placeholder="Search fonts..."
          className="input flex-1 min-w-[200px]"
        />

        <select
          value={filterValid}
          onChange={(e) => {
            setFilterValid(e.target.value as any);
            setPage(0);
          }}
          className="input"
        >
          <option value="all">All Status</option>
          <option value="valid">Valid Only</option>
          <option value="invalid">Invalid Only</option>
        </select>

        <select
          value={filterFormat}
          onChange={(e) => {
            setFilterFormat(e.target.value);
            setPage(0);
          }}
          className="input"
        >
          <option value="all">All Formats</option>
          {formats.map((ext) => (
            <option key={ext} value={ext}>
              {ext}
            </option>
          ))}
        </select>

        <span className="text-sm text-dark-400">
          {filtered.length} of {fonts.length} fonts
        </span>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left py-2 px-3 text-dark-300 font-medium">
                <button onClick={() => handleSort("family_name")} className="flex items-center">
                  Family <SortIcon field="family_name" />
                </button>
              </th>
              <th className="text-left py-2 px-3 text-dark-300 font-medium">
                <button onClick={() => handleSort("style_name")} className="flex items-center">
                  Style <SortIcon field="style_name" />
                </button>
              </th>
              <th className="text-left py-2 px-3 text-dark-300 font-medium hidden md:table-cell">
                <button onClick={() => handleSort("weight_class")} className="flex items-center">
                  Weight <SortIcon field="weight_class" />
                </button>
              </th>
              <th className="text-left py-2 px-3 text-dark-300 font-medium hidden lg:table-cell">
                <button onClick={() => handleSort("glyph_count")} className="flex items-center">
                  Glyphs <SortIcon field="glyph_count" />
                </button>
              </th>
              <th className="text-left py-2 px-3 text-dark-300 font-medium hidden lg:table-cell">
                <button onClick={() => handleSort("extension")} className="flex items-center">
                  Format <SortIcon field="extension" />
                </button>
              </th>
              <th className="text-left py-2 px-3 text-dark-300 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((font, i) => (
              <tr
                key={font.path + i}
                className={`border-b border-dark-800 hover:bg-dark-700/50 cursor-pointer transition-colors ${
                  selectedFont?.path === font.path ? "bg-dark-700" : ""
                }`}
                onClick={() => setSelectedFont(font)}
              >
                <td className="py-2 px-3 text-white">{font.family_name || "Unknown"}</td>
                <td className="py-2 px-3 text-dark-300">{font.style_name || "Regular"}</td>
                <td className="py-2 px-3 text-dark-400 hidden md:table-cell">{font.weight_class}</td>
                <td className="py-2 px-3 text-dark-400 hidden lg:table-cell">
                  {font.glyph_count.toLocaleString()}
                </td>
                <td className="py-2 px-3 hidden lg:table-cell">
                  <span className="badge badge-info">{font.extension}</span>
                </td>
                <td className="py-2 px-3">
                  {font.is_valid ? (
                    <span className="badge badge-success">Valid</span>
                  ) : (
                    <span className="badge badge-danger" title={font.validation_error}>
                      Corrupted
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {paginated.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-dark-500">
                  No fonts match filters
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Font Preview (when selected) */}
      {selectedFont && (
        <PreviewCard font={selectedFont} />
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-dark-400">
          <span>Page</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(0);
            }}
            className="input text-sm py-1"
          >
            {ITEMS_PER_PAGE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size} per page
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="btn-secondary text-sm px-3 py-1 disabled:opacity-50"
          >
            ← Prev
          </button>
          <span className="text-sm text-dark-300 px-3">
            {page + 1} / {Math.max(1, totalPages)}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="btn-secondary text-sm px-3 py-1 disabled:opacity-50"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
