# Scripts index — public release (rebuild + use)

This package is for **dataset users** who want to rebuild or extend PrimeKG-Plus graphs.
Manuscript validation notebooks (03–08, 09–14, path analysis, Table S generation) live in
**[`../PrimeKG-Plus_validation/`](../PrimeKG-Plus_validation/)** (internal).

## Layout

| Role | Path |
|------|------|
| `RELEASE_ROOT` | `PrimeKG-Plus_release/` |
| Build outputs | `PrimeKG/datasets/data/kg/` (`RUN_DATE` = `20260529`) |
| Original PrimeKG | `dataset/baseline/no_dup_kg.csv` |
| Curated literature CSVs | `dataset/literature_curation/curated/` |

Override: `export PRIMEKG_ROOT=/path/to/PrimeKG`

---

## Source preparation (before **01**)

| Step | Folder | Output for **01** |
|------|--------|-------------------|
| Open Targets | `source_prep/opentarget/` | disease–protein associations |
| RepurposedDrugs | `source_prep/repurposed_drug/` | Phase-4 indications |
| SIDER + nSIDES | `source_prep/sider_nsides/` | drug-effect table |

---

## Public pipeline

| # | Notebook / script | Produces |
|---|-------------------|----------|
| **01** | `01_build_graph.ipynb` | `auxillary/kg_raw.csv` → `kg_giant.csv` |
| **02** | `02_disease_grouping.ipynb` | `dataset/primekg_plus.csv`, `nodes.csv`, `edges.csv` |
| **15** | `literature_curation/integrate_primekg_plus_rd.py` | `dataset/literature_curation/primekg_plus_rd.csv` |

**Two graph products:**

- `dataset/primekg_plus.csv` — updated public databases only (no PubMed curation)
- `dataset/literature_curation/primekg_plus_rd.csv` — `primekg_plus.csv` + curated literature (4 neurological disorders)

### Rebuild primekg_plus_rd

```bash
cd scripts/literature_curation
python integrate_primekg_plus_rd.py
```

Inputs: `dataset/primekg_plus.csv`, `dataset/literature_curation/curated/*_final.csv` and `*_additional.csv`

---

## Dataset quick stats (build 20260529)

| Graph | Nodes | Directed edges |
|-------|------:|-----------------:|
| `primekg_plus.csv` | 129,317 | 7,683,206 |
| `primekg_plus_rd.csv` | 129,353 | 7,683,756 (+550 vs primekg_plus) |

Literature verify paths (optional): `dataset/literature_curation/path_analysis/disease_paths/*_verify_literature_direct.csv`

---

## Internal validation (not in this folder)

See `../PrimeKG-Plus_validation/SCRIPTS.md` for 03–08, 09–14, supplementary tables, full path analysis, manuscript update scripts.

---

## Release packaging

| Script | Role |
|--------|------|
| `materialize_release_bundle.sh` | Replace symlinks, copy `curated/` + supplementary tables for Zenodo |
| `docs/ZENODO_UPLOAD_CHECKLIST.md` | Field-by-field Zenodo/GitHub upload guide |
