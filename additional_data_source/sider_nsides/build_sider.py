"""Build SIDER baseline table (step 0 before nSIDES merge).

Reproduces PrimeKG `datasets/processing_scripts/sider.py` with release-relative paths.
Output: primary_data_prep/data/sider/sider.csv
"""
from pathlib import Path
import sys

import pandas as pd

PREP_DIR = Path(__file__).resolve().parent
ADDITIONAL_SOURCE = PREP_DIR.parent
sys.path.insert(0, str(ADDITIONAL_SOURCE))
from release_paths import primary_data_dir, resolve_release_root  # noqa: E402

OUT = primary_data_dir(resolve_release_root()) / "sider" / "sider.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

SIDER_IN = PREP_DIR / "inputs" / "sider"

drug_atc = pd.read_csv(SIDER_IN / "drug_atc.tsv", sep="\t", header=None)
drug_atc.columns = ["stitch", "atc"]
all_se = pd.read_csv(SIDER_IN / "meddra_all_se.tsv", sep="\t", header=None)
all_se.columns = [
    "stitch_id_1",
    "stitch_id_2",
    "UMLS_from_label",
    "meddra_concept_type",
    "UMLS_from_meddra",
    "side_effect_name",
]

all_se = all_se.query('meddra_concept_type=="PT"')
side_effects = pd.merge(drug_atc, all_se, left_on="stitch", right_on="stitch_id_1").get(
    ["atc", "UMLS_from_label", "UMLS_from_meddra", "side_effect_name"]
)
side_effects.to_csv(OUT, index=False)
print(f"Wrote {len(side_effects):,} rows -> {OUT}")
