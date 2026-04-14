"""
Enhanced tests for AI classifier with rule-based fallback.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

from core.ai_classifier import AIClassifier, STYLE_ABBREVS, CATEGORY_KEYWORDS
from models.font_entry import FontEntry


class TestRuleBasedClassification:
    """Tests for rule-based classification (no AI needed)."""

    @pytest.fixture
    def classifier(self):
        return AIClassifier()

    def test_style_expansion_bold(self, classifier):
        """Should expand 'Bd' to 'Bold'."""
        entry = FontEntry(
            path=Path("/test/font.ttf"), filename="font.ttf", extension=".ttf",
            file_size=100, family_name="Roboto", style_name="Bd",
            weight_class=700, glyph_count=876,
        )
        result = classifier._rule_based_classify(entry)
        assert result["corrected_style"] == "Bold"

    def test_style_expansion_italic(self, classifier):
        """Should expand 'It' to 'Italic'."""
        entry = FontEntry(
            path=Path("/test/font.ttf"), filename="font.ttf", extension=".ttf",
            file_size=100, family_name="Roboto", style_name="It",
            weight_class=400, glyph_count=876,
        )
        result = classifier._rule_based_classify(entry)
        assert result["corrected_style"] == "Italic"

    def test_style_expansion_bold_italic(self, classifier):
        """Should expand 'BdIt' to 'BoldItalic'."""
        entry = FontEntry(
            path=Path("/test/font.ttf"), filename="font.ttf", extension=".ttf",
            file_size=100, family_name="Roboto", style_name="BdIt",
            weight_class=700, glyph_count=876,
        )
        result = classifier._rule_based_classify(entry)
        assert result["corrected_style"] == "BoldItalic"

    def test_style_no_expansion(self, classifier):
        """Already correct style should be unchanged."""
        entry = FontEntry(
            path=Path("/test/font.ttf"), filename="font.ttf", extension=".ttf",
            file_size=100, family_name="Roboto", style_name="Bold",
            weight_class=700, glyph_count=876,
        )
        result = classifier._rule_based_classify(entry)
        assert result["corrected_style"] == "Bold"

    def test_family_name_cleaning(self, classifier):
        """Should remove style suffixes from family name."""
        assert classifier._clean_family_name("Roboto Bold") == "Roboto"
        assert classifier._clean_family_name("ArialBd") == "Arial"
        assert classifier._clean_family_name("Open Sans Regular") == "Open Sans"

    def test_category_inference_sans_serif(self, classifier):
        """Should detect sans-serif from family name."""
        assert classifier._infer_category("Roboto", 876) == "sans-serif"
        assert classifier._infer_category("Helvetica Neue", 876) == "sans-serif"
        assert classifier._infer_category("Inter", 876) == "sans-serif"

    def test_category_inference_serif(self, classifier):
        """Should detect serif from family name."""
        assert classifier._infer_category("Georgia", 876) == "serif"
        assert classifier._infer_category("Times New Roman", 876) == "serif"

    def test_category_inference_monospace(self, classifier):
        """Should detect monospace from family name."""
        assert classifier._infer_category("Fira Code", 2000) == "monospace"
        assert classifier._infer_category("Source Code Pro", 2000) == "monospace"

    def test_category_inference_display(self, classifier):
        """Should detect display fonts with few glyphs."""
        assert classifier._infer_category("SpecialFont", 150) == "display"

    def test_category_inference_symbol(self, classifier):
        """Should detect symbol/icon fonts with many glyphs."""
        assert classifier._infer_category("IconFont", 9000) == "symbol"

    def test_confidence_scoring(self, classifier):
        """Confidence should reflect certainty level."""
        # Abbreviated style = higher confidence (we corrected something)
        entry = FontEntry(
            path=Path("/test/font.ttf"), filename="font.ttf", extension=".ttf",
            file_size=100, family_name="RobotoBd", style_name="Bd",
            weight_class=700, glyph_count=876,
        )
        result = classifier._rule_based_classify(entry)
        assert result["confidence"] >= 0.7


class TestAIClassifierFallback:
    """Tests for AI classifier with fallback behavior."""

    @patch("core.ai_classifier.requests.post")
    def test_ai_success(self, mock_post):
        """Successful AI classification should return parsed result."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"corrected_family": "Roboto", "corrected_style": "Bold", "category": "sans-serif", "confidence": 0.95, "reasoning": "test"}'
        }
        mock_post.return_value = mock_response

        classifier = AIClassifier()
        entry = FontEntry(
            path=Path("/test/abc.ttf"), filename="abc.ttf", extension=".ttf",
            file_size=100, family_name="RobotoBd", style_name="Bd",
            weight_class=700, glyph_count=876,
        )
        result = classifier.classify(entry)
        assert result["corrected_family"] == "Roboto"
        assert result["method"] == "ai"

    @patch("core.ai_classifier.requests.post")
    def test_ai_low_confidence_fallback(self, mock_post):
        """Low AI confidence should fall back to rule-based."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"corrected_family": "Unknown", "corrected_style": "Unknown", "category": "unknown", "confidence": 0.3, "reasoning": "not sure"}'
        }
        mock_post.return_value = mock_response

        classifier = AIClassifier()
        entry = FontEntry(
            path=Path("/test/abc.ttf"), filename="abc.ttf", extension=".ttf",
            file_size=100, family_name="Roboto", style_name="Bd",
            weight_class=700, glyph_count=876,
        )
        result = classifier.classify(entry)
        # Should use rule-based since AI confidence < 0.7
        assert result["method"] == "rule_based"
        # Rule-based should still correct "Bd" → "Bold"
        assert result["corrected_style"] == "Bold"

    @patch("core.ai_classifier.requests.post")
    def test_connection_error_fallback(self, mock_post):
        """Connection error should fall back to rule-based."""
        from requests import ConnectionError
        mock_post.side_effect = ConnectionError("Cannot connect")

        classifier = AIClassifier()
        entry = FontEntry(
            path=Path("/test/abc.ttf"), filename="abc.ttf", extension=".ttf",
            file_size=100, family_name="Roboto", style_name="Bd",
            weight_class=700, glyph_count=876,
        )
        result = classifier.classify(entry)
        assert result["method"] == "rule_based"
        assert result["corrected_style"] == "Bold"

    def test_parse_json_markdown_blocks(self):
        """Should extract JSON from markdown code blocks."""
        raw = '''```json
{"corrected_family": "Roboto", "category": "sans-serif"}
```'''
        result = AIClassifier._parse_json(raw)
        assert result is not None
        assert result["corrected_family"] == "Roboto"

    def test_stats_tracking(self):
        """Classification stats should be tracked."""
        classifier = AIClassifier()
        stats = classifier.get_stats()
        assert "total" in stats
        assert "ai_success" in stats
        assert "rule_fallback" in stats


class TestStyleAbbreviations:
    """Verify style abbreviation map completeness."""

    def test_common_abbreviations_exist(self):
        """All common abbreviations should be in the map."""
        assert STYLE_ABBREVS["reg"] == "Regular"
        assert STYLE_ABBREVS["bld"] == "Bold"
        assert STYLE_ABBREVS["bd"] == "Bold"
        assert STYLE_ABBREVS["it"] == "Italic"
        assert STYLE_ABBREVS["med"] == "Medium"
        assert STYLE_ABBREVS["sb"] == "SemiBold"
        assert STYLE_ABBREVS["eb"] == "ExtraBold"
        assert STYLE_ABBREVS["blk"] == "Black"
        assert STYLE_ABBREVS["lt"] == "Light"
        assert STYLE_ABBREVS["thn"] == "Thin"


class TestCategoryKeywords:
    """Verify category keyword map."""

    def test_serif_keywords(self):
        assert "times" in CATEGORY_KEYWORDS["serif"]
        assert "georgia" in CATEGORY_KEYWORDS["serif"]
        assert "garamond" in CATEGORY_KEYWORDS["serif"]

    def test_sans_serif_keywords(self):
        assert "roboto" in CATEGORY_KEYWORDS["sans-serif"]
        assert "helvetica" in CATEGORY_KEYWORDS["sans-serif"]
        assert "inter" in CATEGORY_KEYWORDS["sans-serif"]
