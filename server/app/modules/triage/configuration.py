import json
from pathlib import Path
from app.core.config import settings

CONFIGS_DIR = Path(__file__).parent / "configs"


def load_triage_config(name: str | None = None) -> dict:
    name = name or settings.triage_config
    return json.loads((CONFIGS_DIR / f"{name}.json").read_text(encoding="utf-8"))
