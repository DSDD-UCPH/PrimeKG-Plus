# Zenodo upload checklist — PrimeKG-Plus (build 20260529)

# Maintainer-only — excluded from the public Zenodo bundle (see materialize_release_bundle.sh).

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

- [ ] `dataset/PrimeKG-Plus/primekg_plus.csv` is a real file (~900 MB), not a symlink
- [ ] `dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv` is a real file (~900 MB), not a symlink
- [ ] `dataset/PrimeKG-Plus-RD/curated/` contains 8 CSV files (no broken symlinks)
- [ ] `dataset/baseline/no_dup_kg.csv` materialized (~936 MB)
- [ ] `dataset/supplementary_tables/TableS1–S11.csv` present (plus optional `TableS1_node_totals.csv`, `TableS2_edge_totals.csv`)
- [ ] No `~$*.docx`, `.ipynb_checkpoints`, or author-only paths in tarball
- [ ] Root `README.md` present (folder guide); `LICENSE` and `CITATION.cff` excluded from tarball (GitHub-only)

---

## 2. Zenodo — record metadata

| Field | Suggested value |
|-------|-----------------|
| **Upload type** | Dataset |
| **Title** | PrimeKG-Plus knowledge graphs (build 20260529) |
| **Authors** | All 12 manuscript authors (same order as paper) |
| **Description** | Updated PrimeKG-style biomedical knowledge graphs from public databases, plus a literature-augmented build for four rare neurological diseases (Canavan, Batten, Niemann–Pick type C, Tay–Sachs). Includes rebuild scripts, baseline Original PrimeKG, manuscript supplementary tables S1–S11 (CSV), validation comparison tables, and literature integration audit files. Directed edge counts: `primekg_plus.csv` 7,683,206 edges; `primekg_plus_rd.csv` 7,683,756 edges (+550 novel literature edges). |
| **Publication date** | 2026-06-20 (or acceptance date) |
| **Version** | 1.0.0 / 20260529 |
| **License** | CC-BY 4.0 (dataset); note MIT for code on GitHub |
| **Keywords** | knowledge graph; PrimeKG; biomedical; rare disease; MONDO; literature curation |
| **Related identifier** | Scientific Data paper DOI (add when available) |
| **Related identifier** | Original PrimeKG: 10.7910/DVN/IXA7BM |

---

## 3. Zenodo — files to upload

### Required (core products)

| Path | Role |
|------|------|
| `dataset/PrimeKG-Plus/primekg_plus.csv` | Main graph (DB-only) |
| `dataset/PrimeKG-Plus/nodes.csv`, `dataset/PrimeKG-Plus/edges.csv` | Companion exports |
| `dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv` | Literature-augmented graph |
| `dataset/PrimeKG-Plus-RD/primekg_plus_rd_nodes.csv` | RD node table |
| `dataset/PrimeKG-Plus-RD/primekg_plus_rd_edges.csv` | RD edge companion |
| `README.md` (repo root) | Folder guide — start here after download |
| `dataset/README.md` | Graph catalog and table documentation |

### Strongly recommended

| Path | Role |
|------|------|
| `dataset/baseline/no_dup_kg.csv` | Original PrimeKG comparison |
| `dataset/PrimeKG-Plus-RD/curated/*.csv` | Rebuild inputs (8 files) |
| `dataset/PrimeKG-Plus-RD/curation_source/` | Extracted curation + expert review (~6 MB) |
| `scripts/literature_curation/README.md` | Literature audit trail (steps 03–09) |
| `dataset/PrimeKG-Plus-RD/literature_edges_*.csv` | Integration audit |
| `dataset/PrimeKG-Plus-RD/primekg_plus_rd_integration_summary.json` | Summary stats |
| `dataset/supplementary_tables/TableS*.csv` | Manuscript tables S1–S11 |
| `dataset/comparison_tables/*.csv` | Extra validation comparison outputs (optional) |
| `scripts/` + `additional_data_source/` (no large raw inputs) | Reproducibility |
| `LICENSE` | MIT for code |

### Optional

| Path | Role |
|------|------|
| `dataset/PrimeKG-Plus/auxillary/*.csv` | Intermediate build artifacts |
| `dataset/PrimeKG-Plus-RD/path_analysis/disease_paths/*_verify_literature_direct.csv` | Short verify paths (~7 MB) |
| `zenodo_bundle.tar.gz` | Single-archive upload |

### Do **not** upload to Zenodo

- `PrimeKG-Plus_validation/` (internal QC, full path enumeration)
- Full lab `THUY_DATA_CURATION/` tree (~5 GB with PDFs and legacy KG snapshots) — the release ships a ~6 MB extract under `curation_source/` instead
- Manuscript `.docx` files (journal SI handles those)

---

## 4. GitHub — what to push

| Include | Exclude / link only |
|---------|---------------------|
| `README.md`, `LICENSE`, `CITATION.cff` at repo root | — |
| Full `scripts/`, `additional_data_source/` (scripts + small outputs) | Multi-GB graph CSVs in git (link Zenodo DOI in README) |
| Small CSVs: supplementary tables, literature audit, `curated/` | `additional_data_source/*/inputs/` large upstream dumps |
| `dataset/README.md` | `PrimeKG-Plus_validation/` |
| Git tag `v1.0.0-20260529` | Zenodo tarball root metadata (use Zenodo record fields instead) |

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
| 129,317 nodes; 7,683,206 directed edges | `dataset/PrimeKG-Plus/primekg_plus.csv` |
| 7,683,756 edges; +550 literature | `dataset/PrimeKG-Plus-RD/primekg_plus_rd.csv` |
| Tables S1–S11 | `dataset/supplementary_tables/TableS1–S11.csv` (aligned with SI docx) |
| Rebuild code (MIT) | `scripts/`, `additional_data_source/` on GitHub |
| Literature relations (CC-BY 4.0) | `curated/`, `literature_edges_*.csv` on Zenodo |
