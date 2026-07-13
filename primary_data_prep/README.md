# Primary data preparation (PrimeKG-Plus)

This folder replaces the need to clone [original PrimeKG](https://github.com/mims-harvard/PrimeKG) just to find upstream processing scripts. Scripts under `processing_scripts/` are forks of `PrimeKG/datasets/processing_scripts/`, adapted to:

- write into `primary_data_prep/data/` (override with `PRIMARY_DATA_DIR`)
- use **stable filenames** (no date prefixes)

## Quick start

```bash
cd primary_data_prep
bash primary_data_resources_plus.sh
```

Licensed sources (manual download first, then re-run with env vars):

```bash
export DRUGBANK_SRC=/path/to/drugbank-downloads
export UMLS_SRC=/path/to/umls-download
bash primary_data_resources_plus.sh
```

## Pipeline order

1. **`primary_data_prep/`** (this folder) — public ontologies + licensed DBs → `data/`
2. **`additional_data_source/`** — Open Targets, RepurposeDrugs, SIDER+nSIDES
3. **`scripts/01_build_graph.ipynb`** — reads `primary_data_prep/data/` by default

## Outputs used by notebook 01

| Resource | Path under `data/` |
|----------|-------------------|
| PPI | `ppi/protein_protein.csv` *(manual)* |
| DrugBank | `drugbank/drug_protein.csv`, `drug_drug.csv` |
| DisGeNET | `disgenet/Authors-curated_gene_disease_associations.tsv` *(manual)* |
| DrugCentral | `drugcentral/drug_disease_cleaned.csv` *(manual)* |
| MONDO / HPO / GO / … | `mondo/mondo_terms.csv`, `hpo/hp_terms.csv`, … |
| UMLS↔MONDO (build) | `vocab/umls_mondo_bijective.csv` *(Monarch curation; see SI Section E)* |
| HGNC | `vocab/gene_names.csv`, `gene_map.csv` |

`data/` is gitignored (large downloads). Scripts are versioned in this repo.

## Fork provenance

Processing logic follows the PrimeKG paper pipeline. When in doubt, compare with upstream `datasets/processing_scripts/` in the PrimeKG repository — but you should not need that repo to rebuild PrimeKG-Plus.
