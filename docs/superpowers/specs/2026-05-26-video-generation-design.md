# Video Generation Pipeline — Design Spec

## Summary

Add video generation to fastpub: transform a `PaperDocument` into a motion-graphics MP4 video with AI-generated visuals and TTS narration. The pipeline extends the existing slides renderer (scene scripting + image generation) and adds a video stage (TTS + Remotion rendering).

Target audience: social science researchers. Output: 1080p landscape, up to 5 minutes.

## Architecture

### Two-stage pipeline

**Slides stage** (extended from existing `render_slides`):
1. **Scene script generation** — LLM produces a dynamic array of scenes from the `PaperDocument`. Each scene has a type (`hook`, `problem`, `approach`, `results`, `significance`, `closing`), headline, body text, narration text, and an image prompt. The number and types of scenes are not fixed — the LLM decides based on the paper content.
2. **Image generation** — For each scene, an AI image provider generates a visual that illustrates the paper's content (architecture diagrams, result plots, conceptual illustrations). Images are generated in parallel.
3. **HTML slides** — The existing slides renderer uses the scene data to produce an HTML deck.

Output: `scenes.json` + `images/` directory + HTML slides.

**Video stage** (new):
1. **TTS narration** — Generate audio per scene using the existing xAI TTS. Scene duration is driven by audio length.
2. **Build manifest** — Assemble `manifest.json` from scenes, audio files, and images.
3. **Remotion render** — Shell out to `npx remotion render` which reads the manifest and produces an MP4.

Output: `output.mp4`.

### Scene script output

A single LLM call produces all content for each scene:

- **headline** — short bold text displayed prominently on the slide (max ~8 words)
- **body** — supporting text or key points shown on the slide (1-2 sentences or a short list)
- **narration** — what the voiceover says during this scene (natural spoken style, 2-3 sentences). This is NOT displayed — it goes to TTS for audio.
- **imagePrompt** — a description of a visual that illustrates the paper content. This drives AI image generation.

So each scene maps to three output channels:
1. **Visual text** on slide canvas ← `headline` + `body`
2. **Image** on slide canvas ← AI-generated from `imagePrompt`
3. **Audio** narration ← TTS of `narration`

### Handoff: JSON manifest

The Python pipeline produces a `manifest.json` that Remotion consumes. All asset paths are relative to the job directory.

```json
{
  "meta": {
    "title": "Paper Title",
    "authors": ["Author A", "Author B"],
    "venue": "APSR 2026",
    "year": 2026
  },
  "settings": {
    "fps": 30,
    "width": 1920,
    "height": 1080
  },
  "scenes": [
    {
      "id": "scene-1",
      "type": "hook",
      "durationSec": 5.2,

      // ── Visual text (displayed on slide) ──
      "headline": "Short bold text",
      "body": "Supporting text or empty",

      // ── Audio (TTS narration, not displayed) ──
      "narration": "Full narration text",
      "audioFile": "audio/scene-1.mp3",

      // ── Image (AI-generated, displayed on slide) ──
      "imageFile": "images/scene-1.png",
      "imagePrompt": "Original prompt used",

      "transition": "fade",
      "colorAccent": "#c8aa78"
    }
  ]
}
```

### Monorepo structure

```
fastpub-py/
  fastpub/
    ai/
      tts.py                        # existing
      image_providers/               # NEW
        __init__.py                  # get_provider(name) factory
        base.py                      # ImageProvider ABC
        xai.py                       # XAIImageProvider (grok-2-image)
    pipeline/
      analyze.py                     # existing
      scene_script.py                # NEW — LLM → scene script JSON
      image_gen.py                   # NEW — parallel image generation
    prompts/
      scene_script/                  # existing prompts
    render/
      slides.py                      # MODIFIED — uses scene_script + image_gen
      video.py                       # MODIFIED — TTS + manifest + Remotion
    config.py                        # MODIFIED — add image provider config

  packages/
    remotion-video/                  # NEW — Remotion project
      src/
        index.ts
        Video.tsx                    # root composition
        Scene.tsx                    # unified scene component
        SceneWrapper.tsx             # transition handling
        AudioTrack.tsx               # per-scene audio
        animations/
          fade-in.ts
          slide-in.ts
          scale-reveal.ts
          typewriter.ts
          stagger.ts
        types.ts                     # manifest TypeScript types
      package.json
      tsconfig.json
      remotion.config.ts

  Makefile                           # NEW — setup + build commands
```

### Output structure

```
output/
  paper-name.analysis.json
  paper-name.slides.html
  paper-name.scenes.json
  paper-name.mp4
  paper-name/
    images/
      scene-1.png
      scene-2.png
    audio/                           # video only
      scene-1.mp3
      scene-2.mp3
    manifest.json                    # video only
```

### Internal dependency flow

```
render_slides(doc)
  → generate_scene_script(doc) → scenes.json
  → generate_images(scenes)   → images/
  → build HTML slide deck

render_video(doc)
  → render_slides(doc)              # if not already done
  → generate_tts(scenes)           → audio/
  → build_manifest(scenes, audio, images) → manifest.json
  → npx remotion render            → output.mp4
```

## Image generation

### Provider adapter pattern

```python
class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, width: int, height: int) -> bytes:
        """Generate an image from a text prompt. Returns PNG bytes."""
        ...
```

Start with `XAIImageProvider` (grok-2-image). The adapter interface allows adding OpenAI, Seedance, etc. later.

Configuration via env var (`FASTPUB_IMAGE_PROVIDER=xai`) or CLI flag (`--image-provider xai`).

### Image prompts

The scene script LLM call produces an `imagePrompt` per scene — a description of a visual that illustrates the paper's content (not decorative slide art). A style prefix is prepended to all prompts for consistency.

Images illustrate specific paper concepts: study design diagrams, regression plots, conceptual frameworks, data flow charts.

## Remotion composition

### Component tree

```
<Video>                           reads manifest.json
  <Series>                        sequences scenes
    {scenes.map(scene =>
      <SceneWrapper transition>   handles crossfades
        <Scene scene={scene} />   picks layout by type + image presence
      </SceneWrapper>
    )}
    <AudioTrack />                per-scene narration
```

### Layout rules

| Condition | Layout | Example |
|-----------|--------|---------|
| type = `hook` | Centered, dark gradient bg | Opening question |
| type = `closing` | Centered, dark gradient bg | Title + authors + venue |
| has image | Split: text left (~55%), figure right (~45%) | Method, results |
| text only | Centered text, light bg | Problem, significance |

### Animation primitives

| Primitive | Usage | Timing |
|-----------|-------|--------|
| FadeIn | Headlines, body text | 400-600ms, ease-out, 40px upward offset |
| SlideIn | Images entering frame | 400ms, ease-out, from right |
| ScaleReveal | Image emphasis | scale 0.95→1.0 with fade |
| TypeWriter | Hook headline | character-by-character |
| Stagger | Key points list | 150ms delay between items, slight left slide |
| CrossFade | Scene transitions | 500ms overlap |
| WipeIn | Top gradient bar | left-to-right reveal |

## Visual style

Academic credibility with visual warmth. Targeted at social science researchers.

### Palette

| Token | Value | Usage |
|-------|-------|-------|
| Dark bg | `#1a2332` → `#2a3f5f` gradient | Hook, closing scenes |
| Light bg | `#faf8f5` | Content scenes |
| Primary accent | `#c8aa78` warm gold | Brand, findings, dividers |
| Method | `#4a7c6f` sage green | Method scenes |
| Approach | `#5b8fa8` slate blue | Approach scenes |
| Problem | `#a0635a` clay red | Problem scenes |
| Headings | `#1a2332` | Headlines on light bg |
| Body | `#4a5568` | Body text, key points |

### Typography

- **Headlines**: Georgia serif, 700 weight
- **Hook question**: Georgia italic, 700
- **Body/key points**: System sans-serif (-apple-system)
- **Labels**: Sans-serif, 700, uppercase, wide letter-spacing
- **Brand**: Sans-serif small caps, `#c8aa78`

### Visual details

- Dark scenes: subtle gradient background + decorative circle geometry (low-opacity borders)
- Content scenes: gradient top bar (scene-type colored, wipes in from left)
- Key points: left border accent (2.5px, scene-type colored) with subtle background tint
- Figures: white background, 1px border, soft shadow, 4px border-radius
- "fastpub" watermark: bottom-left on content scenes, top-left on dark scenes

## CLI integration

```bash
# Slides only
fastpub render analysis.json -f slides

# Video only (runs slides stage internally first)
fastpub render analysis.json -f video

# Both (slides stage runs once, shared assets)
fastpub render analysis.json -f slides,video

# Full pipeline
fastpub go paper.pdf -f slides,video --image-provider xai
```

New CLI options:
- `--image-provider`: Image generation provider (default: `xai`)

## Configuration

New env vars:
- `FASTPUB_IMAGE_PROVIDER` — provider name (default: `xai`)

Existing env vars used:
- `XAI_API_KEY` — for both image generation and TTS

## Dependencies

Python (existing):
- httpx, typer, python-dotenv

Python (no new deps needed — image gen uses httpx).

Node.js (new, in `packages/remotion-video/`):
- `remotion`, `@remotion/cli`, `@remotion/bundler`
- React, TypeScript

System:
- Node.js 18+ (for Remotion)
- ffmpeg (already expected)
