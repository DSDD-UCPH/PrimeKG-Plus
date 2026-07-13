"""SapBERT CLS embeddings and L2-normalized cosine similarity for entity matching."""

from __future__ import annotations

__all__ = [
    "cosine_after_l2",
    "embed_sapbert_batch",
    "embed_sapbert_one",
    "embed_sapbert_pool_matrix",
    "sapbert_cosine_sims_vs_pool_live",
]

import numpy as np
import torch


def _l2n_row(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64).ravel()
    n = float(np.linalg.norm(v) + 1e-12)
    return v / n


def embed_sapbert_one(
    name: str,
    tokenizer,
    model: torch.nn.Module,
    device: str,
    max_len: int,
) -> np.ndarray:
    """Encode one string: CLS token, ``padding=max_length``, ``max_length=max_len``."""
    toks = tokenizer(
        [str(name).strip() or " "],
        padding="max_length",
        truncation=True,
        max_length=max_len,
        return_tensors="pt",
    )
    toks = {k: v.to(device) for k, v in toks.items()}
    model.eval()
    with torch.no_grad():
        cls = model(**toks)[0][:, 0, :]
    return cls.detach().cpu().numpy().astype(np.float32, copy=False)[0]


def cosine_after_l2(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity after per-vector L2 normalization."""
    return float(np.dot(_l2n_row(a), _l2n_row(b)))


def embed_sapbert_batch(
    names: list[str],
    tokenizer,
    model: torch.nn.Module,
    device: str,
    max_len: int,
) -> np.ndarray:
    """Batch CLS embeddings (same tokenizer settings as PrimeKG precompute)."""
    batch = [str(x).strip() or " " for x in names]
    toks = tokenizer(
        batch,
        padding="max_length",
        truncation=True,
        max_length=max_len,
        return_tensors="pt",
    )
    toks = {k: v.to(device) for k, v in toks.items()}
    model.eval()
    with torch.no_grad():
        cls = model(**toks)[0][:, 0, :]
    return cls.detach().cpu().numpy().astype(np.float32, copy=False)


def embed_sapbert_pool_matrix(
    pool_names: list[str],
    tokenizer,
    model: torch.nn.Module,
    device: str,
    max_len: int,
    batch_size: int = 256,
    show_progress: bool = True,
) -> np.ndarray:
    """Encode all ``pool_names`` once → ``(n_pool, dim)`` float32 raw vectors.

    Use when SapBERT memmap is unavailable: one forward pass over the pool instead of
    re-encoding the pool for every query (~``n_pool / batch_size`` batches total).
    """
    n_pool = len(pool_names)
    if n_pool == 0:
        dh = int(getattr(model.config, "hidden_size", 768))
        return np.zeros((0, dh), dtype=np.float32)
    first_end = min(int(batch_size), n_pool)
    first = embed_sapbert_batch(
        pool_names[:first_end],
        tokenizer,
        model,
        device,
        max_len,
    )
    _, d = first.shape
    out = np.empty((n_pool, d), dtype=np.float32)
    out[:first_end] = first
    start_iter = range(first_end, n_pool, int(batch_size))
    n_batches = max(0, (n_pool - first_end + int(batch_size) - 1) // int(batch_size))
    batches = start_iter
    if show_progress and n_batches:
        try:
            from tqdm.auto import tqdm

            batches = tqdm(start_iter, total=n_batches, desc="SapBERT encode pool → RAM", unit="batch")
        except ImportError:
            pass

    for start in batches:
        end = min(start + int(batch_size), n_pool)
        out[start:end] = embed_sapbert_batch(
            pool_names[start:end],
            tokenizer,
            model,
            device,
            max_len,
        )
    return out


def sapbert_cosine_sims_vs_pool_live(
    q_sap_row: np.ndarray,
    pool_names: list[str],
    tokenizer,
    model: torch.nn.Module,
    device: str,
    max_len: int,
    batch_size: int = 256,
) -> np.ndarray:
    """Cosine(query, pool_row) by live-encoding each pool batch (no memmap). Cost ~ n_pool/batch forwards."""
    q = _l2n_row(np.asarray(q_sap_row, dtype=np.float32))
    sims = np.empty(len(pool_names), dtype=np.float32)
    n_pool = len(pool_names)
    for start in range(0, n_pool, batch_size):
        end = min(start + batch_size, n_pool)
        emb = embed_sapbert_batch(
            pool_names[start:end],
            tokenizer,
            model,
            device,
            max_len,
        )
        emb_n = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)
        sims[start:end] = emb_n @ q
    return sims
