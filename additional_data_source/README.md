# Additional sources (beyond the 20 primary resources used by PrimeKG)

Scripts read bundled `inputs/` from this folder and **write build outputs into `primary_data_prep/data/`** (same layout as original PrimeKG `datasets/data/`).


| Step | Folder | Script | Output under `primary_data_prep/data/` |
|------|--------|--------|-----------------------------------|
| Open Targets | `opentarget/` | `process_opentarget.ipynb` | `disgenet/OpenTarget/OpenTarget_disease_protein_associations.csv` |
| RepurposeDrugs | `repurposed_drug/` | `process_repurposed_drug.ipynb` | `repurposed_drug/RepurposedDrug_Indication.csv` |
| SIDER + nSIDES | `sider_nsides/` | `build_sider.py` + `process_sider_nsides.ipynb` | `sider/sider.csv`, `sider/sider_with_nsides.csv` |

Run each notebook **from its folder** (`additional_data_source/<name>/`).

## Pipeline order

1. `primary_data_prep/primary_data_resources_plus.sh` — public ontologies + licensed DBs
2. **This folder** — Open Targets, RepurposeDrugs, SIDER+nSIDES
3. `scripts/01_build_graph.ipynb` — reads everything from `primary_data_prep/data/`

The shell script in step 1 also **seeds** bundled CSVs from `additional_data_source/*/outputs/` into `primary_data_prep/data/` when those files are missing (so you can skip regeneration).

## Open Targets

**Output:** `primary_data_prep/data/disgenet/OpenTarget/OpenTarget_disease_protein_associations.csv`

Merged with DisGeNET (`disgenet/Authors-curated_gene_disease_associations.tsv`) in notebook **01**.

| Input (`opentarget/inputs/`) | Role |
|------------------------------|------|
| `opentargets_associations/` | Raw parquet shards (Open Targets FTP) |
| `OpenTargets_associations_merged.csv` | Merged associations |
| `disease.parquet` | Disease metadata |
| `20260417-EnsemblID-Genename.csv` | Ensembl → gene symbol |
| `Authors-curated_gene_disease_associations.tsv` | DisGeNET baseline for filtering |

## RepurposeDrugs

**Output:** `primary_data_prep/data/repurposed_drug/RepurposedDrug_Indication.csv`

Source: [RepurposedDrugs](https://repurposedrugs.org/) Phase 4 pairs.

**External inputs** (from `primary_data_prep/data/` after step 1): DrugCentral cleaned CSV, DrugBank XML, UMLS `MRSTY.RRF` + `umls.csv`.

## SIDER + nSIDES

**Outputs:**

- `primary_data_prep/data/sider/sider.csv` — SIDER baseline (`build_sider.py`)
- `primary_data_prep/data/sider/sider_with_nsides.csv` — merged table for **01**

| Input (`sider_nsides/inputs/`) | Role |
|--------------------------------|------|
| `sider/drug_atc.tsv`, `meddra_all_se.tsv` | Raw SIDER dumps |
| `nsides/csv/high_confidence.csv` | nSIDES high-confidence pairs |
| `nsides/csv/vocab_*.csv` | nSIDES vocabularies |

> **nSIDES folder naming:** Upstream Open nSIDES unpacks as `onsides-v3.1.0/csv/`; copy the three CSV files into `inputs/nsides/csv/` if re-downloading.

```bash
cd additional_data_source/sider_nsides
python build_sider.py
# then run process_sider_nsides.ipynb
```

## Path helper

`additional_data_source/release_paths.py` resolves `RELEASE_ROOT` and `primary_data_prep/data/` for all notebooks in this folder.
