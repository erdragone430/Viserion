from __future__ import annotations

import json
from pathlib import Path


def load_target(name: str) -> dict | None:
    path = Path(__file__).resolve().parent / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())
