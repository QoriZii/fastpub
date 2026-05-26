"""Slide renderer — produces a print-to-PDF HTML slide deck from a PaperDocument.

Each <section class="slide"> is styled to fill exactly one landscape page when
printed (Ctrl+P / Save as PDF), producing a presentation-style PDF with no
external dependencies.
"""
from __future__ import annotations

import html
from pathlib import Path

from fastpub.models import PaperDocument, PaperFigure


_ASPECT_RATIOS = {
    "4:3":  ("10in", "7.5in"),
    "16:9": ("13.333in", "7.5in"),
}


def render_slides(
    doc: PaperDocument,
    output_path: Path,
    no_audio: bool = False,
    aspect: str = "4:3",
    image_provider: str | None = None,
) -> Path:
    """Render PaperDocument to an HTML slide deck that prints as PDF."""
    if aspect not in _ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect!r}. Use '4:3' or '16:9'.")

    if image_provider:
        from fastpub.pipeline.scene_script import generate_scene_script
        from fastpub.pipeline.image_gen import generate_images
        from fastpub.ai.image_providers import get_provider
        from fastpub import config

        import json
        import typer

        typer.echo("  Generating scene script...")
        scenes = generate_scene_script(doc)

        # Save scenes.json for video stage reuse
        base_name = output_path.stem.replace(".slides", "")
        assets_dir = output_path.parent / base_name
        scenes_path = output_path.parent / f"{base_name}.scenes.json"
        scenes_path.write_text(json.dumps(scenes, ensure_ascii=False, indent=2))

        typer.echo(f"  Generating images ({image_provider})...")
        provider = get_provider(image_provider, api_key=config.XAI_API_KEY)
        images_dir = assets_dir / "images"
        image_map = generate_images(scenes, provider, images_dir)

        # Convert scenes to _Slide objects for HTML generation
        slides = _slides_from_scenes(scenes, image_map)
    else:
        slides = _build_slides(doc)

    result = _build_html(doc, slides, aspect=aspect)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# Slide data — deterministic mapping from PaperDocument
# ---------------------------------------------------------------------------

class _Slide:
    __slots__ = ("slide_type", "title", "bullets", "figure_id", "figure_src", "figure_caption")

    def __init__(
        self,
        slide_type: str,
        title: str,
        bullets: list[str] | None = None,
        figure_id: str | None = None,
        figure_src: str | None = None,
        figure_caption: str | None = None,
    ):
        self.slide_type = slide_type
        self.title = title
        self.bullets = bullets or []
        self.figure_id = figure_id
        self.figure_src = figure_src
        self.figure_caption = figure_caption


def _resolved_figure_map(doc: PaperDocument) -> dict[str, tuple[str, str]]:
    """figure_id -> (src, caption), preferring generated visuals."""
    gen_map = {v.for_figure_id: v for v in doc.generated_visuals}
    result = {}
    for fig in doc.figures:
        if fig.usability == "skip":
            continue
        gen = gen_map.get(fig.id)
        result[fig.id] = (gen.src if gen else fig.src, fig.caption)
    return result


def _build_slides(doc: PaperDocument) -> list[_Slide]:
    fig_map = _resolved_figure_map(doc)
    slides: list[_Slide] = []

    def _pick_figure(refs: list[str]) -> tuple[str | None, str | None, str | None]:
        for ref in refs:
            if ref in fig_map:
                src, cap = fig_map[ref]
                return ref, src, cap
        return None, None, None

    # 1. Title
    subtitle_parts = []
    if doc.meta.authors:
        subtitle_parts.append(", ".join(doc.meta.authors))
    if doc.meta.venue:
        v = doc.meta.venue
        if doc.meta.year:
            v += f" ({doc.meta.year})"
        subtitle_parts.append(v)
    slides.append(_Slide("title", doc.meta.title, subtitle_parts))

    # 2. Hook
    if doc.narrative.hook:
        slides.append(_Slide("hook", "Why This Matters", [doc.narrative.hook]))

    # 3. Problem
    if doc.narrative.problem:
        slides.append(_Slide("problem", "The Problem", [doc.narrative.problem]))

    # 4. Method sections
    method_sections = [s for s in doc.sections if s.type == "method"]
    for s in method_sections[:3]:
        fid, fsrc, fcap = _pick_figure(s.figure_refs)
        slides.append(_Slide(
            "method", s.title, s.key_points[:4],
            figure_id=fid, figure_src=fsrc, figure_caption=fcap,
        ))
    if not method_sections and doc.narrative.approach:
        slides.append(_Slide("method", "Our Approach", [doc.narrative.approach]))

    # 5. Results
    result_sections = [s for s in doc.sections if s.type in ("result", "experiment")]
    for s in result_sections[:3]:
        fid, fsrc, fcap = _pick_figure(s.figure_refs)
        slides.append(_Slide(
            "results", s.title, s.key_points[:4],
            figure_id=fid, figure_src=fsrc, figure_caption=fcap,
        ))
    if not result_sections and doc.narrative.results:
        slides.append(_Slide("results", "Key Results", doc.narrative.results[:4]))

    # 6. Significance
    if doc.narrative.significance:
        slides.append(_Slide("significance", "Why It Matters", [doc.narrative.significance]))

    # 7. Takeaway
    takeaway_bullets = []
    if doc.narrative.approach:
        takeaway_bullets.append(doc.narrative.approach)
    if doc.narrative.results:
        takeaway_bullets.append(doc.narrative.results[0])
    if doc.narrative.significance:
        takeaway_bullets.append(doc.narrative.significance)
    if takeaway_bullets:
        slides.append(_Slide("takeaway", "Key Takeaways", takeaway_bullets[:4]))

    return slides


def _slides_from_scenes(scenes: list[dict], image_map: dict[str, str]) -> list[_Slide]:
    """Convert scene script dicts to _Slide objects for HTML rendering."""
    slides: list[_Slide] = []
    for scene in scenes:
        scene_type = scene.get("sceneType", "other")
        headline = scene.get("headline", "")
        body = scene.get("body", "")
        scene_id = scene.get("id", "")

        bullets = [body] if body else []
        figure_src = image_map.get(scene_id)

        slides.append(_Slide(
            slide_type=scene_type,
            title=headline,
            bullets=bullets,
            figure_src=figure_src,
        ))
    return slides


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _esc(s: str) -> str:
    return html.escape(s, quote=True)


_TYPE_COLORS = {
    "title": "#1E3A5F",
    "hook": "#7C3AED",
    "problem": "#DC2626",
    "method": "#2563EB",
    "approach": "#2563EB",
    "results": "#059669",
    "significance": "#D97706",
    "closing": "#1E3A5F",
    "takeaway": "#1E3A5F",
}


def _slide_html(slide: _Slide, index: int) -> str:
    color = _TYPE_COLORS.get(slide.slide_type, "#333")

    if slide.slide_type == "title":
        # Title slide — centered layout
        bullets_html = ""
        if slide.bullets:
            bullets_html = "\n".join(
                f'      <p class="subtitle">{_esc(b)}</p>' for b in slide.bullets
            )
        return f"""<section class="slide slide-title" style="--accent:{color}">
  <div class="slide-inner">
    <div class="slide-center">
      <h1>{_esc(slide.title)}</h1>
{bullets_html}
    </div>
  </div>
  <div class="slide-footer"><span class="slide-num">{index + 1}</span><span class="slide-brand">FastPub</span></div>
</section>"""

    # Content slide
    has_figure = slide.figure_src is not None
    content_class = "slide-split" if has_figure else "slide-full"

    bullets_html = ""
    if slide.bullets:
        items = "\n        ".join(f"<li>{_esc(b)}</li>" for b in slide.bullets)
        bullets_html = f"""      <ul>
        {items}
      </ul>"""

    figure_html = ""
    if has_figure:
        cap = f'\n        <figcaption>{_esc(slide.figure_caption or "")}</figcaption>' if slide.figure_caption else ""
        figure_html = f"""    <div class="slide-figure">
      <figure>
        <img src="{_esc(slide.figure_src or "")}" alt="{_esc(slide.figure_caption or "")}">
{cap}
      </figure>
    </div>"""

    badge = slide.slide_type.upper()

    return f"""<section class="slide {content_class}" style="--accent:{color}">
  <div class="slide-inner">
    <div class="slide-header">
      <span class="badge">{badge}</span>
      <h2>{_esc(slide.title)}</h2>
    </div>
    <div class="slide-body">
      <div class="slide-content">
{bullets_html}
      </div>
{figure_html}
    </div>
  </div>
  <div class="slide-footer"><span class="slide-num">{index + 1}</span><span class="slide-brand">FastPub</span></div>
</section>"""


def _build_html(doc: PaperDocument, slides: list[_Slide], aspect: str = "4:3") -> str:
    slides_html = "\n\n".join(_slide_html(s, i) for i, s in enumerate(slides))
    w, h = _ASPECT_RATIOS[aspect]
    styles = _build_styles(w, h)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(doc.meta.title)} — Slides</title>
{styles}
</head>
<body>
{slides_html}
{_SCRIPT}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Styles — landscape slides that map 1:1 to PDF pages when printed
# ---------------------------------------------------------------------------

def _build_styles(page_w: str, page_h: str) -> str:
    return f"""<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

  @page {{
    size: {page_w} {page_h};
    margin: 0;
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', sans-serif;
    background: #e5e7eb;
    margin: 0;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2rem;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  /* --- Slide container --- */
  .slide {{
    width: {page_w};
    height: {page_h};
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 24px rgba(0,0,0,.12);
    overflow: hidden;
    position: relative;
    page-break-after: always;
    page-break-inside: avoid;
  }}
  .slide-inner {{
    position: absolute;
    top: 0.8in;
    left: 1in;
    right: 1in;
    bottom: 0.8in;
    display: flex;
    flex-direction: column;
  }}
  .slide-footer {{
    position: absolute;
    bottom: 0.25in;
    left: 0.5in;
    right: 0.5in;
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #aaa;
    font-weight: 600;
  }}
  .slide-title .slide-footer {{ color: rgba(255,255,255,.45); }}

  /* --- Title slide --- */
  .slide-title {{
    background: linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 70%, #000) 100%);
    color: #fff;
  }}
  .slide-title .slide-inner {{
    justify-content: center;
    align-items: center;
    text-align: center;
  }}
  .slide-title h1 {{
    font-size: 2.8rem;
    line-height: 1.25;
    max-width: 85%;
    margin-bottom: 0.6rem;
  }}
  .slide-title .subtitle {{
    font-size: 1.15rem;
    opacity: 0.85;
    margin-top: 0.25rem;
  }}

  /* --- Content slides --- */
  .slide-header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5in;
    border-bottom: 3px solid var(--accent);
    padding-bottom: 0.35in;
  }}
  .badge {{
    background: var(--accent);
    color: #fff;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 0.2em 0.6em;
    border-radius: 4px;
    letter-spacing: 0.06em;
    white-space: nowrap;
  }}
  h2 {{
    font-size: 2rem;
    color: #1a1a1a;
    line-height: 1.2;
  }}

  .slide-body {{
    flex: 1;
    display: flex;
    gap: 1in;
    min-height: 0;
  }}
  .slide-content {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }}
  .slide-figure {{
    flex: 0 0 45%;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .slide-figure figure {{
    max-width: 100%;
    max-height: 100%;
    text-align: center;
  }}
  .slide-figure img {{
    max-width: 100%;
    max-height: 4in;
    object-fit: contain;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
  }}
  .slide-figure figcaption {{
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 0.4rem;
  }}

  ul {{
    list-style: none;
    padding: 0;
  }}
  li {{
    font-size: 1.35rem;
    line-height: 1.5;
    color: #374151;
    padding: 0.35em 0 0.35em 1.5em;
    position: relative;
  }}
  li::before {{
    content: '';
    position: absolute;
    left: 0;
    top: 0.7em;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent);
  }}

  /* --- Print --- */
  @media print {{
    body {{
      background: none;
      padding: 0;
      gap: 0;
    }}
    .slide {{
      box-shadow: none;
      border-radius: 0;
      width: {page_w};
      height: {page_h};
    }}
  }}
</style>"""


_SCRIPT = """<script>
// Keyboard navigation for screen preview: arrow keys scroll between slides
document.addEventListener('keydown', (e) => {
  const slides = document.querySelectorAll('.slide');
  if (!slides.length) return;
  const vh = window.innerHeight;
  const current = Math.round(window.scrollY / (vh * 0.9));
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
    e.preventDefault();
    const next = Math.min(current + 1, slides.length - 1);
    slides[next].scrollIntoView({ behavior: 'smooth' });
  } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
    e.preventDefault();
    const prev = Math.max(current - 1, 0);
    slides[prev].scrollIntoView({ behavior: 'smooth' });
  }
});
</script>"""
