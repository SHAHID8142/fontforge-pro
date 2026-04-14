import { useState } from "react";

interface FilterBarProps {
  onFilterChange: (filters: FilterState) => void;
  formats?: string[];
}

interface FilterState {
  search: string;
  validStatus: "all" | "valid" | "invalid";
  format: string;
  category: string;
}

export default function FilterBar({ onFilterChange, formats = [] }: FilterBarProps) {
  const [filters, setFilters] = useState<FilterState>({
    search: "",
    validStatus: "all",
    format: "all",
    category: "all",
  });

  const update = (key: keyof FilterState, value: string) => {
    const next = { ...filters, [key]: value };
    setFilters(next);
    onFilterChange(next);
  };

  const categories = [
    "all",
    "serif",
    "sans-serif",
    "monospace",
    "display",
    "handwriting",
    "script",
    "symbol",
  ];

  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* Search */}
      <div className="flex-1 min-w-[200px]">
        <input
          type="text"
          value={filters.search}
          onChange={(e) => update("search", e.target.value)}
          placeholder="Search by family, style, or filename..."
          className="input w-full"
        />
      </div>

      {/* Status Filter */}
      <select
        value={filters.validStatus}
        onChange={(e) => update("validStatus", e.target.value)}
        className="input"
      >
        <option value="all">All Status</option>
        <option value="valid">✅ Valid</option>
        <option value="invalid">❌ Corrupted</option>
      </select>

      {/* Format Filter */}
      {formats.length > 0 && (
        <select
          value={filters.format}
          onChange={(e) => update("format", e.target.value)}
          className="input"
        >
          <option value="all">All Formats</option>
          {formats.map((ext) => (
            <option key={ext} value={ext}>
              {ext}
            </option>
          ))}
        </select>
      )}

      {/* Category Filter */}
      <select
        value={filters.category}
        onChange={(e) => update("category", e.target.value)}
        className="input"
      >
        {categories.map((cat) => (
          <option key={cat} value={cat}>
            {cat === "all" ? "All Categories" : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </option>
        ))}
      </select>

      {/* Clear */}
      <button
        onClick={() => {
          const cleared: FilterState = {
            search: "",
            validStatus: "all",
            format: "all",
            category: "all",
          };
          setFilters(cleared);
          onFilterChange(cleared);
        }}
        className="text-sm text-dark-400 hover:text-white transition-colors"
      >
        Clear
      </button>
    </div>
  );
}
