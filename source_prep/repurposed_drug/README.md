# RepurposedDrugs (Phase 4) → indication edges (preprocessing for **01**)

Builds `20260405-RepurposedDrug_Indication.csv` — DrugCentral-shaped `(cas_reg_no, umls_cui, indication)` rows merged into **01_build_graph** after anti-join against DrugCentral.

Source: RepurposedDrugs Phase 4 candidate pairs ([RepurposedDrugs](https://repurposedrugs.org/)).

---

## Script

| File | Description |
|------|-------------|
| `process_repurposed_drug.ipynb` | Full pipeline (from `knowledge_graph/20260405-ProcessRepurposedDrug-Phase4.ipynb`) |

**Run from:** this folder (`source_prep/repurposed_drug/`), with `PRIMEKG_ROOT` set to the PrimeKG repo root if auto-detection fails.

---

## Bundled files (this folder)

| Path | Role |
|------|------|
| `inputs/RepurposedDrug.csv` | Raw drug–disease name pairs (`Drug_name`, `Disease_name`) |
| `outputs/20260405-RepurposedDrug_Indication.csv` | Build output consumed by **01** (+383 novel indications after DrugCentral dedup) |

---

## External inputs (under `PrimeKG/datasets/data/`)

Not copied into the release (large / licensed); required only to **regenerate** the output:

| Path | Role |
|------|------|
| `drugcentral/05Oct2023_drug_disease_cleaned.csv` | Reference approved indications; anti-join to find novel pairs |
| `drugbank/Nurset_data_drugbank/2025_01_ver_full_database.xml` | Drug name/synonym → CAS registry number |
| `umls/umls_2025AB.csv` | English UMLS strings for offline disease → CUI resolution |
| `umls/2025AB-full/META/2025AB/META/MRSTY.RRF` | CUI semantic types (disease-like filter) |

Optional: `UMLS_API_KEY` environment variable + `requests` for UTS API fallback when offline resolution fails.

---

## Pipeline summary

1. Load `inputs/RepurposedDrug.csv`
2. Subtract pairs already in DrugCentral indications
3. Resolve drug → CAS via DrugBank XML (fallback DrugCentral CAS map)
4. Resolve disease → UMLS CUI (local ENG + MRSTY; optional UTS API)
5. Write `outputs/20260405-RepurposedDrug_Indication.csv`

Then run **`01_build_graph.ipynb`** (DrugCentral + repurposed indications section).
