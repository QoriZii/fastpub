"""PDF parsing — extract text and images from academic papers."""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedPdf:
    text: str
    images: list[str] = field(default_factory=list)  # base64 data URLs
    page_count: int = 0
    parser: str = "pymupdf"


def parse_pdf(pdf_path: str, parser: str = "pymupdf") -> ParsedPdf:
    """Parse PDF and extract text + images."""
    match parser:
        case "pymupdf":
            return _parse_with_pymupdf(pdf_path)
        case "mineru":
            return _parse_with_mineru(pdf_path)
        case "mineru-cloud":
            return _parse_with_mineru_cloud(pdf_path)
        case _:
            raise ValueError(f"Unknown parser: {parser}")


def _parse_with_pymupdf(pdf_path: str) -> ParsedPdf:
    """Extract text and images using PyMuPDF (fitz).

    Per-page strategy:
    - If a page has usable raster images, extract them (highest quality).
    - Otherwise, if a page has many vector drawings (charts/diagrams),
      render the full page as a screenshot to capture them.
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("pip install pymupdf")

    doc = fitz.open(pdf_path)
    pages_text: list[str] = []
    images: list[str] = []

    MIN_IMAGE_AREA = 150 * 150
    MIN_DRAWINGS_FOR_FIGURE = 20
    PAGE_RENDER_DPI = 150
    # Cap page renders to avoid flooding context with supplementary tables
    MAX_PAGE_RENDERS = 6

    page_render_count = 0

    for page in doc:
        pages_text.append(page.get_text())

        # Try raster images first
        page_has_raster = False
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.width * pix.height < MIN_IMAGE_AREA:
                    continue
                if pix.n > 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img_bytes = pix.tobytes("png")
                b64 = base64.b64encode(img_bytes).decode()
                images.append(f"data:image/png;base64,{b64}")
                page_has_raster = True
            except Exception:
                continue

        # No raster on this page — check for vector figures
        if not page_has_raster and page_render_count < MAX_PAGE_RENDERS:
            drawings = page.get_drawings()
            if len(drawings) >= MIN_DRAWINGS_FOR_FIGURE:
                try:
                    mat = fitz.Matrix(PAGE_RENDER_DPI / 72, PAGE_RENDER_DPI / 72)
                    pix = page.get_pixmap(matrix=mat)
                    img_bytes = pix.tobytes("png")
                    b64 = base64.b64encode(img_bytes).decode()
                    images.append(f"data:image/png;base64,{b64}")
                    page_render_count += 1
                except Exception:
                    continue

    text = "\n\n".join(pages_text)
    return ParsedPdf(text=text, images=images, page_count=len(doc), parser="pymupdf")


def _parse_with_mineru(pdf_path: str) -> ParsedPdf:
    """MinerU self-hosted parser."""
    raise NotImplementedError("MinerU parser not yet implemented")


def _parse_with_mineru_cloud(pdf_path: str) -> ParsedPdf:
    """MinerU cloud parser."""
    raise NotImplementedError("MinerU Cloud parser not yet implemented")
