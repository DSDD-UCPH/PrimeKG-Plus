#!/usr/bin/env python3
"""SapBERT CLS + L2 — cùng cách gọi tokenizer như PrimeKG precompute (`padding=max_length`, `max_len=25`)."""

from __future__ import annotations

import argparse
import sys

import numpy as np
import torch
from sklearn.preprocessing import normalize
from transformers import AutoModel, AutoTokenizer

MODEL = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"
MAX_LEN = 25


class SapBERTEncoder:
    """SapBERT CLS; tokenizer giống precompute PrimeKG (`padding=max_length`, truncation, `max_length`)."""

    def __init__(
        self,
        device: str | None = None,
        model_name: str | None = None,
        default_max_len: int | None = None,
    ):
        d = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.device = torch.device(d)
        self.model_name = model_name or MODEL
        self.default_max_len = int(default_max_len if default_max_len is not None else MAX_LEN)
        self.tok = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device).eval()

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        max_length: int | None = None,
        normalize_embeddings: bool = True,
    ) -> np.ndarray:
        if not texts:
            d = int(self.model.config.hidden_size)
            return np.zeros((0, d), dtype=np.float32)
        texts = [str(t).strip() or " " for t in texts]
        ml = int(max_length) if max_length is not None else self.default_max_len
        self.model.eval()
        batch_dev = next(self.model.parameters()).device
        chunks: list[np.ndarray] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            toks = self.tok(
                batch,
                padding="max_length",
                truncation=True,
                max_length=ml,
                return_tensors="pt",
            )
            toks = {k: v.to(batch_dev) for k, v in toks.items()}
            with torch.no_grad():
                cls = self.model(**toks).last_hidden_state[:, 0, :]
            chunks.append(cls.cpu().numpy().astype(np.float32, copy=False))
        out = np.vstack(chunks)
        if normalize_embeddings:
            out = normalize(out, norm="l2")
        return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("texts", nargs="*", default=["Canavan disease", "Canavan leukodystrophy"])
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--device", type=str, default=None)
    args = p.parse_args()

    enc = SapBERTEncoder(device=args.device)
    uniq = list(dict.fromkeys(args.texts))
    E = enc.encode(uniq, batch_size=args.batch_size)
    idx = {t: i for i, t in enumerate(uniq)}
    # Pairs theo thứ tự người dùng nhập (kể cả trùng lặp); dedupe chỉ để encode.
    for i, a in enumerate(args.texts):
        for b in args.texts[i + 1 :]:
            c = float(np.dot(E[idx[a]], E[idx[b]]))
            print(f"{a!r} ↔ {b!r}: {c:.4f}")
    if len(args.texts) < 2:
        print(
            "# Cần ít nhất 2 chuỗi để có một cặp cosine (vd: ... \"a\" \"b\").",
            file=sys.stderr,
        )
    print("# sapbert_encode_primekg_style: finished OK (exit 0).", file=sys.stderr)


if __name__ == "__main__":
    main()
