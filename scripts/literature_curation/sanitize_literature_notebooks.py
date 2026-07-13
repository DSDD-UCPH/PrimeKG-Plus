#!/usr/bin/env python3
"""Sanitize literature-curation notebooks: portable paths, no secrets, clear stale outputs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LIT_DIR = Path(__file__).resolve().parent
THUY_PREFIX = "/Users/ljw303/YANG_DATA/THUY_DATA_CURATION"

DISEASE_CURATED: dict[str, str] = {
    "03_map_curated_entities_canavan.ipynb": "Canavan disease/20260306-Canavan Disease.csv",
    "04_map_curated_entities_batten.ipynb": "Batten disease/Final_Batten Disease.csv",
    "05_map_curated_entities_npc.ipynb": "Pick Niemann disease/Final_Niemann-Pick Disease.csv",
    "06_map_curated_entities_tay_sachs.ipynb": "Tay-Sachs/Tay-Sachs Disease final.csv",
}

CONFIG_TEMPLATE = '''# --- Config & Imports ---
# Portable paths: override with env vars CURATION_ROOT, PLUS_KG, UMLS_API_KEY, RELEASE_ROOT.

import os
import pandas as pd
import re
import requests
import numpy as np
import torch
from pathlib import Path
from tqdm.auto import tqdm
from transformers import AutoTokenizer, AutoModel
from numpy.linalg import norm

_LIT_DIR = Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd()
_RELEASE_ROOT = Path(os.environ.get("RELEASE_ROOT", str(_LIT_DIR.parents[1])))
CURATION_ROOT = Path(os.environ.get(
    "CURATION_ROOT",
    str(_RELEASE_ROOT / "dataset" / "PrimeKG-Plus-RD" / "curation_source"),
))
PLUS_KG = Path(os.environ.get("PLUS_KG", str(_RELEASE_ROOT / "dataset" / "PrimeKG-Plus" / "primekg_plus.csv")))
KG_FILE = PLUS_KG
POST_DIR = CURATION_ROOT / "Post curation"
BEFORE_BERT_DIR = POST_DIR / "before_bert"
FINALS_V1_DIR = POST_DIR / "finals_v1"
QC_OUTPUTS_DIR = POST_DIR / "qc_outputs"
INTERMEDIATE_DIR = POST_DIR / "intermediate"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
CURATED_CSV = CURATION_ROOT / "{curated_rel}"

UMLS_API_KEY = os.environ.get("UMLS_API_KEY", "")
if not UMLS_API_KEY:
    raise ValueError("Set UMLS_API_KEY (NLM UTS API key) before running UMLS search cells.")

SAPBERT_MODEL = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"
SAPBERT_MAX_LEN = 25
SAPBERT_BATCH = 64

TEST_MODE = False
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
'''

CONFIG_TEMPLATE_07 = '''from pathlib import Path
import os
import pandas as pd

_LIT_DIR = Path.cwd()
_RELEASE_ROOT = Path(os.environ.get("RELEASE_ROOT", str(_LIT_DIR.parents[1])))
CURATION_ROOT = Path(os.environ.get(
    "CURATION_ROOT",
    str(_RELEASE_ROOT / "dataset" / "PrimeKG-Plus-RD" / "curation_source"),
))
BASE_DIR = CURATION_ROOT
POST_DIR = CURATION_ROOT / "Post curation"
BEFORE_BERT_DIR = POST_DIR / "before_bert"
FINALS_V1_DIR = POST_DIR / "finals_v1"
QC_OUTPUTS_DIR = POST_DIR / "qc_outputs"
INTERMEDIATE_DIR = POST_DIR / "intermediate"
'''


INTERMEDIATE_FILES = {
    "20260502-Canavan_disease_all_terms_after_first_UMLS_search.csv",
    "20260509-Canavan_suggested_terms_after_second_UMLS_search.csv",
    "20260509-NPC_disease_For_term_suggestion_before_BERT.csv",
    "20260509-NPC_disease_all_terms_after_first_UMLS_search.csv",
    "NMP_disease_For_term_suggestion_before_BERT.csv",
}

POST_CURATION_FILES = {
    "20260502-Canavan_disease_For_term_suggestion_before_BERT.csv",
    "2026058-Batten_disease_For_term_suggestion_before_BERT.csv",
    "2026058-NPC_disease_For_term_suggestion_before_BERT.csv",
    "20260521-Tay-Sachs_disease_For_term_suggestion_before_BERT.csv",
}

BEFORE_BERT_FILES = {
    "20260502-Canavan_disease_For_term_suggestion_before_BERT.csv",
    "2026058-Batten_disease_For_term_suggestion_before_BERT.csv",
    "2026058-NPC_disease_For_term_suggestion_before_BERT.csv",
    "20260521-Tay-Sachs_disease_For_term_suggestion_before_BERT.csv",
}

FINALS_V1_FILES = {
    "20260508-Batten_final.csv",
    "20260508-Canavan_final.csv",
    "20260508-NMP_final.csv",
    "20260521-Tay-Sachs_final.csv",
}

QC_OUTPUT_FILES = {
    "20260508-Batten_second_search_review.csv",
    "20260508-Canavan_second_search_review.csv",
    "20260508-NPC_second_search_review.csv",
    "20260508-NPC_second_search_review.xlsx",
}


def _curation_output_path(filename: str) -> str:
    if filename in INTERMEDIATE_FILES:
        return f'str(INTERMEDIATE_DIR / "{filename}")'
    if filename in BEFORE_BERT_FILES:
        return f'str(BEFORE_BERT_DIR / "{filename}")'
    if filename in FINALS_V1_FILES:
        return f'str(FINALS_V1_DIR / "{filename}")'
    if filename in QC_OUTPUT_FILES:
        return f'str(QC_OUTPUTS_DIR / "{filename}")'
    if filename in POST_CURATION_FILES:
        return f'str(POST_DIR / "{filename}")'
    return f'str(CURATION_ROOT / "{filename}")'


def patch_curation_outputs(text: str) -> str:
    for name in INTERMEDIATE_FILES | POST_CURATION_FILES | BEFORE_BERT_FILES | FINALS_V1_FILES | QC_OUTPUT_FILES:
        text = text.replace(
            f'str(CURATION_ROOT / "{name}")',
            _curation_output_path(name),
        )
        text = text.replace(
            f'CURATION_ROOT / "{name}"',
            (
                f'INTERMEDIATE_DIR / "{name}"'
                if name in INTERMEDIATE_FILES
                else f'BEFORE_BERT_DIR / "{name}"'
                if name in BEFORE_BERT_FILES
                else f'FINALS_V1_DIR / "{name}"'
                if name in FINALS_V1_FILES
                else f'QC_OUTPUTS_DIR / "{name}"'
                if name in QC_OUTPUT_FILES
                else f'POST_DIR / "{name}"'
            ),
        )
    return text


def patch_thuy_paths(text: str) -> str:
    text = re.sub(
        rf'Path\("{re.escape(THUY_PREFIX)}/([^"]+)"\)',
        r'CURATION_ROOT / "\1"',
        text,
    )
    text = re.sub(
        rf'"{re.escape(THUY_PREFIX)}/([^"]+)"',
        r'str(CURATION_ROOT / "\1")',
        text,
    )
    text = text.replace(
        f'KG_FILE = Path("{THUY_PREFIX}/20260221-kg-old.csv")',
        "KG_FILE = PLUS_KG",
    )
    text = text.replace(
        'UMLS_API_KEY = "0e7df1ad-3321-4e50-b1c6-38c44cfb4009"',
        'UMLS_API_KEY = os.environ.get("UMLS_API_KEY", "")',
    )
    return text


def patch_all_paths(text: str) -> str:
    return patch_curation_outputs(patch_thuy_paths(text))


def replace_config_cell(nb: dict, name: str) -> bool:
    if name in DISEASE_CURATED:
        marker = "# ---------- Config ----------"
        for cell in nb.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            src = "".join(cell.get("source", []))
            if marker not in src and "# --- Config & Imports ---" not in src:
                continue
            cell["source"] = CONFIG_TEMPLATE.format(curated_rel=DISEASE_CURATED[name]).splitlines(keepends=True)
            cell["outputs"] = []
            cell["execution_count"] = None
            return True
    if name == "07_finalize_post_curation.ipynb":
        for cell in nb.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            src = "".join(cell.get("source", []))
            if "DISEASE_FILE_PAIRS" not in src:
                continue
            prefix = CONFIG_TEMPLATE_07 + "\nQC_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)\n\n"
            rest = src.split("DISEASE_FILE_PAIRS", 1)[1]
            rest = rest.replace("BASE_DIR /", "POST_DIR /")
            rest = rest.replace('POST_DIR / "202605', 'BEFORE_BERT_DIR / "202605')
            rest = rest.replace('POST_DIR / "20260521-Tay-Sachs_disease_For_term_suggestion_before_BERT.csv"', 'BEFORE_BERT_DIR / "20260521-Tay-Sachs_disease_For_term_suggestion_before_BERT.csv"')
            rest = rest.replace('POST_DIR / "20260508-', 'FINALS_V1_DIR / "20260508-')
            rest = rest.replace('POST_DIR / "20260521-Tay-Sachs_final.csv"', 'FINALS_V1_DIR / "20260521-Tay-Sachs_final.csv"')
            # If a previous sanitize run incorrectly mapped finals under BEFORE_BERT_DIR, fix it.
            rest = rest.replace('"final": BEFORE_BERT_DIR / "', '"final": FINALS_V1_DIR / "')
            rest = rest.replace("out_dir=OUT_DIR", "out_dir=QC_OUTPUTS_DIR")
            cell["source"] = (prefix + "DISEASE_FILE_PAIRS" + rest).splitlines(keepends=True)
            cell["outputs"] = []
            cell["execution_count"] = None
            return True
    return False


def sanitize_notebook(path: Path) -> bool:
    nb = json.loads(path.read_text(encoding="utf-8"))
    changed = replace_config_cell(nb, path.name)

    for cell in nb.get("cells", []):
        if cell.get("cell_type") not in {"code", "markdown"}:
            continue
        src = cell.get("source", [])
        if isinstance(src, str):
            src = [src]
        new_src = [patch_all_paths(line) for line in src]
        if new_src != src:
            cell["source"] = new_src
            changed = True
        if cell.get("outputs") or cell.get("execution_count") is not None:
            blob = json.dumps(cell.get("outputs", []))
            if THUY_PREFIX in blob or "/Users/ljw303/" in blob:
                cell["outputs"] = []
                cell["execution_count"] = None
                changed = True

    if changed:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    targets = sorted(LIT_DIR.glob("0[3-7]_*.ipynb"))
    if not targets:
        print("No literature notebooks found", file=sys.stderr)
        return 1
    for path in targets:
        if sanitize_notebook(path):
            print(f"patched: {path.name}")
        else:
            print(f"unchanged: {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
