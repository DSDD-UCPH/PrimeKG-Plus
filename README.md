# PrimeKG-Plus release package (public)

Reproducibility bundle for the PrimeKG-Plus dataset (build **20260529**).

**For manuscript validation, literature QC, and supplementary tables**, see the sibling folder
[`../PrimeKG-Plus_validation/`](../PrimeKG-Plus_validation/) (author/internal; not required for typical use).

## Graphs

- **`primekg_plus.csv`** — PrimeKG-Plus from **public databases only** (no PubMed).
- **`primekg_plus_rd.csv`** — **`primekg_plus.csv` + literature edges** for 4 neurological disorders (Canavan, Batten, Niemann–Pick type C, Tay–Sachs).

Same 12-column schema as `primekg_plus.csv`. **`primekg_plus_rd.csv`** adds literature **edges** on top of `primekg_plus.csv`; endpoints with a UMLS CUI that maps to MONDO/HPO are matched or added as new nodes (canonical ontology label). Rows without resolvable endpoints are skipped.

## Layout

```
PrimeKG-Plus_release/
├── README.md
├── LICENSE                    ← MIT (code)
├── CITATION.cff                 ← cite Zenodo DOI after deposit
├── docs/ZENODO_UPLOAD_CHECKLIST.md
├── dataset/
│   ├── primekg_plus.csv, nodes.csv, edges.csv
│   ├── supplementary_tables/    ← Table S1–S9 CSV
│   ├── baseline/no_dup_kg.csv
│   ├── auxillary/
│   └── literature_curation/
│       ├── primekg_plus_rd.csv
│       ├── curated/             ← 8 CSVs to rebuild primekg_plus_rd
│       └── path_analysis/       ← short literature-verify paths only
├── scripts/
│   ├── materialize_release_bundle.sh
│   ├── 01_build_graph.ipynb
│   ├── 02_disease_grouping.ipynb
│   ├── literature_curation/integrate_primekg_plus_rd.py
│   └── source_prep/
└── scripts/SCRIPTS.md
```

Large CSVs may be **symlinks** on the author machine; materialize before Zenodo upload:

```bash
chmod +x scripts/materialize_release_bundle.sh
./scripts/materialize_release_bundle.sh          # copy symlinks + curated + supp tables
./scripts/materialize_release_bundle.sh --tarball  # optional zenodo_bundle.tar.gz
```

See `docs/ZENODO_UPLOAD_CHECKLIST.md` and `dataset/README.md`.

## Quick start

```python
import pandas as pd
from pathlib import Path

ROOT = Path("PrimeKG-Plus_release")
kg = pd.read_csv(ROOT / "dataset/primekg_plus.csv", low_memory=False)
kg_rd = pd.read_csv(ROOT / "dataset/literature_curation/primekg_plus_rd.csv", low_memory=False)
print(len(kg), "edges (public DB)")
print(len(kg_rd), "edges (with literature)")
```

## Rebuild pipeline

1. `source_prep/` → prepare upstream tables  
2. `scripts/01` → `scripts/02` → **`dataset/primekg_plus.csv`**  
3. `scripts/literature_curation/integrate_primekg_plus_rd.py` → **`dataset/literature_curation/primekg_plus_rd.csv`**

Details: `scripts/SCRIPTS.md`

## Before Zenodo / GitHub release

```bash
chmod +x scripts/materialize_release_bundle.sh
./scripts/materialize_release_bundle.sh
```

See `docs/ZENODO_UPLOAD_CHECKLIST.md`.
