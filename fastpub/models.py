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
class PaperSection:
    id: str
    type: str           # problem | method | experiment | result | discussion | other
    title: str
    summary: str
    key_points: list[str] = field(default_factory=list)
    figure_refs: list[str] = field(default_factory=list)
    importance: str = "medium"   # high | medium | low

    @staticmethod
    def from_dict(d: dict) -> PaperSection:
        return PaperSection(
            id=d["id"],
            type=d.get("type", "other"),
            title=d.get("title", ""),
            summary=d.get("summary", ""),
            key_points=d.get("keyPoints", d.get("key_points", [])),
            figure_refs=d.get("figureRefs", d.get("figure_refs", [])),
            importance=d.get("importance", "medium"),
        )


@dataclass
class PaperFigure:
    id: str
    src: str
    caption: str
    ai_description: str = ""
    page_number: int = 0
    type: str = "diagram"        # chart | diagram | table | photo | equation
    usability: str = "use-as-is" # use-as-is | needs-simplification | skip

    @staticmethod
    def from_dict(d: dict) -> PaperFigure:
        return PaperFigure(
            id=d["id"],
            src=d.get("src", ""),
            caption=d.get("caption", ""),
            ai_description=d.get("aiDescription", d.get("ai_description", "")),
            page_number=int(d.get("pageNumber", d.get("page_number", 0))),
            type=d.get("type", "diagram"),
            usability=d.get("usability", "use-as-is"),
        )


@dataclass
class GeneratedVisual:
    id: str
    for_figure_id: str
    src: str
    description: str = ""
    generator: str = "llm-svg"   # image-api | llm-svg

    @staticmethod
    def from_dict(d: dict) -> GeneratedVisual:
        return GeneratedVisual(
            id=d["id"],
            for_figure_id=d.get("forFigureId", d.get("for_figure_id", "")),
            src=d.get("src", ""),
            description=d.get("description", ""),
            generator=d.get("generator", "llm-svg"),
        )


@dataclass
class Narrative:
    hook: str = ""
    problem: str = ""
    approach: str = ""
    results: list[str] = field(default_factory=list)
    significance: str = ""
    audience_level: str = "academic"   # academic | general

    @staticmethod
    def from_dict(d: dict) -> Narrative:
        return Narrative(
            hook=d.get("hook", ""),
            problem=d.get("problem", ""),
            approach=d.get("approach", ""),
            results=d.get("results", []),
            significance=d.get("significance", ""),
            audience_level=d.get("audienceLevel", d.get("audience_level", "academic")),
        )


@dataclass
class PaperDocument:
    meta: PaperMeta
    sections: list[PaperSection] = field(default_factory=list)
    figures: list[PaperFigure] = field(default_factory=list)
    generated_visuals: list[GeneratedVisual] = field(default_factory=list)
    narrative: Narrative = field(default_factory=Narrative)

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
            sections=[PaperSection.from_dict(s) for s in raw.get("sections", [])],
            figures=[PaperFigure.from_dict(f) for f in raw.get("figures", [])],
            generated_visuals=[
                GeneratedVisual.from_dict(v)
                for v in raw.get("generatedVisuals", raw.get("generated_visuals", []))
            ],
            narrative=Narrative.from_dict(raw.get("narrative", {})),
        )

    @staticmethod
    def load(path: Path) -> PaperDocument:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return PaperDocument.from_dict(raw)
