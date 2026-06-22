# Zenodo upload checklist — PrimeKG-Plus (build 20260529)

Use this after running `scripts/materialize_release_bundle.sh` (and optionally `--tarball`).

**GitHub:** https://github.com/DSDD-UCPH/PrimeKG-Plus  
**Code license:** MIT (`LICENSE`)  
**Literature curation data:** CC-BY 4.0 (see manuscript Usage Notes)

---

## 1. Prepare the bundle (local)

```bash
cd PrimeKG-Plus_release
chmod +x scripts/materialize_release_bundle.sh
./scripts/materialize_release_bundle.sh --tarball
```

Verify:

- [ ] `dataset/primekg_plus.csv` is a real file (~900 MB), not a symlink
- [ ] `dataset/literature_curation/primekg_plus_rd.csv` resolves to dated CSV (~900 MB)
- [ ] `dataset/literature_curation/curated/` contains 8 CSV files (no broken symlinks)
- [ ] `dataset/baseline/no_dup_kg.csv` materialized (~936 MB)
- [ ] `dataset/supplementary_tables/TableS1–S9.csv` present (S10–S11 if exported)
- [ ] No `~$*.docx`, `.ipynb_checkpoints`, or author-only paths in tarball

---

## 2. Zenodo — record metadata

| Field | Suggested value |
|-------|-----------------|
| **Upload type** | Dataset |
| **Title** | PrimeKG-Plus knowledge graphs (build 20260529) |
| **Authors** | All 9 manuscript authors (same order as paper) |
| **Description** | Updated PrimeKG-style biomedical knowledge graphs from public databases, plus a literature-augmented build for four rare neurological diseases (Canavan, Batten, Niemann–Pick type C, Tay–Sachs). Includes rebuild scripts, baseline Original PrimeKG, supplementary tables S1–S9, and literature integration audit files. Directed edge counts: `primekg_plus.csv` 7,683,206 edges; `primekg_plus_rd.csv` 7,683,756 edges (+550 novel literature edges). |
| **Publication date** | 2026-06-20 (or acceptance date) |
| **Version** | 1.0.0 / 20260529 |
| **License** | CC-BY 4.0 (dataset); note MIT for code in README |
| **Keywords** | knowledge graph; PrimeKG; biomedical; rare disease; MONDO; literature curation |
| **Related identifier** | Scientific Data paper DOI (add when available) |
| **Related identifier** | Original PrimeKG: 10.7910/DVN/IXA7BM |

---

## 3. Zenodo — files to upload

### Required (core products)

| Path | Role |
|------|------|
| `dataset/primekg_plus.csv` | Main graph (DB-only) |
| `dataset/nodes.csv`, `dataset/edges.csv` | Companion exports |
| `dataset/literature_curation/primekg_plus_rd.csv` | Literature-augmented graph |
| `dataset/literature_curation/primekg_plus_rd_nodes.csv` | RD node table |
| `dataset/literature_curation/primekg_plus_rd_edges.csv` | RD edge companion |
| `README.md`, `dataset/README.md`, `CITATION.cff` | Documentation |

### Strongly recommended

| Path | Role |
|------|------|
| `dataset/baseline/no_dup_kg.csv` | Original PrimeKG comparison |
| `dataset/literature_curation/curated/*.csv` | Rebuild inputs (8 files) |
| `dataset/literature_curation/20260529-literature_edges_*.csv` | Integration audit |
| `dataset/literature_curation/20260529-primekg_plus_rd_integration_summary.json` | Summary stats |
| `dataset/supplementary_tables/TableS*.csv` | Manuscript tables S1–S9 |
| `scripts/` + `source_prep/` (no large raw inputs) | Reproducibility |
| `LICENSE` | MIT for code |

### Optional

| Path | Role |
|------|------|
| `dataset/auxillary/*.csv` | Intermediate build artifacts |
| `dataset/literature_curation/path_analysis/disease_paths/*_verify_literature_direct.csv` | Short verify paths (~7 MB) |
| `zenodo_bundle.tar.gz` | Single-archive upload |

### Do **not** upload to Zenodo

- `PrimeKG-Plus_validation/` (internal QC, full path enumeration)
- `THUY_DATA_CURATION/` raw review Excel (only ship merged `curated/` CSVs)
- Manuscript `.docx` files (journal SI handles those)

---

## 4. GitHub — what to push

| Include | Exclude / link only |
|---------|---------------------|
| Full `scripts/`, `source_prep/` (scripts + small outputs) | Multi-GB graph CSVs in git (link Zenodo DOI in README) |
| `README.md`, `LICENSE`, `CITATION.cff`, `docs/` | `PrimeKG-Plus_validation/` |
| Small CSVs: supplementary tables, literature audit, `curated/` | `source_prep/*/inputs/` large upstream dumps |
| Git tag `v1.0.0-20260529` | Author machine absolute paths in notebooks (prefer env vars) |

**Recommended:** enable [Zenodo–GitHub integration](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content) on `DSDD-UCPH/PrimeKG-Plus` so tagged releases auto-deposit.

---

## 5. After Zenodo deposit

- [ ] Replace `10.5281/zenodo.XXXXXXX` in `CITATION.cff`
- [ ] Update manuscript: Data Records, Data Availability, Usage Notes (DOI + GitHub URL)
- [ ] Add Zenodo badge + DOI link to `README.md`
- [ ] Archive exact tarball checksum in lab notes (SHA-256)

---

## 6. Manuscript cross-check

| Manuscript claim | Bundle path |
|------------------|-------------|
| 129,317 nodes; 7,683,206 directed edges | `dataset/primekg_plus.csv` |
| 7,683,756 edges; +550 literature | `dataset/literature_curation/primekg_plus_rd.csv` |
| Tables S1–S11 | SI PDF + `dataset/supplementary_tables/` (CSV S1–S9; S10–S11 in SI) |
| Rebuild code (MIT) | `scripts/`, `source_prep/` on GitHub |
| Literature relations (CC-BY 4.0) | `curated/`, `literature_edges_*.csv` on Zenodo |
