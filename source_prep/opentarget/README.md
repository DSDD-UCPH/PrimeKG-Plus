# Open Targets → disease–protein associations (preprocessing for **01**)

Produces the file consumed by `scripts/01_build_graph.ipynb`:

`datasets/data/disgenet/OpenTarget/20260426-OpenTarget_disease_protein_associations.csv`

That CSV is concatenated with DisGeNET (`Authors-curated_gene_disease_associations.tsv`) before building `disease_protein` edges.

---

## Script

| File | Description |
|------|-------------|
| `process_opentarget.ipynb` | Full pipeline (`20251120-ProcessOpenTargetData.ipynb`) |

**Run from:** this folder, or set working directory to `PrimeKG/datasets/data/disgenet/OpenTarget/` (as in the original notebook).

Open Targets Platform release used: **25.09** (`association_overall_direct`).

---

## Inputs (`inputs/`)

| File / folder | Role | Size (approx.) |
|---------------|------|----------------|
| `opentargets_associations/` | Raw parquet shards from Open Targets FTP (20 files) | ~29 MB |
| `OpenTargets_associations_merged.csv` | Merged associations (or rebuild from parquets in notebook) | ~226 MB |
| `OpenTargets_associations_merged.parquet` | Parquet alternative to CSV | ~30 MB |
| `disease.parquet` | Open Targets disease metadata (names, dbXRefs, UMLS) | ~5 MB |
| `20260417-EnsemblID-Genename.csv` | Ensembl ID → gene symbol mapping | ~416 KB |
| `Authors-curated_gene_disease_associations.tsv` | DisGeNET baseline (for overlap / novel-pair filtering) | ~11 MB |
| `Homo_sapiens.GRCh38.115.gtf.gz` | Ensembl GTF (only if regenerating Ensembl mapping; optional) | ~100 MB compressed |

**Download raw Open Targets data** (if not present):

```
https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/25.09/output/association_overall_direct/
```

The notebook includes helpers to list and download parquet files into `opentargets_associations/`.

---

## Output (`outputs/`)

| File | Used in |
|------|---------|
| `20260426-OpenTarget_disease_protein_associations.csv` | **01_build_graph** → merged with DisGeNET |

Canonical path on the author machine:

`PrimeKG/datasets/data/disgenet/OpenTarget/20260426-OpenTarget_disease_protein_associations.csv`

---

## Pipeline summary

1. Download / merge Open Targets association parquets → `OpenTargets_associations_merged.csv`
2. Map Ensembl target IDs to gene symbols (`20260417-EnsemblID-Genename.csv`)
3. Join disease metadata (`disease.parquet`) and extract UMLS CUIs
4. Filter against DisGeNET pairs; apply score threshold (see notebook)
5. Write `20260426-OpenTarget_disease_protein_associations.csv`

Then run **`01_build_graph.ipynb`** (DisGeNET + OpenTargets section).

---

## Symlinks

Files in `inputs/` and `outputs/` are **symlinks** to `PrimeKG/datasets/data/` on the author machine. For GitHub or another machine, copy the files or re-run `process_opentarget.ipynb` after downloading Open Targets data.
