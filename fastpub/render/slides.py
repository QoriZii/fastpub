"""Slide renderer — produces a deck-stage HTML presentation from a PaperDocument.

Each <section> is a 1920x1080 slide rendered inside the <deck-stage> web
component, which handles navigation, scaling, keyboard controls, thumbnail
rail, and print-to-PDF.
"""
from __future__ import annotations

import html
from pathlib import Path

from fastpub.models import PaperDocument, PaperFigure, SlideSpec, VisualizationData
from fastpub.render.theme import WARM_SERIF, build_slide_css, font_import_tag


_ASPECT_RATIOS = {
    "4:3":  (1440, 1080),
    "16:9": (1920, 1080),
}


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
        "stats", "narration", "label", "body_is_html",
    )

    def __init__(
        self,
        slide_type: str,
        title: str,
        bullets: list[str] | None = None,
        body: str = "",
        figure_src: str | None = None,
        figure_caption: str | None = None,
        stats: list[tuple[str, str]] | None = None,
        narration: str = "",
        label: str = "",
        body_is_html: bool = False,
    ):
        self.slide_type = slide_type
        self.title = title
        self.bullets = bullets or []
        self.body = body
        self.figure_src = figure_src
        self.figure_caption = figure_caption
        self.stats = stats or []
        self.narration = narration
        self.label = label
        self.body_is_html = body_is_html


def _resolved_figure_map(doc: PaperDocument) -> dict[str, tuple[str, str]]:
    result = {}
    for fig in doc.figures:
        result[fig.id] = (fig.src, fig.caption)
    return result


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
        if viz:
            viz_html = _render_visualization(viz)
            # Add explanation as caption below the viz
            if spec.explanation:
                viz_html += f'\n<p style="font-size:var(--type-small);color:var(--c-text-muted);margin-top:16px;line-height:1.4;">{_esc(spec.explanation)}</p>'

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
            label=spec.layout.replace("_", " ").title(),
            body_is_html=bool(viz_html),
        ))

    return slides


# ---------------------------------------------------------------------------
# Visualization renderers
# ---------------------------------------------------------------------------

def _render_visualization(viz: VisualizationData) -> str:
    """Dispatch to the appropriate visualization renderer."""
    renderers = {
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
    renderer = renderers.get(viz.viz_type)
    if not renderer:
        return ""
    return renderer(viz.title, viz.data)


def _render_bar_chart(title: str, data: dict) -> str:
    labels = data.get("labels", [])
    values = data.get("values", [])
    unit = _esc(data.get("unit", ""))
    color = data.get("color", "var(--c-primary)")
    if not labels or not values:
        return ""
    max_val = max(values) if values else 1

    bars = []
    for label, val in zip(labels, values):
        pct = (val / max_val * 100) if max_val else 0
        bars.append(f"""<div style="display:flex;align-items:center;gap:16px;">
  <span style="min-width:180px;text-align:right;font-size:var(--type-small);white-space:nowrap;">{_esc(str(label))}</span>
  <div style="flex:1;background:var(--c-primary-light);border-radius:8px;height:44px;position:relative;overflow:hidden;">
    <div style="width:{pct:.1f}%;height:100%;background:{color};border-radius:8px;transition:width 0.6s;"></div>
  </div>
  <span style="min-width:80px;font-size:var(--type-small);font-weight:600;">{val}{unit}</span>
</div>""")

    callout = data.get("callout")
    callout_html = ""
    if callout:
        callout_html = f"""<div style="background:var(--c-accent-light);border-left:4px solid var(--c-accent);border-radius:0 12px 12px 0;padding:16px 24px;margin-top:8px;">
  <div style="font-size:var(--type-small);font-weight:700;color:var(--c-accent);">{_esc(str(callout.get("title", "")))}</div>
  <div style="font-size:var(--type-label);color:var(--c-text-muted);">{_esc(callout.get("text", ""))}</div>
</div>"""

    return f"""<div style="display:flex;flex-direction:column;gap:16px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  {chr(10).join(bars)}
  {callout_html}
</div>"""


def _render_stat_card(title: str, data: dict) -> str:
    stats = data.get("stats", [])
    if not stats:
        return ""
    cards = []
    for s in stats:
        delta_html = ""
        if s.get("delta"):
            delta_color = "#16a34a" if s["delta"].startswith("+") else "#dc2626"
            delta_html = f'<span style="font-size:var(--type-label);color:{delta_color};font-weight:500;">{_esc(s["delta"])}</span>'
        stat_color = s.get("color", "var(--c-primary)")
        cards.append(f"""<div class="stat-card">
  <div class="stat-num" style="color:{stat_color};">{_esc(str(s.get("value", "")))}</div>
  <div class="stat-label">{_esc(s.get("label", ""))}</div>
  {delta_html}
</div>""")

    cols = min(len(stats), 3)
    return f"""<div style="display:flex;flex-direction:column;gap:20px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:24px;">
    {chr(10).join(cards)}
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
    r, cx, cy = 90, 120, 120
    stroke_width = 35
    circumference = 2 * 3.14159 * r
    paths = []
    offset = 0
    default_colors = WARM_SERIF.chart_colors

    for i, seg in enumerate(segments):
        pct = seg["value"] / total
        dash = pct * circumference
        gap = circumference - dash
        color = seg.get("color", default_colors[i % len(default_colors)])
        paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += dash

    center_label = data.get("centerLabel", "")
    center_value = data.get("centerValue", "")
    center_html = ""
    if center_value:
        center_html = f'<text x="{cx}" y="{cy-8}" text-anchor="middle" font-size="28" font-weight="700" fill="var(--c-text)">{_esc(str(center_value))}</text><text x="{cx}" y="{cy+18}" text-anchor="middle" font-size="14" fill="var(--c-text-muted)">{_esc(center_label)}</text>'

    legend_items = []
    for i, seg in enumerate(segments):
        color = seg.get("color", default_colors[i % len(default_colors)])
        legend_items.append(f'<div style="display:flex;align-items:center;gap:8px;"><span style="width:14px;height:14px;border-radius:4px;background:{color};flex-shrink:0;"></span><span style="font-size:var(--type-label);">{_esc(seg["label"])} ({seg["value"]})</span></div>')

    # Side bars if provided
    side_bars = data.get("sideBars", [])
    side_bars_html = ""
    if side_bars:
        sb_max = max(sb.get("value", 0) for sb in side_bars) if side_bars else 1
        sb_items = []
        for sb in side_bars:
            sb_pct = (sb["value"] / sb_max * 100) if sb_max else 0
            sb_items.append(f"""<div style="display:flex;align-items:center;gap:12px;">
  <span style="min-width:100px;font-size:var(--type-label);text-align:right;">{_esc(sb.get("label", ""))}</span>
  <div style="flex:1;background:var(--c-primary-light);border-radius:6px;height:28px;overflow:hidden;">
    <div style="width:{sb_pct:.1f}%;height:100%;background:var(--c-primary);border-radius:6px;"></div>
  </div>
  <span style="font-size:var(--type-label);font-weight:600;min-width:40px;">{sb["value"]}</span>
</div>""")
        side_bars_html = f'<div style="display:flex;flex-direction:column;gap:8px;margin-top:16px;">{chr(10).join(sb_items)}</div>'

    return f"""<div style="display:flex;align-items:center;gap:48px;flex:1;justify-content:center;">
  <div style="flex-shrink:0;">
    <svg width="240" height="240" viewBox="0 0 240 240">
      {chr(10).join(paths)}
      {center_html}
    </svg>
  </div>
  <div style="display:flex;flex-direction:column;gap:12px;flex:1;">
    <p style="font-size:var(--type-small);font-weight:600;margin:0;">{_esc(title)}</p>
    {chr(10).join(legend_items)}
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

    header = '<div style="min-width:140px;"></div>' + "".join(
        f'<div style="flex:1;text-align:center;font-weight:700;font-size:var(--type-body);color:var(--c-primary);">{_esc(item.get("name", ""))}</div>'
        for item in items
    )

    rows = []
    for key in all_keys:
        cells = f'<div style="min-width:140px;font-size:var(--type-small);color:var(--c-text-muted);">{_esc(key)}</div>'
        for item in items:
            val = item.get("metrics", {}).get(key, "—")
            cells += f'<div style="flex:1;text-align:center;font-size:var(--type-body);font-weight:500;">{_esc(str(val))}</div>'
        rows.append(f'<div style="display:flex;align-items:center;gap:16px;padding:16px 0;border-bottom:1px solid rgba(0,0,0,0.06);">{cells}</div>')

    return f"""<div style="display:flex;flex-direction:column;gap:16px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  <div style="background:white;border-radius:16px;padding:24px 32px;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
    <div style="display:flex;align-items:center;gap:16px;padding-bottom:16px;border-bottom:2px solid var(--c-primary-light);">{header}</div>
    {chr(10).join(rows)}
  </div>
</div>"""


def _render_funnel(title: str, data: dict) -> str:
    stages = data.get("stages", [])
    if not stages:
        return ""
    max_val = stages[0].get("value", 1)
    if max_val == 0:
        max_val = 1

    bars = []
    for i, stage in enumerate(stages):
        pct = stage["value"] / max_val * 100
        margin = (100 - pct) / 2
        excluded = stage.get("excluded", "")
        excl_html = ""
        if excluded:
            excl_html = f'<span style="font-size:var(--type-label);color:var(--c-accent);white-space:nowrap;">&#8592; {_esc(str(excluded))}</span>'
        bars.append(f"""<div style="display:flex;align-items:center;gap:16px;">
  <span style="min-width:140px;text-align:right;font-size:var(--type-small);">{_esc(stage["label"])}</span>
  <div style="flex:1;position:relative;">
    <div style="margin-left:{margin:.1f}%;width:{pct:.1f}%;height:48px;background:var(--c-primary);border-radius:8px;opacity:{1 - i * 0.15:.2f};display:flex;align-items:center;justify-content:center;">
      <span style="color:white;font-weight:600;font-size:var(--type-small);">{stage["value"]}</span>
    </div>
  </div>
  {excl_html}
</div>""")

    # Side stats if provided
    side_stats = data.get("sideStats", [])
    side_html = ""
    if side_stats:
        stat_items = []
        for ss in side_stats:
            stat_items.append(f'<div style="text-align:center;"><div style="font-size:var(--type-subtitle);font-weight:700;color:var(--c-primary);">{_esc(str(ss.get("value", "")))}</div><div style="font-size:var(--type-label);color:var(--c-text-muted);">{_esc(ss.get("label", ""))}</div></div>')
        side_html = f'<div style="min-width:140px;display:flex;flex-direction:column;gap:20px;justify-content:center;">{chr(10).join(stat_items)}</div>'

    funnel_content = f"""<div style="display:flex;flex-direction:column;gap:12px;flex:1;">
  {chr(10).join(bars)}
</div>"""

    if side_html:
        funnel_content = f"""<div style="display:flex;gap:32px;flex:1;align-items:center;">
  <div style="display:flex;flex-direction:column;gap:12px;flex:1;">
    {chr(10).join(bars)}
  </div>
  {side_html}
</div>"""

    return f"""<div style="display:flex;flex-direction:column;gap:16px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  {funnel_content}
</div>"""


def _render_steps(title: str, data: dict) -> str:
    steps = data.get("steps", [])
    if not steps:
        return ""

    items = []
    for step in steps:
        num = step.get("number", "")
        items.append(f"""<div style="display:flex;gap:20px;align-items:flex-start;">
  <div style="width:48px;height:48px;border-radius:50%;background:var(--c-primary);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:var(--type-small);flex-shrink:0;">{num}</div>
  <div style="flex:1;">
    <p style="margin:0;font-weight:600;font-size:var(--type-body);">{_esc(step.get("title", ""))}</p>
    <p style="margin:4px 0 0;font-size:var(--type-small);color:var(--c-text-muted);line-height:1.4;">{_esc(step.get("description", ""))}</p>
  </div>
</div>""")

    return f"""<div style="display:flex;flex-direction:column;gap:24px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  {chr(10).join(items)}
</div>"""


def _render_proportion(title: str, data: dict) -> str:
    blocks = data.get("blocks", [])
    total = data.get("total", sum(b.get("count", 0) for b in blocks))
    if not blocks or total == 0:
        return ""

    default_colors = WARM_SERIF.chart_colors
    cells = []
    for i, b in enumerate(blocks):
        color = b.get("color", default_colors[i % len(default_colors)])
        for _ in range(b.get("count", 0)):
            cells.append(f'<div style="width:40px;height:40px;border-radius:6px;background:{color};"></div>')

    legend = []
    for i, b in enumerate(blocks):
        color = b.get("color", default_colors[i % len(default_colors)])
        pct = b.get("count", 0) / total * 100
        legend.append(f'<div style="display:flex;align-items:center;gap:8px;"><span style="width:14px;height:14px;border-radius:4px;background:{color};"></span><span style="font-size:var(--type-label);">{_esc(b["label"])} ({pct:.0f}%)</span></div>')

    return f"""<div style="display:flex;flex-direction:column;gap:20px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  <div style="display:flex;flex-wrap:wrap;gap:6px;">
    {chr(10).join(cells)}
  </div>
  <div style="display:flex;gap:24px;">
    {chr(10).join(legend)}
  </div>
</div>"""


def _render_flow(title: str, data: dict) -> str:
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    if not nodes:
        return ""

    # Render nodes with arrows between them
    parts = []
    for i, node in enumerate(nodes):
        parts.append(f"""<div style="background:white;border:2px solid var(--c-primary);border-radius:12px;padding:16px 24px;font-size:var(--type-small);font-weight:600;text-align:center;min-width:120px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">{_esc(node["label"])}</div>""")
        if i < len(nodes) - 1:
            parts.append('<div style="font-size:32px;color:var(--c-primary);display:flex;align-items:center;">&#8594;</div>')

    return f"""<div style="display:flex;flex-direction:column;gap:24px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;justify-content:center;">
    {chr(10).join(parts)}
  </div>
</div>"""


def _render_area_blocks(title: str, data: dict) -> str:
    """Proportional area blocks — large/medium/small rectangles showing relative sizes."""
    blocks = data.get("blocks", [])
    if not blocks:
        return ""

    default_colors = WARM_SERIF.chart_colors

    # Size presets: height and font sizing
    size_map = {
        "large": ("180px", "1fr", "var(--type-subtitle)", "var(--type-small)"),
        "medium": ("140px", "1fr", "var(--type-body)", "var(--type-label)"),
        "small": ("100px", "1fr", "var(--type-small)", "var(--type-label)"),
    }

    block_html = []
    for i, b in enumerate(blocks):
        color = b.get("color", default_colors[i % len(default_colors)])
        size = b.get("size", "medium")
        h, _, val_size, label_size = size_map.get(size, size_map["medium"])
        value = _esc(str(b.get("value", "")))
        label = _esc(b.get("label", ""))
        detail = _esc(b.get("detail", ""))
        sub_detail = _esc(b.get("subDetail", ""))

        detail_html = f'<span style="font-size:{label_size};opacity:0.85;">{detail}</span>' if detail else ""
        sub_html = f'<span style="font-size:{label_size};opacity:0.7;">{sub_detail}</span>' if sub_detail else ""

        block_html.append(f"""<div style="background:{color};border-radius:16px;padding:24px 28px;min-height:{h};display:flex;flex-direction:column;justify-content:space-between;color:white;flex:1;">
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
        side_html = f"""<div style="min-width:260px;background:white;border-radius:16px;padding:24px;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
  <p style="font-size:var(--type-small);font-weight:600;margin:0 0 12px;">{_esc(side_list.get("title", ""))}</p>
  <ul style="margin:0;padding-left:20px;">{li_html}</ul>
</div>"""

    inner = f"""<div style="display:flex;gap:16px;flex:1;align-items:stretch;">
  {chr(10).join(block_html)}
</div>"""

    if side_html:
        inner = f"""<div style="display:flex;gap:32px;flex:1;align-items:stretch;">
  <div style="flex:1;display:flex;flex-direction:column;gap:16px;">
    <div style="display:flex;gap:16px;flex:1;align-items:stretch;">
      {chr(10).join(block_html)}
    </div>
  </div>
  {side_html}
</div>"""

    return f"""<div style="display:flex;flex-direction:column;gap:20px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  {inner}
</div>"""


def _render_stacked_bar(title: str, data: dict) -> str:
    """Horizontal stacked bar with legend and optional callout."""
    segments = data.get("segments", [])
    if not segments:
        return ""

    default_colors = WARM_SERIF.chart_colors
    total = sum(s.get("value", 0) for s in segments)
    if total == 0:
        return ""

    # Build stacked segments
    seg_html = []
    for i, s in enumerate(segments):
        color = s.get("color", default_colors[i % len(default_colors)])
        pct = s["value"] / total * 100
        seg_html.append(f'<div style="width:{pct:.1f}%;height:100%;background:{color};display:flex;align-items:center;justify-content:center;color:white;font-weight:600;font-size:var(--type-label);overflow:hidden;white-space:nowrap;">{pct:.0f}%</div>')

    # Legend
    legend_items = []
    for i, s in enumerate(segments):
        color = s.get("color", default_colors[i % len(default_colors)])
        legend_items.append(f'<div style="display:flex;align-items:center;gap:8px;"><span style="width:14px;height:14px;border-radius:4px;background:{color};flex-shrink:0;"></span><span style="font-size:var(--type-label);">{_esc(s["label"])} ({s["value"]})</span></div>')

    # Country labels if provided
    countries = data.get("countries", [])
    countries_html = ""
    if countries:
        tags = " ".join(f'<span style="background:var(--c-primary-light);color:var(--c-primary);padding:6px 16px;border-radius:20px;font-size:var(--type-label);font-weight:500;">{_esc(c)}</span>' for c in countries)
        countries_html = f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{tags}</div>'

    # Callout if provided
    callout = data.get("callout")
    callout_html = ""
    if callout:
        callout_html = f"""<div style="background:var(--c-accent-light);border-left:4px solid var(--c-accent);border-radius:0 12px 12px 0;padding:16px 24px;">
  <div style="font-size:var(--type-subtitle);font-weight:700;color:var(--c-accent);">{_esc(str(callout.get("value", "")))}</div>
  <div style="font-size:var(--type-label);color:var(--c-text-muted);">{_esc(callout.get("label", ""))}</div>
</div>"""

    return f"""<div style="display:flex;flex-direction:column;gap:20px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  <div style="display:flex;height:64px;border-radius:12px;overflow:hidden;">
    {chr(10).join(seg_html)}
  </div>
  <div style="display:flex;gap:24px;flex-wrap:wrap;">
    {chr(10).join(legend_items)}
  </div>
  {countries_html}
  {callout_html}
</div>"""


def _render_card_grid(title: str, data: dict) -> str:
    """Numbered cards in a grid layout."""
    cards = data.get("cards", [])
    if not cards:
        return ""

    cols = data.get("columns", 2)
    card_html = []
    for c in cards:
        num = c.get("number", "")
        card_html.append(f"""<div style="background:white;border-radius:16px;padding:32px;box-shadow:0 2px 12px rgba(0,0,0,0.06);display:flex;gap:20px;align-items:flex-start;">
  <div style="width:44px;height:44px;border-radius:50%;background:var(--c-primary);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:var(--type-small);flex-shrink:0;">{num}</div>
  <div style="flex:1;">
    <p style="margin:0;font-weight:600;font-size:var(--type-small);">{_esc(c.get("title", ""))}</p>
    <p style="margin:8px 0 0;font-size:var(--type-label);color:var(--c-text-muted);line-height:1.5;">{_esc(c.get("description", ""))}</p>
  </div>
</div>""")

    return f"""<div style="display:flex;flex-direction:column;gap:20px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:20px;">
    {chr(10).join(card_html)}
  </div>
</div>"""


def _render_two_panel(title: str, data: dict) -> str:
    """Side-by-side concept panels with optional tags."""
    left = data.get("left", {})
    right = data.get("right", {})
    if not left and not right:
        return ""

    def _panel(panel: dict) -> str:
        color = panel.get("color", "var(--c-primary)")
        tags = panel.get("tags", [])
        tags_html = ""
        if tags:
            tag_spans = " ".join(
                f'<span style="background:rgba(255,255,255,0.15);padding:6px 14px;border-radius:20px;font-size:var(--type-label);">{_esc(t)}</span>'
                for t in tags
            )
            tags_html = f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;">{tag_spans}</div>'

        return f"""<div style="flex:1;background:{color};border-radius:20px;padding:40px;color:white;display:flex;flex-direction:column;gap:16px;">
  <p style="font-size:var(--type-body);font-weight:700;margin:0;">{_esc(panel.get("title", ""))}</p>
  <p style="font-size:var(--type-small);margin:0;opacity:0.9;line-height:1.5;">{_esc(panel.get("description", ""))}</p>
  {tags_html}
</div>"""

    panels = []
    if left:
        panels.append(_panel(left))
    if right:
        panels.append(_panel(right))

    return f"""<div style="display:flex;flex-direction:column;gap:20px;flex:1;justify-content:center;">
  <p style="font-size:var(--type-small);font-weight:600;margin:0;color:var(--c-text-muted);">{_esc(title)}</p>
  <div style="display:flex;gap:24px;">
    {chr(10).join(panels)}
  </div>
</div>"""


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _esc(s: str) -> str:
    return html.escape(s, quote=True)


# Scene type -> background style
_BG_STYLES = {
    "title": "dark",
    "closing": "dark",
    "significance": "dark",
    "accent": "dark",
    "dark": "dark",
}


def _slide_html(slide: _Slide, index: int) -> str:
    bg = _BG_STYLES.get(slide.slide_type, "")
    bg_class = f" {bg}" if bg else ""

    if slide.slide_type == "title":
        return _title_slide(slide, index)
    if slide.slide_type == "closing":
        return _closing_slide(slide, index)
    return _content_slide(slide, index, bg_class)


def _title_slide(slide: _Slide, index: int) -> str:
    subtitle_html = ""
    if slide.bullets:
        subtitle_html = "\n".join(
            f'      <p class="slide-subtitle">{_esc(b)}</p>' for b in slide.bullets
        )

    return f"""  <section data-label="{_esc(f'{index+1:02d} Title')}">
    <div class="slide-pad dark" style="justify-content: flex-end; gap: 32px; position: relative; overflow: hidden;">
      <svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0;pointer-events:none;opacity:0.12;">
        <circle cx="1600" cy="200" r="320" fill="none" stroke="var(--c-primary)" stroke-width="3"/>
        <circle cx="1650" cy="250" r="200" fill="none" stroke="var(--c-accent)" stroke-width="2"/>
        <rect x="1400" y="600" width="400" height="400" rx="16" fill="none" stroke="var(--c-primary)" stroke-width="2" transform="rotate(15 1600 800)"/>
        <line x1="0" y1="900" x2="800" y2="900" stroke="var(--c-primary)" stroke-width="2" opacity="0.5"/>
      </svg>
      <p class="label">{_esc(slide.bullets[1] if len(slide.bullets) > 1 else '')}</p>
      <h1 class="slide-title" style="font-size: 72px; max-width: 1400px;">{_esc(slide.title)}</h1>
{subtitle_html}
    </div>
  </section>"""


def _closing_slide(slide: _Slide, index: int) -> str:
    body_html = ""
    if slide.body:
        body_html = f'      <p style="font-size: var(--type-body); color: rgba(255,255,255,0.5); margin: 0; max-width: 900px;">{_esc(slide.body)}</p>'

    return f"""  <section data-label="{_esc(f'{index+1:02d} {slide.label}')}">
    <div class="slide-pad dark" style="justify-content: center; align-items: center; gap: 40px; text-align: center; position: relative; overflow: hidden;">
      <svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0;pointer-events:none;opacity:0.08;">
        <circle cx="300" cy="800" r="320" fill="none" stroke="var(--c-primary)" stroke-width="3"/>
        <circle cx="1600" cy="200" r="200" fill="none" stroke="var(--c-accent)" stroke-width="2"/>
        <rect x="100" y="100" width="300" height="300" rx="16" fill="none" stroke="var(--c-primary)" stroke-width="2" transform="rotate(-10 250 250)"/>
      </svg>
      <p class="label" style="font-size: var(--type-small);">Thank You</p>
      <h2 class="slide-title" style="font-size: 56px; max-width: 1200px;">{_esc(slide.title)}</h2>
{body_html}
    </div>
  </section>"""


def _content_slide(slide: _Slide, index: int, bg_class: str) -> str:
    has_image = slide.figure_src is not None
    has_bullets = bool(slide.bullets)
    has_body = bool(slide.body)

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
            items.append(f"""          <div style="display: flex; gap: 16px; align-items: flex-start;">
            <span style="color: var(--c-accent); font-size: 28px; line-height: 1; margin-top: 4px; flex-shrink: 0;">&#9679;</span>
            <span style="font-size: var(--type-body); line-height: 1.5;">{_esc(b)}</span>
          </div>""")
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
        <figure style="max-width: 100%; text-align: center;">
          <img src="{_esc(slide.figure_src or "")}" alt="{_esc(slide.figure_caption or slide.title)}" style="max-width: 100%; max-height: 560px; object-fit: contain; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.12);">{cap}
        </figure>
      </div>"""

    # Layout: split if image, full if not
    if has_image and (has_body or has_bullets):
        body_html = f"""    <div style="display: flex; gap: 64px; flex: 1; align-items: center; margin-top: 16px;">
      <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 24px;">
{chr(10).join(content_parts)}
      </div>
{image_html}
    </div>"""
    elif has_image:
        body_html = f"""    <div style="flex: 1; display: flex; align-items: center; justify-content: center; margin-top: 16px;">
{image_html}
    </div>"""
    else:
        body_html = f"""    <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 24px; margin-top: 16px;">
{chr(10).join(content_parts)}
    </div>"""

    return f"""  <section data-label="{_esc(f'{index+1:02d} {slide.label or slide.slide_type.title()}')}">
    <div class="slide-pad{bg_class}" style="gap: var(--gap-title);">
      <p class="label">{_esc(slide.label)}</p>
      <h2 class="slide-title">{_esc(slide.title)}</h2>
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
    slides_html = "\n\n".join(_slide_html(s, i) for i, s in enumerate(slides))

    # Speaker notes JSON
    import json
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

