#!/usr/bin/env python3
"""Sanitize notebooks in the public release bundle (paths + clear stale outputs)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RELEASE = Path(__file__).resolve().parents[1]

# (old, new) replacements applied to each source line in code/markdown cells
SOURCE_REPLACEMENTS: list[tuple[str, str]] = [
    (
        'os.chdir("/Users/ljw303/YANG_DATA/PrimeKG/datasets/data/disgenet/OpenTarget")',
        "# Run from additional_data_source/opentarget/ — uses ./inputs and ./outputs",
    ),
    (
        '"/Users/ljw303/YANG_DATA/PrimeKG/datasets/data/disgenet/OpenTarget/opentargets_associations"',
        '"inputs/opentargets_associations"',
    ),
    (
        '"/Users/ljw303/YANG_DATA/PrimeKG/datasets/data/disgenet/OpenTarget/disease.parquet"',
        '"inputs/disease.parquet"',
    ),
    (
        'data_path = "/Users/ljw303/YANG_DATA/PrimeKG/datasets/data/"',
        'data_path = os.environ.get("PRIMEKG_ROOT", "..") + "/datasets/data/"  # set PRIMEKG_ROOT for full rebuild',
    ),
    (
        'Path("/Users/ljw303/YANG_DATA/PrimeKG/PrimeKG-Plus_release/scripts/literature_curation")',
        "Path(__file__).resolve().parent" if False else "Path.cwd()",
    ),
    (
        'SCRIPT_DIR = Path("/Users/ljw303/YANG_DATA/PrimeKG/PrimeKG-Plus_release/scripts/literature_curation")',
        "SCRIPT_DIR = Path.cwd()",
    ),
    (
        'PRIMEKG_ROOT = Path(os.environ.get("PRIMEKG_ROOT", "/Users/ljw303/YANG_DATA/PrimeKG"))',
        "PRIMEKG_ROOT = Path(os.environ.get('PRIMEKG_ROOT', str(Path.cwd().parents[2])))",
    ),
    (
        'CURATION_ROOT = Path(os.environ.get("CURATION_ROOT", "/Users/ljw303/YANG_DATA/THUY_DATA_CURATION"))',
        "CURATED_DIR = Path(os.environ.get('CURATED_DIR', str(Path.cwd().parents[2] / 'dataset/PrimeKG-Plus-RD/curated')))",
    ),
    (
        'curation_root = Path(os.environ.get("CURATION_ROOT", "/Users/ljw303/YANG_DATA/THUY_DATA_CURATION"))',
        "curated_dir = Path(os.environ.get('CURATED_DIR', str(Path.cwd().parents[2] / 'dataset/PrimeKG-Plus-RD/curated')))",
    ),
    (
        "`THUY_DATA_CURATION/20260508-*_final.csv`",
        "`dataset/PrimeKG-Plus-RD/curated/*_final.csv`",
    ),
    (
        "/Users/ljw303/YANG_DATA/PrimeKG/datasets/data/umls/umls_2025AB.csv",
        "str(Path(os.environ['PRIMEKG_ROOT']) / 'datasets/data/umls/umls_2025AB.csv')",
    ),
]

# Shell magics with absolute paths → relative
SHELL_REPLACEMENTS = [
    (
        "ls /Users/ljw303/YANG_DATA/PrimeKG/datasets/data/disgenet/OpenTarget/opentargets_associations",
        "ls inputs/opentargets_associations",
    ),
]


def patch_source(text: str) -> str:
    for old, new in SOURCE_REPLACEMENTS:
        text = text.replace(old, new)
    for old, new in SHELL_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def sanitize_notebook(path: Path) -> bool:
    nb = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for cell in nb.get("cells", []):
        if cell.get("outputs") or cell.get("execution_count") is not None:
            cell["outputs"] = []
            cell["execution_count"] = None
            changed = True
        src = cell.get("source", [])
        if isinstance(src, str):
            lines = [src]
        else:
            lines = list(src)
        new_lines = [patch_source(line) for line in lines]
        if new_lines != lines:
            cell["source"] = new_lines
            changed = True
    if changed:
        path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    notebooks = sorted(RELEASE.rglob("*.ipynb"))
    n = 0
    for p in notebooks:
        if ".ipynb_checkpoints" in str(p):
            continue
        if sanitize_notebook(p):
            print(f"patched: {p.relative_to(RELEASE)}")
            n += 1
    print(f"done ({n} notebook(s) updated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
