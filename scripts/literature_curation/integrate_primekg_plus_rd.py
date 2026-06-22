#!/usr/bin/env python3
"""
Integrate rare-disease literature relations into PrimeKG-Plus → ``primekg_plus_rd``.

Release products (two graphs only):
  - ``primekg_plus.csv``   — updated public databases (directions 1–2); no PubMed curation
  - ``primekg_plus_rd.csv`` — ``primekg_plus.csv`` + all curated PubMed/PMC relations (direction 3)

Curated input pool (always merged, no v1/v2 split in output):
  - ``THUY_DATA_CURATION/*_final.csv`` (algorithm mapping)
  - ``THUY_DATA_CURATION/Post curation/merged_expert_v2/*_additional_relations_v2.csv`` (expert merge delta)

Outputs (under ``dataset/literature_curation/`` by default)
-----------------------------------------------------------
- ``primekg_plus_rd.csv`` / ``primekg_plus_rd_nodes.csv`` / ``primekg_plus_rd_edges.csv``
- ``literature_edges_integrated.csv`` — provenance (PMID, disease cohort, source file)
- ``literature_edges_skipped.csv``    — rows not integrated + reason
- ``primekg_plus_rd_integration_summary.json``

Usage: ``python integrate_primekg_plus_rd.py``  |  ``python integrate_primekg_plus_rd.py --dry-run``
       ``python integrate_primekg_plus_rd.py --review-only``  — write resolved relation CSVs only (no primekg_plus_rd)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.entity_resolver import EntityResolver, ResolvedNode  # noqa: E402
from lib.relation_config import (  # noqa: E402
    DISPLAY_RELATION,
    KG_EDGE_COLUMNS,
    KG_OUTPUT_COLUMNS,
    UNSUPPORTED_RELATIONS,
    display_for_relation,
    normalize_relation,
)


def resolve_primekg_root() -> Path:
    if env := os.environ.get("PRIMEKG_ROOT"):
        return Path(env).expanduser().resolve()
    # scripts/literature_curation → scripts → PrimeKG-Plus_release → PrimeKG
    candidate = SCRIPT_DIR.parents[2]
    if (candidate / "datasets").exists():
        return candidate
    return Path("/Users/ljw303/YANG_DATA/PrimeKG")


def resolve_release_root() -> Path:
    return SCRIPT_DIR.parents[1]


@dataclass(frozen=True)
class DiseaseSpec:
    name: str
    final_v1: Path
    additional_v2: Path | None = None


def default_disease_specs(curation_root: Path) -> list[DiseaseSpec]:
    post = curation_root / "Post curation"
    v2 = post / "merged_expert_v2"
    return [
        DiseaseSpec("Canavan", curation_root / "20260508-Canavan_final.csv", v2 / "Canavan_additional_relations_v2.csv"),
        DiseaseSpec("Batten", curation_root / "20260508-Batten_final.csv", v2 / "Batten_additional_relations_v2.csv"),
        DiseaseSpec("NPC", curation_root / "20260508-NMP_final.csv", v2 / "NPC_additional_relations_v2.csv"),
        DiseaseSpec("Tay-Sachs", curation_root / "20260521-Tay-Sachs_final.csv", v2 / "Tay-Sachs_additional_relations_v2.csv"),
    ]


def load_literature_table(path: Path, disease: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    df["disease_cohort"] = disease
    df["source_file"] = path.name
    return df


def collect_literature_rows(specs: list[DiseaseSpec]) -> pd.DataFrame:
    """Merge algorithm finals + expert-merge additional rows into one curated pool."""
    frames: list[pd.DataFrame] = []
    for spec in specs:
        if spec.final_v1.exists():
            frames.append(load_literature_table(spec.final_v1, spec.name))
        else:
            print(f"WARNING: missing final: {spec.final_v1}")
        if spec.additional_v2 and spec.additional_v2.exists():
            extra = load_literature_table(spec.additional_v2, spec.name)
            if "integratable" in extra.columns:
                extra = extra[extra["integratable"].astype(str).str.lower().isin({"true", "1", "yes"})]
            frames.append(extra)
        elif spec.additional_v2:
            print(f"WARNING: missing v2 additional: {spec.additional_v2}")
    if not frames:
        raise FileNotFoundError("No literature CSV files found under CURATION_ROOT.")
    out = pd.concat(frames, ignore_index=True)
    key_cols = ["entity1", "entity2", "Relation", "PMID", "disease_cohort"]
    out = out.drop_duplicates(subset=key_cols, keep="first")
    return out


def node_to_side(node: ResolvedNode) -> dict[str, str]:
    return {
        "id": node.node_id,
        "type": node.node_type,
        "name": node.node_name,
        "source": node.node_source,
    }


def build_literature_edge(
    row: pd.Series,
    x: ResolvedNode,
    y: ResolvedNode,
    relation: str,
) -> dict[str, str]:
    return {
        "relation": relation,
        "display_relation": display_for_relation(relation),
        "x_id": x.node_id,
        "x_type": x.node_type,
        "x_name": x.node_name,
        "x_source": x.node_source,
        "y_id": y.node_id,
        "y_type": y.node_type,
        "y_name": y.node_name,
        "y_source": y.node_source,
    }


def edge_key(edge: dict[str, str]) -> tuple:
    return (
        edge["relation"],
        edge["x_id"],
        edge["x_type"],
        edge["x_source"],
        edge["y_id"],
        edge["y_type"],
        edge["y_source"],
    )


def build_node_index_lookup(nodes: pd.DataFrame) -> dict[tuple[str, str, str], int]:
    """Map (node_id, node_type, node_source) → node_index; first wins on duplicates."""
    lookup: dict[tuple[str, str, str], int] = {}
    for row in nodes.itertuples(index=False):
        key = (str(row.node_id), str(row.node_type), str(row.node_source))
        if key not in lookup:
            lookup[key] = int(row.node_index)
    return lookup


def index_literature_edges(lit_edges: pd.DataFrame, lookup: dict[tuple[str, str, str], int]) -> pd.DataFrame:
    """Attach x_index / y_index to literature edges via node lookup (no pandas merge)."""
    rows: list[dict] = []
    for row in lit_edges.itertuples(index=False):
        x_key = (str(row.x_id), str(row.x_type), str(row.x_source))
        y_key = (str(row.y_id), str(row.y_type), str(row.y_source))
        x_idx = lookup.get(x_key)
        y_idx = lookup.get(y_key)
        if x_idx is None or y_idx is None:
            raise RuntimeError(f"Missing node index for edge: {x_key} or {y_key}")
        rows.append(
            {
                "relation": row.relation,
                "display_relation": row.display_relation,
                "x_index": x_idx,
                "x_id": row.x_id,
                "x_type": row.x_type,
                "x_name": row.x_name,
                "x_source": row.x_source,
                "y_index": y_idx,
                "y_id": row.y_id,
                "y_type": row.y_type,
                "y_name": row.y_name,
                "y_source": row.y_source,
            }
        )
    return pd.DataFrame(rows, columns=KG_OUTPUT_COLUMNS)


def integrate_literature(
    literature: pd.DataFrame,
    resolver: EntityResolver,
    base_kg: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    integrated_rows: list[dict] = []
    provenance_rows: list[dict] = []
    skipped_rows: list[dict] = []

    base_keys = set(
        tuple(row[c] for c in ["relation", "x_id", "x_type", "x_source", "y_id", "y_type", "y_source"])
        for _, row in base_kg.iterrows()
    )

    seen_lit: set[tuple] = set()

    for idx, row in literature.iterrows():
        rel_raw = row.get("Relation")
        relation = normalize_relation(rel_raw)
        base_skip = {
            "row_index": int(idx),
            "disease_cohort": row.get("disease_cohort"),
            "source_file": row.get("source_file"),
            "entity1": row.get("entity1"),
            "entity2": row.get("entity2"),
            "Relation": rel_raw,
            "PMID": row.get("PMID"),
        }

        if not relation:
            skipped_rows.append({**base_skip, "reason": "empty_relation"})
            continue
        if relation in UNSUPPORTED_RELATIONS:
            skipped_rows.append({**base_skip, "reason": f"unsupported_relation:{relation}"})
            continue
        if relation not in DISPLAY_RELATION and relation not in base_kg["relation"].unique():
            # Allow relation if it exists in base kg even if not in DISPLAY_RELATION dict.
            if relation not in set(base_kg["relation"].unique()):
                skipped_rows.append({**base_skip, "reason": f"unknown_relation:{relation}"})
                continue

        n1 = resolver.resolve_or_create(
            row.get("entity1"),
            row.get("entity1_status"),
            row.get("entity_type1"),
            row.get("entity1_suggested_name"),
            row.get("second_search_suggested_name"),
            row.get("entity1_expert_cui"),
        )
        n2 = resolver.resolve_or_create(
            row.get("entity2"),
            row.get("entity2_status"),
            row.get("entity_type2"),
            row.get("entity2_suggested_name"),
            row.get("second_search_suggested_name"),
            row.get("entity2_expert_cui"),
        )

        if not n1:
            skipped_rows.append({**base_skip, "reason": "unresolved_entity1", "entity1_status": row.get("entity1_status")})
            continue
        if not n2:
            skipped_rows.append({**base_skip, "reason": "unresolved_entity2", "entity2_status": row.get("entity2_status")})
            continue

        edge = build_literature_edge(row, n1, n2, relation)
        ek = edge_key(edge)
        if ek in seen_lit:
            skipped_rows.append({**base_skip, "reason": "duplicate_literature_row"})
            continue
        seen_lit.add(ek)

        already_in_base = ek in base_keys
        integrated_rows.append(edge)
        provenance_rows.append(
            {
                **base_skip,
                "relation_integrated": relation,
                "display_relation": edge["display_relation"],
                "x_id": edge["x_id"],
                "x_type": edge["x_type"],
                "x_name": edge["x_name"],
                "x_source": edge["x_source"],
                "y_id": edge["y_id"],
                "y_type": edge["y_type"],
                "y_name": edge["y_name"],
                "y_source": edge["y_source"],
                "entity1_resolve_method": n1.method,
                "entity2_resolve_method": n2.method,
                "already_in_base_kg": already_in_base,
            }
        )

    lit_df = pd.DataFrame(integrated_rows)
    prov_df = pd.DataFrame(provenance_rows)
    skip_df = pd.DataFrame(skipped_rows)
    return lit_df, prov_df, skip_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Build primekg_plus_rd = primekg_plus.csv + all curated literature (4 neurological disorders)")
    parser.add_argument("--dry-run", action="store_true", help="Print summary only; do not write outputs")
    parser.add_argument(
        "--review-only",
        action="store_true",
        help="Write resolved literature relation CSVs for QC; do not write primekg_plus_rd / primekg_plus_rd_nodes",
    )
    parser.add_argument("--run-date", default=os.environ.get("RUN_DATE", "20260529"), help="Build date tag")
    args = parser.parse_args()

    primekg_root = resolve_primekg_root()
    release_root = resolve_release_root()
    curation_root = Path(os.environ.get("CURATION_ROOT", "/Users/ljw303/YANG_DATA/THUY_DATA_CURATION"))
    data_dir = primekg_root / "datasets" / "data"

    plus_kg = Path(os.environ.get("PLUS_KG", release_root / "dataset" / "primekg_plus.csv"))
    plus_nodes = Path(os.environ.get("PLUS_NODES", release_root / "dataset" / "nodes.csv"))
    out_dir = Path(os.environ.get("KG_RD_OUT_DIR", release_root / "dataset" / "literature_curation"))
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"PrimeKG root:    {primekg_root}")
    print(f"Base kg:         {plus_kg}")
    print(f"Base nodes:      {plus_nodes}")
    print(f"Curation root:   {curation_root}")
    print(f"Output dir:      {out_dir}")

    base_kg = pd.read_csv(plus_kg, low_memory=False)
    nodes = pd.read_csv(plus_nodes, low_memory=False)
    print(f"Base kg edges:   {len(base_kg):,}")
    print(f"Base nodes:      {len(nodes):,}")

    specs = default_disease_specs(curation_root)
    literature = collect_literature_rows(specs)
    print(f"Curated pool rows: {len(literature):,} (finals + expert-merge additional, deduped)")

    resolver = EntityResolver(nodes, data_dir)
    lit_edges, provenance, skipped = integrate_literature(literature, resolver, base_kg)

    # Merge: base + novel literature edges only (skip duplicates already in base).
    novel_mask = ~provenance["already_in_base_kg"] if len(provenance) else pd.Series(dtype=bool)
    novel_lit = lit_edges.loc[novel_mask.values].reset_index(drop=True) if len(lit_edges) else lit_edges

    nodes_rd = resolver.extend_nodes(nodes)
    lookup = build_node_index_lookup(nodes_rd)
    novel_indexed = index_literature_edges(novel_lit, lookup) if len(novel_lit) else pd.DataFrame(columns=KG_OUTPUT_COLUMNS)
    kg_rd = pd.concat([base_kg[KG_OUTPUT_COLUMNS], novel_indexed], ignore_index=True)
    edges_rd = kg_rd[["relation", "display_relation", "x_index", "y_index"]].copy()

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_date": args.run_date,
        "base_kg_edges": int(len(base_kg)),
        "base_nodes": int(len(nodes)),
        "literature_new_nodes": int(len(resolver.new_nodes)),
        "kg_rd_nodes": int(len(nodes_rd)),
        "curated_input_rows": int(len(literature)),
        "curated_integrated_rows": int(len(lit_edges)),
        "curated_novel_rows": int(len(novel_lit)),
        "curated_skipped_rows": int(len(skipped)),
        "kg_rd_edges": int(len(kg_rd)),
        "kg_rd_delta_edges": int(len(kg_rd) - len(base_kg)),
        "by_disease_integrated": provenance.groupby("disease_cohort").size().to_dict() if len(provenance) else {},
        "by_disease_skipped": skipped.groupby("disease_cohort").size().to_dict() if len(skipped) else {},
        "skip_reasons": skipped["reason"].value_counts().to_dict() if len(skipped) and "reason" in skipped.columns else {},
    }

    print("\n--- Integration summary ---")
    for k, v in summary.items():
        if k not in {"created_at_utc", "by_disease_integrated", "by_disease_skipped", "skip_reasons"}:
            print(f"  {k}: {v}")
    if summary["by_disease_integrated"]:
        print("  integrated by disease:", summary["by_disease_integrated"])
    if summary["skip_reasons"]:
        print("  skip reasons:", summary["skip_reasons"])

    if args.dry_run:
        print("\n(dry-run: no files written)")
        if resolver.new_nodes:
            print(f"  would add {len(resolver.new_nodes)} literature nodes")
        return

    tag = args.run_date
    provenance_path = out_dir / f"{tag}-literature_edges_integrated.csv"
    skipped_path = out_dir / f"{tag}-literature_edges_skipped.csv"
    novel_path = out_dir / f"{tag}-literature_edges_novel.csv"
    nodes_added_path = out_dir / f"{tag}-literature_nodes_added.csv"
    summary_path = out_dir / f"{tag}-primekg_plus_rd_integration_summary.json"

    provenance.to_csv(provenance_path, index=False)
    skipped.to_csv(skipped_path, index=False)
    if len(novel_lit):
        novel_indexed.to_csv(novel_path, index=False)
    if resolver.new_nodes:
        pd.DataFrame(resolver.new_nodes).to_csv(nodes_added_path, index=False)
    (summary_path).write_text(json.dumps(summary, indent=2))

    print(f"\nWrote review files under {out_dir}:")
    print(f"  {provenance_path.name}  ({len(provenance):,} resolved relations, all tiers)")
    if len(novel_lit):
        print(f"  {novel_path.name}  ({len(novel_lit):,} novel edges not yet in base kg)")
    print(f"  {skipped_path.name}  ({len(skipped):,} skipped)")
    if resolver.new_nodes:
        print(f"  {nodes_added_path.name}  ({len(resolver.new_nodes):,} new nodes)")
    print(f"  {summary_path.name}")

    if args.review_only:
        print("\n(review-only: primekg_plus_rd / primekg_plus_rd_nodes not written)")
        return

    kg_rd_path = out_dir / f"{tag}-primekg_plus_rd.csv"
    nodes_rd_path = out_dir / f"{tag}-primekg_plus_rd_nodes.csv"
    edges_rd_path = out_dir / f"{tag}-primekg_plus_rd_edges.csv"
    kg_rd_alias = out_dir / "primekg_plus_rd.csv"
    nodes_rd_alias = out_dir / "primekg_plus_rd_nodes.csv"
    edges_rd_alias = out_dir / "primekg_plus_rd_edges.csv"

    kg_rd.to_csv(kg_rd_path, index=False)
    nodes_rd.to_csv(nodes_rd_path, index=False)
    edges_rd.to_csv(edges_rd_path, index=False)

    for alias, target in [
        (kg_rd_alias, kg_rd_path),
        (nodes_rd_alias, nodes_rd_path),
        (edges_rd_alias, edges_rd_path),
    ]:
        if alias.exists() or alias.is_symlink():
            alias.unlink()
        try:
            alias.symlink_to(target.name)
        except OSError:
            alias.write_bytes(target.read_bytes())

    print(f"\nWrote {kg_rd_path}")
    print(f"Wrote {nodes_rd_path}")
    print(f"Wrote {edges_rd_path}")
    print(f"Wrote provenance + skipped + summary under {out_dir}")


if __name__ == "__main__":
    main()
