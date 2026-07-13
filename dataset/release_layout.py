"""Canonical dataset folder names for PrimeKG-Plus release bundles."""
from pathlib import Path

PLUS_DIRNAME = "PrimeKG-Plus"
PLUS_RD_DIRNAME = "PrimeKG-Plus-RD"


def plus_dir(release_root: Path) -> Path:
    return release_root / "dataset" / PLUS_DIRNAME


def plus_rd_dir(release_root: Path) -> Path:
    return release_root / "dataset" / PLUS_RD_DIRNAME
