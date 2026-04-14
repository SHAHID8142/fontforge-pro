import { useState, useEffect, useRef } from "react";

interface PreviewCardProps {
  font: {
    path: string;
    filename: string;
    family_name: string;
    style_name: string;
    weight_class: number;
    glyph_count: number;
  };
}

export default function PreviewCard({ font }: PreviewCardProps) {
  const [fontSize, setFontSize] = useState(48);
  const [previewText, setPreviewText] = useState("The quick brown fox jumps over the lazy dog");
  const [fontLoaded, setFontLoaded] = useState(false);
  const fontNameRef = useRef(`preview-font-${font.filename}`);

  // Load font using @font-face + FontFace API
  useEffect(() => {
    let cancelled = false;

    async function loadFont() {
      try {
        // Convert file path to file:// URL for webview
        const fontUrl = `file://${font.path}`;
        const fontFace = new FontFace(fontNameRef.current, `url("${fontUrl}")`);
        const loaded = await fontFace.load();
        if (!cancelled) {
          document.fonts.add(loaded);
          setFontLoaded(true);
        }
      } catch (err) {
        console.warn(`Failed to load font ${font.filename}:`, err);
        setFontLoaded(false);
      }
    }

    loadFont();
    return () => {
      cancelled = true;
    };
  }, [font.path, font.filename]);

  const fontFamily = fontLoaded ? fontNameRef.current : "system-ui, sans-serif";

  const weightMap: Record<number, string> = {
    100: "Thin",
    200: "ExtraLight",
    300: "Light",
    400: "Regular",
    500: "Medium",
    600: "SemiBold",
    700: "Bold",
    800: "ExtraBold",
    900: "Black",
  };

  return (
    <div className="card space-y-4">
      {/* Font Info */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">
            {font.family_name || "Unknown"}
          </h3>
          <p className="text-sm text-dark-400">
            {font.style_name || "Regular"} · {weightMap[font.weight_class] || `W${font.weight_class}`}
          </p>
        </div>
        <span className="text-xs text-dark-500">{font.filename}</span>
      </div>

      {/* Preview Text */}
      <div
        className="min-h-[80px] flex items-center text-dark-100 overflow-hidden"
        style={{
          fontFamily,
          fontSize: `${fontSize}px`,
          fontWeight: font.weight_class || 400,
        }}
      >
        {previewText}
      </div>

      {/* Controls */}
      <div className="space-y-3 pt-3 border-t border-dark-700">
        {/* Font Size Slider */}
        <div>
          <div className="flex justify-between text-xs text-dark-400 mb-1">
            <span>Size</span>
            <span>{fontSize}px</span>
          </div>
          <input
            type="range"
            min={12}
            max={120}
            value={fontSize}
            onChange={(e) => setFontSize(Number(e.target.value))}
            className="w-full accent-accent-500"
          />
        </div>

        {/* Custom Preview Text */}
        <input
          type="text"
          value={previewText}
          onChange={(e) => setPreviewText(e.target.value)}
          placeholder="Type custom preview text..."
          className="input w-full text-sm"
        />

        {/* Glyph Count */}
        <div className="flex items-center gap-4 text-xs text-dark-500">
          <span>{font.glyph_count} glyphs</span>
          {!fontLoaded && (
            <span className="text-yellow-400">⚠️ Preview unavailable</span>
          )}
        </div>
      </div>
    </div>
  );
}
