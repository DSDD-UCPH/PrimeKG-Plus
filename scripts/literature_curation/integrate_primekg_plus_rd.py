#!/usr/bin/env python3
"""Backward-compatible alias for :mod:`09_integrate_primekg_plus_rd` (same CLI)."""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("09_integrate_primekg_plus_rd.py")), run_name="__main__")
