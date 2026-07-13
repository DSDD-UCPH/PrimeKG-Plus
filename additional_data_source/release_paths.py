"""Shared path resolution for additional_data_source notebooks and scripts."""
from __future__ import annotations

import os
from pathlib import Path


def resolve_release_root() -> Path:
    if env := os.environ.get("RELEASE_ROOT"):
        root = Path(env).expanduser().resolve()
        if (root / "dataset").is_dir() and (root / "primary_data_prep").is_dir():
            return root
        raise FileNotFoundError(f"RELEASE_ROOT invalid: {root}")

    for start in (Path.cwd().resolve(),):
        for parent in (start, *start.parents):
            if parent.name == "PrimeKG-Plus_release" and (parent / "dataset").is_dir():
                return parent

    raise FileNotFoundError(
        "Cannot find PrimeKG-Plus_release. Run from this repo or set RELEASE_ROOT."
    )


def primary_data_dir(release_root: Path | None = None) -> Path:
    if env := os.environ.get("PRIMARY_DATA_DIR"):
        return Path(env).expanduser().resolve()
    root = release_root or resolve_release_root()
    return root / "primary_data_prep" / "data"
