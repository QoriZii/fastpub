# FastPub

Transform academic papers into promotional multimedia materials.

FastPub takes a research paper (PDF) and generates accessible, audience-friendly outputs: bilingual web pages, narrated slide decks, and short-form explainer videos.

## Install

```bash
git clone <repo-url> && cd fastpub-py
uv sync
```

Requirements:
- Python >= 3.11
- ffmpeg (only for video rendering): `brew install ffmpeg`

## Quick Start

```bash
# Set your API key
cp .env.example .env
# Edit .env with your xAI API key

# One-shot: analyze + render web page
uv run fastpub go paper.pdf

# Or step by step
uv run fastpub analyze paper.pdf
uv run fastpub render paper.analysis.json -f web
```

## Commands

### `fastpub analyze <pdf>`

Parse a paper and produce a structured `analysis.json` (PaperDocument).

```bash
uv run fastpub analyze paper.pdf
uv run fastpub analyze paper.pdf --audience general --parser pymupdf
```

Options:
- `-o, --output <path>` — Output JSON path (default: `$FASTPUB_OUTDIR/<name>.analysis.json`)
- `-p, --parser <provider>` — `pymupdf` (default), `mineru`, or `mineru-cloud`
- `--audience <level>` — `academic` or `general`

### `fastpub render <analysis.json>`

Generate output from a PaperDocument.

```bash
uv run fastpub render paper.analysis.json -f web
uv run fastpub render paper.analysis.json -f slides
uv run fastpub render paper.analysis.json -f video
uv run fastpub render paper.analysis.json -f web,slides,video
```

Options:
- `-f, --format <formats>` — Comma-separated: `web`, `slides`, `video` (default: `web`)
- `-o, --output <path>` — Output path
- `--voice <voice-id>` — TTS voice: `eve`, `ara`, `rex`, `sal`, `leo`
- `--no-audio` — Skip narration generation

### `fastpub go <pdf>`

One-shot: analyze + render without manual editing.

```bash
uv run fastpub go paper.pdf -f web
uv run fastpub go paper.pdf -f web,slides --audience general
```

Accepts all options from both `analyze` and `render`.

## Configuration

FastPub reads config from `.env` in the project root.

Copy `.env.example` to get started:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `XAI_API_KEY` | xAI API key | `xai-...` |
| `XAI_MODEL` | Model ID | `grok-3` |
| `FASTPUB_OUTDIR` | Default output directory | `~/fastpub-output` |
| `LOG_LEVEL` | Log verbosity | `debug`, `info`, `warn`, `error` |

## Output Formats

### Web (`-f web`)

Self-contained bilingual HTML page with:
- English/Chinese language toggle
- Responsive layout with dark mode
- Narrative cards, section summaries, figure gallery
- No external dependencies — single `.html` file

### Slides (`-f slides`)

PowerPoint file (`.pptx`) — not yet implemented.

### Video (`-f video`)

MP4 explainer video — not yet implemented.

## Pipeline Architecture

```
PDF → Parse (pymupdf) → Analyze (xAI LLM) → [Edit] → Render
                                                  ├── Web (HTML)
                                                  ├── Slides (PPTX)
                                                  └── Video (MP4)
```

The canonical `analysis.json` (PaperDocument) sits at the center. Edit it between analyze and render to fine-tune outputs.

## Project Structure

```
fastpub/
├── config.py               # Environment config
├── models.py               # PaperDocument dataclasses
├── cli/main.py             # Typer CLI commands
├── pipeline/
│   ├── utils.py            # xAI client, JSON parsing
│   ├── parse_pdf.py        # PDF extraction (pymupdf)
│   ├── analyze.py          # LLM paper analysis
│   └── translate.py        # LLM Chinese translation
├── prompts/                # Prompt templates (.txt)
├── render/
│   ├── web.py              # HTML renderer
│   ├── slides.py           # PPTX renderer (stub)
│   ├── video.py            # Video renderer (stub)
│   └── templates/          # HTML templates
└── ai/tts.py               # xAI TTS client
```

## Development

```bash
uv run fastpub analyze paper.pdf    # Run directly
uv run python -m fastpub.cli.main   # Alternative
```

## License

MIT
