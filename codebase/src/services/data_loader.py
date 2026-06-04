from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# codebase/src/services/data_loader.py → parents[2] = codebase/
ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "hanoi_places.json"


@lru_cache(maxsize=1)
def load_hanoi_data() -> dict:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_FILE}")
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def get_places() -> list[dict]:
    return load_hanoi_data()["places"]


def get_restaurants() -> list[dict]:
    return load_hanoi_data()["restaurants"]


def get_bars() -> list[dict]:
    return load_hanoi_data()["bars"]


def get_dataset_as_json_str() -> str:
    return json.dumps(load_hanoi_data(), ensure_ascii=False, separators=(",", ":"))
