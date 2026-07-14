"""
load_config.py
==============
A small utility function so that all scripts/notebooks read config.yaml 
in exactly the same way (single source of truth for cut-off parameters).
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_config(config_path: str | Path | None = None) -> dict:
    """
    Load config.yaml. If `config_path` is not provided, automatically search 
    in the repo root (2 levels above this file: src/ -> root).
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    cfg = load_config()
    print("Config loaded successfully. Top-level keys:", list(cfg.keys()))