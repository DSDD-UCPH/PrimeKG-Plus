# PrimeKG-Plus: a literature-derived expansion of a multimodal precision medicine knowledge graph
----
**Note**: the manuscript is in submission and can be accessed on bioRxiv at: https://submit.biorxiv.org/submission/pdf?msid=BIORXIV/2026/738415&roleName=author&msversion=2
(ver 2 - latest)


[![GitHub Repo](https://img.shields.io/badge/GitHub-DSDD--UCPH%2FPrimeKG--Plus-blue)](https://github.com/DSDD-UCPH/PrimeKG-Plus)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zenodo](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.20796545-blue)](https://doi.org/10.5281/zenodo.20796545)

[**GitHub**](https://github.com/DSDD-UCPH/PrimeKG-Plus) | [**Zenodo dataset**](https://doi.org/10.5281/zenodo.20796545) | [**Original PrimeKG**](https://github.com/mims-harvard/PrimeKG) | [**Dataset guide**](dataset/README.md)

## TL;DR

This release provides **two PrimeKG-compatible knowledge graphs** (build **20260529**), both distributed via [Zenodo](https://doi.org/10.5281/zenodo.20796545):


### PrimeKG-Plus
`dataset/PrimeKG-Plus/primekg_plus.csv`

Extends [PrimeKG](#) with updated public biomedical resources through **Dec 2025**, plus **Open Targets**, **RepurposeDrugs**, and **SIDER+nSIDES**.

- **Nodes:** 129,317
- **Directed edges:** 7,683,206
- **PubMed-derived relations:** *none included*

### PrimeKG-Plus-RD
`dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv`

The *literature-augmented build* for four rare neurological disorders — Canavan disease, Batten disease, Niemann–Pick disease type C, and Tay–Sachs disease. Contains every edge in `primekg_plus.csv`, plus expert-validated novel literature edges.

- **Nodes:** 129,353
- **Directed edges:** 7,683,756
- **New literature edges:** 550 *(derived from 637 curated PubMed abstracts and PMC full-text articles)*
- **New ontology nodes:** 36
  


## Table of Contents

- [Unique features of PrimeKG-Plus](#unique-features-of-primekg-plus)
- [Using PrimeKG-Plus](#using-primekg-plus)
- [Building an updated PrimeKG-Plus](#building-an-updated-primekg-plus)
- [Citing PrimeKG-Plus](#citing-primekg-plus)
- [Data hosting](#data-hosting)
- [License](#license)

## Unique features of PrimeKG-Plus
- **Updated public databases:** Refreshed upstream sources relative to original PrimeKG, including Open Targets disease–protein associations, RepurposeDrugs Phase-4 indications, and SIDER integrated with nSIDES.
- **Two graph products:** `primekg_plus.csv` (public databases only) and `primekg_plus_rd.csv` (`primekg_plus.csv` + **550** curated literature edges for four studied neurological disorders).
- **PrimeKG-compatible schema:** Same edge-list format as PrimeKG (`relation`, `display_relation`, `x_id`, `y_id`, …) with companion `nodes.csv` and `edges.csv` exports.
- **Validation bundle:** Manuscript supplementary tables (S1–S11), comparison tables against original PrimeKG, and a bundled Original PrimeKG baseline (`dataset/baseline/no_dup_kg.csv`).
- **Self-contained rebuild:** Processing scripts live in this repository (`primary_data_prep/`, `additional_data_source/`); no separate PrimeKG checkout is required to find upstream preprocessing code.

## Using PrimeKG-Plus

Graph CSVs are distributed via **Zenodo** (not stored in git). After downloading the archive and cloning this repo with local data:

### Getting started in Python

```python
import pandas as pd
from pathlib import Path

ROOT = Path("PrimeKG-Plus_release")  # Zenodo extract or repo root

# Public-database graph
kg = pd.read_csv(ROOT / "dataset/PrimeKG-Plus/primekg_plus.csv", low_memory=False)

# Literature-augmented graph (four rare neurological disorders)
kg_rd = pd.read_csv(
    ROOT / "dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv",
    low_memory=False,
)

print(len(kg), "directed edges (primekg_plus)")
print(len(kg_rd), "directed edges (primekg_plus_rd)")
```

For file-level documentation (tables, literature curation, supplementary CSVs), see [`dataset/README.md`](dataset/README.md).

## Building an updated PrimeKG-Plus

### Downloading and curating primary data resources
Run from `primary_data_prep/`:

```bash
cd primary_data_prep
bash primary_data_resources_plus.sh
```

Licensed sources (DrugBank, UMLS) require manual download first; then re-run with `DRUGBANK_SRC` and `UMLS_SRC` set. All processed files are written under `primary_data_prep/data/`. Details: [`primary_data_prep/README.md`](primary_data_prep/README.md).

| Database | Processing script | Expected output under `primary_data_prep/data/` |
|----------|-------------------|--------------------------------------------------|
| Bgee | `processing_scripts/bgee.py` | `bgee/anatomy_gene.csv` |
| Comparative Toxicogenomics Database | `processing_scripts/ctd.py` | `ctd/exposure_data.csv` |
| DisGeNET | — *(manual)* | `disgenet/Authors-curated_gene_disease_associations.tsv` |
| DrugBank | `drugbank_drug_drug.py`, `drugbank_drug_protein.py`, `drugbank_atc.py` | `drugbank/drug_drug.csv`, `drugbank/drug_protein.csv`; `vocab/drugbank_atc_codes.csv` |
| DrugCentral | — *(manual)* | `drugcentral/drug_disease_cleaned.csv` |
| Entrez Gene | `processing_scripts/ncbigene.py` | `ncbigene/protein_go_associations.csv` |
| Gene Ontology | `processing_scripts/go.py` | `go/go_terms_info.csv`, `go/go_terms_relations.csv` |
| Human Phenotype Ontology | `processing_scripts/hpo.py`, `hpoa.py` | `hpo/hp_terms.csv`, `hp_parents.csv`, `hp_references.csv`, `disease_phenotype_pos.csv`, `disease_phenotype_neg.csv` |
| MONDO | `processing_scripts/mondo.py` | `mondo/mondo_terms.csv`, `mondo_parents.csv`, `mondo_references.csv`, … |
| Reactome | `processing_scripts/reactome.py` | `reactome/reactome_ncbi.csv`, `reactome_terms.csv`, `reactome_relations.csv` |
| UBERON | `processing_scripts/uberon.py` | `uberon/uberon_terms.csv`, `uberon_rels.csv`, `uberon_is_a.csv` |
| UMLS | `processing_scripts/umls.py`, `map_umls_mondo.py` | `umls/umls.csv`; `vocab/umls_mondo.csv` |
| UMLS–MONDO (build) | — *(Monarch curation)* | `vocab/umls_mondo_bijective.csv` |
| PPI | — *(manual merge)* | `ppi/protein_protein.csv` |
| HGNC | `primary_data_resources_plus.sh` | `vocab/gene_names.csv`, `vocab/gene_map.csv` |

### Curating additional Plus-only sources

Scripts in `additional_data_source/` write into the same `primary_data_prep/data/` tree. Details: [`additional_data_source/README.md`](additional_data_source/README.md).

| Source | Script | Expected output |
|--------|--------|-----------------|
| Open Targets | `opentarget/process_opentarget.ipynb` | `disgenet/OpenTarget/OpenTarget_disease_protein_associations.csv` |
| RepurposeDrugs (Phase 4) | `repurposed_drug/process_repurposed_drug.ipynb` | `repurposed_drug/RepurposedDrug_Indication.csv` |
| SIDER + nSIDES | `sider_nsides/build_sider.py`, `process_sider_nsides.ipynb` | `sider/sider.csv`, `sider/sider_with_nsides.csv` |

### Harmonizing datasets into PrimeKG-Plus

After upstream tables are in `primary_data_prep/data/`:

```bash
jupyter nbconvert --execute scripts/01_build_graph.ipynb
jupyter nbconvert --execute scripts/02_disease_grouping.ipynb
cd scripts/literature_curation && python 09_integrate_primekg_plus_rd.py
```

| Step | Script | Output |
|------|--------|--------|
| 1 | `scripts/01_build_graph.ipynb` | `dataset/PrimeKG-Plus/auxillary/kg_raw.csv`, `kg_giant.csv` |
| 2 | `scripts/02_disease_grouping.ipynb` | `dataset/PrimeKG-Plus/primekg_plus.csv`, `nodes.csv`, `edges.csv` |
| 3–8 | `scripts/literature_curation/03_*` … `08_*` | Curated literature CSVs (full audit trail; see `literature_curation/README.md`) |
| 9 | `scripts/literature_curation/09_integrate_primekg_plus_rd.py` | `dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv` |

Full pipeline index: [`scripts/SCRIPTS.md`](scripts/SCRIPTS.md).

## Citing PrimeKG-Plus

If you use PrimeKG-Plus, cite the Zenodo record and the manuscript (in submission):

```
@dataset{primekg_plus_2026,
  title  = {PrimeKG-Plus knowledge graphs (build 20260529)},
  author = {Nguyen, Trinh Trung Duong
            and Nguyen-Phuong, Thuy
            and Nguyen, Quy-Hoai
            and Abbasi, Amna Mumtaz
            and Le Phan, Hanh-Dung
            and Nguyen, Luong Bao-Anh
            and Phan, Nhat-Thien
            and Curabaz, Nurettin Nusret
            and Hauser, Alexander S.
            and Tanoli, Ziaurrehman
            and Nguyen, Dinh Truong
            and Kooistra, Albert J.},
  year   = {2026},
  doi    = {10.5281/zenodo.20796545},
  url    = {https://doi.org/10.5281/zenodo.20796545}
}
```

Manuscript: *PrimeKG-Plus: a literature-derived expansion of a multimodal precision medicine knowledge graph* — *Scientific Data* (under review). See also [`CITATION.cff`](CITATION.cff).

Please cite [original PrimeKG](https://doi.org/10.1038/s41597-023-01960-3) when comparing against or building on the baseline graph.

## Data hosting

PrimeKG-Plus graphs and tables are hosted on [Zenodo](https://doi.org/10.5281/zenodo.20796545) (DOI [10.5281/zenodo.20796545](https://doi.org/10.5281/zenodo.20796545)). Rebuild code is on [GitHub](https://github.com/DSDD-UCPH/PrimeKG-Plus). Large graph CSVs are **not** committed to git; use Zenodo for downloads.

## License

- **Code** in this repository: [MIT](LICENSE).
- **Literature-curated relations** (`dataset/PrimeKG-Plus-RD/curated/`, integration outputs): CC-BY 4.0 (manuscript Usage Notes).
- **Bundled graph and table data:** see Zenodo record terms and upstream source licenses for individual databases.
