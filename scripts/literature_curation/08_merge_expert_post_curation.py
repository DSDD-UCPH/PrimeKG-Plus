#!/usr/bin/env python3
"""
Merge QC-team expert review columns into literature-mapping finals (v2) and
estimate how many additional curated relations become integratable.

Pipeline per disease
--------------------
1. Load algorithm final (v1) from Post curation folder.
2. Parse team Excel review (file c; Tay-Sachs uses a different schema).
3. Build entity-level expert lookup (accept / reject, suggested name, CUI).
4. Augment name->status mapping with expert-approved CUIs and KG name matches.
5. Re-evaluate all curated relations (not only v1 rows) with v1 vs v2 mapping.
6. Write:
   - {disease}_expert_entity_review.csv
   - {disease}_final_v2.csv
   - post_curation_merge_summary.csv

Usage
-----
    python 08_merge_expert_post_curation.py
    python 08_merge_expert_post_curation.py --out-dir /path/to/output
    python 08_merge_expert_post_curation.py --curated-dir dataset/PrimeKG-Plus-RD/curated
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Paths (override with env: CURATION_ROOT, PLUS_NODES, CURATED_DIR)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_RELEASE_ROOT = _SCRIPT_DIR.parents[1]


def _default_curation_root() -> Path:
    if env := os.environ.get("CURATION_ROOT"):
        return Path(env).expanduser().resolve()
    bundled = _RELEASE_ROOT / "dataset" / "PrimeKG-Plus-RD" / "curation_source"
    if bundled.is_dir():
        return bundled
    for candidate in (
        _RELEASE_ROOT.parent.parent / "THUY_DATA_CURATION",
        _RELEASE_ROOT.parent / "THUY_DATA_CURATION",
    ):
        if candidate.is_dir():
            return candidate
    return bundled


THUY = _default_curation_root()
POST = THUY / "Post curation"
INTERMEDIATE = POST / "intermediate"
REVIEW = POST / "Review after second suggest"
FINALS_V1 = POST / "finals_v1"
BEFORE_BERT = POST / "before_bert"
KG_NODES = Path(
    os.environ.get(
        "PLUS_NODES",
        str(_RELEASE_ROOT / "dataset" / "PrimeKG-Plus" / "nodes.csv"),
    )
)

DEFAULT_OUT = POST / "merged_expert_v2"
DEFAULT_CURATED_DIR = _RELEASE_ROOT / "dataset" / "PrimeKG-Plus-RD" / "curated"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def norm_name(x: Any) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def is_accepted(val: Any) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip().lower()
    if s in {"1", "1.0", "yes", "y", "accept", "accepted", "acepted"}:
        return True
    if s in {"0", "0.0", "no", "n", "reject", "rejected"}:
        return False
    if "1 acept" in s or "1 accept" in s:
        return True
    return False


def is_rejected(val: Any) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip().lower()
    return s in {"0", "0.0", "no", "n", "reject", "rejected"}


def clean_str(x: Any) -> str | None:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None
    return s


def extract_cuis(text: Any) -> set[str]:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return set()
    return set(re.findall(r"C\d{5,7}", str(text)))


def status_from_mapping(name: str, kg_norm: set[str], name_to_cui: dict[str, set[str]]) -> str:
    n = norm_name(name)
    if not n:
        return "invalid"
    if n in kg_norm:
        return "in_kg"
    cuis = sorted(name_to_cui.get(n, set()))
    if cuis:
        return "|".join(cuis)
    return "invalid"


def relation_key(row: pd.Series) -> tuple:
    return (
        norm_name(row.get("entity1")),
        norm_name(row.get("entity2")),
        str(row.get("Relation", "")).strip().lower(),
        str(row.get("PMID", "")).strip().lower(),
    )


def load_kg_name_norms(kg_nodes_path: Path) -> set[str]:
    nodes = pd.read_csv(kg_nodes_path, usecols=["node_name"])
    return set(nodes["node_name"].dropna().astype(str).map(norm_name))


def strip_cols(df: pd.DataFrame) -> pd.DataFrame:
  out = df.copy()
  out.columns = [str(c).strip() for c in out.columns]
  return out


# ---------------------------------------------------------------------------
# Curated loaders (disease-specific column naming)
# ---------------------------------------------------------------------------
def load_curated_canavan(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    rows = []
    for _, r in raw.iterrows():
        e1, e2 = clean_str(r.get("x_name ")), clean_str(r.get("y_name"))
        if not e1 or not e2:
            continue
        rows.append(
            {
                "entity1": e1,
                "entity2": e2,
                "entity_type1": clean_str(r.get("x_type ")),
                "entity_type2": clean_str(r.get("y_type")),
                "Relation": clean_str(r.get("relation ")) or clean_str(r.get("relation")),
                "PMID": clean_str(r.get("doi/PMID")),
            }
        )
    return pd.DataFrame(rows)


def load_curated_batten_npc(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    rows = []
    for _, r in raw.iterrows():
        e1, e2 = clean_str(r.get("x_name ")), clean_str(r.get("y_name"))
        if not e1 or not e2:
            continue
        rel = clean_str(r.get("relation")) or clean_str(r.get("relation "))
        rows.append(
            {
                "entity1": e1,
                "entity2": e2,
                "entity_type1": clean_str(r.get("x_type ")),
                "entity_type2": clean_str(r.get("y_type")),
                "Relation": rel,
                "PMID": clean_str(r.get("doi/PMID")),
            }
        )
    return pd.DataFrame(rows)


def load_curated_tay(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    rows = []
    for _, r in raw.iterrows():
        e1, e2 = clean_str(r.get("X_NAME")), clean_str(r.get("Y_NAME"))
        if not e1 or not e2:
            continue
        rows.append(
            {
                "entity1": e1,
                "entity2": e2,
                "entity_type1": clean_str(r.get("X_TYPE")),
                "entity_type2": clean_str(r.get("Y_TYPE")),
                "Relation": clean_str(r.get("RELATION")),
                "PMID": clean_str(r.get("DOI/PMID")),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Expert review parsers
# ---------------------------------------------------------------------------
@dataclass
class DiseaseConfig:
    name: str
    curated_csv: Path
    curated_loader: str
    final_v1_csv: Path
    review_dir: Path
    review_format: str  # second_search_review | suggested_terms
    file_c: str
    first_umls_csv: Path | None = None
    second_umls_csv: Path | None = None
    extra_notes: str = ""


def parse_second_search_review(df: pd.DataFrame, disease: str) -> pd.DataFrame:
    """Normalize Canavan / Batten / NPC team file c (second_search_review)."""
    df = strip_cols(df)

    if disease == "Batten":
        entity_col = "entity_name ( tên gốc)" if "entity_name ( tên gốc)" in df.columns else "entity_name"
        type_col = "entity_type ( entity type gốc)" if "entity_type ( entity type gốc)" in df.columns else "entity_type"
        algo_name_col = "suggested_name ( thuật toán)"
        algo_cui_col = "observed_statuses (CUI)"
        expert_accept_col = "expert opinion ( cô Hoài, cô Thúy)"
        expert_name_col = "suggested name"
        expert_cui_col = "observed_statuses (CUI).1"
    elif disease == "NPC":
        entity_col = "entity_name"
        type_col = "entity_type"
        algo_name_col = "suggested_name ( thuật toán sg)"
        algo_cui_col = "observed_statuses"
        expert_accept_col = "acepted/ reject (expert)"
        if expert_accept_col not in df.columns:
            expert_accept_col = "acepted/ reject ( expert)"
        expert_name_col = "suggested_name (expert)"
        expert_cui_col = "observed_statuses (CUI)"
    else:  # Canavan
        entity_col = "entity_name"
        type_col = "entity_type"
        algo_name_col = "suggested_name ( thuật toán sg)"
        algo_cui_col = "observed_statuses"
        expert_accept_col = "acepted/ reject ( cô Hoài)"
        expert_name_col = "suggested name cô Hoài)"
        expert_cui_col = "observed_statuses (CUI)"

    out = pd.DataFrame(
        {
            "entity_name": df[entity_col].map(clean_str),
            "entity_type": df.get(type_col, pd.Series([None] * len(df))).map(clean_str),
            "algo_accepted": df.get("accepted_in_second_search", pd.Series([None] * len(df))).map(
                lambda x: True if str(x).strip().lower() == "yes" else False if str(x).strip().lower() == "no" else None
            ),
            "algo_suggested_name": df.get(algo_name_col, pd.Series([None] * len(df))).map(clean_str),
            "algo_cui": df.get(algo_cui_col, pd.Series([None] * len(df))).map(
                lambda x: "|".join(sorted(extract_cuis(x))) or None
            ),
            "expert_accepted": df.get(expert_accept_col, pd.Series([None] * len(df))).map(is_accepted),
            "expert_rejected": df.get(expert_accept_col, pd.Series([None] * len(df))).map(is_rejected),
            "expert_suggested_name": df.get(expert_name_col, pd.Series([None] * len(df))).map(clean_str),
            "expert_cui": df.get(expert_cui_col, pd.Series([None] * len(df))).map(
                lambda x: "|".join(sorted(extract_cuis(x))) or None
            ),
            "note": df.get("Note", df.get("note", pd.Series([None] * len(df)))).map(clean_str),
        }
    )
    out["entity_name_norm"] = out["entity_name"].map(norm_name)
    return out.dropna(subset=["entity_name"]).drop_duplicates(subset=["entity_name_norm"], keep="first")


def parse_suggested_terms_review(df: pd.DataFrame) -> pd.DataFrame:
    """Tay-Sachs: file c is suggested_terms_after_second_UMLS_search + expert columns."""
    df = strip_cols(df)
    out = pd.DataFrame(
        {
            "entity_name": df["original_name"].map(clean_str),
            "entity_type": df.get("expected_entity_type", pd.Series([None] * len(df))).map(clean_str),
            "algo_accepted": df.get("type_match_expected_category", pd.Series([None] * len(df))).map(
                lambda x: True if x is True or str(x).strip().lower() == "true" else False
            ),
            "algo_suggested_name": df.get("suggested_name", pd.Series([None] * len(df))).map(clean_str),
            "algo_cui": df.get("suggested_cui", pd.Series([None] * len(df))).map(clean_str),
            "expert_accepted": df.get("Expert opinion ( cô  Thúy- cô Hoài)", pd.Series([None] * len(df))).map(
                lambda x: str(x).strip().lower() == "yes"
            ),
            "expert_rejected": df.get("Expert opinion ( cô  Thúy- cô Hoài)", pd.Series([None] * len(df))).map(
                lambda x: str(x).strip().lower() == "no"
            ),
            "expert_suggested_name": df.get("suggested name_expert", pd.Series([None] * len(df))).map(clean_str),
            "expert_cui": df.get("CUI_expert", pd.Series([None] * len(df))).map(clean_str),
            "note": df.get("suggested name_curator (opinion)", pd.Series([None] * len(df))).map(clean_str),
            "PMID": df.get("PMID", pd.Series([None] * len(df))).map(clean_str),
            "relation": df.get("relation", pd.Series([None] * len(df))).map(clean_str),
            "entity_side": df.get("entity_side", pd.Series([None] * len(df))).map(clean_str),
        }
    )
    out["entity_name_norm"] = out["entity_name"].map(norm_name)
    return out.dropna(subset=["entity_name"]).drop_duplicates(subset=["entity_name_norm"], keep="first")


# ---------------------------------------------------------------------------
# Mapping builders
# ---------------------------------------------------------------------------
def build_algo_mapping_from_final(final_df: pd.DataFrame) -> tuple[set[str], dict[str, set[str]]]:
    kg_norm: set[str] = set()
    name_to_cui: dict[str, set[str]] = {}

    final_df = strip_cols(final_df)
    for side in (1, 2):
        ent = f"entity{side}"
        st = f"entity{side}_status"
        if ent not in final_df.columns:
            continue
        for _, r in final_df.iterrows():
            name = clean_str(r.get(ent))
            status = clean_str(r.get(st))
            if not name or not status:
                continue
            n = norm_name(name)
            if status == "in_kg":
                kg_norm.add(n)
            elif status != "invalid":
                name_to_cui.setdefault(n, set()).update(extract_cuis(status))
    return kg_norm, name_to_cui


def augment_from_first_umls(path: Path | None, name_to_cui: dict[str, set[str]]) -> None:
    if path is None or not path.exists():
        return
    df = pd.read_csv(path)
    if "matched_cui" not in df.columns:
        return
    valid = df
    if "out_of_expected_tuis" in df.columns:
        valid = df[df["out_of_expected_tuis"] == False]  # noqa: E712
    for _, r in valid.iterrows():
        n = norm_name(r.get("entity_name"))
        cuis = extract_cuis(r.get("matched_cui"))
        if n and cuis:
            name_to_cui.setdefault(n, set()).update(cuis)


def augment_from_second_umls(path: Path | None, name_to_cui: dict[str, set[str]]) -> None:
    if path is None or not path.exists():
        return
    df = pd.read_csv(path)
    if "type_match_expected_category" in df.columns:
        df = df[df["type_match_expected_category"] == True]  # noqa: E712
    name_col = "original_name" if "original_name" in df.columns else "entity_name"
    cui_col = "suggested_cui" if "suggested_cui" in df.columns else "matched_cui"
    for _, r in df.iterrows():
        n = norm_name(r.get(name_col))
        cuis = extract_cuis(r.get(cui_col))
        if n and cuis:
            name_to_cui.setdefault(n, set()).update(cuis)


def augment_from_expert(
    expert_df: pd.DataFrame,
    kg_norm: set[str],
    name_to_cui: dict[str, set[str]],
) -> pd.DataFrame:
    """Apply expert-approved mappings; return audit frame with resolution status."""
    audit = expert_df.copy()
    resolutions = []

    for i, r in expert_df.iterrows():
        if not r.get("expert_accepted"):
            resolutions.append("not_accepted")
            continue
        n = r["entity_name_norm"]
        suggested = clean_str(r.get("expert_suggested_name"))
        cui_field = clean_str(r.get("expert_cui")) or clean_str(r.get("algo_cui"))
        cuis = extract_cuis(cui_field)

        if cuis:
            name_to_cui.setdefault(n, set()).update(cuis)
            resolutions.append("expert_cui")
        elif suggested and norm_name(suggested) in kg_norm:
            kg_norm.add(n)
            resolutions.append("expert_name_in_kg")
        elif suggested:
            # Map original entity to KG via expert preferred label
            if norm_name(suggested) not in kg_norm:
                kg_norm.add(norm_name(suggested))
            name_to_cui.setdefault(n, set())  # still unresolved CUI
            resolutions.append("expert_name_only_pending_cui")
        elif cuis := extract_cuis(r.get("algo_cui")):
            name_to_cui.setdefault(n, set()).update(cuis)
            resolutions.append("expert_accept_algo_cui")
        else:
            resolutions.append("expert_accept_unresolved")

    audit["expert_resolution"] = resolutions
    return audit


def evaluate_relations(
    curated_df: pd.DataFrame,
    kg_norm: set[str],
    name_to_cui: dict[str, set[str]],
) -> pd.DataFrame:
    out = curated_df.copy()
    out["entity1_status"] = out["entity1"].map(lambda x: status_from_mapping(x, kg_norm, name_to_cui))
    out["entity2_status"] = out["entity2"].map(lambda x: status_from_mapping(x, kg_norm, name_to_cui))
    out["integratable"] = (out["entity1_status"] != "invalid") & (out["entity2_status"] != "invalid")
    return out


def merge_expert_columns_to_final(final_v1: pd.DataFrame, expert_df: pd.DataFrame) -> pd.DataFrame:
    """Attach expert review columns to each entity side in final v2."""
    final_v1 = strip_cols(final_v1)
    expert_lookup = expert_df.set_index("entity_name_norm")
    out = final_v1.copy()

    for side in (1, 2):
        ent = f"entity{side}"
        out[f"{ent}_expert_accepted"] = out[ent].map(
            lambda x: expert_lookup.loc[norm_name(x), "expert_accepted"] if norm_name(x) in expert_lookup.index else None
        )
        out[f"{ent}_expert_suggested_name"] = out[ent].map(
            lambda x: expert_lookup.loc[norm_name(x), "expert_suggested_name"] if norm_name(x) in expert_lookup.index else None
        )
        out[f"{ent}_expert_cui"] = out[ent].map(
            lambda x: expert_lookup.loc[norm_name(x), "expert_cui"] if norm_name(x) in expert_lookup.index else None
        )
        out[f"{ent}_expert_resolution"] = out[ent].map(
            lambda x: expert_lookup.loc[norm_name(x), "expert_resolution"] if norm_name(x) in expert_lookup.index else None
        )

    out["mapping_version"] = "v2_expert_merged"
    return out


# ---------------------------------------------------------------------------
# Disease registry
# ---------------------------------------------------------------------------
DISEASES: list[DiseaseConfig] = [
    DiseaseConfig(
        name="Canavan",
        curated_csv=THUY / "Canavan disease/20260306-Canavan Disease.csv",
        curated_loader="canavan",
        final_v1_csv=FINALS_V1 / "20260508-Canavan_final.csv",
        review_dir=REVIEW / "Canavan_check_QC team",
        review_format="second_search_review",
        file_c="c, 20260508-Canavan_second_search_review.xlsx",
        first_umls_csv=INTERMEDIATE / "20260502-Canavan_disease_all_terms_after_first_UMLS_search.csv",
        second_umls_csv=INTERMEDIATE / "20260509-Canavan_suggested_terms_after_second_UMLS_search.csv",
    ),
    DiseaseConfig(
        name="Batten",
        curated_csv=THUY / "Batten disease/Final_Batten Disease.csv",
        curated_loader="batten_npc",
        final_v1_csv=FINALS_V1 / "20260508-Batten_final.csv",
        review_dir=REVIEW / "Batten_check_QC team",
        review_format="second_search_review",
        file_c="20260612-Batten_second_search_review.xlsx",
        extra_notes="No first/second UMLS CSV exported; v1 mapping rebuilt from final + file c.",
    ),
    DiseaseConfig(
        name="NPC",
        curated_csv=THUY / "Pick Niemann disease/Final_Niemann-Pick Disease.csv",
        curated_loader="batten_npc",
        final_v1_csv=FINALS_V1 / "20260508-NMP_final.csv",
        review_dir=REVIEW / "NMP_check_QC team",
        review_format="second_search_review",
        file_c="c, 20260613-NPC_second_search_review.xlsx",
        first_umls_csv=INTERMEDIATE / "20260509-NPC_disease_all_terms_after_first_UMLS_search.csv",
        extra_notes="Uses latest team file c (2026-06-13).",
    ),
    DiseaseConfig(
        name="Tay-Sachs",
        curated_csv=THUY / "Tay-Sachs/Tay-Sachs Disease final.csv",
        curated_loader="tay",
        final_v1_csv=FINALS_V1 / "20260521-Tay-Sachs_final.csv",
        review_dir=REVIEW / "Tay-Sachs_check- QC team",
        review_format="suggested_terms",
        file_c="c, 20260521-Tay-Sachs_suggested_terms_after_second_UMLS_search.xlsx",
        second_umls_csv=INTERMEDIATE / "20260521-Tay-Sachs_suggested_terms_after_second_UMLS_search.csv",
        extra_notes="File c is full UMLS second-search table (not second_search_review).",
    ),
]


def load_curated(cfg: DiseaseConfig) -> pd.DataFrame:
    if cfg.curated_loader == "canavan":
        return load_curated_canavan(cfg.curated_csv)
    if cfg.curated_loader == "batten_npc":
        return load_curated_batten_npc(cfg.curated_csv)
    if cfg.curated_loader == "tay":
        return load_curated_tay(cfg.curated_csv)
    raise ValueError(cfg.curated_loader)


def process_disease(cfg: DiseaseConfig, kg_norm_global: set[str], out_dir: Path) -> dict[str, Any]:
    final_v1 = strip_cols(pd.read_csv(cfg.final_v1_csv))
    curated = load_curated(cfg)

  # --- parse expert review ---
    review_path = cfg.review_dir / cfg.file_c
    review_raw = pd.read_excel(review_path)
    if cfg.review_format == "suggested_terms":
        expert_df = parse_suggested_terms_review(review_raw)
    else:
        expert_df = parse_second_search_review(review_raw, cfg.name)

    # --- algorithm v1 mapping ---
    kg_norm, name_to_cui = build_algo_mapping_from_final(final_v1)
    augment_from_first_umls(cfg.first_umls_csv, name_to_cui)
    augment_from_second_umls(cfg.second_umls_csv, name_to_cui)

    eval_v1 = evaluate_relations(curated, kg_norm, name_to_cui)
    v1_keys = set(map(relation_key, eval_v1[eval_v1.integratable].to_dict("records")))

    # --- expert v2 mapping ---
    kg_norm_v2 = set(kg_norm)
    name_to_cui_v2 = {k: set(v) for k, v in name_to_cui.items()}
    expert_audit = augment_from_expert(expert_df, kg_norm_v2, name_to_cui_v2)

    # Expert suggested names that exactly match a PrimeKG node label
    for _, r in expert_audit[expert_audit.expert_accepted].iterrows():
        suggested = clean_str(r.get("expert_suggested_name"))
        if suggested and norm_name(suggested) in kg_norm_global:
            kg_norm_v2.add(r["entity_name_norm"])

    eval_v2 = evaluate_relations(curated, kg_norm_v2, name_to_cui_v2)
    v2_keys = set(map(relation_key, eval_v2[eval_v2.integratable].to_dict("records")))
    new_keys = v2_keys - v1_keys

    # --- outputs ---
    expert_out = out_dir / f"{cfg.name}_expert_entity_review.csv"
    expert_audit.to_csv(expert_out, index=False)

    final_v2 = merge_expert_columns_to_final(final_v1, expert_audit)
    final_v2_out = out_dir / f"{cfg.name}_final_v2.csv"
    final_v2.to_csv(final_v2_out, index=False)

    new_rel_out = out_dir / f"{cfg.name}_additional_relations_v2.csv"
    eval_v2["relation_key"] = eval_v2.apply(relation_key, axis=1)
    eval_v2[eval_v2["relation_key"].isin(new_keys)].drop(columns=["relation_key"]).to_csv(new_rel_out, index=False)

    # Tay-Sachs: also write second_search_review-compatible file for uniformity
    if cfg.review_format == "suggested_terms":
        pool_a = pd.read_csv(BEFORE_BERT / "20260521-Tay-Sachs_disease_For_term_suggestion_before_BERT.csv")
        pool_norm = set(pool_a.entity_name.map(norm_name))
        tay_review = expert_audit[expert_audit.entity_name_norm.isin(pool_norm)].copy()
        tay_review["accepted_in_second_search"] = tay_review["expert_resolution"].map(
            lambda x: "yes" if x in {"expert_cui", "expert_name_in_kg", "expert_accept_algo_cui"} else "no"
        )
        tay_review.to_csv(out_dir / "Tay-Sachs_second_search_review_reconstructed.csv", index=False)

    summary = {
        "disease": cfg.name,
        "review_format": cfg.review_format,
        "curated_relations": len(curated),
        "final_v1_relations": len(final_v1),
        "integratable_v1_from_curated": len(v1_keys),
        "integratable_v2_from_curated": len(v2_keys),
        "additional_relations_v2": len(new_keys),
        "expert_entities_reviewed": len(expert_audit),
        "expert_accepted_entities": int(expert_audit.expert_accepted.sum()),
        "expert_resolved_cui": int((expert_audit.expert_resolution == "expert_cui").sum()),
        "expert_resolved_kg_name": int((expert_audit.expert_resolution == "expert_name_in_kg").sum()),
        "expert_name_only_pending": int((expert_audit.expert_resolution == "expert_name_only_pending_cui").sum()),
        "notes": cfg.extra_notes,
    }
    return summary


def publish_release_curated(out_dir: Path, curated_dir: Path) -> None:
    """Copy merge outputs into release ``curated/`` filenames for step 09."""
    curated_dir.mkdir(parents=True, exist_ok=True)
    for cfg in DISEASES:
        src = out_dir / f"{cfg.name}_additional_relations_v2.csv"
        if not src.is_file():
            print(f"warn: missing additional relations for {cfg.name}: {src}")
            continue
        dst = curated_dir / f"{cfg.name}_additional.csv"
        dst.write_bytes(src.read_bytes())
        print(f"release curated: {dst.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge expert post-curation reviews into final v2.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--kg-nodes", type=Path, default=KG_NODES)
    parser.add_argument(
        "--curated-dir",
        type=Path,
        default=None,
        help=f"Also write {{Disease}}_additional.csv for step 09 (default: {DEFAULT_CURATED_DIR})",
    )
    parser.add_argument(
        "--publish-release",
        action="store_true",
        help=f"Shorthand for --curated-dir {DEFAULT_CURATED_DIR}",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    kg_norm_global = load_kg_name_norms(args.kg_nodes)

    summaries = []
    for cfg in DISEASES:
        print(f"Processing {cfg.name}...")
        summaries.append(process_disease(cfg, kg_norm_global, args.out_dir))

    summary_df = pd.DataFrame(summaries)
    summary_path = args.out_dir / "post_curation_merge_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    curated_dir = args.curated_dir
    if args.publish_release and curated_dir is None:
        curated_dir = DEFAULT_CURATED_DIR
    if curated_dir is not None:
        publish_release_curated(args.out_dir, curated_dir)

    print("\n=== Post-curation expert merge summary ===")
    print(summary_df.to_string(index=False))
    print(f"\nOutputs written to: {args.out_dir}")
    if curated_dir is not None:
        print(f"Release additional CSVs written to: {curated_dir}")


if __name__ == "__main__":
    main()
