# Rare-disease literature layer (`primekg_plus_rd`)

PrimeKG-Plus ships **two graph products**:

| File | Description |
|------|-------------|
| `../primekg_plus.csv` | Updated public databases only (directions 1–2). **No** PubMed-curated edges. |
| `primekg_plus_rd.csv` | **`primekg_plus.csv` + literature-derived edges** for four neurological disorders (direction 3). |

Build **20260529** (integrated 2026-06-20):

| Product | Nodes | Directed edges |
|---------|------:|---------------:|
| `primekg_plus.csv` | 129,317 | 7,683,206 |
| `primekg_plus_rd.csv` | 129,353 | 7,683,756 (+550 novel literature edges) |

## Curated input pool

Single merged pool (algorithm finals + expert-merge additional rows):

| Source | Rows (approx.) |
|--------|---------------:|
| Mapped finals (`curated/*_final.csv`) | ~1,087 |
| Expert additional (`curated/*_additional.csv`) | ~215 |
| **Deduped pool** | **1,290** |

Integration script: `scripts/literature_curation/integrate_primekg_plus_rd.py`

## Integration outcomes (20260529)

| Metric | Count |
|--------|------:|
| Curated pool (deduped) | 1,290 |
| Edges integrated into `primekg_plus_rd` | 626 |
| Novel vs `primekg_plus.csv` | **550** |
| Skipped (duplicate edge, unsupported relation type, unresolved endpoint) | 664 |

**Novel edges by disease:** NPC 353 · Batten 131 · Canavan 30 · Tay-Sachs 36.

## Files in this folder

| File | Role |
|------|------|
| `primekg_plus_rd.csv` | Rare-disease graph (= `primekg_plus` + literature) |
| `primekg_plus_rd_nodes.csv` | Node table (+36 literature nodes vs `primekg_plus`) |
| `primekg_plus_rd_edges.csv` | Companion edge export |
| `20260529-literature_edges_integrated.csv` | Provenance (PMID, disease cohort, resolve method) |
| `20260529-literature_edges_skipped.csv` | Audit of non-integrated curated rows |
| `20260529-primekg_plus_rd_integration_summary.json` | Machine-readable summary |
| `curated/` | Symlinks to mapped relation CSVs per disease |

## Rebuild

```bash
export CURATION_ROOT=/path/to/THUY_DATA_CURATION
cd PrimeKG-Plus_release/scripts/literature_curation
python integrate_primekg_plus_rd.py
```
