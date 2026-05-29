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


def test_web_uses_warm_colors():
    html = _build_html(_make_doc(), _make_zh())
    assert "#F2EDE8" in html  # linen bg
    assert "#9B6B3D" in html  # copper primary
    assert "#2E2A26" in html  # charcoal


def test_web_has_dark_mode():
    html = _build_html(_make_doc(), _make_zh())
    assert "prefers-color-scheme" in html


def test_web_has_section_badges():
    html = _build_html(_make_doc(), _make_zh())
    assert 'class="badge' in html


def test_web_has_narrative_cards():
    html = _build_html(_make_doc(), _make_zh())
    assert 'class="narrative-grid"' in html
    assert 'class="card"' in html


def test_web_has_paper_sections_with_bullets():
    html = _build_html(_make_doc(), _make_zh())
    assert 'class="paper-section"' in html
    assert "<li>" in html


def test_web_centered_layout():
    html = _build_html(_make_doc(), _make_zh())
    assert "max-width: var(--max-w)" in html


def test_web_keywords_as_pills():
    html = _build_html(_make_doc(), _make_zh())
    assert "kw1" in html
    assert 'class="tag"' in html


def test_web_lang_toggle_works():
    html = _build_html(_make_doc(), _make_zh())
    assert "setLang" in html
    assert 'id="btn-en"' in html
    assert 'id="btn-zh"' in html


def test_web_no_google_fonts():
    html = _build_html(_make_doc(), _make_zh())
    assert "fonts.googleapis.com" not in html


def test_web_system_fonts():
    html = _build_html(_make_doc(), _make_zh())
    assert "-apple-system" in html
