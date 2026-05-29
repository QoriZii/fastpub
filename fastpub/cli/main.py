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

def _get_zh(doc) -> dict:
    """Return zh translations from doc."""
    if doc.zh:
        return doc.zh
    typer.echo("  Warning: no zh translations found. Re-run analysis to generate them.", err=True)
    return {}


def _resolve_pdf(pdf: str) -> tuple[str, str]:
    """Validate PDF path/URL and return (resolved_path, base_name)."""
    from fastpub.pipeline.parse_pdf import _is_url
    if _is_url(pdf):
        base_name = Path(pdf.split("?")[0].split("#")[0]).stem or "paper"
        return pdf, base_name
    pdf_path = Path(pdf).expanduser().resolve()
    if not pdf_path.exists():
        typer.echo(f"Error: {pdf_path} not found.", err=True)
        raise typer.Exit(1)
    return str(pdf_path), pdf_path.stem


# ── analyze ───────────────────────────────────────────────────────────────────

@app.command()
def analyze(
    pdf: str = typer.Argument(..., help="Path or URL to PDF file"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output path for analysis.json"),
    parser: str = typer.Option("pymupdf", "-p", "--parser", help="PDF parser: pymupdf | mineru | mineru-cloud"),
    audience: str = typer.Option("academic", "--audience", help="Target audience: academic | general"),
):
    """Parse a paper PDF and produce analysis.json (PaperDocument)."""
    from fastpub.pipeline.parse_pdf import parse_pdf
    from fastpub.pipeline.analyze import analyze_paper

    pdf, base_name = _resolve_pdf(pdf)
    out_path = output or config.OUTPUT_DIR / f"{base_name}.analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Parsing: {Path(pdf).name} (parser={parser})")
    parsed = parse_pdf(pdf, parser=parser)
    typer.echo(f"  {parsed.page_count} pages, {len(parsed.images)} images")

    doc = analyze_paper(parsed.text, parsed.images, audience=audience)
    doc.save(out_path)

    typer.echo(f"\nDone! \"{doc.meta.title}\"")
    typer.echo(f"  Web sections: {len(doc.web_sections)}")
    typer.echo(f"  Slides: {len(doc.slides)}")
    typer.echo(f"  Figures: {len(doc.figures)}")
    typer.echo(f"  Output: {out_path}")


# ── render ────────────────────────────────────────────────────────────────────

@app.command()
def render(
    analysis: Path = typer.Argument(..., help="Path to analysis.json"),
    format: str = typer.Option("web", "-f", "--format", help="Comma-separated: web, slides"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output path"),
    aspect: str = typer.Option("4:3", "--aspect", help="Slide aspect ratio: 4:3 | 16:9"),
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
                from fastpub.render.web import render_web

                typer.echo(f"Rendering web page…")
                zh = _get_zh(doc)
                out_path = output or out_dir / f"{base_name}.html"
                result = render_web(doc, zh, out_path)
                typer.echo(f"  Web page: {result}")

            case "slides":
                from fastpub.render.slides import render_slides

                out_path = output or out_dir / f"{base_name}.slides.html"
                result = render_slides(doc, out_path, aspect=aspect)
                typer.echo(f"  Slides: {result}")

            case _:
                typer.echo(f"Unknown format: {fmt}", err=True)
                raise typer.Exit(1)


# ── go ────────────────────────────────────────────────────────────────────────

@app.command()
def go(
    pdf: str = typer.Argument(..., help="Path or URL to PDF file"),
    format: str = typer.Option("web", "-f", "--format", help="Comma-separated: web, slides"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output directory"),
    parser: str = typer.Option("pymupdf", "-p", "--parser", help="PDF parser: pymupdf | mineru | mineru-cloud"),
    audience: str = typer.Option("academic", "--audience", help="Target audience: academic | general"),
    aspect: str = typer.Option("4:3", "--aspect", help="Slide aspect ratio: 4:3 | 16:9"),
):
    """One-shot: analyze + render without manual editing."""
    from fastpub.pipeline.parse_pdf import parse_pdf
    from fastpub.pipeline.analyze import analyze_paper

    pdf, base_name = _resolve_pdf(pdf)
    out_dir = (output or config.OUTPUT_DIR).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Analyze ---
    typer.echo("\n--- Step 1/2: Analyzing paper ---")
    parsed = parse_pdf(pdf, parser=parser)
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
                from fastpub.render.web import render_web

                zh = _get_zh(doc)
                result = render_web(doc, zh, out_dir / f"{base_name}.html")
                typer.echo(f"  Web page: {result}")

            case "slides":
                from fastpub.render.slides import render_slides
                result = render_slides(doc, out_dir / f"{base_name}.slides.html", aspect=aspect)
                typer.echo(f"  Slides: {result}")

            case _:
                typer.echo(f"Unknown format: {fmt}", err=True)
                raise typer.Exit(1)

    typer.echo("\nDone! All outputs generated.")


if __name__ == "__main__":
    app()
