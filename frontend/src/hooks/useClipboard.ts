import { useState, useEffect } from "react";

export function useClipboard() {
  const [clipboardText, setClipboardText] = useState("");

  useEffect(() => {
    const handleCopy = () => {
      navigator.clipboard.readText().then((text) => {
        setClipboardText(text);
      }).catch(() => {
        // Clipboard permission denied
      });
    };

    // Poll clipboard every 500ms (for clipboard monitoring feature)
    const interval = setInterval(handleCopy, 500);
    return () => clearInterval(interval);
  }, []);

  return { clipboardText };
}
