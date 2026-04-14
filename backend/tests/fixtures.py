"""
Test font fixtures — creates minimal font files for testing.
Uses fontTools.fontBuilder for proper font construction.
"""

from pathlib import Path
from fontTools import ttLib
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen


def create_minimal_ttf(path: str, family: str = "TestFont", style: str = "Regular",
                        weight: int = 400, version: str = "1.000",
                        glyph_count: int = 1, corrupt: bool = False) -> str:
    """
    Create a minimal TTF font using FontBuilder.
    """
    num_glyphs = max(glyph_count, 1)
    glyph_order = [".notdef"] + [f"g{i}" for i in range(1, num_glyphs)]

    fb = FontBuilder(1000, isTTF=True)

    # Create empty glyph outlines using TTGlyphPen
    pen = TTGlyphPen(None)
    empty_glyph = pen.glyph()

    glyphs = {}
    for name in glyph_order:
        glyphs[name] = empty_glyph

    fb.setupGlyphOrder(glyph_order)
    fb.setupGlyf(glyphs)
    fb.setupCharacterMap({c: ".notdef" for c in range(32, 127)})
    fb.setupHorizontalMetrics({name: (500, 0) for name in glyph_order})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({
        "familyName": family,
        "styleName": style,
    })
    fb.setupOS2(usWeightClass=weight)
    fb.setupPost()
    fb.setupHead(unitsPerEm=1000)
    fb.save(path)

    if corrupt:
        font = ttLib.TTFont(path)
        del font["cmap"]
        font.save(path)
        font.close()

    return path


class FontFactory:
    """Factory for creating test font files."""

    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
        self.created_fonts = []

    def create_ttf(self, **kwargs) -> str:
        """Create a test TTF font."""
        if "path" not in kwargs:
            name = kwargs.get("family", "Test") + "-" + kwargs.get("style", "Regular") + ".ttf"
            kwargs["path"] = str(self.tmp_path / name)
        path = create_minimal_ttf(**kwargs)
        self.created_fonts.append(path)
        return path

    def create_family(self, family: str = "Roboto", styles: list = None,
                      weight: int = 400) -> list:
        """Create a complete font family with multiple styles."""
        if styles is None:
            styles = ["Regular", "Bold", "Italic", "Bold Italic"]

        weight_map = {
            "Regular": 400,
            "Bold": 700,
            "Italic": 400,
            "Bold Italic": 700,
            "Light": 300,
            "Medium": 500,
            "SemiBold": 600,
            "ExtraBold": 800,
        }

        paths = []
        for style in styles:
            w = weight_map.get(style, weight)
            path = self.create_ttf(family=family, style=style, weight=w)
            paths.append(path)
        return paths
