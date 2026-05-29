import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Model config (FASTPUB_MODEL falls back to XAI_MODEL for backward compat)
FASTPUB_MODEL: str = os.environ.get("FASTPUB_MODEL", os.environ.get("XAI_MODEL", "grok-3"))

def _detect_provider(model: str) -> str:
    if model.startswith("deepseek-"):
        return "deepseek"
    return "xai"

FASTPUB_PROVIDER: str = os.environ.get("FASTPUB_PROVIDER", _detect_provider(FASTPUB_MODEL))

# DeepSeek
DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "")

# Output directory
OUTPUT_DIR: Path = Path(os.environ.get("FASTPUB_OUTDIR", "~/fastpub-output")).expanduser()

# Templates directory — default to fastpub/render/templates/
TEMPLATES_DIR: Path = Path(
    os.environ.get("FASTPUB_TEMPLATES_DIR",
                   Path(__file__).parent / "render" / "templates")
)
