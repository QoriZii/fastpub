from fastpub.render.theme import ThemeTokens, WARM_SERIF, build_web_css, build_slide_css, font_import_tag


def test_warm_serif_has_all_colors():
    assert WARM_SERIF.bg == "#F2EDE8"
    assert WARM_SERIF.bg_dark == "#2E2A26"
    assert WARM_SERIF.fg == "#1A1208"
    assert WARM_SERIF.fg_light == "#F2EDE8"
    assert WARM_SERIF.primary == "#9B6B3D"
    assert WARM_SERIF.accent == "#B85C3A"
    assert WARM_SERIF.muted == "#6B6662"
    assert WARM_SERIF.chart_neutral == "#B8B0A8"
    assert len(WARM_SERIF.chart_colors) == 4


def test_warm_serif_has_typography():
    assert "Lora" in WARM_SERIF.font_heading
    assert "Nunito Sans" in WARM_SERIF.font_body
    assert "fonts.googleapis.com" in WARM_SERIF.font_import_url


def test_font_import_tag_returns_link():
    tag = font_import_tag(WARM_SERIF)
    assert tag.startswith("<link")
    assert WARM_SERIF.font_import_url in tag


def test_build_web_css_contains_tokens():
    css = build_web_css(WARM_SERIF)
    assert "<style>" in css
    assert WARM_SERIF.bg in css
    assert WARM_SERIF.fg in css
    assert WARM_SERIF.primary in css
    assert "prefers-color-scheme" in css
    assert "--accent" in css


def test_build_slide_css_contains_tokens():
    css = build_slide_css(WARM_SERIF)
    assert "<style>" in css
    assert "--c-bg:" in css
    assert WARM_SERIF.bg in css
    assert WARM_SERIF.primary in css
    assert "--font-heading:" in css
    assert "Lora" in css
    assert "--c-bg-accent" not in css
