# PrimeKG-Plus dataset files

## Main files (same roles as PrimeKG Dataverse)

| File | Description | Build |
|------|-------------|-------|
| `primekg_plus.csv` | Full directed edge list (12 columns, PrimeKG schema) | `20260529-primekg_plus.csv` |
| `nodes.csv` | Unique nodes | `20260529-nodes.csv` |
| `edges.csv` | Edge export (companion) | `20260529-edges.csv` |

**Release stats:** 129,317 nodes · 7,683,206 directed edges (`primekg_plus.csv`) · 30 relation types.

**Literature graph:** `literature_curation/primekg_plus_rd.csv` — same as `primekg_plus.csv` + **550** PubMed/PMC edges for 4 neurological disorders (see root `README.md`).

## Baseline (comparison)

| File | Description |
|------|-------------|
| `baseline/no_dup_kg.csv` | Published Original PrimeKG (deduplicated) |

Source: `PrimeKG/dataverse_files/no_dup_kg.csv` ([Dataverse](https://doi.org/10.7910/DVN/IXA7BM)).

## Auxiliary (rebuild pipeline)

| File | Stage |
|------|--------|
| `auxillary/kg_raw.csv` | Before giant-component extraction |
| `auxillary/kg_giant.csv` | Giant component only |
| `auxillary/kg_grouped.csv` | After disease grouping |
| `auxillary/kg_grouped_diseases_bert_map.csv` | MONDO → group name map |
| `auxillary/20260616_dup_name_group_fixes.csv` | Expert overrides for duplicate disease names |

## Supplementary tables

CSV copies of manuscript comparison tables **S1–S9** live in `dataset/supplementary_tables/` (copied during `scripts/materialize_release_bundle.sh` from the validation build). Tables **S10–S11** appear in the Supplementary Information document only.

Internal regeneration scripts (Table S1–S9) are in **`../PrimeKG-Plus_validation/`** (author/internal).

## `primekg_plus_rd.csv`

Same 12-column schema. Adds literature **edges**; disease/phenotype endpoints with UMLS CUI → MONDO/HPO are matched or added as new nodes. Rebuild: `integrate_primekg_plus_rd.py`.

| File | Role |
|------|------|
| `literature_curation/primekg_plus_rd.csv` | Main file |
| `literature_curation/curated/` | Input CSVs to rebuild (`integrate_primekg_plus_rd.py`) |

### Literature verify paths (optional)

`literature_curation/path_analysis/disease_paths/*_verify_literature_direct.csv` — short paths for literature reconciliation (~7 MB total). Full path enumeration outputs are in **`../PrimeKG-Plus_validation/`**.

## Supplementary tables (internal)

Table S1–S9 and script **03** are in **`../PrimeKG-Plus_validation/dataset/supplementary_tables/`** (manuscript validation; not required for graph use).

## Symlinks

On the author machine, large files are symlinks into `PrimeKG/datasets/data/kg/` and `PrimeKG/dataverse_files/`. For Zenodo/GitHub release, run:

```bash
./scripts/materialize_release_bundle.sh
```

This replaces symlinks with file copies and populates `literature_curation/curated/` plus `supplementary_tables/`.
