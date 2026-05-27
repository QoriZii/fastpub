from dataclasses import dataclass, field


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

    # Misc
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


def font_import_tag(theme: ThemeTokens) -> str:
    return f'<link href="{theme.font_import_url}" rel="stylesheet">'


def build_web_css(theme: ThemeTokens) -> str:
    return f"""<style>
body {{
  font-family: {theme.font_body};
  background: {theme.bg};
  color: {theme.fg};
  line-height: 1.7;
  margin: 0;
  padding: 0;
}}
header {{
  background: {theme.bg_dark};
  padding: 3rem;
}}
h1 {{
  font-family: {theme.font_heading};
  color: {theme.fg_light};
  font-size: 1.75rem;
  margin: 0 0 1rem;
}}
.accent-line {{
  width: 48px;
  height: 3px;
  background: {theme.primary};
  margin: 1rem 0;
}}
.authors,
.venue {{
  color: {theme.muted};
}}
.tag {{
  border: 1px solid {theme.primary};
  color: {theme.primary};
  background: transparent;
  border-radius: 4px;
  padding: 0.15rem 0.5rem;
  font-size: 0.8rem;
  display: inline-block;
}}
.lang-toggle button.active {{
  background: {theme.primary};
  color: {theme.fg_light};
}}
.hook blockquote {{
  font-family: {theme.font_heading};
  font-style: italic;
  border-left: 3px solid {theme.primary};
  padding-left: 1rem;
  margin: 1rem 0;
}}
h2 {{
  font-family: {theme.font_heading};
  color: {theme.fg};
}}
.sub-issues {{
  display: flex;
  flex-direction: column;
  padding-left: 1rem;
  border-left: 2px solid {theme.chart_neutral};
}}
.sub-issue h4 {{
  color: {theme.primary};
  margin: 0 0 0.25rem;
}}
.sub-issue p {{
  color: {theme.fg};
  margin: 0 0 0.5rem;
}}
footer {{
  border-top: 1px solid {theme.chart_neutral};
  color: {theme.muted};
  padding: 1rem;
}}
</style>"""


def build_slide_css(theme: ThemeTokens) -> str:
    return f"""<style>
:root {{
  --c-bg: {theme.bg};
  --c-bg-dark: {theme.bg_dark};
  --c-text: {theme.fg};
  --c-text-light: {theme.fg_light};
  --c-text-muted: {theme.muted};
  --c-primary: {theme.primary};
  --c-primary-light: {theme.chart_neutral};
  --c-accent: {theme.accent};
  --c-accent-light: #FEF0EA;
  --font: {theme.font_body};
  --font-heading: {theme.font_heading};

  /* Type scale */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;

  /* Slide padding */
  --slide-pad: 3rem;
}}

body {{
  font-family: var(--font);
  background: var(--c-bg);
  color: var(--c-text);
  margin: 0;
  padding: 0;
}}

.slide {{
  background: var(--c-bg);
  padding: var(--slide-pad);
  min-height: 100vh;
  box-sizing: border-box;
}}

.slide.dark {{
  background: var(--c-bg-dark);
  color: var(--c-text-light);
}}

.slide-title {{
  font-family: var(--font-heading);
  color: var(--c-text);
  font-size: var(--text-3xl);
  line-height: 1.2;
  margin: 0 0 var(--space-4);
}}

.dark .slide-title {{
  color: var(--c-text-light);
}}

.label {{
  font-family: var(--font);
  letter-spacing: {theme.slide_label_tracking};
  text-transform: uppercase;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--c-text-muted);
}}

.dark .label {{
  color: var(--c-primary);
}}

.accent-line {{
  width: 48px;
  height: 3px;
  background: var(--c-primary);
  margin: var(--space-3) 0;
}}

.stat-card {{
  background: var(--c-bg);
  border: 1px solid var(--c-primary-light);
  border-radius: 8px;
  padding: var(--space-4);
}}

.stat-card .stat-num {{
  font-family: var(--font-heading);
  font-size: var(--text-4xl);
  font-weight: 700;
  color: var(--c-primary);
  line-height: 1;
}}

.stat-card .stat-label {{
  font-family: var(--font);
  font-size: var(--text-sm);
  color: var(--c-text-muted);
  margin-top: var(--space-1);
}}
</style>"""
