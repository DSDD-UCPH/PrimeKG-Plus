# Curation source (extracted literature inputs)

Portable copy of the **PubMed/PMC curation workspace** for four rare neurological diseases. Default `CURATION_ROOT` for steps **03–08**.

## Layout (cleaned)

```
curation_source/
├── README.md
├── Canavan disease/          ← raw curated spreadsheets (step 03 input)
├── Batten disease/
├── Pick Niemann disease/
├── Tay-Sachs/
└── Post curation/            ← pipeline outputs (steps 03–08)
    ├── *_final.csv
    ├── *_For_term_suggestion_before_BERT.csv
    ├── *_second_search_review.csv
    ├── intermediate/         ← UMLS / second-search tables (no duplicates at root)
    ├── merged_expert_v2/     ← expert-merge outputs (step 08)
    └── Review after second suggest/   ← QC team Excel files
```

**Rebuild graph only?** Use `../curated/` (8 files) — you do not need to open this folder.

## Not included

- Legacy KG snapshots (`kg-old.csv`, ~2.3 GB) — use `PLUS_KG` = `dataset/PrimeKG-Plus/primekg_plus.csv`
- PDF paper archives
- Duplicate CSV copies that previously sat at `curation_source/` root

## Refresh from lab tree

```bash
CURATION_ROOT=/path/to/THUY_DATA_CURATION ./scripts/materialize_release_bundle.sh
```

Copies spreadsheets, `Post curation/`, and intermediate tables into this folder (deduplicated).
