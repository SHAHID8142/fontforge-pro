import { useMemo } from "react";
import { findDuplicates } from "../../lib/api";

interface Step3ReviewIssuesProps {
  state: any;
  setState: (fn: (s: any) => any) => void;
  onNext: () => void;
}

export default function Step3ReviewIssues({
  state,
  setState,
  onNext,
}: Step3ReviewIssuesProps) {
  const fonts = state.fonts || [];

  // Analyze issues from scanned fonts
  const issues = useMemo(() => {
    const corrupted = fonts.filter((f: any) => !f.is_valid).length;

    // Count misnamed: filename doesn't match family-style
    const misnamed = fonts.filter((f: any) => {
      if (!f.is_valid) return false;
      const expected = `${f.family_name || "Unknown"}-${f.style_name || "Regular"}`;
      const actual = (f.filename || "").replace(/\.[^.]+$/, "");
      return actual !== expected;
    }).length;

    // Count incomplete families
    const families = new Map<string, Set<string>>();
    fonts.forEach((f: any) => {
      if (!f.is_valid) return;
      const family = f.family_name || "Unknown";
      const style = (f.style_name || "Regular").toLowerCase().replace(/[\s-]/g, "");
      if (!families.has(family)) families.set(family, new Set());
      families.get(family)!.add(style);
    });

    const completeFamilies = ["regular", "bold", "italic", "bolditalic"];
    let incompleteCount = 0;
    families.forEach((styles) => {
      const isComplete = completeFamilies.every((s) => styles.has(s));
      if (!isComplete) incompleteCount++;
    });

    return {
      corrupted,
      duplicates: 0, // Will be populated when "Find Duplicates" runs
      misnamed,
      incomplete_families: incompleteCount,
      complete_families: families.size - incompleteCount,
    };
  }, [fonts]);

  const handleFindDuplicates = async () => {
    try {
      const result = await findDuplicates(fonts);
      const dupCount = result.duplicate_groups?.reduce(
        (sum: number, g: any) => sum + (g.duplicates?.length || 0),
        0
      ) || 0;
      setState((s: any) => ({
        ...s,
        issues: { ...issues, duplicates: dupCount },
        duplicateGroups: result.duplicate_groups || [],
      }));
    } catch {
      setState((s: any) => ({
        ...s,
        issues: { ...issues, duplicates: 0 },
      }));
    }
  };

  const issueTypes = [
    {
      key: "corrupted",
      label: "Corrupted Fonts",
      icon: "⚠️",
      color: "badge-danger",
      description: "Fonts with broken structure or missing tables",
      action: "Move to quarantine",
    },
    {
      key: "duplicates",
      label: "Duplicates",
      icon: "🔄",
      color: "badge-warning",
      description: "Identical or near-identical font files",
      action: "Find Duplicates",
      actionFn: handleFindDuplicates,
    },
    {
      key: "misnamed",
      label: "Misnamed Fonts",
      icon: "✏️",
      color: "badge-info",
      description: "Filename doesn't match internal metadata",
      action: "Auto-rename",
    },
    {
      key: "incomplete_families",
      label: "Incomplete Families",
      icon: "📁",
      color: "badge-warning",
      description: "Font families missing required styles",
      action: "View details",
    },
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Review Issues</h2>
        <p className="mt-2 text-dark-300">
          Found {fonts.length} fonts with the following issues:
        </p>
      </div>

      {/* Issues Grid */}
      <div className="grid grid-cols-2 gap-4">
        {issueTypes.map((issue) => {
          const count = issues[issue.key as keyof typeof issues] as number;
          return (
            <div key={issue.key} className="card flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{issue.icon}</span>
                <div>
                  <p className="font-medium text-white">{issue.label}</p>
                  <p className="text-xs text-dark-400">{issue.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`badge ${issue.color} text-lg px-3 py-1`}>
                  {count.toLocaleString()}
                </span>
                {issue.actionFn && (
                  <button
                    onClick={issue.actionFn}
                    className="text-xs text-accent-400 hover:text-accent-300"
                  >
                    {issue.action}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="card">
        <h3 className="text-sm font-medium text-dark-200 mb-2">What will happen</h3>
        <ul className="space-y-2 text-sm text-dark-300">
          <li className="flex items-center gap-2">
            <span className="text-green-400">→</span>
            Corrupted fonts → <code className="text-accent-400">/quarantine/corrupted_fonts/</code>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-400">→</span>
            Duplicates → <code className="text-accent-400">/duplicates/</code> (best version kept)
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-400">→</span>
            Misnamed → <code className="text-accent-400">{`{Family}-{Style}.ttf`}</code>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-400">→</span>
            Grouped into <code className="text-accent-400">complete/incomplete families</code>
          </li>
        </ul>
      </div>

      {/* Actions */}
      <div className="flex justify-center gap-4">
        <button onClick={onNext} className="btn-primary text-lg px-8">
          Apply All Fixes →
        </button>
      </div>
    </div>
  );
}
