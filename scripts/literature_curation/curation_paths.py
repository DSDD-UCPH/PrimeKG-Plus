"""Shared path resolution for literature-curation notebooks and scripts."""

from __future__ import annotations

import os
from pathlib import Path

_LIT_DIR = Path(__file__).resolve().parent
_RELEASE_ROOT = Path(os.environ.get("RELEASE_ROOT", str(_LIT_DIR.parents[1])))


def default_curation_root() -> Path:
    if env := os.environ.get("CURATION_ROOT"):
        return Path(env).expanduser().resolve()
    bundled = _RELEASE_ROOT / "dataset" / "PrimeKG-Plus-RD" / "curation_source"
    if bundled.is_dir():
        return bundled
    for candidate in (
        _RELEASE_ROOT.parent.parent / "THUY_DATA_CURATION",
        _RELEASE_ROOT.parent / "THUY_DATA_CURATION",
    ):
        if candidate.is_dir():
            return candidate
    return bundled


def default_plus_kg() -> Path:
    if env := os.environ.get("PLUS_KG"):
        return Path(env).expanduser().resolve()
    return _RELEASE_ROOT / "dataset" / "PrimeKG-Plus" / "primekg_plus.csv"


def default_plus_nodes() -> Path:
    if env := os.environ.get("PLUS_NODES"):
        return Path(env).expanduser().resolve()
    return _RELEASE_ROOT / "dataset" / "PrimeKG-Plus" / "nodes.csv"


def default_curated_dir() -> Path:
    if env := os.environ.get("CURATED_DIR"):
        return Path(env).expanduser().resolve()
    return _RELEASE_ROOT / "dataset" / "PrimeKG-Plus-RD" / "curated"


RELEASE_ROOT = _RELEASE_ROOT
CURATION_ROOT = default_curation_root()
PLUS_KG = default_plus_kg()
PLUS_NODES = default_plus_nodes()
CURATED_DIR = default_curated_dir()
POST_CURATION_DIR = CURATION_ROOT / "Post curation"
INTERMEDIATE_DIR = POST_CURATION_DIR / "intermediate"
