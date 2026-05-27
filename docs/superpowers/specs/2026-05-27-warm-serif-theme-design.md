# Warm Serif Theme for FastPub

Extract the design style from "Digital Nudges & Recommender Systems for Obesity Prevention" (Forberger et al., IJMR 2026) and apply it as FastPub's default theme for web and slide outputs via a standalone theme module.

## Design Tokens

### Colors

| Token | Hex | Usage |
|---|---|---|
| `bg` | `#F2EDE8` | Light slide/web background (linen) |
| `bg_dark` | `#2E2A26` | Dark slides, web header (warm charcoal) |
| `fg` | `#2E2A26` | Text on light backgrounds |
| `fg_light` | `#F2EDE8` | Text on dark backgrounds |
| `primary` | `#9B6B3D` | Section labels, accent lines, sub-issue titles (copper) |
| `accent` | `#B85C3A` | Large callout stats, alert data (terra cotta) |
| `muted` | `#8A8480` | Secondary text on dark backgrounds |
| `chart_neutral` | `#D5CFC9` | Bar chart backgrounds, table borders, left-border lines |
| `chart_colors` | `["#2E2A26", "#9B6B3D", "#D5CFC9", "#B85C3A"]` | 4-color system for charts (black, copper, gray, terra cotta) |

### Typography

| Token | Value | Usage |
|---|---|---|
| `font_heading` | `'Playfair Display', Georgia, serif` | All headings, callout stats, hook quotes |
| `font_body` | `'Inter', -apple-system, sans-serif` | Body text, labels, bullets |
| `font_import_url` | Google Fonts URL for Playfair Display (400;700;900) + Inter (400;500;600;700) | `<link>` tag in output HTML |
| `slide_label_tracking` | `0.12em` | Letter-spacing for uppercase section labels |

### Visual Elements

- **Copper accent line:** 48px wide, 3px tall, `primary` color, placed below titles as separator
- **Section labels (slides):** Inter, uppercase, `0.12em` letter-spacing, `primary` color
- **Tag pills:** `primary`-colored border, no fill, 4px border-radius
- **Callout numbers:** Playfair Display, large size, `accent` color
- **Numbered lists (dark slides):** Muted large numbers (01, 02...) with bold title + description

## Architecture

### New file: `fastpub/render/theme.py`

```python
@dataclass
class ThemeTokens:
    # Colors
    bg: str
    bg_dark: str
    fg: str
    fg_light: str
    primary: str
    accent: str
    muted: str
    chart_neutral: str
    chart_colors: list[str]
    # Typography
    font_heading: str
    font_body: str
    font_import_url: str
    # Slides
    slide_label_tracking: str

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
```

Functions:
- `build_web_css(theme: ThemeTokens) -> str` — generates full CSS for web output
- `build_slide_css(theme: ThemeTokens) -> str` — generates full CSS for slide output
- `font_import_tag(theme: ThemeTokens) -> str` — returns `<link>` tag for font import

### Changes to `fastpub/render/web.py`

- Delete `_build_styles()` function
- Import `WARM_SERIF`, `build_web_css`, `font_import_tag` from `theme`
- Replace `_build_styles()` call with `build_web_css(WARM_SERIF)` and `font_import_tag(WARM_SERIF)`
- Remove section type badges from `_build_section_html()` — drop the `<span class="badge">` element
- Change sub-issue rendering: replace bordered card divs with plain text under a left border line (2px solid `chart_neutral`, 16px left padding)
- Remove `@media (prefers-color-scheme: dark)` — single light theme only
- Header becomes a dark band: title, authors, venue, keywords on `bg_dark` background
- Keywords use bordered pills (`primary` border, no fill) instead of filled accent pills
- Hook blockquote uses `primary` left border with Playfair italic text

### Changes to `fastpub/render/slides.py`

- Delete `_build_styles()` function
- Import `WARM_SERIF`, `build_slide_css`, `font_import_tag` from `theme`
- Replace `_build_styles()` call with `build_slide_css(WARM_SERIF)` and `font_import_tag(WARM_SERIF)`
- Replace `DM Sans` / `DM Mono` font imports with theme's `font_import_url`

**Slide layout changes in `_content_slide()`:**
- Title area is always full-width at the top: section label + serif title + copper accent line
- Below the title, content splits into left-right two columns: visualization/data on the left, commentary/captions on the right
- When there is no visualization (bullets-only slide), the left-right split still applies: bullets left, body text or explanation right

**Title and closing slides (`_title_slide`, `_closing_slide`):**
- Remain full-width, no left-right split
- Dark background (`bg_dark`)
- Title slide: bottom-anchored with copper accent line above title
- Closing slide: centered with summary stats
- Remove decorative SVG circles/rectangles from both

**CSS variable mapping (slide):**
- `--c-bg` → `theme.bg`
- `--c-bg-dark` → `theme.bg_dark`
- `--c-bg-accent` → removed (use `bg_dark` for all dark slides)
- `--c-text` → `theme.fg`
- `--c-text-light` → `theme.fg_light`
- `--c-text-muted` → `theme.muted`
- `--c-primary` → `theme.primary`
- `--c-primary-light` → `theme.chart_neutral`
- `--c-accent` → `theme.accent`
- `--c-accent-light` → light tint of `theme.accent` (e.g., `#FEF0EA`)
- `--font` → `theme.font_body`
- `--font-heading` → new variable for `theme.font_heading`

**Visualization renderers:** No structural changes. They already use CSS vars (`var(--c-primary)`, `var(--c-accent)`, etc.) which will pick up the new colors automatically. The `default_colors` lists in donut, proportion, stacked_bar, and area_blocks renderers should be updated to use `theme.chart_colors` instead of hardcoded teal/coral values.

### Unchanged files

- `fastpub/render/templates/deck-stage.js` — no changes
- `fastpub/models.py` — no changes
- `fastpub/pipeline/*` — no changes
- `fastpub/render/templates/paper.html` — unused by web.py (builds HTML directly), can be left as-is

## Contrast Rules

All text must have sufficient contrast:
- On `bg` (#F2EDE8): use `fg` (#2E2A26) for body text, `primary` (#9B6B3D) for accent text only when bold/large
- On `bg_dark` (#2E2A26): use `fg_light` (#F2EDE8) for primary text, `muted` (#8A8480) for secondary metadata only
- Never use `muted` on light backgrounds
- Callout numbers in `accent` (#B85C3A) are only used at large sizes where contrast is less critical

## Testing

- Run `uv run fastpub go <pdf> -f web` and verify the web output matches the approved mockup
- Run `uv run fastpub go <pdf> -f slides` and verify slides match the approved layouts
- Verify all 12 visualization types render correctly with the new color palette
- Check that the lang toggle (EN/中文) still works in the web output
