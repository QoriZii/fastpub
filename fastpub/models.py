from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class PaperMeta:
    title: str
    authors: list[str]
    venue: str = ""
    year: int | None = None
    abstract: str = ""
    keywords: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> PaperMeta:
        return PaperMeta(
            title=d.get("title", ""),
            authors=d.get("authors", []),
            venue=d.get("venue", ""),
            year=d.get("year"),
            abstract=d.get("abstract", ""),
            keywords=d.get("keywords", []),
        )


@dataclass
class SubIssue:
    title: str
    description: str

    @staticmethod
    def from_dict(d: dict) -> SubIssue:
        return SubIssue(
            title=d.get("title", ""),
            description=d.get("description", ""),
        )


@dataclass
class WebSection:
    """One of the 5 fixed web sections: problem, approach, meaning, result, limitation."""
    type: str
    summary: str
    sub_issues: list[SubIssue] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> WebSection:
        return WebSection(
            type=d.get("type", ""),
            summary=d.get("summary", ""),
            sub_issues=[
                SubIssue.from_dict(si)
                for si in d.get("subIssues", d.get("sub_issues", []))
            ],
        )


@dataclass
class VisualizationData:
    """Data for an HTML/CSS visualization to replace a paper figure."""
    viz_type: str          # bar_chart | stat_card | donut_chart | comparison | funnel | steps | proportion | flow
    title: str
    data: dict = field(default_factory=dict)

    @staticmethod
    def from_dict(d: dict) -> VisualizationData:
        return VisualizationData(
            viz_type=d.get("vizType", d.get("viz_type", "")),
            title=d.get("title", ""),
            data=d.get("data", {}),
        )


@dataclass
class PaperFigure:
    id: str
    src: str
    caption: str
    ai_description: str = ""
    page_number: int = 0
    type: str = "diagram"        # chart | diagram | table | photo | equation
    visualization: VisualizationData | None = None

    @staticmethod
    def from_dict(d: dict) -> PaperFigure:
        viz_raw = d.get("visualization")
        return PaperFigure(
            id=d["id"],
            src=d.get("src", ""),
            caption=d.get("caption", ""),
            ai_description=d.get("aiDescription", d.get("ai_description", "")),
            page_number=int(d.get("pageNumber", d.get("page_number", 0))),
            type=d.get("type", "diagram"),
            visualization=VisualizationData.from_dict(viz_raw) if viz_raw else None,
        )


@dataclass
class SlideSpec:
    """One slide in the presentation, produced by the LLM."""
    id: str
    layout: str            # title | section_header | content | figure | two_column | closing
    title: str
    section: str = ""      # e.g. "Context", "Methods", "Results", "Discussion"
    subtitle: str = ""
    bullets: list[str] = field(default_factory=list)
    explanation: str = ""  # what this slide shows and why it matters
    narrative: str = ""    # story thread connecting to the next slide
    figure_ref: str = ""
    visualization: VisualizationData | None = None

    @staticmethod
    def from_dict(d: dict) -> SlideSpec:
        viz_raw = d.get("visualization")
        return SlideSpec(
            id=d.get("id", ""),
            layout=d.get("layout", "content"),
            title=d.get("title", ""),
            section=d.get("section", ""),
            subtitle=d.get("subtitle", ""),
            bullets=d.get("bullets", []),
            explanation=d.get("explanation", ""),
            narrative=d.get("narrative", ""),
            figure_ref=d.get("figureRef", d.get("figure_ref", "")),
            visualization=VisualizationData.from_dict(viz_raw) if viz_raw else None,
        )


@dataclass
class PaperDocument:
    meta: PaperMeta
    hook: str = ""
    web_sections: list[WebSection] = field(default_factory=list)
    figures: list[PaperFigure] = field(default_factory=list)
    slides: list[SlideSpec] = field(default_factory=list)
    zh: dict = field(default_factory=dict)

    # ── Serialisation ──────────────────────────────────────────────

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2))

    @staticmethod
    def from_dict(raw: dict) -> PaperDocument:
        return PaperDocument(
            meta=PaperMeta.from_dict(raw.get("meta", {})),
            hook=raw.get("hook", ""),
            web_sections=[
                WebSection.from_dict(s)
                for s in raw.get("webSections", raw.get("web_sections", []))
            ],
            figures=[PaperFigure.from_dict(f) for f in raw.get("figures", [])],
            slides=[SlideSpec.from_dict(s) for s in raw.get("slides", [])],
            zh=raw.get("zh", {}),
        )

    @staticmethod
    def load(path: Path) -> PaperDocument:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return PaperDocument.from_dict(raw)
