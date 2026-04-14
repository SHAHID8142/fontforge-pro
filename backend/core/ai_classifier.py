from __future__ import annotations

"""
AI classifier — integrates with Ollama for font classification.
Supports prompt optimization, confidence filtering, and fallback chaining.
"""

import json
import logging
import re
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen3:4b"
FALLBACK_MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Minimum confidence to accept AI result
CONFIDENCE_THRESHOLD = 0.7

# Style abbreviation expansion map
STYLE_ABBREVS = {
    "reg": "Regular",
    "bld": "Bold",
    "bd": "Bold",
    "it": "Italic",
    "itl": "Italic",
    "i": "Italic",
    "bdit": "BoldItalic",
    "bdi": "BoldItalic",
    "bi": "BoldItalic",
    "med": "Medium",
    "m": "Medium",
    "sb": "SemiBold",
    "semibold": "SemiBold",
    "smb": "SemiBold",
    "eb": "ExtraBold",
    "extrabold": "ExtraBold",
    "xb": "ExtraBold",
    "blk": "Black",
    "black": "Black",
    "bk": "Black",
    "thn": "Thin",
    "th": "Thin",
    "lt": "Light",
    "light": "Light",
    "hair": "Hairline",
    "cond": "Condensed",
    "narrow": "Narrow",
    "wide": "Wide",
    "ext": "Expanded",
}

# Category keywords for rule-based fallback
CATEGORY_KEYWORDS = {
    "serif": {"serif", "times", "georgia", "garamond", "baskerville", "minion"},
    "sans-serif": {"sans", "helvetica", "arial", "roboto", "open sans", "inter", "lato"},
    "monospace": {"mono", "code", "consolas", "courier", "source code", "fira code", "jetbrains"},
    "handwriting": {"hand", "script", "brush", "marker", "pencil", "write"},
    "display": {"display", "title", "headline", "decorative", "stencil"},
    "symbol": {"symbol", "icon", "emoji", "dingbat", "arrows"},
}

PROMPT_TEMPLATE = """You are a font classification expert. Analyze this font metadata and return ONLY valid JSON.

Font Metadata:
- Filename: "{filename}"
- Internal Family: "{family}"
- Internal Style: "{style}"
- Weight Class: {weight}
- Glyph Count: {glyph_count}

Your tasks:
1. Correct the family name if it has typos or abbreviations (e.g., "RobotoBd" → "Roboto")
2. Correct the style name if abbreviated (e.g., "Bd" → "Bold", "Reg" → "Regular")
3. Classify the font category based on family name patterns and glyph count

Return your analysis in this exact JSON format:
{{
  "corrected_family": "Corrected family name",
  "corrected_style": "Corrected style name",
  "category": "one of: serif, sans-serif, display, handwriting, monospace, script, symbol, unknown",
  "confidence": 0.95,
  "reasoning": "Brief one-sentence explanation"
}}

Rules:
- Do not include any text outside the JSON object
- Confidence should reflect how certain you are (0.0-1.0)
- Use glyph count as a hint: >3000 likely CJK or symbol, >1000 likely full Latin+Extended, <500 likely display/special
"""

PROMPT_LIGHT = """Analyze this font and return JSON:

Filename: "{filename}"
Family: "{family}"
Style: "{style}"
Weight: {weight}

Return: {{"corrected_family":"...", "corrected_style":"...", "category":"...", "confidence":0.9}}
Only valid JSON, no other text."""


class AIClassifier:
    """
    Classifies fonts using Ollama local AI.

    Features:
    - Prompt optimization (full vs light templates)
    - Confidence filtering
    - Rule-based fallback
    - Model fallback chain
    - Style abbreviation expansion
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        fallback_model: str = FALLBACK_MODEL,
        ollama_url: str = OLLAMA_URL,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        use_light_prompt: bool = False,
    ):
        self.model = model
        self.fallback_model = fallback_model
        self.ollama_url = ollama_url
        self.confidence_threshold = confidence_threshold
        self.prompt_template = PROMPT_LIGHT if use_light_prompt else PROMPT_TEMPLATE
        self._stats = {"total": 0, "ai_success": 0, "rule_fallback": 0, "low_confidence": 0}

    def classify(self, font_entry) -> dict:
        """
        Classify a single font using AI with rule-based fallback.

        Returns:
            dict with corrected_family, corrected_style, category, confidence, reasoning
        """
        self._stats["total"] += 1

        # Step 1: Rule-based style expansion
        rule_based = self._rule_based_classify(font_entry)

        # Step 2: Try AI classification
        ai_result = self._ai_classify(font_entry)

        if ai_result and ai_result.get("confidence", 0) >= self.confidence_threshold:
            self._stats["ai_success"] += 1
            return {
                **ai_result,
                "method": "ai",
            }

        # Step 3: Low confidence — use rule-based result
        if ai_result:
            self._stats["low_confidence"] += 1
            logger.debug(
                f"Low AI confidence ({ai_result.get('confidence', 0):.2f}) "
                f"for {font_entry.filename}, using rule-based"
            )

        self._stats["rule_fallback"] += 1
        return {
            **rule_based,
            "method": "rule_based",
            "reasoning": "Rule-based classification (AI unavailable or low confidence)",
        }

    def _rule_based_classify(self, font_entry) -> dict:
        """
        Apply rule-based classification as fallback.

        Rules:
        - Expand style abbreviations
        - Infer category from family name keywords
        - Infer corrections from filename patterns
        """
        family = font_entry.family_name or ""
        style = font_entry.style_name or ""
        filename = font_entry.filename or ""

        # Expand style abbreviations
        style_lower = style.lower().strip().replace(" ", "").replace("-", "")
        expanded_style = STYLE_ABBREVS.get(style_lower, style)

        # Clean family name (remove common suffixes)
        corrected_family = self._clean_family_name(family)

        # Category inference from family name
        category = self._infer_category(corrected_family, font_entry.glyph_count)

        # Confidence based on how much rule-based logic applied
        confidence = 0.6  # Base confidence for rule-based

        if corrected_family != family:
            confidence = 0.7  # Higher if we corrected something
        if expanded_style != style:
            confidence = max(confidence, 0.7)

        return {
            "corrected_family": corrected_family,
            "corrected_style": expanded_style,
            "category": category,
            "confidence": confidence,
        }

    @staticmethod
    def _clean_family_name(family: str) -> str:
        """Remove common suffixes from family name."""
        if not family:
            return "Unknown"

        # Remove trailing style indicators
        suffixes = [
            " Regular", " Bold", " Italic", " Bold Italic",
            " Medium", " Light", " Thin", " Black",
            "Bd", "Reg", "It", "Med", "Lt", "Blk",
        ]
        cleaned = family
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip()
                break

        return cleaned or "Unknown"

    @staticmethod
    def _infer_category(family: str, glyph_count: int) -> str:
        """Infer font category from family name and glyph count."""
        family_lower = family.lower()

        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in family_lower for kw in keywords):
                return category

        # Glyph count hints
        if glyph_count > 8000:
            return "symbol"  # Likely CJK or special
        if glyph_count < 200:
            return "display"  # Very few glyphs = decorative

        return "unknown"

    def _ai_classify(self, font_entry) -> dict | None:
        """Try AI classification with model fallback chain."""
        prompt = self.prompt_template.format(
            filename=font_entry.filename,
            family=font_entry.family_name or "Unknown",
            style=font_entry.style_name or "Unknown",
            weight=font_entry.weight_class,
            glyph_count=font_entry.glyph_count,
        )

        # Try primary model
        result = self._generate(prompt, self.model)
        if result:
            return result

        # Fallback to smaller model
        logger.warning(f"Primary model {self.model} failed, trying {self.fallback_model}")
        result = self._generate(prompt, self.fallback_model)
        return result

    def _generate(self, prompt: str, model: str) -> dict | None:
        """Send prompt to Ollama and parse JSON response."""
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 500,
                    },
                },
                timeout=60,
            )
            response.raise_for_status()
            raw = response.json()["response"]
            return self._parse_json(raw)
        except requests.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.ollama_url}")
            return None
        except Exception as e:
            logger.error(f"AI classification failed for {model}: {e}")
            return None

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        """Extract JSON from AI response."""
        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in text (handles markdown code blocks)
        try:
            # Remove markdown code blocks if present
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
            start = cleaned.index("{")
            end = cleaned.rindex("}") + 1
            return json.loads(cleaned[start:end])
        except (ValueError, json.JSONDecodeError):
            return None

    def classify_batch(
        self, font_entries: list, progress_callback: Callable | None = None
    ) -> list[dict]:
        """Classify multiple fonts with progress reporting."""
        results = []
        for i, entry in enumerate(font_entries):
            result = self.classify(entry)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(font_entries))

        logger.info(
            f"Batch classification complete: {self._stats['ai_success']} AI, "
            f"{self._stats['rule_fallback']} rule-based, "
            f"{self._stats['low_confidence']} low confidence"
        )
        return results

    def get_stats(self) -> dict:
        """Get classification statistics."""
        return dict(self._stats)
