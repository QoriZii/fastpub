import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# xAI
XAI_API_KEY: str = os.environ.get("XAI_API_KEY", "")
XAI_MODEL: str = os.environ.get("XAI_MODEL", "grok-3")

# Image generation
IMAGE_PROVIDER: str = os.environ.get("FASTPUB_IMAGE_PROVIDER", "xai")

# Output directory
OUTPUT_DIR: Path = Path(os.environ.get("FASTPUB_OUTDIR", "~/fastpub-output")).expanduser()

# Templates directory — default to fastpub/render/templates/
TEMPLATES_DIR: Path = Path(
    os.environ.get("FASTPUB_TEMPLATES_DIR",
                   Path(__file__).parent / "render" / "templates")
)
