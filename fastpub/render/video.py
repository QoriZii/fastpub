"""Video renderer — produces an MP4 video from a PaperDocument."""
from __future__ import annotations

from pathlib import Path

from fastpub.models import PaperDocument


def render_video(doc: PaperDocument, output_path: Path, no_audio: bool = False) -> Path:
    """Render PaperDocument to MP4 video. Requires playwright + ffmpeg."""
    raise NotImplementedError(
        "Video rendering not yet implemented.\n"
        "Will use playwright + ffmpeg."
    )
