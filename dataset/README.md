# PrimeKG-Plus dataset

This file documents the dataset contents in the [Zenodo archive](https://doi.org/10.5281/zenodo.20796545).

Code and rebuild documentation: <https://github.com/DSDD-UCPH/PrimeKG-Plus>  
Code license: MIT  
Literature curation data: CC-BY 4.0  
Cite: Zenodo DOI `10.5281/zenodo.20796545` (full reference in GitHub `CITATION.cff`)

## What is in this folder
```text
dataset/
├── README.md
├── PrimeKG-Plus/
│   ├── primekg_plus.csv
│   ├── nodes.csv
│   ├── edges.csv
│   └── auxillary/
├── PrimeKG-Plus-RD/
│   ├── primekg_plus_rd.csv
│   ├── primekg_plus_rd_nodes.csv
│   ├── primekg_plus_rd_edges.csv
│   ├── curated/
│   └── …
├── baseline/
├── comparison_tables/
└── supplementary_tables/
```

The file names and intermediate exports intentionally follow the naming and content structure of [original PrimeKG](https://github.com/mims-harvard/PrimeKG) as closely as possible. This includes names such as `nodes.csv`, `edges.csv`, `kg_raw.csv`, and `kg_giant.csv`.

## `PrimeKG-Plus/`

Public-database graph (no PubMed-derived edges):

- `primekg_plus.csv`: 129,317 nodes and 7,683,206 directed edges
- `nodes.csv`: companion node table
- `edges.csv`: companion edge export
- `auxillary/`: intermediate rebuild files (`kg_raw.csv`, `kg_giant.csv`, `kg_grouped.csv`, …)

## Quick start

If you only want one file to analyze, start with:

- `PrimeKG-Plus/primekg_plus.csv`
  Base PrimeKG-Plus graph before rare-disease literature augmentation.  
  Contains 30 relation types.  
  Use `PrimeKG-Plus/nodes.csv` and `PrimeKG-Plus/edges.csv` as companion exports.

- `PrimeKG-Plus-RD/primekg_plus_rd.csv`
  Most complete graph in the release.  
  Adds curated literature edges on top of `primekg_plus.csv` for Canavan, Batten, Niemann-Pick type C, and Tay-Sachs diseases.
  Disease and phenotype endpoints with a UMLS CUI that maps to MONDO or HPO are matched to existing nodes when possible; otherwise new nodes may be added. Rows with unsupported relations or unresolved endpoints are skipped.  
  Matching companion files are under `PrimeKG-Plus-RD/`.

  Quick summary:
  - Curated input pool: 1,290 rows
  - Integrated into `primekg_plus_rd`: 626 rows
  - Novel vs `primekg_plus.csv`: 550 edges
  - Skipped: 664 rows
  - Novel edges by disease: NPC 353, Batten 131, Canavan 30, Tay-Sachs 36

## Folders inside `dataset/`

- `PrimeKG-Plus/`: public-database graph + companion tables + build intermediates
- `PrimeKG-Plus-RD/`: literature-augmented graph and curation audit files
- `baseline/`: deduplicated Original PrimeKG for comparison
- `comparison_tables/`: extra graph-comparison outputs used during validation (not numbered in the manuscript)
- `supplementary_tables/`: CSV versions of manuscript Supplementary Tables S1–S11

## `PrimeKG-Plus-RD/`

This folder contains the rare-disease literature augmentation details for the base graph.

Files in `PrimeKG-Plus-RD/`:

- `primekg_plus_rd.csv`: main rare-disease graph
- `primekg_plus_rd_nodes.csv`: node table, including 36 literature-added nodes
- `primekg_plus_rd_edges.csv`: edge companion export
- `literature_edges_integrated.csv`: provenance table for integrated literature relations
- `literature_edges_novel.csv`: literature edges not already present in `primekg_plus.csv`
- `literature_edges_skipped.csv`: curated rows that were not integrated, with reasons
- `literature_nodes_added.csv`: nodes added during literature integration
- `primekg_plus_rd_integration_summary.json`: optional QC summary for one integration run
- `curated/`: curated input CSVs by disease (`*_final.csv`, `*_additional.csv`); direct rebuild inputs for `primekg_plus_rd.csv`
- `curation_source/`: extracted curation workspace (~6 MB) — spreadsheets, expert Excel reviews, post-curation intermediates; default `CURATION_ROOT` for steps 03–08 (see `curation_source/README.md`)

`primekg_plus_rd_integration_summary.json` is not required for graph analysis. It is mainly useful for reviewers, reproducibility checks, and comparing rebuilds without parsing the audit CSVs.

Optional verify paths:

- `PrimeKG-Plus-RD/path_analysis/disease_paths/*_verify_literature_direct.csv`

These short path files help inspect how curated literature relations connect within the graph.

## `baseline/`

This folder contains the comparison baseline:

- `baseline/no_dup_kg.csv`: published Original PrimeKG, deduplicated

Source: Harvard Dataverse ([DOI 10.7910/DVN/IXA7BM](https://doi.org/10.7910/DVN/IXA7BM)).

## `auxillary/` (under `PrimeKG-Plus/`)

Intermediate rebuild files that mirror the PrimeKG-style pipeline:

- `PrimeKG-Plus/auxillary/kg_raw.csv`: before giant-component extraction
- `PrimeKG-Plus/auxillary/kg_giant.csv`: giant component only
- `PrimeKG-Plus/auxillary/kg_grouped.csv`: after disease grouping
- `PrimeKG-Plus/auxillary/kg_grouped_diseases_bert_map.csv`: MONDO to group-name mapping
- `PrimeKG-Plus/auxillary/dup_name_group_fixes.csv`: expert overrides for duplicate disease names
- `PrimeKG-Plus/auxillary/kg_grouping_review_merge.csv`: pre-computed expert review — clusters assigned a merged group name
- `PrimeKG-Plus/auxillary/kg_grouping_review_reject.csv`: pre-computed expert review — clusters confirmed as separate (no merge)

These files are mainly useful for reproducibility, tracing how `primekg_plus.csv` was assembled, and understanding the disease-grouping stage.

## `supplementary_tables/`

CSV exports of manuscript **Supplementary Tables S1–S11**, aligned with `SUPPLEMENTARY_INFORMATION_v2.docx`:

| File | Manuscript table |
|------|------------------|
| `TableS1_node_types.csv` | S1 — node counts by entity type |
| `TableS1_node_totals.csv` | S1 — total node count summary row |
| `TableS2_edge_types.csv` | S2 — directed edge counts by relation type |
| `TableS2_edge_totals.csv` | S2 — total directed-edge summary row |
| `TableS3_disease_grouping.csv` | S3 — disease node grouping statistics |
| `TableS4_disease_degree.csv` | S4 — disease-node degree distribution |
| `TableS5_literature_curation_columns.csv` | S5 — literature curation output columns |
| `TableS6_relation_types.csv` | S6 — predefined PrimeKG relationship types |
| `TableS7_curated_examples.csv` | S7 — example curated relationship rows |
| `TableS8_curated_column_definitions.csv` | S8 — column definitions for curated relationships |
| `TableS9_umls_semantic_types.csv` | S9 — UMLS semantic types (TUIs) per entity type |
| `TableS10_mapping_ambiguity.csv` | S10 — mapping ambiguity examples |
| `TableS11_umls_mondo_vocabulary.csv` | S11 — UMLS–MONDO vocabulary summary |

Regenerate with `PrimeKG-Plus_validation/scripts/build_manuscript_supplementary_tables.py` (S1–S4 from graphs; S5–S11 extracted from the SI docx).

## `comparison_tables/`

Additional validation outputs comparing Original PrimeKG and PrimeKG-Plus. These are **not** numbered supplementary tables in the manuscript:

- `graph_pipeline_stages.csv` — directed edge counts through the PrimeKG post-processing pipeline
- `connected_components.csv` — giant-component statistics
- `selected_metrics.csv` — selected metrics with large absolute or relative change
- `edge_overlap.csv` — directed edge overlap by relation type
- `drug_protein_by_display_relation.csv` — DrugBank drug–protein edges by interaction type

## Rebuild

There are two rebuild paths:

- Rebuild `primekg_plus.csv` from the upstream sources
- Rebuild `primekg_plus_rd.csv` from `primekg_plus.csv` plus the curated literature files

### Rebuild `primekg_plus.csv`

Prepare upstream files (all inside this repo — no PrimeKG checkout required):

1. **`primary_data_prep/`** — run `primary_data_resources_plus.sh` (see [`primary_data_prep/README.md`](../primary_data_prep/README.md))
2. **`additional_data_source/`** — Open Targets, RepurposeDrugs, SIDER+nSIDES (see [`additional_data_source/README.md`](../additional_data_source/README.md))

Then run the public build pipeline:

```bash
jupyter nbconvert --execute scripts/01_build_graph.ipynb
jupyter nbconvert --execute scripts/02_disease_grouping.ipynb
```

This produces:

- `dataset/PrimeKG-Plus/primekg_plus.csv`
- `dataset/PrimeKG-Plus/nodes.csv`
- `dataset/PrimeKG-Plus/edges.csv`
- intermediate files in `dataset/PrimeKG-Plus/auxillary/`

See also:

- `primary_data_prep/README.md` for primary database download/processing
- `additional_data_source/README.md` for Open Targets, RepurposeDrugs, SIDER+nSIDES
- `scripts/SCRIPTS.md` for the full pipeline overview

### Rebuild `primekg_plus_rd.csv`

After `primekg_plus.csv` and `nodes.csv` are available, run:

```bash
cd scripts/literature_curation
python 09_integrate_primekg_plus_rd.py
```

Full literature pipeline (steps 03–09): [`scripts/literature_curation/README.md`](../scripts/literature_curation/README.md)

Default inputs are:

- `dataset/PrimeKG-Plus/primekg_plus.csv`
- `dataset/PrimeKG-Plus/nodes.csv`
- `dataset/PrimeKG-Plus-RD/curated/*.csv`

Override paths with `PLUS_KG`, `PLUS_NODES`, `CURATED_DIR`, or `PRIMEKG_ROOT`.
