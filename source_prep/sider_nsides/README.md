# SIDER + nSIDES → `sider_with_nsides.csv` (preprocessing for **01**)

Produces the drug–adverse-effect table consumed by `scripts/01_build_graph.ipynb` for **drug_effect** edges:

`source_prep/sider_nsides/outputs/sider_with_nsides.csv`

Pipeline: reproduce author **SIDER** table, augment with high-confidence **Open nSIDES** (release v3.1.0) associations, map RxNorm ingredients to ATC via DrugBank.

> **Folder naming:** This release uses `inputs/nsides/csv/`. The upstream Open nSIDES GitHub release unpacks as `onsides-v3.1.0/csv/` ([tatonetti-lab/onsides](https://github.com/tatonetti-lab/onsides)); copy those three CSV files here if re-downloading.

---

## Scripts

| File | Step | Description |
|------|------|-------------|
| `build_sider.py` | 0 | SIDER 4.1 MedDRA PT → `inputs/sider/sider.csv` |
| `process_sider_nsides.ipynb` | 1 | Merge SIDER + nSIDES → `outputs/sider_with_nsides.csv` |

Original notebook: `datasets/data/nSIDES/exploit_nSIDES_for_SIDER_integration.ipynb`

**Run from:** `source_prep/sider_nsides/` (set `PRIMEKG_ROOT` if auto-detection fails).

---

## Bundled files (this folder)

| Path | Role |
|------|------|
| `inputs/sider/drug_atc.tsv` | SIDER drug→ATC mapping (raw) |
| `inputs/sider/meddra_all_se.tsv` | SIDER MedDRA side effects (raw) |
| `inputs/sider/sider.csv` | SIDER baseline (~202k rows; output of step 0) |
| `inputs/nsides/csv/high_confidence.csv` | nSIDES high-confidence ingredient–effect pairs |
| `inputs/nsides/csv/vocab_meddra_adverse_effect.csv` | nSIDES MedDRA effect vocabulary |
| `inputs/nsides/csv/vocab_rxnorm_ingredient.csv` | nSIDES RxNorm ingredient vocabulary |
| `outputs/sider_with_nsides.csv` | Merged table for **01** (~175k rows) |

The full Open nSIDES release includes larger files (e.g. `product_adverse_effect.csv`, ~1.3 GB) that are **not** required by this pipeline.

---

## External input (regenerate only)

| Path under `PrimeKG/datasets/data/` | Role |
|-------------------------------------|------|
| `drugbank/Nurset_data_drugbank/2025_01_ver_full_database.xml` | RxNorm → ATC mapping for nSIDES rows |

---

## Pipeline summary

1. `python build_sider.py` → `inputs/sider/sider.csv` (skip if bundled copy is sufficient)
2. Run `process_sider_nsides.ipynb`:
   - Map nSIDES MedDRA effects to UMLS CUIs via SIDER effect vocabulary
   - Fill ATC codes from DrugBank XML (RxNorm ingredient IDs)
   - Concatenate with SIDER; dedupe on `(atc, UMLS_from_meddra, side_effect_name)`
3. Run **`01_build_graph.ipynb`** (SIDER drug_effect section)

---

## Canonical path on author machine

`PrimeKG/datasets/data/sider/sider_with_nsides.csv` (symlink target for release `outputs/` copy)
