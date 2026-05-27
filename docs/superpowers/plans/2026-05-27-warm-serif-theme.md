# Warm Serif Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the visual style from the "Digital Nudges" PDF and apply it as FastPub's default theme via a standalone `theme.py` module, updating both web and slide renderers.

**Architecture:** New `fastpub/render/theme.py` holds a `ThemeTokens` dataclass and CSS generator functions. Both `web.py` and `slides.py` delete their `_build_styles()` and import from `theme.py`. Slide layout changes to title-on-top with left-right content below.

**Tech Stack:** Python 3.11+, dataclasses, HTML/CSS generation, Google Fonts (Playfair Display + Inter)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `fastpub/render/theme.py` | Create | ThemeTokens dataclass, WARM_SERIF instance, CSS generators |
| `fastpub/render/web.py` | Modify | Import theme, delete `_build_styles`, restyle HTML structure |
| `fastpub/render/slides.py` | Modify | Import theme, delete `_build_styles`, two-column layout, update default_colors |
| `tests/test_theme.py` | Create | Unit tests for theme module |
| `tests/test_web_render.py` | Create | Tests for web renderer output |
| `tests/test_slide_render.py` | Create | Tests for slide renderer output |

---

### Task 1: Create theme.py with ThemeTokens and WARM_SERIF

**Files:**
- Create: `fastpub/render/theme.py`
- Create: `tests/test_theme.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_theme.py`:

```python
from fastpub.render.theme import ThemeTokens, WARM_SERIF, build_web_css, build_slide_css, font_import_tag


def test_warm_serif_has_all_colors():
    assert WARM_SERIF.bg == "#F2EDE8"
    assert WARM_SERIF.bg_dark == "#2E2A26"
    assert WARM_SERIF.fg == "#2E2A26"
    assert WARM_SERIF.fg_light == "#F2EDE8"
    assert WARM_SERIF.primary == "#9B6B3D"
    assert WARM_SERIF.accent == "#B85C3A"
    assert WARM_SERIF.muted == "#8A8480"
    assert WARM_SERIF.chart_neutral == "#D5CFC9"
    assert len(WARM_SERIF.chart_colors) == 4


def test_warm_serif_has_typography():
    assert "Playfair Display" in WARM_SERIF.font_heading
    assert "Inter" in WARM_SERIF.font_body
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
    assert "Playfair Display" in css
    assert "Inter" in css
    # No dark mode media query
    assert "prefers-color-scheme" not in css


def test_build_slide_css_contains_tokens():
    css = build_slide_css(WARM_SERIF)
    assert "<style>" in css
    assert "--c-bg:" in css
    assert WARM_SERIF.bg in css
    assert WARM_SERIF.primary in css
    assert "--font-heading:" in css
    assert "Playfair Display" in css
    # No accent background (removed per spec)
    assert "--c-bg-accent" not in css
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/qin/Apps/fastpub-py && uv run pytest tests/test_theme.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'fastpub.render.theme'`

- [ ] **Step 3: Create theme.py**

Create `fastpub/render/theme.py`:

```python
"""Design token system for FastPub output themes."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ThemeTokens:
    """All design tokens needed to style web and slide outputs."""
    # Colors
    bg: str
    bg_dark: str
    fg: str
    fg_light: str
    primary: str
    accent: str
    muted: str
    chart_neutral: str
    chart_colors: list[str] = field(default_factory=list)
    # Typography
    font_heading: str = ""
    font_body: str = ""
    font_import_url: str = ""
    # Slides
    slide_label_tracking: str = "0.12em"


WARM_SERIF = ThemeTokens(
    bg="#F2EDE8",
    bg_dark="#2E2A26",
    fg="#2E2A26",
    fg_light="#F2EDE8",
    primary="#9B6B3D",
    accent="#B85C3A",
    muted="#8A8480",
    chart_neutral="#D5CFC9",
    chart_colors=["#2E2A26", "#9B6B3D", "#D5CFC9", "#B85C3A"],
    font_heading="'Playfair Display', Georgia, serif",
    font_body="'Inter', -apple-system, sans-serif",
    font_import_url="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@400;500;600;700&display=swap",
    slide_label_tracking="0.12em",
)


def font_import_tag(theme: ThemeTokens) -> str:
    """Return a <link> tag for importing web fonts."""
    return f'<link href="{theme.font_import_url}" rel="stylesheet">'


def build_web_css(theme: ThemeTokens) -> str:
    """Generate the full <style> block for web page output."""
    return f"""<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: {theme.font_body};
    background: {theme.bg}; color: {theme.fg};
    line-height: 1.7; margin: 0;
  }}
  header {{
    background: {theme.bg_dark}; padding: 3rem 3rem 2.5rem;
  }}
  header .inner {{ max-width: 720px; }}
  h1 {{
    font-family: {theme.font_heading}; font-size: 1.75rem;
    font-weight: 700; line-height: 1.2; color: {theme.fg_light};
    margin-bottom: 0.5rem;
  }}
  .accent-line {{
    width: 48px; height: 3px; background: {theme.primary};
    border-radius: 2px; margin: 1rem 0;
  }}
  .authors {{ color: {theme.muted}; font-size: 0.85rem; }}
  .venue {{ color: {theme.muted}; font-size: 0.8rem; font-style: italic; margin-top: 0.25rem; }}
  .keywords {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.75rem; }}
  .tag {{
    border: 1px solid {theme.primary}; color: {theme.primary};
    padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.7rem;
  }}

  .lang-toggle {{
    display: flex; gap: 4px; margin-bottom: 1.5rem;
  }}
  .lang-toggle button {{
    border: none; padding: 0.35rem 0.75rem; border-radius: 4px;
    cursor: pointer; font-size: 0.8rem; font-weight: 600;
    background: transparent; color: {theme.muted};
    border: 1px solid {theme.muted};
  }}
  .lang-toggle button.active {{
    background: {theme.primary}; color: {theme.fg_light};
    border-color: {theme.primary};
  }}

  .hook blockquote {{
    font-family: {theme.font_heading}; font-size: 1.1rem;
    font-style: italic; border-left: 3px solid {theme.primary};
    padding: 0.75rem 1.25rem; margin: 0;
    background: rgba(155,107,61,0.06); border-radius: 0 8px 8px 0;
    color: {theme.fg};
  }}

  .content {{ max-width: 720px; padding: 0 3rem; }}
  .abstract, .web-section, .figures {{ margin: 2rem 0; }}
  h2 {{
    font-family: {theme.font_heading}; font-size: 1.3rem;
    font-weight: 700; margin-bottom: 0.5rem; color: {theme.fg};
  }}
  .section-summary {{
    font-size: 0.9rem; line-height: 1.7; margin-bottom: 1rem;
    color: {theme.fg};
  }}

  .sub-issues {{
    display: flex; flex-direction: column; gap: 0.85rem;
    padding-left: 1rem; border-left: 2px solid {theme.chart_neutral};
  }}
  .sub-issue h4 {{
    font-size: 0.85rem; font-weight: 600; margin-bottom: 0.15rem;
    color: {theme.primary};
  }}
  .sub-issue p {{ font-size: 0.8rem; color: {theme.fg}; line-height: 1.6; }}

  .figure-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
  figure {{ overflow: hidden; }}
  figure img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
  figcaption {{ padding: 0.5rem 0; font-size: 0.8rem; color: {theme.fg}; }}
  .ai-desc {{ color: {theme.muted}; margin-top: 0.2rem; font-size: 0.75rem; }}

  footer {{
    margin-top: 3rem; padding: 1.5rem 3rem;
    border-top: 1px solid {theme.chart_neutral};
    color: {theme.muted}; font-size: 0.75rem;
  }}
</style>"""


def build_slide_css(theme: ThemeTokens) -> str:
    """Generate the full <style> block for slide deck output."""
    return f"""<style>
  :root {{
    /* Type scale */
    --type-title: 64px;
    --type-subtitle: 44px;
    --type-body: 34px;
    --type-small: 28px;
    --type-label: 24px;

    /* Spacing */
    --pad-top: 100px;
    --pad-bottom: 80px;
    --pad-x: 100px;
    --gap-title: 52px;
    --gap-item: 28px;

    /* Colors */
    --c-bg: {theme.bg};
    --c-bg-dark: {theme.bg_dark};
    --c-text: {theme.fg};
    --c-text-light: {theme.fg_light};
    --c-text-muted: {theme.muted};
    --c-primary: {theme.primary};
    --c-primary-light: {theme.chart_neutral};
    --c-accent: {theme.accent};
    --c-accent-light: #FEF0EA;

    /* Font */
    --font: {theme.font_body};
    --font-heading: {theme.font_heading};
  }}

  deck-stage {{
    font-family: var(--font);
  }}

  section {{
    background: var(--c-bg);
    color: var(--c-text);
    transition: opacity 0.4s ease;
  }}

  .slide-pad {{
    padding: var(--pad-top) var(--pad-x) var(--pad-bottom);
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
  }}

  .slide-pad.dark {{
    background: var(--c-bg-dark);
    color: var(--c-text-light);
  }}

  .slide-title {{
    font-family: var(--font-heading);
    font-size: var(--type-title);
    font-weight: 700;
    line-height: 1.15;
    margin: 0;
    letter-spacing: -0.02em;
  }}

  .slide-subtitle {{
    font-size: var(--type-subtitle);
    font-weight: 400;
    line-height: 1.35;
    margin: 0;
    color: var(--c-text-muted);
  }}

  .dark .slide-subtitle {{
    color: var(--c-text-muted);
  }}

  .slide-body {{
    font-size: var(--type-body);
    line-height: 1.5;
    margin: 0;
  }}

  .label {{
    font-family: var(--font);
    font-size: var(--type-label);
    text-transform: uppercase;
    letter-spacing: {theme.slide_label_tracking};
    color: var(--c-primary);
    margin: 0;
  }}

  .dark .label {{
    color: var(--c-primary);
  }}

  .accent-line {{
    width: 48px;
    height: 3px;
    background: var(--c-primary);
    border-radius: 2px;
  }}

  .stat-card {{
    background: white;
    border-radius: 16px;
    padding: 40px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }}
  .dark .stat-card {{
    background: rgba(255,255,255,0.08);
  }}
  .stat-card .stat-num {{
    font-family: var(--font-heading);
    font-size: 80px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.03em;
  }}
  .stat-card .stat-label {{
    font-size: var(--type-small);
    line-height: 1.35;
    color: var(--c-text-muted);
  }}
  .dark .stat-card .stat-label {{
    color: rgba(255,255,255,0.55);
  }}
</style>"""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/qin/Apps/fastpub-py && uv run pytest tests/test_theme.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add fastpub/render/theme.py tests/test_theme.py
git commit -m "feat: add theme.py with ThemeTokens and CSS generators"
```

---

### Task 2: Restyle web.py to use theme

**Files:**
- Modify: `fastpub/render/web.py`
- Create: `tests/test_web_render.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_web_render.py`:

```python
from fastpub.models import PaperDocument, PaperMeta, WebSection, SubIssue
from fastpub.render.web import _build_html


def _make_doc():
    return PaperDocument(
        meta=PaperMeta(
            title="Test Paper",
            authors=["Alice", "Bob"],
            venue="Test Journal",
            year=2026,
            abstract="An abstract.",
            keywords=["kw1", "kw2"],
        ),
        hook="This matters because...",
        web_sections=[
            WebSection(
                type="problem",
                summary="A summary.",
                sub_issues=[SubIssue(title="Issue 1", description="Desc 1")],
            ),
        ],
    )


def _make_zh():
    return {
        "meta": {"title": "测试论文", "abstract": "摘要"},
        "hook": "这很重要因为...",
        "webSections": [
            {"type": "problem", "summary": "总结", "subIssues": [{"title": "问题1", "description": "描述1"}]}
        ],
    }


def test_web_uses_warm_serif_colors():
    html = _build_html(_make_doc(), _make_zh())
    assert "#F2EDE8" in html  # linen bg
    assert "#9B6B3D" in html  # copper primary
    assert "#2E2A26" in html  # charcoal
    assert "Playfair Display" in html
    assert "Inter" in html


def test_web_no_dark_mode():
    html = _build_html(_make_doc(), _make_zh())
    assert "prefers-color-scheme" not in html


def test_web_no_section_badges():
    html = _build_html(_make_doc(), _make_zh())
    assert 'class="badge' not in html


def test_web_sub_issues_no_card_border():
    html = _build_html(_make_doc(), _make_zh())
    # Sub-issues should use left border line, not card divs
    assert "border-left: 2px solid" in html or "border-left:2px solid" in html or "sub-issues" in html
    # No card-style borders on individual sub-issues
    assert "border-radius: 8px" not in html or ".sub-issue" not in html.split("border-radius: 8px")[0].split("</style>")[-1]


def test_web_header_is_dark_band():
    html = _build_html(_make_doc(), _make_zh())
    # Header should have dark background
    assert '<header' in html
    # The CSS should style header with bg_dark
    assert "#2E2A26" in html


def test_web_keywords_bordered_pills():
    html = _build_html(_make_doc(), _make_zh())
    assert "kw1" in html
    # Tags should have border style, not filled background
    css_section = html.split("<style>")[1].split("</style>")[0]
    assert "border:" in css_section or "border: 1px solid" in css_section


def test_web_lang_toggle_works():
    html = _build_html(_make_doc(), _make_zh())
    assert "setLang" in html
    assert 'id="btn-en"' in html
    assert 'id="btn-zh"' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/qin/Apps/fastpub-py && uv run pytest tests/test_web_render.py -v`
Expected: FAIL — current web.py still uses old blue/teal styles

- [ ] **Step 3: Modify web.py**

Apply these changes to `fastpub/render/web.py`:

1. Add import at top:
```python
from fastpub.render.theme import WARM_SERIF, build_web_css, font_import_tag
```

2. Delete `_SECTION_ICONS` dict (lines 52-58) — unused after badge removal.

3. Delete `_build_styles()` function (lines 218-301).

4. Replace `_build_section_html` — remove badge span, change sub-issue markup to plain text with left border:

```python
def _build_section_html(s: WebSection, zh_s: dict) -> str:
    en_label, zh_label = _SECTION_LABELS.get(s.type, (s.type.title(), s.type.title()))
    zh_summary = zh_s.get("summary", s.summary)
    zh_sub_issues = zh_s.get("subIssues", zh_s.get("sub_issues", []))

    sub_items = []
    for i, si in enumerate(s.sub_issues):
        zh_si = zh_sub_issues[i] if i < len(zh_sub_issues) else {}
        sub_items.append(f"""<div class="sub-issue">
      <h4>
        <span class="en">{_esc(si.title)}</span>
        <span class="zh" hidden>{_esc(zh_si.get("title", si.title))}</span>
      </h4>
      <p>
        <span class="en">{_esc(si.description)}</span>
        <span class="zh" hidden>{_esc(zh_si.get("description", si.description))}</span>
      </p>
    </div>""")

    sub_html = "\n    ".join(sub_items)

    return f"""<section class="web-section section-{s.type}">
  <h2>
    <span class="en">{en_label}</span>
    <span class="zh" hidden>{zh_label}</span>
  </h2>
  <div class="accent-line"></div>
  <p class="section-summary">
    <span class="en">{_esc(s.summary)}</span>
    <span class="zh" hidden>{_esc(zh_summary)}</span>
  </p>
  <div class="sub-issues">
    {sub_html}
  </div>
</section>"""
```

5. Replace `_build_html` — dark header band, no duplicate title, content wrapper:

```python
def _build_html(doc: PaperDocument, zh: dict[str, Any]) -> str:
    zh_meta = zh.get("meta", {})
    zh_hook = zh.get("hook", doc.hook)
    zh_web_sections = {s.get("type", ""): s for s in zh.get("webSections", zh.get("web_sections", []))}
    zh_figures = {f.get("id", ""): f for f in zh.get("figures", [])}
    figures = [f for f in _resolved_figures(doc)]

    theme = WARM_SERIF

    # Header parts
    venue_html = ""
    if doc.meta.venue:
        year_part = f" ({doc.meta.year})" if doc.meta.year else ""
        venue_html = f'  <p class="venue">{_esc(doc.meta.venue)}{year_part}</p>'

    keywords_html = ""
    if doc.meta.keywords:
        tags = " ".join(f'<span class="tag">{_esc(k)}</span>' for k in doc.meta.keywords)
        keywords_html = f'  <div class="keywords">{tags}</div>'

    # Web sections
    sections_html = "\n".join(
        _build_section_html(s, zh_web_sections.get(s.type, {}))
        for s in doc.web_sections
    )

    # Figures
    figures_html = _build_figures_html(figures, zh_figures) if figures else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(doc.meta.title)}</title>
{font_import_tag(theme)}
{build_web_css(theme)}
</head>
<body>

<header>
  <div class="inner">
    <nav class="lang-toggle">
      <button id="btn-en" class="active" onclick="setLang('en')">EN</button>
      <button id="btn-zh" onclick="setLang('zh')">中文</button>
    </nav>
    <h1>
      <span class="en">{_esc(doc.meta.title)}</span>
      <span class="zh" hidden>{_esc(zh_meta.get("title", doc.meta.title))}</span>
    </h1>
    <div class="accent-line"></div>
    <p class="authors">{_esc(", ".join(doc.meta.authors))}</p>
{venue_html}
{keywords_html}
  </div>
</header>

<div class="content">

<section class="hook">
  <blockquote>
    <span class="en">{_esc(doc.hook)}</span>
    <span class="zh" hidden>{_esc(zh_hook)}</span>
  </blockquote>
</section>

<section class="abstract">
  <h2>
    <span class="en">Abstract</span>
    <span class="zh" hidden>摘要</span>
  </h2>
  <div class="accent-line"></div>
  <p>
    <span class="en">{_esc(doc.meta.abstract)}</span>
    <span class="zh" hidden>{_esc(zh_meta.get("abstract", ""))}</span>
  </p>
</section>

{sections_html}

{figures_html}

</div>

<footer>
  <p>Generated by <strong>FastPub</strong></p>
</footer>

{_build_script()}
</body>
</html>"""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/qin/Apps/fastpub-py && uv run pytest tests/test_web_render.py tests/test_theme.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add fastpub/render/web.py tests/test_web_render.py
git commit -m "feat: restyle web renderer with warm serif theme"
```

---

### Task 3: Restyle slides.py — CSS and font import

**Files:**
- Modify: `fastpub/render/slides.py`
- Create: `tests/test_slide_render.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_slide_render.py`:

```python
from fastpub.models import PaperDocument, PaperMeta, WebSection, SubIssue
from fastpub.render.slides import render_slides
from pathlib import Path
import tempfile


def _make_doc():
    return PaperDocument(
        meta=PaperMeta(
            title="Test Paper",
            authors=["Alice"],
            venue="Test Venue",
            year=2026,
            abstract="Abstract text.",
        ),
        hook="Why this matters.",
        web_sections=[
            WebSection(
                type="problem",
                summary="Problem summary.",
                sub_issues=[SubIssue(title="Sub 1", description="Desc 1")],
            ),
        ],
    )


def test_slides_use_warm_serif_colors():
    doc = _make_doc()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.slides.html"
        render_slides(doc, out)
        html = out.read_text()
    assert "#F2EDE8" in html  # linen bg
    assert "#9B6B3D" in html  # copper primary
    assert "Playfair Display" in html
    assert "Inter" in html


def test_slides_no_dm_sans():
    doc = _make_doc()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.slides.html"
        render_slides(doc, out)
        html = out.read_text()
    assert "DM+Sans" not in html
    assert "DM+Mono" not in html


def test_slides_no_accent_bg():
    doc = _make_doc()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.slides.html"
        render_slides(doc, out)
        html = out.read_text()
    assert "--c-bg-accent" not in html


def test_slides_have_font_heading_var():
    doc = _make_doc()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.slides.html"
        render_slides(doc, out)
        html = out.read_text()
    assert "--font-heading:" in html


def test_slides_title_no_svg_decorations():
    doc = _make_doc()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.slides.html"
        render_slides(doc, out)
        html = out.read_text()
    assert "<svg" not in html


def test_slides_content_has_accent_line():
    doc = _make_doc()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.slides.html"
        render_slides(doc, out)
        html = out.read_text()
    assert "accent-line" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/qin/Apps/fastpub-py && uv run pytest tests/test_slide_render.py -v`
Expected: Several FAIL — old colors, DM Sans still present, SVGs still present

- [ ] **Step 3: Modify slides.py — CSS and font import**

Apply these changes:

1. Add import at top of `slides.py`:
```python
from fastpub.render.theme import WARM_SERIF, build_slide_css, font_import_tag
```

2. Delete `_build_styles()` function (lines 870-1004).

3. Remove `_BG_STYLES` entry for `"accent"` and `"significance"` — map them to `"dark"` instead:
```python
_BG_STYLES = {
    "title": "dark",
    "closing": "dark",
    "significance": "dark",
    "accent": "dark",
    "dark": "dark",
}
```

4. In `_build_html()` (line 837-863), replace the font `<link>` tag and `_build_styles()` call:

Replace line 844:
```python
    # Old: <link href="https://fonts.googleapis.com/css2?family=DM+Sans...
```
with:
```python
{font_import_tag(WARM_SERIF)}
```

Replace line 850 (`{_build_styles()}`):
```python
{build_slide_css(WARM_SERIF)}
```

5. Update `default_colors` in `_render_donut_chart` (line 283), `_render_proportion` (line 451), `_render_area_blocks` (line 502), and `_render_stacked_bar` (line 570):

Change all four from:
```python
default_colors = ["#0d7c7f", "#d97757", "#6366f1", "#16a34a", "#f59e0b", "#ec4899"]
```
to:
```python
default_colors = WARM_SERIF.chart_colors
```

(For `_render_proportion` line 451 which has 5 items, same change — `WARM_SERIF.chart_colors` has 4 items which is fine since they cycle via `i % len()`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/qin/Apps/fastpub-py && uv run pytest tests/test_slide_render.py tests/test_theme.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add fastpub/render/slides.py tests/test_slide_render.py
git commit -m "feat: restyle slide CSS with warm serif theme"
```

---

### Task 4: Refactor slide layouts — title on top, left-right below

**Files:**
- Modify: `fastpub/render/slides.py`
- Modify: `tests/test_slide_render.py`

- [ ] **Step 1: Add layout tests**

Append to `tests/test_slide_render.py`:

```python
def test_slides_content_has_two_column_layout():
    """Content slides should have title on top, then left-right columns below."""
    doc = _make_doc()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.slides.html"
        render_slides(doc, out)
        html = out.read_text()
    # Should contain the two-column flex container
    assert "slide-columns" in html


def test_slides_title_slide_bottom_anchored():
    """Title slide should be bottom-anchored with accent line."""
    doc = _make_doc()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.slides.html"
        render_slides(doc, out)
        html = out.read_text()
    # Title slide should justify to flex-end
    assert "flex-end" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/qin/Apps/fastpub-py && uv run pytest tests/test_slide_render.py::test_slides_content_has_two_column_layout -v`
Expected: FAIL — `"slide-columns"` not in html

- [ ] **Step 3: Refactor _title_slide**

Replace `_title_slide` in `slides.py`:

```python
def _title_slide(slide: _Slide, index: int) -> str:
    subtitle_html = ""
    if slide.bullets:
        subtitle_html = "\n".join(
            f'      <p class="slide-subtitle">{_esc(b)}</p>' for b in slide.bullets
        )

    return f"""  <section data-label="{_esc(f'{index+1:02d} Title')}">
    <div class="slide-pad dark" style="justify-content: flex-end; gap: 32px;">
      <div class="accent-line"></div>
      <h1 class="slide-title" style="font-size: 72px; max-width: 1400px;">{_esc(slide.title)}</h1>
{subtitle_html}
    </div>
  </section>"""
```

- [ ] **Step 4: Refactor _closing_slide**

Replace `_closing_slide` in `slides.py`:

```python
def _closing_slide(slide: _Slide, index: int) -> str:
    body_html = ""
    if slide.body:
        body_html = f'      <p style="font-size: var(--type-body); color: var(--c-text-muted); margin: 0; max-width: 900px;">{_esc(slide.body)}</p>'

    return f"""  <section data-label="{_esc(f'{index+1:02d} {slide.label}')}">
    <div class="slide-pad dark" style="justify-content: center; align-items: center; gap: 40px; text-align: center;">
      <div class="accent-line"></div>
      <h2 class="slide-title" style="font-size: 56px; max-width: 1200px;">{_esc(slide.title)}</h2>
{body_html}
    </div>
  </section>"""
```

- [ ] **Step 5: Refactor _content_slide — title on top, two columns below**

Replace `_content_slide` in `slides.py`:

```python
def _content_slide(slide: _Slide, index: int, bg_class: str) -> str:
    has_image = slide.figure_src is not None
    has_bullets = bool(slide.bullets)
    has_body = bool(slide.body)

    # Build left column (visualization / data)
    left_parts = []

    if has_body and not has_bullets:
        if slide.body_is_html:
            left_parts.append(f'        {slide.body}')
        else:
            left_parts.append(
                f'        <p class="slide-body">{_esc(slide.body)}</p>'
            )

    if has_bullets:
        items = []
        for b in slide.bullets:
            items.append(f"""            <div style="display: flex; gap: 16px; align-items: flex-start;">
              <span style="color: var(--c-accent); font-size: 28px; line-height: 1; margin-top: 4px; flex-shrink: 0;">&#9679;</span>
              <span style="font-size: var(--type-body); line-height: 1.5;">{_esc(b)}</span>
            </div>""")
        left_parts.append(
            '        <div style="display: flex; flex-direction: column; gap: var(--gap-item);">\n'
            + "\n".join(items)
            + "\n        </div>"
        )

    # Build right column (commentary / image)
    right_parts = []

    if has_image:
        cap = ""
        if slide.figure_caption:
            cap = f'\n            <figcaption style="font-size: var(--type-label); color: var(--c-text-muted); margin-top: 12px;">{_esc(slide.figure_caption)}</figcaption>'
        right_parts.append(f"""        <figure style="max-width: 100%; text-align: center;">
            <img src="{_esc(slide.figure_src or "")}" alt="{_esc(slide.figure_caption or slide.title)}" style="max-width: 100%; max-height: 560px; object-fit: contain; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.12);">{cap}
          </figure>""")

    # If we only have left content and no right, still use two-column but right is empty
    left_html = chr(10).join(left_parts) if left_parts else ""
    right_html = chr(10).join(right_parts) if right_parts else ""

    body_html = f"""    <div class="slide-columns" style="display: flex; gap: 64px; flex: 1; align-items: center; margin-top: 16px;">
      <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 24px;">
{left_html}
      </div>
      <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 24px;">
{right_html}
      </div>
    </div>"""

    return f"""  <section data-label="{_esc(f'{index+1:02d} {slide.label or slide.slide_type.title()}')}">
    <div class="slide-pad{bg_class}" style="gap: var(--gap-title);">
      <div>
        <p class="label">{_esc(slide.label)}</p>
        <h2 class="slide-title">{_esc(slide.title)}</h2>
        <div class="accent-line" style="margin-top: 16px;"></div>
      </div>
{body_html}
    </div>
  </section>"""
```

- [ ] **Step 6: Run all tests**

Run: `cd /Users/qin/Apps/fastpub-py && uv run pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add fastpub/render/slides.py tests/test_slide_render.py
git commit -m "feat: refactor slide layouts — title on top, two-column below"
```

---

### Task 5: Integration test with real PDF

**Files:**
- No new files

- [ ] **Step 1: Run web render on existing analysis**

Run: `cd /Users/qin/Apps/fastpub-py && uv run fastpub render examples/ijmr-2026-1-e73151.analysis.json -f web -o /tmp/test-web.html`

Open `/tmp/test-web.html` in a browser and verify:
- Dark header band with linen body
- Playfair Display headings, Inter body text
- Copper accent lines under section titles
- No section badges
- Sub-issues as plain text with left border
- Bordered keyword pills
- Lang toggle works

- [ ] **Step 2: Run slide render on existing analysis**

Run: `cd /Users/qin/Apps/fastpub-py && uv run fastpub render examples/ijmr-2026-1-e73151.analysis.json -f slides -o /tmp/test-slides.html`

Open `/tmp/test-slides.html` in a browser and verify:
- Linen slide background, warm charcoal dark slides
- Playfair Display headings
- Copper section labels and accent lines
- Title on top, two-column content below
- No decorative SVGs on title/closing
- Bar charts, donut charts, etc. use the warm 4-color palette

- [ ] **Step 3: Commit any final fixes**

If any adjustments are needed, fix and commit:
```bash
git add -u
git commit -m "fix: polish warm serif theme after integration test"
```
