from __future__ import annotations

import json
from pathlib import Path


def load_target(name: str) -> dict:
    path = Path(__file__).resolve().parent / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing target config: {path}\n"
            f"Copy targets/{name}.example.json to targets/{name}.json and fill in the values."
        )
    return json.loads(path.read_text())
