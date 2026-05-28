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
    font_mono: str
    font_import_url: str

    # Misc
    slide_label_tracking: str


WARM_SERIF = ThemeTokens(
    bg="#F2EDE8",
    bg_dark="#2E2A26",
    fg="#1A1208",
    fg_light="#F2EDE8",
    primary="#9B6B3D",
    accent="#B85C3A",
    muted="#6B6662",
    chart_neutral="#B8B0A8",
    chart_colors=["#1A1208", "#9B6B3D", "#8A7F77", "#B85C3A"],
    font_heading="'Lora', Georgia, serif",
    font_body="'Nunito Sans', -apple-system, sans-serif",
    font_mono="'JetBrains Mono', 'SF Mono', monospace",
    font_import_url="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Lora:wght@400;700&family=Nunito+Sans:wght@300;400;600;700&display=swap",
    slide_label_tracking="0.12em",
)


def font_import_tag(theme: ThemeTokens) -> str:
    return f'<link href="{theme.font_import_url}" rel="stylesheet">'


def build_web_css(theme: ThemeTokens) -> str:
    return f"""<style>
  :root {{
    --bg: {theme.bg}; --fg: {theme.fg}; --accent: {theme.primary};
    --card-bg: #fff; --border: {theme.chart_neutral}; --muted: {theme.muted};
    --max-w: 800px;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: {theme.bg_dark}; --fg: {theme.fg_light}; --accent: {theme.accent};
      --card-bg: #3a3530; --border: #4a4540; --muted: #a09c98;
    }}
  }}
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg); color: var(--fg);
    line-height: 1.7; padding: 2rem 1rem; max-width: var(--max-w); margin: 0 auto;
  }}
  header {{ text-align: center; margin-bottom: 2.5rem; }}
  h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; line-height: 1.3; }}
  .authors {{ color: var(--muted); margin-bottom: 0.25rem; }}
  .venue {{ color: var(--muted); font-style: italic; margin-bottom: 0.5rem; }}
  .keywords {{ display: flex; flex-wrap: wrap; gap: 0.4rem; justify-content: center; }}
  .tag {{
    background: var(--accent); color: #fff; padding: 0.15rem 0.5rem;
    border-radius: 999px; font-size: 0.75rem;
  }}

  .lang-toggle {{
    position: fixed; top: 1rem; right: 1rem; z-index: 100;
    display: flex; gap: 0; border-radius: 6px; overflow: hidden;
    border: 1px solid var(--border);
  }}
  .lang-toggle button {{
    border: none; padding: 0.35rem 0.75rem; cursor: pointer;
    background: var(--card-bg); color: var(--fg); font-size: 0.85rem;
  }}
  .lang-toggle button.active {{ background: var(--accent); color: #fff; }}

  .narrative blockquote {{
    font-size: 1.2rem; font-style: italic; border-left: 4px solid var(--accent);
    padding: 0.75rem 1rem; margin: 1.5rem 0; background: var(--card-bg);
    border-radius: 0 8px 8px 0;
  }}
  .narrative-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem; margin: 1.5rem 0;
  }}
  .card {{
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 8px; padding: 1rem;
  }}
  .card h4 {{ color: var(--accent); margin-bottom: 0.4rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }}

  .abstract, .paper-section, .figures {{ margin: 2rem 0; }}
  h2 {{ font-size: 1.3rem; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }}
  .badge {{
    font-size: 0.65rem; padding: 0.15rem 0.45rem; border-radius: 4px;
    text-transform: uppercase; font-weight: 600; letter-spacing: 0.04em;
  }}
  .badge-problem {{ background: #fecaca; color: #991b1b; }}
  .badge-method {{ background: #bfdbfe; color: #1e40af; }}
  .badge-result {{ background: #bbf7d0; color: #166534; }}
  .badge-discussion {{ background: #e9d5ff; color: #6b21a8; }}
  .badge-other {{ background: var(--border); color: var(--muted); }}

  .paper-section ul {{ padding-left: 1.5rem; margin-top: 0.5rem; }}
  .paper-section li {{ margin-bottom: 0.25rem; }}

  .figure-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
  figure {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  figure img {{ width: 100%; height: auto; display: block; }}
  figcaption {{ padding: 0.75rem; font-size: 0.85rem; }}
  .ai-desc {{ color: var(--muted); margin-top: 0.3rem; font-size: 0.8rem; }}

  footer {{ margin-top: 3rem; text-align: center; color: var(--muted); font-size: 0.8rem; }}
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
  --c-card: #FFFFFF;
  --c-delta-pos: #16a34a;
  --c-delta-neg: #dc2626;
  --c-shadow: rgba(0,0,0,0.06);
  --font: {theme.font_body};
  --font-heading: {theme.font_heading};
  --font-mono: {theme.font_mono};

  /* Type scale — px values for 1920×1080 slide canvas */
  --text-xs: 22px;
  --text-sm: 26px;
  --text-base: 30px;
  --text-lg: 36px;
  --text-xl: 42px;
  --text-2xl: 52px;
  --text-3xl: 60px;
  --text-4xl: 80px;
  --text-md: 28px;
  --type-label: var(--text-xs);
  --type-small: var(--text-sm);
  --type-body: var(--text-base);
  --type-subtitle: var(--text-2xl);

  /* Spacing — px for 1920×1080 canvas */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* Slide layout */
  --slide-pad: 80px;
  --gap-title: 20px;
  --gap-item: 24px;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: var(--font);
  background: var(--c-bg);
  color: var(--c-text);
  margin: 0;
  padding: 0;
}}

/* ── Slide pad: the inner frame of every slide ── */
.slide-pad {{
  display: flex;
  flex-direction: column;
  gap: var(--gap-title);
  width: 100%;
  height: 100%;
  padding: var(--slide-pad);
  box-sizing: border-box;
  color: var(--c-text);
}}


/* ── Type hierarchy ──
   L1  Slide title    — serif, 60px, bold, dark
   L2  Chart name     — sans, 28px, semibold, copper
   L3  Chart content  — sans, 26px, regular, dark
   L4  Explanation    — serif, 26px, regular, muted + left border
*/
.slide-title {{
  font-family: var(--font-heading);
  color: var(--c-text);
  font-size: var(--text-3xl);
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
}}

.slide-body {{
  font-family: var(--font);
  font-size: var(--type-body);
  font-weight: 400;
  line-height: 1.6;
  color: var(--c-text);
  max-width: 900px;
}}


.label {{
  font-family: var(--font-mono);
  letter-spacing: {theme.slide_label_tracking};
  text-transform: uppercase;
  font-size: var(--type-label);
  font-weight: 500;
  color: var(--c-primary);
  margin: 0;
}}


.accent-line {{
  width: 48px;
  height: 3px;
  background: var(--c-primary);
  margin: var(--space-3) 0;
}}

.stat-item {{
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}}

.stat-item::before {{
  content: '';
  display: block;
  width: 100%;
  height: 2px;
  background: var(--c-text);
  margin-bottom: var(--space-3);
}}

.stat-num {{
  font-family: var(--font-heading);
  font-size: var(--text-4xl);
  font-weight: 700;
  color: var(--c-primary);
  line-height: 1;
}}

.stat-label {{
  font-family: var(--font);
  font-size: var(--type-small);
  color: var(--c-text);
}}

/* ── Viz utilities ── */
.viz {{ display:flex; flex-direction:column; gap:var(--gap-item); flex:1; justify-content:center; }}
.viz-title {{ font-family:var(--font); font-size:var(--text-md); font-weight:600; margin:0; color:var(--c-primary); }}
.viz-caption {{ font-family:var(--font-heading); font-size:var(--type-small); font-weight:400; color:var(--c-text-muted); margin-top:16px; line-height:1.5; border-left:3px solid var(--c-primary); padding-left:20px; }}


.viz-legend {{ display:flex; gap:24px; flex-wrap:wrap; }}
.viz-swatch {{ display:flex; align-items:center; gap:12px; font-size:var(--type-small); color:var(--c-text); }}
.viz-swatch::before {{ content:''; width:24px; height:24px; border-radius:4px; background:var(--swatch-color); flex-shrink:0; }}

.viz-bar-track {{ flex:1; background:var(--c-primary-light); border-radius:12px; height:64px; position:relative; overflow:hidden; }}
.viz-bar-fill {{ height:100%; border-radius:12px; transition:width 0.6s; }}

.viz-num {{ font-family:var(--font-mono); font-size:var(--type-body); font-weight:500; color:var(--c-text-muted); flex-shrink:0; min-width:40px; }}

.viz-callout {{ max-width:360px; }}
.viz-callout-title {{ font-family:var(--font-heading); font-size:var(--type-body); font-weight:700; color:var(--c-primary); line-height:1.4; }}
.viz-callout-text {{ font-family:var(--font-heading); font-size:var(--type-small); font-weight:400; color:var(--c-text-muted); margin-top:var(--space-3); line-height:1.5; }}

.bullet-item {{ display:flex; gap:16px; align-items:flex-start; }}
.bullet-item::before {{ content:'\\2014'; color:var(--c-text-muted); font-size:var(--type-body); line-height:1.6; flex-shrink:0; }}
.bullet-item span {{ font-size:var(--type-body); line-height:1.6; }}

/* ── Table ── */
.viz-table {{ width:100%; border-collapse:collapse; }}
.viz-table th {{ text-align:left; font-family:var(--font-mono); font-size:var(--type-label); font-weight:500; letter-spacing:0.08em; text-transform:uppercase; color:var(--c-text-muted); padding:16px 20px; border-bottom:2px solid var(--c-text); }}
.viz-table td {{ font-size:var(--type-small); padding:18px 20px; border-bottom:1px solid var(--c-primary-light); color:var(--c-text); }}
.viz-table td:first-child {{ font-weight:600; }}
.viz-table tr:last-child td {{ border-bottom:2px solid var(--c-primary); }}

/* ── Funnel ── */
.funnel-stage {{ display:flex; align-items:center; gap:24px; }}
.funnel-box {{ flex:1; border:1px solid var(--c-primary-light); padding:16px 32px; display:flex; justify-content:space-between; align-items:center; font-size:var(--type-small); }}
.funnel-box .funnel-val {{ font-family:var(--font-heading); font-size:var(--text-2xl); font-weight:700; }}
.funnel-box.funnel-final {{ background:var(--c-primary); color:var(--c-text-light); border-color:var(--c-primary); }}
.funnel-box.funnel-final .funnel-val {{ color:var(--c-text-light); }}
.funnel-arrow {{ text-align:center; font-size:var(--type-body); color:var(--c-text-muted); padding:4px 0; }}
.funnel-excl {{ font-family:var(--font-mono); font-size:var(--type-label); color:var(--c-text-muted); white-space:nowrap; min-width:200px; }}

/* ── Two-panel ── */
.panel {{ flex:1; display:flex; flex-direction:column; gap:var(--space-4); }}
.panel-rule {{ width:100%; height:3px; }}
.panel-tags {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:auto; }}
.panel-tag {{ border:1px solid var(--c-primary-light); padding:6px 16px; border-radius:4px; font-family:var(--font-mono); font-size:var(--type-label); font-weight:500; color:var(--c-text); }}

/* ── Layout utilities ── */
.flex-col {{ display:flex; flex-direction:column; gap:var(--gap-item); }}
.flex-center {{ display:flex; align-items:center; justify-content:center; }}
.split {{ display:flex; gap:48px; flex:1; align-items:center; }}
.split-main {{ flex:3; display:flex; flex-direction:column; justify-content:center; gap:24px; }}
.split-aside {{ flex:2; display:flex; flex-direction:column; justify-content:center; }}


/* ── Viz content patterns ── */
.bar-row {{ display:grid; grid-template-columns:200px 1fr auto; align-items:center; gap:16px; }}
.bar-label {{ text-align:right; font-size:var(--type-small); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.bar-value {{ font-size:var(--type-small); font-weight:600; min-width:80px; }}
.item-row {{ display:flex; gap:16px; align-items:flex-start; }}
.item-title {{ margin:0; font-weight:600; font-size:var(--type-body); }}
.item-desc {{ margin:8px 0 0; font-size:var(--type-small); color:var(--c-text-muted); line-height:1.5; }}
.text-muted {{ font-size:var(--type-small); color:var(--c-text-muted); line-height:1.5; }}
.flow-node {{ border:1px solid var(--c-primary-light); padding:16px 24px; font-size:var(--type-small); font-weight:600; text-align:center; min-width:120px; }}
.flow-arrow {{ font-size:var(--text-lg); color:var(--c-primary); display:flex; align-items:center; }}
.pill {{ background:var(--c-primary-light); color:var(--c-primary); padding:6px 16px; border-radius:20px; font-size:var(--type-label); font-weight:500; }}
.panel-title {{ font-family:var(--font-heading); font-size:var(--text-xl); font-weight:700; margin:0; }}
.prop-cell {{ width:56px; height:56px; border-radius:8px; }}
.footer-note {{ font-size:var(--type-small); color:var(--c-text-muted); margin-top:var(--space-4); text-align:right; }}
</style>"""
