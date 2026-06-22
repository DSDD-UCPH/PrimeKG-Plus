# Literature integration (public release)

Integrates expert-curated PubMed/PMC relations for four neurological disorders into **`primekg_plus_rd.csv`**.

## Run

```bash
cd PrimeKG-Plus_release/scripts/literature_curation
python integrate_primekg_plus_rd.py
python integrate_primekg_plus_rd.py --dry-run
```

## Inputs

| Input | Location |
|-------|----------|
| Base graph | `dataset/primekg_plus.csv` |
| Node index | `dataset/nodes.csv` |
| Curated relations | `dataset/literature_curation/curated/*_final.csv` |
| Expert-merge additional | `dataset/literature_curation/curated/*_additional.csv` |

## Outputs

| Output | Location |
|--------|----------|
| **`primekg_plus_rd.csv`** | `dataset/literature_curation/primekg_plus_rd.csv` |
| Helpers | `lib/entity_resolver.py`, `lib/relation_config.py` |

## Mapping & QC workflow (internal)

Literature entity mapping (09–12), post-curation QC (13), and expert merge audit (14) are documented and stored under
**[`../../PrimeKG-Plus_validation/`](../../PrimeKG-Plus_validation/)** — not required for end users who consume pre-built `primekg_plus_rd.csv`.

## Key numbers (build 20260529)

| Metric | Value |
|--------|------:|
| Curated pool (deduped) | 1,290 |
| Integrated into kg_rd | 626 |
| Novel vs primekg_plus.csv | 550 |
