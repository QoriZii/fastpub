# FastPub

Transform academic papers into promotional multimedia materials.

FastPub takes a research paper (PDF) and generates accessible, audience-friendly outputs: bilingual web pages and data-rich slide decks.

## Install

```bash
git clone <repo-url> && cd fastpub-py
make setup          # installs Python dependencies
```

Or manually:

```bash
uv sync
```

Requirements:
- Python >= 3.11

## Quick Start

```bash
# Set your API key
cp .env.example .env
# Edit .env — set FASTPUB_MODEL and the matching API key

# One-shot: analyze + render web page
uv run fastpub go paper.pdf

# Works with URLs too
uv run fastpub go https://example.com/paper.pdf -f web,slides

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
uv run fastpub render paper.analysis.json -f web,slides
```

Options:
- `-f, --format <formats>` — Comma-separated: `web`, `slides` (default: `web`)
- `-o, --output <path>` — Output path
- `--aspect <ratio>` — Slide aspect ratio: `4:3` (default) or `16:9`

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

| Variable | Description | Default |
|---|---|---|
| `FASTPUB_MODEL` | Model ID | `grok-3` |
| `FASTPUB_PROVIDER` | Provider override (auto-detected from model name) | `xai` |
| `XAI_API_KEY` | xAI API key (for grok models) | — |
| `DEEPSEEK_API_KEY` | DeepSeek API key (for deepseek models) | — |
| `FASTPUB_OUTDIR` | Default output directory | `~/fastpub-output` |

Supported models:
- **xAI**: `grok-3` (default), and other grok models
- **DeepSeek**: `deepseek-v4-flash`, and other deepseek models

The provider is auto-detected from the model name (`deepseek-*` → DeepSeek, otherwise xAI). Override with `FASTPUB_PROVIDER` if needed.

## Output Formats

### Web (`-f web`)

Self-contained bilingual HTML page with:
- English/Chinese language toggle
- Responsive layout with dark mode
- 5 structured sections (Problem, Approach, Meaning, Results, Limitations)
- No external dependencies — single `.html` file

### Slides (`-f slides`)

HTML slide deck with:
- Data-rich visualizations (bar charts, donut charts, funnels, stat cards, etc.)
- Narrative story arc from problem to conclusions
- Speaker notes
- Configurable aspect ratio (`--aspect 4:3` or `16:9`)

## Pipeline Architecture

```
PDF → Parse (pymupdf) → Analyze (LLM) → [Edit] → Render
                                                  ├── Web (HTML)
                                                  └── Slides (HTML)
```

The canonical `analysis.json` (PaperDocument) sits at the center. Edit it between analyze and render to fine-tune outputs.

## Project Structure

```
fastpub/
├── config.py               # Environment config
├── models.py               # PaperDocument dataclasses
├── cli/main.py             # Typer CLI commands
├── pipeline/
│   ├── utils.py            # LLM client (xAI, DeepSeek), JSON parsing
│   ├── parse_pdf.py        # PDF extraction (pymupdf, local or URL)
│   └── analyze.py          # LLM paper analysis (web + slides, bilingual)
├── prompts/                # Prompt templates (.txt)
├── render/
│   ├── web.py              # Bilingual HTML renderer
│   ├── slides.py           # Slide deck renderer (12 viz types)
│   └── templates/          # HTML templates
```

## Development

```bash
uv run fastpub analyze paper.pdf    # Run directly
uv run python -m fastpub.cli.main   # Alternative
```

## License

MIT
