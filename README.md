# PrimeKG-Plus: a refreshed and rare-disease-enriched precision medicine knowledge graph

Pipeline and release for an updated, PrimeKG-compatible biomedical knowledge graph: refreshed public databases (through December 2025), three added resources ([Open Targets](https://www.opentargets.org/), [RepurposeDrugs](https://repurposedrugs.org/), SIDER+nSIDES), and optional literature-curated edges for four rare neurological disorders.

> **Notes**
>
> 1. If you **only want to use the released graphs**, skip to [Using PrimeKG-Plus](#using-primekg-plus)
> 2. If you want to **rebuild the public-database graph**, skip to [Building PrimeKG-Plus](#building-primekg-plus)
> 3. If you want to **add the rare-disease literature layer**, skip to [Literature-augmented graph (PrimeKG-Plus-RD)](#literature-augmented-graph-primekg-plus-rd)
> 4. Large CSV graphs are hosted on [Zenodo](https://doi.org/10.5281/zenodo.20796545), not in git

[![GitHub](https://img.shields.io/badge/GitHub-DSDD--UCPH%2FPrimeKG--Plus-blue)](https://github.com/DSDD-UCPH/PrimeKG-Plus)
[![Zenodo](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.20796545-blue)](https://doi.org/10.5281/zenodo.20796545)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Manuscript (bioRxiv): https://www.biorxiv.org/content/10.64898/2026.07.14.738415v1  
Original PrimeKG: https://github.com/mims-harvard/PrimeKG

---

## Why PrimeKG-Plus?

PrimeKG is widely used for precision-medicine network analyses, but its public release reflects a **June 2021** data cutoff. PrimeKG-Plus is a **necessary refresh**, not a lightweight add-on:

| Contribution | What it does |
|--------------|--------------|
| Database update | Rebuilds all 20 original PrimeKG sources to Dec 2025 releases |
| New resources | Adds Open Targets, RepurposeDrugs (Phase 4), and SIDER+nSIDES |
| Rare-disease layer | Curates literature relations for Canavan, Batten, NPC, and Tay–Sachs |

Two graph products are released:

| Product | File | Nodes | Directed edges | Literature edges |
|---------|------|------:|---------------:|-----------------:|
| **PrimeKG-Plus** | `dataset/PrimeKG-Plus/primekg_plus.csv` | 129,317 | 7,683,206 | none |
| **PrimeKG-Plus-RD** | `dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv` | 129,353 | 7,683,756 | +550 novel |

Build tag: **20260529**

---

## Pipeline components

1. **Primary data prep** (`primary_data_prep/`)  
   Download and process the original PrimeKG upstream resources (Bgee, CTD, DrugBank, MONDO, HPO, Reactome, UMLS, …).

2. **Additional Plus-only sources** (`additional_data_source/`)  
   Prepare Open Targets, RepurposeDrugs, and SIDER+nSIDES into the same `primary_data_prep/data/` tree.

3. **Graph assembly** (`scripts/01_build_graph.ipynb`, `scripts/02_disease_grouping.ipynb`)  
   Harmonize tables into a PrimeKG-compatible edge list → `primekg_plus.csv`.

4. **Literature curation** (`scripts/literature_curation/`)  
   Map, QC, and integrate expert-validated PubMed/PMC relations → `primekg_plus_rd.csv`.

---

## Installation

1. Clone the repository

```bash
git clone https://github.com/DSDD-UCPH/PrimeKG-Plus.git
cd PrimeKG-Plus
```

2. Create a Python environment (Python ≥ 3.10 recommended) and install dependencies used by the notebooks/scripts, for example:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install pandas numpy jupyter jupyterlab
# Add any extra packages required by individual notebooks as you run them
```

> Rebuild notebooks expect a standard scientific Python stack. See folder-level READMEs if a step needs extra packages.

---

## Using PrimeKG-Plus

### 1. Download the Zenodo archive

Graph CSVs are **not** stored in git. Download from Zenodo and place/extract so that `dataset/` matches the repo layout:

```bash
# Example — adjust URL/filename to the current Zenodo file name
wget "https://zenodo.org/records/20796545/files/PrimeKG-Plus_release.tar.gz?download=1" -O PrimeKG-Plus_release.tar.gz
tar -xzf PrimeKG-Plus_release.tar.gz
# Ensure dataset/PrimeKG-Plus/ and dataset/PrimeKG-Plus-RD/ are available under the repo root
```

Zenodo DOI: https://doi.org/10.5281/zenodo.20796545

### 2. Load a graph in Python

```python
import pandas as pd
from pathlib import Path

ROOT = Path(".")  # repo root / Zenodo extract

# Public-database graph (recommended starting point)
kg = pd.read_csv(ROOT / "dataset/PrimeKG-Plus/primekg_plus.csv", low_memory=False)

# Literature-augmented graph (four rare neurological disorders)
kg_rd = pd.read_csv(
    ROOT / "dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv",
    low_memory=False,
)

print(len(kg), "directed edges (primekg_plus)")
print(len(kg_rd), "directed edges (primekg_plus_rd)")
print(kg["relation"].value_counts().head())
```

### 3. Which file should I use?

| Goal | Use |
|------|-----|
| General drug-repurposing / ML on an up-to-date PrimeKG schema | `primekg_plus.csv` |
| Rare-disease analyses for Canavan / Batten / NPC / Tay–Sachs | `primekg_plus_rd.csv` |
| Compare against original PrimeKG | `dataset/baseline/no_dup_kg.csv` |
| File-level documentation | [`dataset/README.md`](dataset/README.md) |

Schema follows original PrimeKG (`relation`, `display_relation`, `x_id`, `y_id`, …) with companion `nodes.csv` / `edges.csv` exports.

---

## Building PrimeKG-Plus

> If you only want to reproduce the released graphs, download Zenodo and skip rebuild steps.  
> Licensed sources (**DrugBank**, **UMLS**) require manual download before a full rebuild.

### Step A — Primary biomedical resources

```bash
cd primary_data_prep
bash primary_data_resources_plus.sh

# After placing licensed archives locally:
# DRUGBANK_SRC=/path/to/drugbank UMLS_SRC=/path/to/umls bash primary_data_resources_plus.sh
```

Processed tables are written under `primary_data_prep/data/`.  
Details: [`primary_data_prep/README.md`](primary_data_prep/README.md)

### Step B — Plus-only additional sources

| Source | Script | Output (under `primary_data_prep/data/`) |
|--------|--------|------------------------------------------|
| Open Targets | `additional_data_source/opentarget/process_opentarget.ipynb` | `disgenet/OpenTarget/OpenTarget_disease_protein_associations.csv` |
| RepurposeDrugs | `additional_data_source/repurposed_drug/process_repurposed_drug.ipynb` | `repurposed_drug/RepurposedDrug_Indication.csv` |
| SIDER + nSIDES | `additional_data_source/sider_nsides/build_sider.py` (+ notebook) | `sider/sider.csv`, `sider/sider_with_nsides.csv` |

Details: [`additional_data_source/README.md`](additional_data_source/README.md)

### Step C — Assemble the public-database graph

```bash
jupyter nbconvert --execute scripts/01_build_graph.ipynb
jupyter nbconvert --execute scripts/02_disease_grouping.ipynb
```

| Step | Script | Main output |
|------|--------|-------------|
| 1 | `scripts/01_build_graph.ipynb` | `dataset/PrimeKG-Plus/auxillary/kg_raw.csv`, `kg_giant.csv` |
| 2 | `scripts/02_disease_grouping.ipynb` | `dataset/PrimeKG-Plus/primekg_plus.csv`, `nodes.csv`, `edges.csv` |

---

## Literature-augmented graph (PrimeKG-Plus-RD)

Focused on four rare neurological disorders: **Canavan**, **Batten**, **Niemann–Pick type C**, and **Tay–Sachs** (637 PubMed/PMC articles; expert-validated relations).

### Fast path — integrate release curated tables only

If `primekg_plus.csv` and curated CSVs are already present:

```bash
cd scripts/literature_curation
python 09_integrate_primekg_plus_rd.py
```

Output: `dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv`

### Full curation pipeline (rebuild from scratch)

| # | Script | Role |
|---|--------|------|
| 03–06 | `literature_curation/03_*` … `06_*` | Per-disease entity mapping |
| 07 | `07_finalize_post_curation.ipynb` | Second-search QC |
| 08 | `08_merge_expert_post_curation.py` | Expert merge of additional relations |
| 09 | `09_integrate_primekg_plus_rd.py` | Integrate into `primekg_plus_rd.csv` |

Full index: [`scripts/SCRIPTS.md`](scripts/SCRIPTS.md)  
Curation details: [`scripts/literature_curation/README.md`](scripts/literature_curation/README.md)

---

## Repository layout

```text
PrimeKG-Plus/
├── README.md                      # this guide (see also readme-ref.md drafts)
├── primary_data_prep/             # original PrimeKG sources → processed CSVs
├── additional_data_source/        # Open Targets, RepurposeDrugs, SIDER+nSIDES
├── scripts/
│   ├── 01_build_graph.ipynb
│   ├── 02_disease_grouping.ipynb
│   └── literature_curation/       # rare-disease literature pipeline
├── dataset/                       # graphs + tables (large CSVs via Zenodo)
│   ├── PrimeKG-Plus/
│   ├── PrimeKG-Plus-RD/
│   ├── baseline/
│   ├── comparison_tables/
│   └── supplementary_tables/
├── CITATION.cff
└── LICENSE
```

---

## Data hosting and license

- **Graphs & tables:** [Zenodo 10.5281/zenodo.20796545](https://doi.org/10.5281/zenodo.20796545)
- **Code:** [GitHub DSDD-UCPH/PrimeKG-Plus](https://github.com/DSDD-UCPH/PrimeKG-Plus) — MIT
- **Literature-curated relations:** CC-BY 4.0 (see manuscript Usage Notes)
- Upstream databases keep their own licenses (DrugBank, UMLS, etc.)

---

## Citation

If you use PrimeKG-Plus, please cite the Zenodo record and the manuscript:

```
@dataset{primekg_plus_2026,
  title  = {PrimeKG-Plus knowledge graphs (build 20260529)},
  author = {Nguyen, Trinh Trung Duong and Nguyen-Phuong, Thuy
            and Nguyen, Quy-Hoai and Abbasi, Amna Mumtaz
            and Le Phan, Hanh-Dung and Nguyen, Luong Bao-Anh
            and Phan, Nhat-Thien and Curabaz, Nurettin Nusret
            and Hauser, Alexander S. and Tanoli, Ziaurrehman
            and Nguyen, Dinh Truong and Kooistra, Albert J.},
  year   = {2026},
  doi    = {10.5281/zenodo.20796545},
  url    = {https://doi.org/10.5281/zenodo.20796545}
}
```

Manuscript: *PrimeKG-Plus: a refreshed and rare-disease-enriched precision medicine knowledge graph* (bioRxiv / under review). See [`CITATION.cff`](CITATION.cff).

Please also cite [original PrimeKG](https://doi.org/10.1038/s41597-023-01960-3) when comparing against or building on the baseline graph.

## License
- **Code**: MIT License (see [LICENSE](LICENSE))
- **Data**: CC0 1.0 Universal (see [DATA_LICENSE](DATA_LICENSE.md)) — 
  full dataset also archived on [Zenodo](https://zenodo.org/records/20796545) under CC0.

---

## Contact

Questions, bugs, or contributions: open an issue or pull request on [GitHub](https://github.com/DSDD-UCPH/PrimeKG-Plus).
