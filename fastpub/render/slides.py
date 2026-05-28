"""Slide renderer — produces a deck-stage HTML presentation from a PaperDocument.

Each <section> is a 1920x1080 slide rendered inside the <deck-stage> web
component, which handles navigation, scaling, keyboard controls, thumbnail
rail, and print-to-PDF.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from fastpub.models import PaperDocument, SlideSpec, VisualizationData
from fastpub.render.theme import WARM_SERIF, build_slide_css, font_import_tag


_ASPECT_RATIOS = {
    "4:3":  (1440, 1080),
    "16:9": (1920, 1080),
}

_CHART_COLORS = WARM_SERIF.chart_colors
_NUM_CHART_COLORS = len(_CHART_COLORS)


def render_slides(
    doc: PaperDocument,
    output_path: Path,
    aspect: str = "16:9",
) -> Path:
    """Render PaperDocument to an HTML slide deck."""
    if aspect not in _ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect!r}. Use '4:3' or '16:9'.")

    if doc.slides:
        slides = _slides_from_specs(doc)
    else:
        slides = _build_slides(doc)

    w, h = _ASPECT_RATIOS[aspect]
    narrations = [s.narration for s in slides]
    result = _build_html(doc, slides, narrations, w, h)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# Slide data
# ---------------------------------------------------------------------------

class _Slide:
    __slots__ = (
        "slide_type", "title", "bullets", "body",
        "figure_src", "figure_caption",
        "narration", "label", "body_is_html",
        "explanation", "viz_type",
    )

    def __init__(
        self,
        slide_type: str,
        title: str,
        bullets: list[str] | None = None,
        body: str = "",
        figure_src: str | None = None,
        figure_caption: str | None = None,
        narration: str = "",
        label: str = "",
        body_is_html: bool = False,
        explanation: str = "",
        viz_type: str = "",
    ):
        self.slide_type = slide_type
        self.title = title
        self.bullets = bullets or []
        self.body = body
        self.figure_src = figure_src
        self.figure_caption = figure_caption
        self.narration = narration
        self.label = label
        self.body_is_html = body_is_html
        self.explanation = explanation
        self.viz_type = viz_type



def _build_slides(doc: PaperDocument) -> list[_Slide]:
    """Build slides from PaperDocument (fallback when no SlideSpec available)."""
    slides: list[_Slide] = []

    # Title
    subtitle_parts = []
    if doc.meta.authors:
        subtitle_parts.append(", ".join(doc.meta.authors))
    if doc.meta.venue:
        v = doc.meta.venue
        if doc.meta.year:
            v += f" ({doc.meta.year})"
        subtitle_parts.append(v)
    slides.append(_Slide("title", doc.meta.title, subtitle_parts, label="Title"))

    # Hook
    if doc.hook:
        slides.append(_Slide("hook", "Why This Matters", body=doc.hook, label="Context"))

    # Web sections as slides
    _section_labels = {
        "problem": ("The Problem", "Problem"),
        "approach": ("Our Approach", "Methods"),
        "meaning": ("Why It Matters", "Impact"),
        "result": ("Key Results", "Results"),
        "limitation": ("Limitations", "Limitations"),
    }
    for ws in doc.web_sections:
        title, label = _section_labels.get(ws.type, (ws.type.title(), ws.type.title()))
        bullets = [si.title for si in ws.sub_issues[:4]]
        slides.append(_Slide(ws.type, title, bullets, body=ws.summary, label=label))

    # Closing
    slides.append(_Slide("closing", "Key Takeaways", label="Summary"))

    return slides


def _slides_from_specs(doc: PaperDocument) -> list[_Slide]:
    """Convert SlideSpec objects from unified analysis into _Slide objects."""
    fig_map = {f.id: f for f in doc.figures}
    slides: list[_Slide] = []

    _layout_to_type = {
        "title": "title",
        "section_header": "hook",
        "content": "approach",
        "figure": "results",
        "two_column": "results",
        "closing": "closing",
        "accent": "accent",
        "dark": "dark",
    }

    for spec in doc.slides:
        slide_type = _layout_to_type.get(spec.layout, "approach")

        # Resolve visualization: prefer spec-level, then figure-level
        viz = spec.visualization
        fig_src = None
        fig_caption = None
        if spec.figure_ref and spec.figure_ref in fig_map:
            fig = fig_map[spec.figure_ref]
            fig_caption = fig.caption
            if not viz and fig.visualization:
                viz = fig.visualization
            if not viz:
                fig_src = fig.src  # fall back to original image

        # Build body from visualization HTML if available
        viz_html = ""
        viz_type_name = ""
        if viz:
            viz_html = _render_visualization(viz)
            viz_type_name = viz.viz_type

        # For non-viz slides, use explanation as body text
        body = viz_html if viz_html else spec.explanation

        slides.append(_Slide(
            slide_type=slide_type,
            title=spec.title,
            bullets=spec.bullets if not viz_html else [],
            body=body,
            figure_src=fig_src if not viz_html else None,
            figure_caption=fig_caption,
            narration=spec.narrative,
            label=spec.section or spec.layout.replace("_", " ").title(),
            body_is_html=bool(viz_html),
            explanation=spec.explanation if viz_html else "",
            viz_type=viz_type_name,
        ))

    return slides


# ---------------------------------------------------------------------------
# Visualization renderers
# ---------------------------------------------------------------------------

_VIZ_RENDERERS: dict | None = None


def _render_visualization(viz: VisualizationData) -> str:
    """Dispatch to the appropriate visualization renderer."""
    global _VIZ_RENDERERS
    if _VIZ_RENDERERS is None:
        _VIZ_RENDERERS = {
            "bar_chart": _render_bar_chart,
            "stat_card": _render_stat_card,
            "donut_chart": _render_donut_chart,
            "comparison": _render_comparison,
            "funnel": _render_funnel,
            "steps": _render_steps,
            "proportion": _render_proportion,
            "flow": _render_flow,
            "area_blocks": _render_area_blocks,
            "stacked_bar": _render_stacked_bar,
            "card_grid": _render_card_grid,
            "two_panel": _render_two_panel,
        }
    renderer = _VIZ_RENDERERS.get(viz.viz_type)
    if not renderer:
        return ""
    return renderer(viz.title, viz.data)


# ---------------------------------------------------------------------------
# Shared viz helpers
# ---------------------------------------------------------------------------

def _viz_title(title: str) -> str:
    return f'<p class="viz-title">{_esc(title)}</p>'


def _swatch(label: str, color: str) -> str:
    return f'<div class="viz-swatch" style="--swatch-color:{color};"><span>{_esc(label)}</span></div>'


def _chart_color(index: int) -> str:
    return _CHART_COLORS[index % _NUM_CHART_COLORS]


def _fmt_num(num) -> str:
    """Format a number as zero-padded two digits (01, 02) or pass through."""
    if isinstance(num, (int, float)) or (isinstance(num, str) and num.isdigit()):
        return f"{int(num):02d}"
    return str(num)


def _callout(title: str, text: str) -> str:
    if not title:
        return ""
    text_html = f'<div class="viz-callout-text">{_esc(text)}</div>' if text else ""
    return f'<div class="viz-callout"><div class="viz-callout-title">{_esc(title)}</div>{text_html}</div>'


def _render_bar_chart(title: str, data: dict) -> str:
    labels = data.get("labels", [])
    values = data.get("values", [])
    unit = _esc(data.get("unit", ""))
    color = "var(--c-primary)"
    if not labels or not values:
        return ""
    max_val = max(values) if values else 1

    bars = []
    for label, val in zip(labels, values):
        pct = (val / max_val * 100) if max_val else 0
        bars.append(f"""<div class="bar-row">
  <span class="bar-label">{_esc(str(label))}</span>
  <div class="viz-bar-track">
    <div class="viz-bar-fill" style="width:{pct:.1f}%;background:{color};"></div>
  </div>
  <span class="bar-value">{val} {unit}</span>
</div>""")

    co = data.get("callout")
    callout_html = _callout(co.get("title", ""), co.get("text", "")) if co else ""

    if callout_html:
        return f"""<div class="viz">
  {_viz_title(title)}
  <div class="split">
    <div class="flex-col" style="flex:1;">
      {chr(10).join(bars)}
    </div>
    {callout_html}
  </div>
</div>"""

    return f"""<div class="viz">
  {_viz_title(title)}
  {chr(10).join(bars)}
</div>"""


def _render_stat_card(title: str, data: dict) -> str:
    stats = data.get("stats", [])
    if not stats:
        return ""
    items = []
    for i, s in enumerate(stats):
        delta_html = ""
        if s.get("delta"):
            delta_color = "var(--c-delta-pos)" if s["delta"].startswith("+") else "var(--c-delta-neg)"
            delta_html = f' <span style="font-size:var(--type-small);color:{delta_color};font-weight:500;">{_esc(s["delta"])}</span>'
        # Alternate primary/accent colors for visual variety — ignore LLM color overrides
        stat_color = "var(--c-primary)" if i % 2 == 0 else "var(--c-accent)"
        items.append(f"""<div class="stat-item">
  <div class="stat-num" style="color:{stat_color};">{_esc(str(s.get("value", "")))}{delta_html}</div>
  <div class="stat-label">{_esc(s.get("label", ""))}</div>
</div>""")

    cols = min(len(stats), 4)
    return f"""<div class="viz" style="justify-content:flex-end;">
  {_viz_title(title)}
  <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:32px;">
    {chr(10).join(items)}
  </div>
</div>"""


def _render_donut_chart(title: str, data: dict) -> str:
    segments = data.get("segments", [])
    if not segments:
        return ""

    total = sum(s.get("value", 0) for s in segments)
    if total == 0:
        return ""

    # Build SVG donut
    r, cx, cy = 150, 200, 200
    stroke_width = 55
    circumference = 2 * 3.14159 * r
    paths = []
    offset = 0
    for i, seg in enumerate(segments):
        pct = seg["value"] / total
        dash = pct * circumference
        gap = circumference - dash
        color = _chart_color(i)
        paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += dash

    center_label = data.get("centerLabel", "")
    center_value = data.get("centerValue", "")
    center_html = ""
    if center_value:
        center_html = f'<text x="{cx}" y="{cy-16}" text-anchor="middle" font-size="56" font-weight="700" fill="var(--c-text)">{_esc(str(center_value))}</text><text x="{cx}" y="{cy+32}" text-anchor="middle" font-size="28" fill="var(--c-text)">{_esc(center_label)}</text>'

    legend_items = [_swatch(f'{seg["label"]} ({seg["value"]})', _chart_color(i)) for i, seg in enumerate(segments)]

    # Side bars if provided
    side_bars = data.get("sideBars", [])
    side_bars_html = ""
    if side_bars:
        sb_max = max(sb.get("value", 0) for sb in side_bars) if side_bars else 1
        sb_items = []
        for sb in side_bars:
            sb_pct = (sb["value"] / sb_max * 100) if sb_max else 0
            sb_items.append(f"""<div class="bar-row" style="grid-template-columns:140px 1fr auto;">
  <span class="bar-label">{_esc(sb.get("label", ""))}</span>
  <div class="viz-bar-track" style="height:44px;">
    <div class="viz-bar-fill" style="width:{sb_pct:.1f}%;background:var(--c-primary);"></div>
  </div>
  <span class="bar-value" style="min-width:50px;">{sb["value"]}</span>
</div>""")
        side_bars_html = f'<div class="flex-col" style="gap:8px;margin-top:16px;">{chr(10).join(sb_items)}</div>'

    svg_title = f'{_esc(title)} — ' + ', '.join(f'{s["label"]}: {s["value"]}' for s in segments)
    return f"""<div class="split" style="justify-content:center;">
  <div style="flex-shrink:0;">
    <svg width="400" height="400" viewBox="0 0 400 400" role="img" aria-label="{_esc(svg_title)}">
      <title>{_esc(svg_title)}</title>
      {chr(10).join(paths)}
      {center_html}
    </svg>
  </div>
  <div class="flex-col" style="gap:12px;flex:1;">
    {_viz_title(title)}
    <div class="viz-legend" style="flex-direction:column;">{chr(10).join(legend_items)}</div>
    {side_bars_html}
  </div>
</div>"""


def _render_comparison(title: str, data: dict) -> str:
    items = data.get("items", [])
    if len(items) < 2:
        return ""

    # Get all metric keys
    all_keys = []
    for item in items:
        for k in item.get("metrics", {}):
            if k not in all_keys:
                all_keys.append(k)

    header_cells = "<th></th>" + "".join(
        f'<th style="text-align:center;">{_esc(item.get("name", ""))}</th>'
        for item in items
    )

    rows = []
    for key in all_keys:
        cells = f'<td>{_esc(key)}</td>'
        for item in items:
            val = item.get("metrics", {}).get(key, "\u2014")
            cells += f'<td style="text-align:center;">{_esc(str(val))}</td>'
        rows.append(f'<tr>{cells}</tr>')

    return f"""<div class="viz">
  {_viz_title(title)}
  <table class="viz-table">
    <thead><tr>{header_cells}</tr></thead>
    <tbody>{chr(10).join(rows)}</tbody>
  </table>
</div>"""


def _render_funnel(title: str, data: dict) -> str:
    stages = data.get("stages", [])
    if not stages:
        return ""

    parts = []
    for i, stage in enumerate(stages):
        is_last = i == len(stages) - 1
        final_cls = " funnel-final" if is_last else ""
        excluded = stage.get("excluded", "")
        excl_html = f'<span class="funnel-excl">\u2212{_esc(str(excluded))}</span>' if excluded else '<span class="funnel-excl"></span>'

        parts.append(f"""<div class="funnel-stage">
  <div class="funnel-box{final_cls}">
    <span>{_esc(stage["label"])}</span>
    <span class="funnel-val">{stage["value"]:,}</span>
  </div>
  {excl_html}
</div>""")
        if not is_last:
            parts.append('<div class="funnel-arrow">\u2193</div>')

    # Side stats as footer note
    side_stats = data.get("sideStats", [])
    footer = ""
    if side_stats:
        notes = " \u00b7 ".join(f'{ss.get("value", "")} {ss.get("label", "")}' for ss in side_stats)
        footer = f'<p class="footer-note">{_esc(notes)}</p>'

    return f"""<div class="viz">
  {_viz_title(title)}
  <div class="flex-col" style="gap:0;max-width:700px;">
    {chr(10).join(parts)}
  </div>
  {footer}
</div>"""


def _render_steps(title: str, data: dict) -> str:
    steps = data.get("steps", [])
    if not steps:
        return ""

    cols = data.get("columns", 1)
    items = []
    for step in steps:
        num = step.get("number", "")
        num_str = _fmt_num(num)
        items.append(f"""<div class="item-row">
  <span class="viz-num">{_esc(num_str)}</span>
  <div style="flex:1;">
    <p class="item-title">{_esc(step.get("title", ""))}</p>
    <p class="item-desc">{_esc(step.get("description", ""))}</p>
  </div>
</div>""")

    if cols > 1:
        grid = f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:24px 48px;">{chr(10).join(items)}</div>'
    else:
        grid = chr(10).join(items)

    return f"""<div class="viz" style="gap:24px;">
  {_viz_title(title)}
  {grid}
</div>"""


def _render_proportion(title: str, data: dict) -> str:
    blocks = data.get("blocks", [])
    total = data.get("total", sum(b.get("count", 0) for b in blocks))
    if not blocks or total == 0:
        return ""

    cells = []
    legend = []
    for i, b in enumerate(blocks):
        color = _chart_color(i)
        count = b.get("count", 0)
        for _ in range(count):
            cells.append(f'<div class="prop-cell" style="background:{color};"></div>')
        pct = count / total * 100
        legend.append(_swatch(f'{b["label"]} ({pct:.0f}%)', color))

    return f"""<div class="viz">
  {_viz_title(title)}
  <div style="display:flex;flex-wrap:wrap;gap:6px;">
    {chr(10).join(cells)}
  </div>
  <div class="viz-legend">
    {chr(10).join(legend)}
  </div>
</div>"""


def _render_flow(title: str, data: dict) -> str:
    nodes = data.get("nodes", [])
    if not nodes:
        return ""

    parts = []
    for i, node in enumerate(nodes):
        parts.append(f'<div class="flow-node">{_esc(node["label"])}</div>')
        if i < len(nodes) - 1:
            parts.append('<div class="flow-arrow">&#8594;</div>')

    return f"""<div class="viz" style="gap:24px;">
  {_viz_title(title)}
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;justify-content:center;">
    {chr(10).join(parts)}
  </div>
</div>"""


def _render_area_blocks(title: str, data: dict) -> str:
    """Proportional area blocks — large/medium/small rectangles showing relative sizes."""
    blocks = data.get("blocks", [])
    if not blocks:
        return ""

    # Size presets: height and font sizing
    size_map = {
        "large": ("240px", "1fr", "var(--type-subtitle)", "var(--type-small)"),
        "medium": ("180px", "1fr", "var(--type-body)", "var(--type-small)"),
        "small": ("140px", "1fr", "var(--type-small)", "var(--type-label)"),
    }

    block_html = []
    for i, b in enumerate(blocks):
        color = _chart_color(i)
        size = b.get("size", "medium")
        h, _, val_size, label_size = size_map.get(size, size_map["medium"])
        value = _esc(str(b.get("value", "")))
        label = _esc(b.get("label", ""))
        detail = _esc(b.get("detail", ""))
        sub_detail = _esc(b.get("subDetail", ""))

        detail_html = f'<span style="font-size:{label_size};opacity:0.85;">{detail}</span>' if detail else ""
        sub_html = f'<span style="font-size:{label_size};opacity:0.7;">{sub_detail}</span>' if sub_detail else ""

        block_html.append(f"""<div style="background:{color};border-radius:16px;padding:24px 28px;min-height:{h};display:flex;flex-direction:column;justify-content:space-between;color:var(--c-text-light);flex:1;">
  <div style="font-size:{val_size};font-weight:700;">{value}</div>
  <div style="display:flex;flex-direction:column;gap:4px;">
    <span style="font-size:{label_size};font-weight:600;">{label}</span>
    {detail_html}
    {sub_html}
  </div>
</div>""")

    # Side list if provided
    side_html = ""
    side_list = data.get("sideList")
    if side_list:
        items = side_list.get("items", [])
        li_html = "".join(f'<li style="font-size:var(--type-label);line-height:1.6;">{_esc(str(item))}</li>' for item in items)
        side_html = f"""<div style="min-width:260px;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0 0 12px;">{_esc(side_list.get("title", ""))}</p>
  <ul style="margin:0;padding-left:20px;list-style:none;">{li_html}</ul>
</div>"""

    blocks_joined = "\n".join(block_html)

    inner = f"""<div style="display:flex;gap:16px;flex:1;align-items:stretch;">
  {blocks_joined}
</div>"""

    if side_html:
        inner = f"""<div style="display:flex;gap:32px;flex:1;align-items:stretch;">
  <div style="flex:1;display:flex;flex-direction:column;gap:16px;">
    <div style="display:flex;gap:16px;flex:1;align-items:stretch;">
      {blocks_joined}
    </div>
  </div>
  {side_html}
</div>"""

    return f"""<div class="viz">
  {_viz_title(title)}
  {inner}
</div>"""


def _render_stacked_bar(title: str, data: dict) -> str:
    """Horizontal stacked bar with legend and optional callout."""
    segments = data.get("segments", [])
    if not segments:
        return ""

    total = sum(s.get("value", 0) for s in segments)
    if total == 0:
        return ""

    # Build stacked segments
    seg_html = []
    for i, s in enumerate(segments):
        color = _chart_color(i)
        pct = s["value"] / total * 100
        seg_html.append(f'<div style="width:{pct:.1f}%;height:100%;background:{color};display:flex;align-items:center;justify-content:center;color:var(--c-text-light);font-weight:600;font-size:var(--type-small);overflow:hidden;white-space:nowrap;">{pct:.0f}%</div>')

    # Legend
    legend_items = []
    for i, s in enumerate(segments):
        color = _chart_color(i)
        legend_items.append(_swatch(f'{s["label"]} ({s["value"]})', color))

    # Country labels if provided
    countries = data.get("countries", [])
    countries_html = ""
    if countries:
        tags = " ".join(f'<span class="pill">{_esc(c)}</span>' for c in countries)
        countries_html = f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{tags}</div>'

    # Callout if provided
    callout = data.get("callout")
    callout_html = ""
    if callout:
        callout_html = _callout(str(callout.get("value", "")), callout.get("label", ""))

    left_parts = f"""<div class="flex-col" style="flex:1;">
  <div style="display:flex;height:56px;overflow:hidden;">
    {chr(10).join(seg_html)}
  </div>
  <div class="viz-legend">
    {chr(10).join(legend_items)}
  </div>
  {countries_html}
</div>"""

    if callout_html:
        content = f"""<div class="split">
  {left_parts}
  {callout_html}
</div>"""
    else:
        content = left_parts

    return f"""<div class="viz">
  {_viz_title(title)}
  {content}
</div>"""


def _render_card_grid(title: str, data: dict) -> str:
    """Numbered items in a grid layout."""
    cards = data.get("cards", [])
    if not cards:
        return ""

    cols = data.get("columns", 2)
    card_html = []
    for c in cards:
        num = c.get("number", "")
        # Format as zero-padded two-digit number like the reference
        num_str = _fmt_num(num)
        card_html.append(f"""<div class="item-row">
  <span class="viz-num">{_esc(num_str)}</span>
  <div style="flex:1;">
    <p class="item-title">{_esc(c.get("title", ""))}</p>
    <p class="item-desc">{_esc(c.get("description", ""))}</p>
  </div>
</div>""")

    return f"""<div class="viz">
  {_viz_title(title)}
  <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:24px 48px;">
    {chr(10).join(card_html)}
  </div>
</div>"""


def _render_two_panel(title: str, data: dict) -> str:
    """Side-by-side concept panels with optional tags."""
    left = data.get("left", {})
    right = data.get("right", {})
    if not left and not right:
        return ""

    def _panel(panel: dict, idx: int = 0) -> str:
        color = _chart_color(idx)
        tags = panel.get("tags", [])
        tags_html = ""
        if tags:
            tag_spans = " ".join(f'<span class="panel-tag">{_esc(t)}</span>' for t in tags)
            label = panel.get("tagsLabel", "")
            label_html = f'<span class="label" style="margin:0;">{_esc(label)}</span>' if label else ""
            tags_html = f'<div class="panel-tags">{label_html}{tag_spans}</div>'

        return f"""<div class="panel">
  <div class="panel-rule" style="background:{color};"></div>
  <p class="panel-title">{_esc(panel.get("title", ""))}</p>
  <p class="text-muted" style="margin:0;">{_esc(panel.get("description", ""))}</p>
  {tags_html}
</div>"""

    panels = []
    if left:
        panels.append(_panel(left, 0))
    if right:
        panels.append(_panel(right, 1))

    return f"""<div class="viz">
  {_viz_title(title)}
  <div style="display:flex;gap:48px;">
    {chr(10).join(panels)}
  </div>
</div>"""


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _slide_html(slide: _Slide, index: int, doc: PaperDocument | None = None) -> str:
    if slide.slide_type == "title":
        return _title_slide(slide, index, doc)
    if slide.slide_type == "closing":
        return _closing_slide(slide, index)
    return _content_slide(slide, index)


def _title_slide(slide: _Slide, index: int, doc: PaperDocument | None = None) -> str:
    meta = doc.meta if doc else None
    title = meta.title if meta and meta.title else slide.title

    # Authors
    authors_html = ""
    if meta and meta.authors:
        authors_html = f'      <p style="font-size: var(--type-body); color: var(--c-text); margin: 0;">{_esc(", ".join(meta.authors))}</p>'

    # Venue + year
    venue_html = ""
    venue_parts = []
    if meta and meta.venue:
        venue_parts.append(meta.venue)
    if meta and meta.year:
        venue_parts.append(str(meta.year))
    if venue_parts:
        venue_html = f'      <p style="font-size: var(--type-small); color: var(--c-text-muted); margin: 0; font-weight: 300;">{_esc(" · ".join(venue_parts))}</p>'

    return f"""  <section data-label="{_esc(f'{index+1:02d} Title')}" aria-label="{_esc(title)}">
    <div class="slide-pad" style="justify-content: center; gap: 24px;">
      <div class="accent-line"></div>
      <h1 class="slide-title" style="font-size: var(--text-4xl); max-width: 1400px;">{_esc(title)}</h1>
{authors_html}
{venue_html}
    </div>
  </section>"""


def _closing_slide(slide: _Slide, index: int) -> str:
    body_html = ""
    if slide.body:
        if slide.body_is_html:
            body_html = f'      <div style="max-width: 1000px;">{slide.body}</div>'
        else:
            body_html = f'      <p style="font-size: var(--type-body); color: var(--c-text-muted); margin: 0; max-width: 900px; line-height: 1.6;">{_esc(slide.body)}</p>'

    return f"""  <section data-label="{_esc(f'{index+1:02d} {slide.label}')}" aria-label="{_esc(slide.title)}">
    <div class="slide-pad" style="justify-content: center; align-items: center; gap: 32px; text-align: center;">
      <div class="accent-line"></div>
      <h2 class="slide-title" style="font-size: var(--text-3xl); max-width: 1200px;">{_esc(slide.title)}</h2>
{body_html}
      <p style="font-size: var(--type-small); color: var(--c-text-muted); margin-top: var(--space-8);">Thank you</p>
    </div>
  </section>"""


# Viz types that are wide/multi-element — explanation goes below
_WIDE_VIZ_TYPES = {"stat_card", "comparison", "steps", "card_grid", "two_panel", "funnel"}


def _content_slide(slide: _Slide, index: int) -> str:
    has_image = slide.figure_src is not None
    has_bullets = bool(slide.bullets)
    has_body = bool(slide.body)
    has_explanation = bool(slide.explanation)

    # Build content area
    content_parts = []

    if has_body and not has_bullets:
        if slide.body_is_html:
            content_parts.append(f'      {slide.body}')
        else:
            content_parts.append(
                f'      <p class="slide-body">{_esc(slide.body)}</p>'
            )

    if has_bullets:
        items = []
        for b in slide.bullets:
            items.append(f'          <div class="bullet-item"><span>{_esc(b)}</span></div>')
        content_parts.append(
            '      <div style="display: flex; flex-direction: column; gap: var(--gap-item);">\n'
            + "\n".join(items)
            + "\n      </div>"
        )

    # Image area
    image_html = ""
    if has_image:
        cap = ""
        if slide.figure_caption:
            cap = f'\n          <figcaption style="font-size: var(--type-label); color: var(--c-text-muted); margin-top: 12px;">{_esc(slide.figure_caption)}</figcaption>'
        image_html = f"""      <div style="flex: 1; display: flex; align-items: center; justify-content: center; min-width: 0;">
        <figure style="max-width: 100%; text-align: center; margin: 0;">
          <img src="{_esc(slide.figure_src or "")}" alt="{_esc(slide.figure_caption or slide.title)}" style="max-width: 100%; max-height: 560px; object-fit: contain; border-radius: 12px; box-shadow: 0 4px 24px var(--c-shadow);">{cap}
        </figure>
      </div>"""

    # Explanation HTML
    explanation_html = ""
    if has_explanation:
        explanation_html = f'<p class="viz-caption">{_esc(slide.explanation)}</p>'

    # Layout: determine how to place explanation relative to chart
    is_wide_viz = slide.viz_type in _WIDE_VIZ_TYPES

    if has_image and (has_body or has_bullets):
        body_html = f"""    <div class="split" style="gap:64px;">
      <div class="split-main" style="flex:1;">
{chr(10).join(content_parts)}
      </div>
{image_html}
    </div>"""
    elif has_image:
        body_html = f"""    <div class="flex-center" style="flex:1;">
{image_html}
    </div>"""
    elif has_explanation and slide.body_is_html and not is_wide_viz:
        # Single chart: chart left (60%), explanation right (40%)
        body_html = f"""    <div class="split">
      <div class="split-main">
{chr(10).join(content_parts)}
      </div>
      <div class="split-aside">
        {explanation_html}
      </div>
    </div>"""
    elif has_explanation and slide.body_is_html and is_wide_viz:
        # Wide/multi chart: chart on top, explanation below
        body_html = f"""    <div class="flex-col" style="flex:1;justify-content:center;">
{chr(10).join(content_parts)}
      {explanation_html}
    </div>"""
    else:
        body_html = f"""    <div class="flex-col" style="flex:1;justify-content:center;">
{chr(10).join(content_parts)}
    </div>"""

    return f"""  <section data-label="{_esc(f'{index+1:02d} {slide.label or slide.slide_type.title()}')}" aria-label="{_esc(slide.title)}">
    <div class="slide-pad">
      <p class="label">{_esc(slide.label)}</p>
      <h2 class="slide-title">{_esc(slide.title)}</h2>
      <div class="accent-line"></div>
{body_html}
    </div>
  </section>"""


def _build_html(
    doc: PaperDocument,
    slides: list[_Slide],
    narrations: list[str],
    width: int,
    height: int,
) -> str:
    slides_html = "\n\n".join(_slide_html(s, i, doc) for i, s in enumerate(slides))

    notes_json = json.dumps(narrations, ensure_ascii=False, indent=2)

    # Read deck-stage.js from templates
    templates_dir = Path(__file__).parent / "templates"
    deck_stage_js = (templates_dir / "deck-stage.js").read_text(encoding="utf-8")
    # Escape closing tags so the browser doesn't prematurely close the <script> block
    deck_stage_js = deck_stage_js.replace("</script>", "<\\/script>").replace("</style>", "<\\/style>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(doc.meta.title)} — Slides</title>

{font_import_tag(WARM_SERIF)}

<script type="application/json" id="speaker-notes">
{notes_json}
</script>

{build_slide_css(WARM_SERIF)}
<script>{deck_stage_js}</script>
</head>
<body>

<style>deck-stage:not(:defined){{visibility:hidden}}</style>
<deck-stage width="{width}" height="{height}">

{slides_html}

</deck-stage>

</body>
</html>"""

