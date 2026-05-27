from fastpub.models import PaperDocument, PaperMeta, WebSection, SubIssue
from fastpub.render.web import _build_html


def _make_doc():
    return PaperDocument(
        meta=PaperMeta(
            title="Test Paper",
            authors=["Alice", "Bob"],
            venue="Test Journal",
            year=2026,
            abstract="An abstract.",
            keywords=["kw1", "kw2"],
        ),
        hook="This matters because...",
        web_sections=[
            WebSection(
                type="problem",
                summary="A summary.",
                sub_issues=[SubIssue(title="Issue 1", description="Desc 1")],
            ),
        ],
    )


def _make_zh():
    return {
        "meta": {"title": "测试论文", "abstract": "摘要"},
        "hook": "这很重要因为...",
        "webSections": [
            {"type": "problem", "summary": "总结", "subIssues": [{"title": "问题1", "description": "描述1"}]}
        ],
    }


def test_web_uses_warm_serif_colors():
    html = _build_html(_make_doc(), _make_zh())
    assert "#F2EDE8" in html  # linen bg
    assert "#9B6B3D" in html  # copper primary
    assert "#2E2A26" in html  # charcoal
    assert "Playfair Display" in html
    assert "Inter" in html


def test_web_no_dark_mode():
    html = _build_html(_make_doc(), _make_zh())
    assert "prefers-color-scheme" not in html


def test_web_no_section_badges():
    html = _build_html(_make_doc(), _make_zh())
    assert 'class="badge' not in html


def test_web_sub_issues_left_border():
    html = _build_html(_make_doc(), _make_zh())
    # CSS should contain left border for sub-issues
    assert "sub-issues" in html
    # No card-style borders on individual sub-issues
    assert 'class="sub-issue"' in html


def test_web_header_is_dark_band():
    html = _build_html(_make_doc(), _make_zh())
    assert '<header' in html
    assert "#2E2A26" in html


def test_web_keywords_bordered_pills():
    html = _build_html(_make_doc(), _make_zh())
    assert "kw1" in html
    css_section = html.split("<style>")[1].split("</style>")[0]
    assert "border:" in css_section or "border: 1px solid" in css_section


def test_web_lang_toggle_works():
    html = _build_html(_make_doc(), _make_zh())
    assert "setLang" in html
    assert 'id="btn-en"' in html
    assert 'id="btn-zh"' in html


def test_web_has_font_import():
    html = _build_html(_make_doc(), _make_zh())
    assert "fonts.googleapis.com" in html
    assert "<link" in html


def test_web_has_accent_lines():
    html = _build_html(_make_doc(), _make_zh())
    assert 'class="accent-line"' in html


def test_web_has_content_wrapper():
    html = _build_html(_make_doc(), _make_zh())
    assert 'class="content"' in html
