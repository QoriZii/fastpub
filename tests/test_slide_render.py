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
