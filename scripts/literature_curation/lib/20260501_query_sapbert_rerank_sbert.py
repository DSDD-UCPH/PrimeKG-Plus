#!/usr/bin/env python3
"""
Query full UMLS embedding pool: top-10 by SapBERT cosine, rerank by SBERT, report top-2.

Reads embedding_manifest.json in --out-dir (default: embedding_pool_2025AB).
Uses chunked scan for SapBERT (memory-safe).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SapBERT top-10 -> SBERT rerank -> top-2")
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/Users/ljw303/YANG_DATA/PrimeKG/datasets/data/umls/embedding_pool_2025AB"),
        help="Directory with embedding_manifest.json and memmaps",
    )
    p.add_argument(
        "--queries",
        type=str,
        nargs="+",
        default=["diabetes", "high blood pressure", "pneumonia", "heart attack", "migraine headache"],
    )
    p.add_argument("--sap-topk", type=int, default=10, help="Retrieve top-K by SapBERT")
    p.add_argument("--final-topk", type=int, default=2, help="After SBERT rerank, keep top-K")
    p.add_argument("--chunk", type=int, default=20000, help="Rows per chunk for SapBERT scan")
    p.add_argument("--device", type=str, default=None, help="cuda|cpu (default: manifest or cuda if available)")
    return p.parse_args()


def l2n_rows(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    d = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    out = (x / d).astype(np.float32, copy=False)
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def embed_sapbert(names: list[str], tokenizer, model, device: str, max_len: int) -> np.ndarray:
    toks = tokenizer(
        names,
        padding="max_length",
        truncation=True,
        max_length=max_len,
        return_tensors="pt",
    )
    toks = {k: v.to(device) for k, v in toks.items()}
    with torch.no_grad():
        cls = model(**toks)[0][:, 0, :]
    return cls.detach().cpu().numpy().astype(np.float32, copy=False)


def embed_sbert(names: list[str], model: SentenceTransformer) -> np.ndarray:
    arr = model.encode(
        names,
        convert_to_numpy=True,
        normalize_embeddings=False,
        show_progress_bar=False,
    )
    return arr.astype(np.float32, copy=False)


def merge_sap_top(prev: list[tuple[float, int]], loc: list[tuple[float, int]], k: int) -> list[tuple[float, int]]:
    prev = prev + loc
    prev.sort(key=lambda t: -t[0])
    return prev[:k]


def sapbert_topk_chunked(
    q: np.ndarray,
    sap_mm: np.memmap,
    n: int,
    chunk: int,
    k: int,
    beam: int,
) -> list[tuple[float, int]]:
    """q: (D,) float32, L2-normalized."""
    q = np.nan_to_num(q.astype(np.float64), nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    qn = l2n_rows(q.reshape(1, -1))[0]
    best: list[tuple[float, int]] = []
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        A = sap_mm[start:end].astype(np.float32, copy=False)
        A = l2n_rows(A)
        s = A @ qn
        m = min(beam, s.shape[0])
        idx = np.argpartition(s, -m)[-m:]
        idx = idx[np.argsort(s[idx])[::-1]]
        loc = [(float(s[i]), start + int(i)) for i in idx]
        best = merge_sap_top(best, loc, k=max(k, beam))
    return best[:k]


def fetch_meta(conn: sqlite3.Connection, ords: list[int]) -> dict[int, tuple[str, str]]:
    if not ords:
        return {}
    cur = conn.cursor()
    out: dict[int, tuple[str, str]] = {}
    step = 400
    for i in range(0, len(ords), step):
        chunk = ords[i : i + step]
        ph = ",".join(["?"] * len(chunk))
        for r in cur.execute(
            f"SELECT ord, cui, canonical_name FROM embed_rows WHERE ord IN ({ph})",
            chunk,
        ):
            out[int(r[0])] = (str(r[1]), str(r[2]))
    return out


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    manifest_path = out_dir / "embedding_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    n = int(manifest["n_cui_embedded"])
    sap_path = manifest["embeddings"]["sapbert"]["file"]
    sbert_path = manifest["embeddings"]["sbert"]["file"]
    sap_name = manifest["embeddings"]["sapbert"]["model"]
    sbert_name = manifest["embeddings"]["sbert"]["model"]
    max_len = int(manifest["embeddings"]["sapbert"]["max_len"])
    db_path = manifest["sqlite_path"]

    device = args.device or manifest.get("device") or ("cuda" if torch.cuda.is_available() else "cpu")

    tok = AutoTokenizer.from_pretrained(sap_name)
    sap_model = AutoModel.from_pretrained(sap_name).to(device).eval()
    sb_model = SentenceTransformer(sbert_name, device=device)

    sap_mm = np.memmap(sap_path, mode="r", dtype=np.float16, shape=tuple(manifest["embeddings"]["sapbert"]["shape"]))
    sbert_mm = np.memmap(sbert_path, mode="r", dtype=np.float16, shape=tuple(manifest["embeddings"]["sbert"]["shape"]))

    conn = sqlite3.connect(str(db_path))
    beam = max(64, args.sap_topk * 4)

    for qtext in args.queries:
        q_sap = embed_sapbert([qtext], tok, sap_model, device, max_len)[0]
        sap_top = sapbert_topk_chunked(q_sap, sap_mm, n, args.chunk, args.sap_topk, beam)
        ords = [t[1] for t in sap_top]
        meta = fetch_meta(conn, ords)

        q_sb = embed_sbert([qtext], sb_model)[0]
        q_sb = l2n_rows(q_sb.reshape(1, -1))[0]

        reranked: list[tuple[float, float, int]] = []
        for sap_sc, ord_ in sap_top:
            row = sbert_mm[ord_].astype(np.float32, copy=False)
            row = l2n_rows(row.reshape(1, -1))[0]
            sb_sc = float(np.dot(row, q_sb))
            reranked.append((sb_sc, sap_sc, ord_))
        reranked.sort(key=lambda t: -t[0])
        final = reranked[: args.final_topk]

        print(f"\n=== Query: {qtext!r} ===")
        print("  SapBERT top-10 (ord, sap_cos, cui | name):")
        for rank, (sap_sc, ord_) in enumerate(sap_top, 1):
            cui, name = meta.get(ord_, ("?", f"(missing ord={ord_})"))
            print(f"    {rank:2d}  ord={ord_}  sap={sap_sc:.4f}  {cui}  |  {name}")
        print(f"  SBERT rerank -> top-{args.final_topk}:")
        for rank, (sb_sc, sap_sc, ord_) in enumerate(final, 1):
            cui, name = meta.get(ord_, ("?", f"(missing ord={ord_})"))
            print(f"    {rank}  sb={sb_sc:.4f}  (sap was {sap_sc:.4f})  {cui}  |  {name}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
