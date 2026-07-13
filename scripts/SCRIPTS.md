# Scripts index — public release (rebuild + use)

This package is for **dataset users** who want to rebuild or extend PrimeKG-Plus graphs.

## Layout

| Role | Path |
|------|------|
| `RELEASE_ROOT` | `PrimeKG-Plus_release/` (this folder's parent) |
| Primary upstream CSVs | `primary_data_prep/data/` (`PRIMARY_DATA_DIR` override) |
| Build outputs (full rebuild) | `dataset/PrimeKG-Plus/auxillary/` (stable filenames, e.g. `kg_giant.csv`) |
| Original PrimeKG baseline | `dataset/baseline/no_dup_kg.csv` |
| Curated literature CSVs | `dataset/PrimeKG-Plus-RD/curated/` |

---

## Primary data prep (before **01**)

| Step | Folder | Role |
|------|--------|------|
| Public + licensed DBs | `primary_data_prep/` | Download/process ontologies, DrugBank, UMLS, etc. → `primary_data_prep/data/` |
| Open Targets | `additional_data_source/opentarget/` | → `primary_data_prep/data/disgenet/OpenTarget/` |
| RepurposeDrugs | `additional_data_source/repurposed_drug/` | → `primary_data_prep/data/repurposed_drug/` |
| SIDER + nSIDES | `additional_data_source/sider_nsides/` | → `primary_data_prep/data/sider/` |

```bash
cd primary_data_prep
bash primary_data_resources_plus.sh
# licensed: DRUGBANK_SRC=... UMLS_SRC=... bash primary_data_resources_plus.sh
```

Details: [`primary_data_prep/README.md`](../primary_data_prep/README.md), [`additional_data_source/README.md`](../additional_data_source/README.md).

---

## Public pipeline

| # | Notebook / script | Produces |
|---|-------------------|----------|
| **01** | `01_build_graph.ipynb` | `auxillary/kg_raw.csv` → `kg_giant.csv` |
| **02** | `02_disease_grouping.ipynb` | `dataset/PrimeKG-Plus/primekg_plus.csv`, `nodes.csv`, `edges.csv` |
| **03** | `literature_curation/03_map_curated_entities_canavan.ipynb` | Canavan entity mapping (audit; needs `CURATION_ROOT`) |
| **04** | `literature_curation/04_map_curated_entities_batten.ipynb` | Batten entity mapping |
| **05** | `literature_curation/05_map_curated_entities_npc.ipynb` | NPC entity mapping |
| **06** | `literature_curation/06_map_curated_entities_tay_sachs.ipynb` | Tay–Sachs entity mapping |
| **07** | `literature_curation/07_finalize_post_curation.ipynb` | Second-search QC tables per disease |
| **08** | `literature_curation/08_merge_expert_post_curation.py` | Expert-merge additional relations |
| **09** | `literature_curation/09_integrate_primekg_plus_rd.py` | `dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv` |

**Literature curation details (run order, env vars, manual expert step):** [`literature_curation/README.md`](literature_curation/README.md)

**Two graph products:**

- `dataset/PrimeKG-Plus/primekg_plus.csv` — updated public databases only (no PubMed curation)
- `dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv` — `primekg_plus.csv` + curated literature (4 neurological disorders)

### Rebuild primekg_plus_rd (release curated CSVs only)

```bash
cd scripts/literature_curation
python 09_integrate_primekg_plus_rd.py
```

(`integrate_primekg_plus_rd.py` is an alias for step **09**.)

Inputs: `dataset/PrimeKG-Plus/primekg_plus.csv`, `dataset/PrimeKG-Plus-RD/curated/*_final.csv` and `*_additional.csv`

---

## Dataset quick stats (build 20260529)

| Graph | Nodes | Directed edges |
|-------|------:|-----------------:|
| `primekg_plus.csv` | 129,317 | 7,683,206 |
| `primekg_plus_rd.csv` | 129,353 | 7,683,756 (+550 vs primekg_plus) |

Literature verify paths (optional): `dataset/PrimeKG-Plus-RD/path_analysis/disease_paths/*_verify_literature_direct.csv`

---

## Optional utilities

| Script | Role |
|--------|------|
| `literature_curation/lib/query_sapbert_rerank_sbert.py` | SapBERT + SBERT UMLS pool query (requires local UMLS embedding memmap) |
