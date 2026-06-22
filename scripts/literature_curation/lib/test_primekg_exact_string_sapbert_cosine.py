#!/usr/bin/env python3
"""
Quick check: if a query string is **identical** to a pool `canonical_name` and you re-encode it
with the **same** SapBERT settings as precompute, the L2-normalized cosine vs that pool row
should be **1.0** (within float noise from fp16 memmap).

If you see cosine ~0.3 (or anything far from 1) for short strings while long strings look fine,
the pool artefacts are usually **internally inconsistent** (SQLite / memmap / CSV from different
runs) or the interpreter is not the one used for precompute (broken or mismatched torch). Re-run
``20260502_precompute_primekg_candidate_embeddings.py`` in one shot, or use ``--verify-names-csv``
to confirm ``primekg_pool_names_ordered.csv`` matches SQLite for sampled rows.

Also scans an optional CSV for entity strings that are exact members of the pool and prints
a few examples for manual inspection.

Usage (from anywhere):
  python knowledge_graph/test_primekg_exact_string_sapbert_cosine.py \\
      --embed-dir /path/to/embedding_pool_primekg_names

With curated / relationship CSV:
  python knowledge_graph/test_primekg_exact_string_sapbert_cosine.py \\
      --embed-dir ... \\
      --scan-csv /path/to/novel_relationships.csv \\
      --scan-cols entity1,entity2
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

# Local import: same folder as this script
_KG = Path(__file__).resolve().parent
if str(_KG) not in sys.path:
    sys.path.insert(0, str(_KG))

from embedding_pool_loader import load_precomputed_embedding_pool  # noqa: E402
from sapbert_pool_encode import cosine_after_l2, embed_sapbert_one  # noqa: E402


def load_names_csv_subset(names_csv: Path, ords: set[int]) -> dict[int, str]:
    """Read ``ord -> name`` from ``primekg_pool_names_ordered.csv`` for the given ord set."""
    out: dict[int, str] = {}
    with names_csv.open(encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            o = int(row["ord"])
            if o in ords:
                out[o] = row["name"]
                if len(out) == len(ords):
                    break
    return out


def collect_exact_pool_hits_from_csv(
    csv_path: Path,
    cols: list[str],
    pool_set: set[str],
    max_rows: int,
    case_insensitive: bool,
) -> list[str]:
    import pandas as pd

    hits: list[str] = []
    seen: set[str] = set()
    for chunk in pd.read_csv(csv_path, usecols=cols, chunksize=200_000, low_memory=False, nrows=max_rows):
        for col in cols:
            if col not in chunk.columns:
                raise ValueError(f"Column {col!r} not in CSV")
            s = chunk[col].dropna().astype(str).str.strip()
            s = s[(s.str.len() > 0) & (s.str.lower() != "nan")]
            for x in s.unique().tolist():
                key = x.lower() if case_insensitive else x
                pool_has = key in pool_set if case_insensitive else x in pool_set
                if pool_has and x not in seen:
                    seen.add(x)
                    hits.append(x)
    return hits


def main() -> None:
    p = argparse.ArgumentParser(description="Test SapBERT cosine==1 for exact string pool hits.")
    p.add_argument(
        "--embed-dir",
        type=Path,
        required=True,
        help="PrimeKG precompute dir (embedding_manifest.json + sap memmap).",
    )
    p.add_argument(
        "--scan-csv",
        type=Path,
        default=None,
        help="Optional CSV: scan columns for strings that are exact pool names.",
    )
    p.add_argument(
        "--scan-cols",
        type=str,
        default="entity1,entity2",
        help="Comma-separated column names to scan.",
    )
    p.add_argument("--max-csv-rows", type=int, default=500_000, help="Max rows read from scan CSV (total).")
    p.add_argument("--self-samples", type=int, default=8, help="Random pool rows to self-check.")
    p.add_argument("--max-hits-print", type=int, default=15, help="Max CSV-derived hits to print.")
    p.add_argument(
        "--case-insensitive",
        action="store_true",
        help="Match CSV strings to pool using lowercased equality (pool index still uses original casing).",
    )
    p.add_argument(
        "--sapbert-model",
        type=str,
        default="cambridgeltl/SapBERT-from-PubMedBERT-fulltext",
    )
    p.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument(
        "--verify-names-csv",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Cross-check manifest names_csv vs SQLite canonical_name for self-check ords (default on).",
    )
    args = p.parse_args()

    _embed = Path(args.embed_dir).expanduser().resolve()
    if not _embed.is_dir():
        print(f"Không tìm thấy thư mục pool: {_embed}", file=sys.stderr)
        if str(args.embed_dir).strip() == "PRIMEKG_EMBEDDING_POOL_DIR":
            print(
                "→ Bạn đã truyền **chuỗi** `PRIMEKG_EMBEDDING_POOL_DIR`, không phải đường dẫn.\n"
                "  Trong notebook (đã có biến sau ô Config):\n"
                "    import subprocess, sys\n"
                "    subprocess.check_call([sys.executable, \"test_primekg_exact_string_sapbert_cosine.py\",\n"
                "      \"--embed-dir\", str(PRIMEKG_EMBEDDING_POOL_DIR)], cwd=\"knowledge_graph\")\n"
                "  hoặc điền **đường dẫn tuyệt đối** vào --embed-dir trong lệnh shell.",
                file=sys.stderr,
            )
        sys.exit(1)
    args.embed_dir = _embed

    pool = load_precomputed_embedding_pool(args.embed_dir)
    manifest = pool["manifest"]
    names: list[str] = pool["canonical_names"]
    sap_mm = pool["sap_mm"]
    n_pool = int(pool["n_pool"])
    max_len = int(manifest["embeddings"]["sapbert"]["max_len"])

    if case_insensitive := args.case_insensitive:
        lower_to_ord: dict[str, int] = {}
        for i, n in enumerate(names):
            low = n.lower()
            if low not in lower_to_ord:
                lower_to_ord[low] = i
        pool_lookup = set(lower_to_ord.keys())
    else:
        name_to_ord = {n: i for i, n in enumerate(names)}
        pool_lookup = set(name_to_ord.keys())

    print("embed_dir:", args.embed_dir.resolve())
    print("n_pool:", n_pool, "SapBERT max_len:", max_len, "device:", args.device)
    print("manifest normalize:", manifest.get("normalize"), "  pool manifest model:", manifest["embeddings"]["sapbert"]["model"])
    try:
        import transformers  # noqa: WPS433

        print("torch:", torch.__version__, "  transformers:", transformers.__version__)
    except Exception:
        print("torch:", torch.__version__)

    tokenizer = AutoTokenizer.from_pretrained(args.sapbert_model)
    model = AutoModel.from_pretrained(args.sapbert_model).to(args.device)
    model.eval()

    # --- A) Self-check: re-encode pool string at random rows ---
    rng = random.Random(0)
    sample_idx = sorted(rng.sample(range(n_pool), k=min(args.self_samples, n_pool)))
    csv_subset: dict[int, str] = {}
    names_csv_key = manifest.get("names_csv")
    if args.verify_names_csv and names_csv_key:
        p_csv = Path(names_csv_key)
        if p_csv.is_file():
            csv_subset = load_names_csv_subset(p_csv, set(sample_idx))
        else:
            print(f"\n(Warning: manifest names_csv missing or not a file: {names_csv_key!r})")

    print("\n=== Self-check (query == pool canonical_name at same ord) ===")
    worst = 1.0
    for i in sample_idx:
        s = names[i]
        if csv_subset:
            cs = csv_subset.get(i)
            if cs is None:
                print(f"  ord={i:6d}  (names_csv: ord not found before EOF — truncated CSV?)")
            elif cs != s:
                print(f"  ord={i:6d}  MISMATCH: SQLite={s!r} vs names_csv={cs!r}")
        q = embed_sapbert_one(s, tokenizer, model, args.device, max_len)
        row = sap_mm[i].astype(np.float32, copy=False)
        c = cosine_after_l2(q, row)
        worst = min(worst, c)
        print(f"  ord={i:6d}  cos={c:.8f}  name={s[:80]!r}{'...' if len(s) > 80 else ''}")
    print(f"  min_cosine_in_batch = {worst:.8f}  (expect ~1.0)")
    if worst < 0.99:
        print(
            "\n  Diagnosis: cosine far from 1 usually means sqlite/memmap/manifest are from different\n"
            "  runs, or this Python does not match the precompute stack. Re-run precompute in one\n"
            "  directory, or compare manifest['embeddings']['sapbert']['file'] mtime vs sqlite."
        )

    # --- B) Optional CSV: strings that exactly exist in pool ---
    if args.scan_csv is None:
        print("\n(No --scan-csv: skip CSV hit scan.)")
        return

    cols = [c.strip() for c in args.scan_cols.split(",") if c.strip()]
    hits = collect_exact_pool_hits_from_csv(
        args.scan_csv,
        cols,
        pool_lookup,
        max_rows=args.max_csv_rows,
        case_insensitive=case_insensitive,
    )
    print(f"\n=== CSV exact pool hits (unique strings, first {args.max_hits_print} shown) ===")
    print(f"  scan: {args.scan_csv}  cols={cols}  case_insensitive={case_insensitive}")
    if not hits:
        print("  (none found)")
        return

    def resolve_ord(s: str) -> int:
        if case_insensitive:
            return lower_to_ord[s.lower()]
        return name_to_ord[s]

    for s in hits[: args.max_hits_print]:
        j = resolve_ord(s)
        q = embed_sapbert_one(s, tokenizer, model, args.device, max_len)
        row = sap_mm[j].astype(np.float32, copy=False)
        c = cosine_after_l2(q, row)
        print(f"  ord={j:6d}  cos={c:.8f}  hit={s[:100]!r}{'...' if len(s) > 100 else ''}")

    if len(hits) > args.max_hits_print:
        print(f"  ... ({len(hits) - args.max_hits_print} more hits not printed)")


if __name__ == "__main__":
    main()
