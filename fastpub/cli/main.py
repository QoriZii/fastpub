"""fastpub CLI

Commands:
  analyze <pdf>       Parse paper and produce analysis.json (PaperDocument)
  render <analysis>   Render analysis.json into output format(s)
  go <pdf>            One-shot: analyze + render
"""
from __future__ import annotations

import datetime
import json
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Optional

import typer

from fastpub import config

def _version_callback(value: bool):
    if value:
        typer.echo(f"fastpub {pkg_version('fastpub')}")
        raise typer.Exit()

app = typer.Typer(help="Transform academic papers into promotional multimedia materials.")

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-V", callback=_version_callback, is_eager=True, help="Show version and exit"),
):
    pass


# ── helpers ───────────────────────────────────────────────────────────────────

def _outdir(name: str, base: Optional[Path] = None) -> Path:
    return (base or config.OUTPUT_DIR) / name


# ── analyze ───────────────────────────────────────────────────────────────────

@app.command()
def analyze(
    pdf: Path = typer.Argument(..., help="Path to PDF file"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output path for analysis.json"),
    parser: str = typer.Option("pymupdf", "-p", "--parser", help="PDF parser: pymupdf | mineru | mineru-cloud"),
    audience: str = typer.Option("academic", "--audience", help="Target audience: academic | general"),
):
    """Parse a paper PDF and produce analysis.json (PaperDocument)."""
    from fastpub.pipeline.parse_pdf import parse_pdf
    from fastpub.pipeline.analyze import analyze_paper

    pdf = pdf.expanduser().resolve()
    if not pdf.exists():
        typer.echo(f"Error: {pdf} not found.", err=True)
        raise typer.Exit(1)

    base_name = pdf.stem
    out_path = output or config.OUTPUT_DIR / f"{base_name}.analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Parsing: {pdf.name} (parser={parser})")
    parsed = parse_pdf(str(pdf), parser=parser)
    typer.echo(f"  {parsed.page_count} pages, {len(parsed.images)} images")

    doc = analyze_paper(parsed.text, parsed.images, audience=audience)
    doc.save(out_path)

    typer.echo(f"\nDone! \"{doc.meta.title}\"")
    typer.echo(f"  Sections: {len(doc.sections)}")
    typer.echo(f"  Figures: {len(doc.figures)}")
    typer.echo(f"  Output: {out_path}")


# ── render ────────────────────────────────────────────────────────────────────

@app.command()
def render(
    analysis: Path = typer.Argument(..., help="Path to analysis.json"),
    format: str = typer.Option("web", "-f", "--format", help="Comma-separated: web, slides, video"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output path"),
    aspect: str = typer.Option("4:3", "--aspect", help="Slide aspect ratio: 4:3 | 16:9"),
    voice: Optional[str] = typer.Option(None, "--voice", help="TTS voice: eve, ara, rex, sal, leo"),
    no_audio: bool = typer.Option(False, "--no-audio", help="Skip audio generation"),
    image_provider: Optional[str] = typer.Option(None, "--image-provider", help="Image generation provider: xai"),
):
    """Render analysis.json into output format(s)."""
    from fastpub.models import PaperDocument

    analysis = analysis.expanduser().resolve()
    if not analysis.exists():
        typer.echo(f"Error: {analysis} not found.", err=True)
        raise typer.Exit(1)

    doc = PaperDocument.load(analysis)
    formats = [f.strip() for f in format.split(",")]
    base_name = analysis.stem.replace(".analysis", "")
    out_dir = output.parent if output else analysis.parent

    for fmt in formats:
        match fmt:
            case "web":
                from fastpub.pipeline.translate import translate_to_chinese
                from fastpub.render.web import render_web

                typer.echo(f"Rendering web page…")
                zh = translate_to_chinese(doc)
                out_path = output or out_dir / f"{base_name}.html"
                result = render_web(doc, zh, out_path)
                typer.echo(f"  Web page: {result}")

            case "slides":
                from fastpub.render.slides import render_slides

                out_path = output or out_dir / f"{base_name}.slides.html"
                result = render_slides(doc, out_path, no_audio=no_audio, aspect=aspect, image_provider=image_provider)
                typer.echo(f"  Slides: {result}")

            case "video":
                from fastpub.render.video import render_video

                out_path = output or out_dir / f"{base_name}.mp4"
                result = render_video(doc, out_path, no_audio=no_audio)
                typer.echo(f"  Video: {result}")

            case _:
                typer.echo(f"Unknown format: {fmt}", err=True)
                raise typer.Exit(1)


# ── go ────────────────────────────────────────────────────────────────────────

@app.command()
def go(
    pdf: Path = typer.Argument(..., help="Path to PDF file"),
    format: str = typer.Option("web", "-f", "--format", help="Comma-separated: web, slides, video"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output directory"),
    parser: str = typer.Option("pymupdf", "-p", "--parser", help="PDF parser: pymupdf | mineru | mineru-cloud"),
    audience: str = typer.Option("academic", "--audience", help="Target audience: academic | general"),
    aspect: str = typer.Option("4:3", "--aspect", help="Slide aspect ratio: 4:3 | 16:9"),
    voice: Optional[str] = typer.Option(None, "--voice", help="TTS voice: eve, ara, rex, sal, leo"),
    no_audio: bool = typer.Option(False, "--no-audio", help="Skip audio generation"),
    image_provider: Optional[str] = typer.Option(None, "--image-provider", help="Image generation provider: xai"),
):
    """One-shot: analyze + render without manual editing."""
    from fastpub.pipeline.parse_pdf import parse_pdf
    from fastpub.pipeline.analyze import analyze_paper

    pdf = pdf.expanduser().resolve()
    if not pdf.exists():
        typer.echo(f"Error: {pdf} not found.", err=True)
        raise typer.Exit(1)

    base_name = pdf.stem
    out_dir = (output or config.OUTPUT_DIR).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Analyze ---
    typer.echo("\n--- Step 1/2: Analyzing paper ---")
    parsed = parse_pdf(str(pdf), parser=parser)
    typer.echo(f"  {parsed.page_count} pages, {len(parsed.images)} images")

    doc = analyze_paper(parsed.text, parsed.images, audience=audience)
    analysis_path = out_dir / f"{base_name}.analysis.json"
    doc.save(analysis_path)
    typer.echo(f"  Analysis: {analysis_path}")

    # --- Step 2: Render ---
    typer.echo("\n--- Step 2/2: Rendering outputs ---")
    formats = [f.strip() for f in format.split(",")]

    for fmt in formats:
        match fmt:
            case "web":
                from fastpub.pipeline.translate import translate_to_chinese
                from fastpub.render.web import render_web

                zh = translate_to_chinese(doc)
                result = render_web(doc, zh, out_dir / f"{base_name}.html")
                typer.echo(f"  Web page: {result}")

            case "slides":
                from fastpub.render.slides import render_slides
                result = render_slides(doc, out_dir / f"{base_name}.slides.html", no_audio=no_audio, aspect=aspect, image_provider=image_provider)
                typer.echo(f"  Slides: {result}")

            case "video":
                from fastpub.render.video import render_video
                result = render_video(doc, out_dir / f"{base_name}.mp4", no_audio=no_audio)
                typer.echo(f"  Video: {result}")

            case _:
                typer.echo(f"Unknown format: {fmt}", err=True)
                raise typer.Exit(1)

    typer.echo("\nDone! All outputs generated.")


if __name__ == "__main__":
    app()
