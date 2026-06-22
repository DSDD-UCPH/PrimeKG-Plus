"""PrimeKG relation normalization and display labels for literature edges."""

from __future__ import annotations

import pandas as pd

# Curated relation string → canonical PrimeKG relation (strip typos / aliases).
RELATION_ALIASES: dict[str, str] = {
    " bioprocess_protein": "bioprocess_protein",
    " anatomy_disease": "anatomy_disease",
    "off_label_use": "off-label use",
    "bioprocess_cellcompt": "bioprocess_cellcomp",
}

# relation → display_relation (from 20260529-primekg_plus.csv); default = relation itself.
DISPLAY_RELATION: dict[str, str] = {
    "anatomy_anatomy": "parent-child",
    "anatomy_protein_absent": "expression absent",
    "anatomy_protein_present": "expression present",
    "bioprocess_bioprocess": "parent-child",
    "bioprocess_protein": "interacts with",
    "cellcomp_cellcomp": "parent-child",
    "cellcomp_protein": "interacts with",
    "contraindication": "contraindication",
    "disease_disease": "parent-child",
    "disease_phenotype_negative": "phenotype absent",
    "disease_phenotype_positive": "phenotype present",
    "disease_protein": "associated with",
    "drug_drug": "synergistic interaction",
    "drug_effect": "side effect",
    "drug_protein": "target",
    "exposure_bioprocess": "interacts with",
    "exposure_cellcomp": "interacts with",
    "exposure_disease": "linked to",
    "exposure_exposure": "parent-child",
    "exposure_molfunc": "interacts with",
    "exposure_protein": "interacts with",
    "indication": "indication",
    "molfunc_molfunc": "parent-child",
    "molfunc_protein": "interacts with",
    "off-label use": "off-label use",
    "pathway_pathway": "parent-child",
    "pathway_protein": "interacts with",
    "phenotype_phenotype": "parent-child",
    "phenotype_protein": "associated with",
    "protein_protein": "ppi",
}

# Relations present in curated corpus but not in PrimeKG schema (logged, skipped).
UNSUPPORTED_RELATIONS: frozenset[str] = frozenset(
    {
        "anatomy_disease",
        "bioprocess_disease",
        "bioprocess_phenotype",
        "bioprocess_cellcomp",  # typo variant in curation
        "disease_pathway",
        "pathology_anatomy_present",
        "pathology_phenotype",
        "lipid_protein",
        "exposure_phenotype",
        "phenotype_anatomy",
        "phenotype_cellcomp",
        "drug_bioprocess",
    }
)

KG_EDGE_COLUMNS: list[str] = [
    "relation",
    "display_relation",
    "x_id",
    "x_type",
    "x_name",
    "x_source",
    "y_id",
    "y_type",
    "y_name",
    "y_source",
]

KG_OUTPUT_COLUMNS: list[str] = [
    "relation",
    "display_relation",
    "x_index",
    "x_id",
    "x_type",
    "x_name",
    "x_source",
    "y_index",
    "y_id",
    "y_type",
    "y_name",
    "y_source",
]


def normalize_relation(raw: str | None) -> str | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    rel = RELATION_ALIASES.get(str(raw), str(raw).strip())
    if not rel:
        return None
    return rel


def display_for_relation(relation: str) -> str:
    return DISPLAY_RELATION.get(relation, relation)
