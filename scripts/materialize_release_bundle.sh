#!/usr/bin/env bash
# Materialize PrimeKG-Plus_release for Zenodo/GitHub upload:
# - Replace symlinks with real file copies
# - Copy curated literature CSVs into dataset/PrimeKG-Plus-RD/curated/
# - Copy supplementary tables into dataset/supplementary_tables/
# - Canonicalize literature graph filenames (primekg_plus_rd*.csv)
# - Remove author-only / junk files before Zenodo tarball
#
# Usage:
#   ./scripts/materialize_release_bundle.sh
#   ./scripts/materialize_release_bundle.sh --tarball   # also create ../zenodo_bundle.tar.gz
#
# Environment overrides:
#   PRIMEKG_ROOT      default: parent of release folder (PrimeKG repo root)
#   CURATION_ROOT     default: ../../THUY_DATA_CURATION (lab tree; copied into bundle)
#   VALIDATION_ROOT   default: ../PrimeKG-Plus_validation
#   RELEASE_ROOT      default: repo root (parent of scripts/)

set -euo pipefail

MAKE_TARBALL=0
if [[ "${1:-}" == "--tarball" ]]; then
  MAKE_TARBALL=1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELEASE_ROOT="${RELEASE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PARENT_DIR="$(cd "$RELEASE_ROOT/.." && pwd)"
PRIMEKG_ROOT="${PRIMEKG_ROOT:-$PARENT_DIR}"
CURATION_ROOT="${CURATION_ROOT:-$(cd "$PARENT_DIR/.." && pwd)/THUY_DATA_CURATION}"
VALIDATION_ROOT="${VALIDATION_ROOT:-$PARENT_DIR/PrimeKG-Plus_validation}"
KG_DIR="$PRIMEKG_ROOT/datasets/data/kg"

log() { printf '[materialize] %s\n' "$*"; }
die() { printf '[materialize] ERROR: %s\n' "$*" >&2; exit 1; }

materialize_path() {
  local rel="$1"
  local dst="$RELEASE_ROOT/$rel"
  if [[ ! -e "$dst" ]]; then
    log "skip missing: $rel"
    return 0
  fi
  if [[ -L "$dst" ]]; then
    local target
    target="$(readlink -f "$dst" 2>/dev/null || readlink "$dst")"
    [[ -f "$target" ]] || die "broken symlink: $rel -> $target"
    log "materialize symlink: $rel"
    cp -f "$target" "${dst}.tmp"
    mv -f "${dst}.tmp" "$dst"
  elif [[ -f "$dst" ]]; then
    log "ok (regular file): $rel"
  fi
}

canonicalize_literature_graph_exports() {
  local lit_dir="$RELEASE_ROOT/dataset/PrimeKG-Plus-RD"
  local dated canonical
  local names=(
    primekg_plus_rd.csv
    primekg_plus_rd_nodes.csv
    primekg_plus_rd_edges.csv
  )

  for canonical in "${names[@]}"; do
    dated="20260529-${canonical}"
    if [[ -f "$lit_dir/$dated" ]]; then
      materialize_path "dataset/PrimeKG-Plus-RD/$dated"
      log "canonicalize: $dated -> $canonical"
      cp -f "$lit_dir/$dated" "$lit_dir/${canonical}.tmp"
      mv -f "$lit_dir/${canonical}.tmp" "$lit_dir/$canonical"
      rm -f "$lit_dir/$dated"
    elif [[ -L "$lit_dir/$canonical" || -f "$lit_dir/$canonical" ]]; then
      materialize_path "dataset/PrimeKG-Plus-RD/$canonical"
    fi
  done
}

copy_curated() {
  local curated_dir="$RELEASE_ROOT/dataset/PrimeKG-Plus-RD/curated"
  local curation_src="$RELEASE_ROOT/dataset/PrimeKG-Plus-RD/curation_source"
  mkdir -p "$curated_dir"
  [[ -d "$curation_src" ]] || [[ -d "$CURATION_ROOT" ]] || die "curation source not found (run copy_curation_source first or set CURATION_ROOT)"

  local root="${curation_src}"
  if [[ ! -d "$root" ]]; then
    root="$CURATION_ROOT"
  fi

  local pairs=(
    "Canavan_final.csv|$root/Post curation/finals_v1/20260508-Canavan_final.csv"
    "Batten_final.csv|$root/Post curation/finals_v1/20260508-Batten_final.csv"
    "NPC_final.csv|$root/Post curation/finals_v1/20260508-NMP_final.csv"
    "Tay-Sachs_final.csv|$root/Post curation/finals_v1/20260521-Tay-Sachs_final.csv"
    "Canavan_additional.csv|$root/Post curation/merged_expert_v2/Canavan_additional_relations_v2.csv"
    "Batten_additional.csv|$root/Post curation/merged_expert_v2/Batten_additional_relations_v2.csv"
    "NPC_additional.csv|$root/Post curation/merged_expert_v2/NPC_additional_relations_v2.csv"
    "Tay-Sachs_additional.csv|$root/Post curation/merged_expert_v2/Tay-Sachs_additional_relations_v2.csv"
  )

  local pair name src
  for pair in "${pairs[@]}"; do
    IFS='|' read -r name src <<< "$pair"
    [[ -f "$src" ]] || die "missing curated source: $src"
    rm -f "$curated_dir/$name"
    cp -f "$src" "$curated_dir/${name}.tmp"
    mv -f "$curated_dir/${name}.tmp" "$curated_dir/$name"
    log "curated: $name"
  done
}

copy_curation_source() {
  local dst="$RELEASE_ROOT/dataset/PrimeKG-Plus-RD/curation_source"
  [[ -d "$CURATION_ROOT" ]] || die "CURATION_ROOT not found: $CURATION_ROOT"

  log "curation_source: curated disease inputs (CSV only)"
  rm -rf "$dst/Canavan disease" "$dst/Batten disease" "$dst/Pick Niemann disease" "$dst/Tay-Sachs"
  mkdir -p "$dst/Canavan disease" "$dst/Batten disease" "$dst/Pick Niemann disease" "$dst/Tay-Sachs"

  # Keep only the canonical curated input per disease (steps 03–06, 08).
  cp -f "$CURATION_ROOT/Canavan disease/20260306-Canavan Disease.csv" "$dst/Canavan disease/"
  cp -f "$CURATION_ROOT/Batten disease/Final_Batten Disease.csv" "$dst/Batten disease/"
  cp -f "$CURATION_ROOT/Pick Niemann disease/Final_Niemann-Pick Disease.csv" "$dst/Pick Niemann disease/"
  cp -f "$CURATION_ROOT/Tay-Sachs/Tay-Sachs Disease final.csv" "$dst/Tay-Sachs/"

  log "curation_source: Post curation/"
  rm -rf "$dst/Post curation"
  rsync -a --exclude='.DS_Store' --exclude='*.zip' "$CURATION_ROOT/Post curation/" "$dst/Post curation/"

  # Normalize Post curation layout to a stable, deduplicated structure.
  mkdir -p "$dst/Post curation/before_bert" "$dst/Post curation/finals_v1" "$dst/Post curation/qc_outputs" "$dst/Post curation/intermediate"

  # Move before-BERT pools into before_bert/
  for name in \
    "20260502-Canavan_disease_For_term_suggestion_before_BERT.csv" \
    "2026058-Batten_disease_For_term_suggestion_before_BERT.csv" \
    "2026058-NPC_disease_For_term_suggestion_before_BERT.csv" \
    "20260521-Tay-Sachs_disease_For_term_suggestion_before_BERT.csv"; do
    [[ -f "$dst/Post curation/$name" ]] && mv -f "$dst/Post curation/$name" "$dst/Post curation/before_bert/$name"
  done

  # Move mapping finals into finals_v1/
  for name in \
    "20260508-Canavan_final.csv" \
    "20260508-Batten_final.csv" \
    "20260508-NMP_final.csv" \
    "20260521-Tay-Sachs_final.csv"; do
    [[ -f "$dst/Post curation/$name" ]] && mv -f "$dst/Post curation/$name" "$dst/Post curation/finals_v1/$name"
  done

  # Move QC outputs into qc_outputs/
  for name in \
    "20260508-Canavan_second_search_review.csv" \
    "20260508-Batten_second_search_review.csv" \
    "20260508-NPC_second_search_review.csv" \
    "20260508-NPC_second_search_review.xlsx"; do
    [[ -f "$dst/Post curation/$name" ]] && mv -f "$dst/Post curation/$name" "$dst/Post curation/qc_outputs/$name"
  done

  # Keep this in intermediate/ for step 08 input consistency.
  if [[ -f "$dst/Post curation/20260521-Tay-Sachs_suggested_terms_after_second_UMLS_search.csv" ]]; then
    mv -f \
      "$dst/Post curation/20260521-Tay-Sachs_suggested_terms_after_second_UMLS_search.csv" \
      "$dst/Post curation/intermediate/20260521-Tay-Sachs_suggested_terms_after_second_UMLS_search.csv"
  fi

  log "curation_source: intermediate pipeline CSVs (root-only, no duplicates)"
  mkdir -p "$dst/Post curation/intermediate"
  local intermediate=(
    "20260502-Canavan_disease_all_terms_after_first_UMLS_search.csv"
    "20260509-Canavan_suggested_terms_after_second_UMLS_search.csv"
    "20260509-NPC_disease_For_term_suggestion_before_BERT.csv"
    "20260509-NPC_disease_all_terms_after_first_UMLS_search.csv"
    "NMP_disease_For_term_suggestion_before_BERT.csv"
  )
  local name src
  for name in "${intermediate[@]}"; do
    src="$CURATION_ROOT/$name"
    [[ -f "$src" ]] || continue
    cp -f "$src" "$dst/Post curation/intermediate/$name"
  done

  local n
  n="$(find "$dst" -type f | wc -l | tr -d ' ')"
  log "curation_source: $n file(s) -> dataset/PrimeKG-Plus-RD/curation_source/ ($(du -sh "$dst" | cut -f1))"
}

copy_supplementary_tables() {
  local src_dir="$VALIDATION_ROOT/dataset/supplementary_tables"
  local dst_dir="$RELEASE_ROOT/dataset/supplementary_tables"
  mkdir -p "$dst_dir"
  if [[ ! -d "$src_dir" ]]; then
    log "warn: supplementary tables not found at $src_dir — skip"
    return 0
  fi
  cp -f "$src_dir"/TableS*.csv "$dst_dir/" 2>/dev/null || true
  local n
  n="$(find "$dst_dir" -maxdepth 1 -name 'TableS*.csv' | wc -l | tr -d ' ')"
  log "supplementary tables copied: $n file(s) -> dataset/supplementary_tables/"
}

copy_comparison_tables() {
  local src_dir="$VALIDATION_ROOT/dataset/comparison_tables"
  local dst_dir="$RELEASE_ROOT/dataset/comparison_tables"
  mkdir -p "$dst_dir"
  if [[ ! -d "$src_dir" ]]; then
    log "warn: comparison tables not found at $src_dir — skip"
    return 0
  fi
  cp -f "$src_dir"/*.csv "$dst_dir/" 2>/dev/null || true
  local n
  n="$(find "$dst_dir" -maxdepth 1 -name '*.csv' | wc -l | tr -d ' ')"
  log "comparison tables copied: $n file(s) -> dataset/comparison_tables/"
}

clean_for_zenodo_bundle() {
  log "cleaning author-only and junk files"

  # Accidental nested extract of a previous tarball.
  if [[ -d "$RELEASE_ROOT/PrimeKG-Plus_release" ]]; then
    rm -rf "$RELEASE_ROOT/PrimeKG-Plus_release"
    log "removed nested PrimeKG-Plus_release/ extract"
  fi

  find "$RELEASE_ROOT" -name '.DS_Store' -delete 2>/dev/null || true

  rm -rf "$RELEASE_ROOT/docs"

  rm -f \
    "$RELEASE_ROOT/scripts/literature_curation/knowledge_graph.code-workspace" \
    "$RELEASE_ROOT/scripts/literature_curation/20260621-Yang_review_curated_relations_to_be_added.ipynb" \
    "$RELEASE_ROOT/scripts/literature_curation/lib/test_primekg_exact_string_sapbert_cosine.py"
}

log "RELEASE_ROOT=$RELEASE_ROOT"
log "PRIMEKG_ROOT=$PRIMEKG_ROOT"
[[ -d "$KG_DIR" ]] || die "KG build dir not found: $KG_DIR"

materialize_path "dataset/PrimeKG-Plus/primekg_plus.csv"
materialize_path "dataset/PrimeKG-Plus/nodes.csv"
materialize_path "dataset/PrimeKG-Plus/edges.csv"
materialize_path "dataset/baseline/no_dup_kg.csv"

for f in kg_raw.csv kg_giant.csv kg_grouped.csv kg_grouped_diseases_bert_map.csv dup_name_group_fixes.csv kg_grouping_review_merge.csv kg_grouping_review_reject.csv; do
  materialize_path "dataset/PrimeKG-Plus/auxillary/$f"
done

canonicalize_literature_graph_exports
copy_curation_source
copy_curated
copy_supplementary_tables
copy_comparison_tables
clean_for_zenodo_bundle

if [[ "$MAKE_TARBALL" == "1" ]]; then
  TARBALL="${TARBALL:-$RELEASE_ROOT/zenodo_bundle.tar.gz}"
  log "creating $TARBALL (user-facing bundle only)"
  # Write tarball inside RELEASE_ROOT (listed in .gitignore).
  # Exclude only a nested extract folder, not the root being packed.
  tar -czf "$TARBALL" \
    --exclude='.ipynb_checkpoints' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='.git' \
    --exclude='zenodo_bundle.tar.gz' \
    --exclude='PrimeKG-Plus_release/PrimeKG-Plus_release' \
    --exclude='LICENSE' \
    --exclude='CITATION.cff' \
    --exclude='docs' \
    --exclude='scripts/materialize_release_bundle.sh' \
    --exclude='scripts/sanitize_public_notebooks.py' \
    --exclude='scripts/literature_curation/sanitize_literature_notebooks.py' \
    --exclude='scripts/ZENODO_UPLOAD_CHECKLIST.md' \
    --exclude='scripts/literature_curation/lib/test_*.py' \
    --exclude='scripts/literature_curation/*Yang_review*' \
    --exclude='scripts/literature_curation/*.code-workspace' \
    --exclude='additional_data_source/sider_nsides/inputs' \
    --exclude='additional_data_source/repurposed_drug/inputs' \
    --exclude='dataset/PrimeKG-Plus-RD/20260529-primekg_plus_rd.csv' \
    --exclude='dataset/PrimeKG-Plus-RD/20260529-primekg_plus_rd_nodes.csv' \
    --exclude='dataset/PrimeKG-Plus-RD/20260529-primekg_plus_rd_edges.csv' \
    -C "$(dirname "$RELEASE_ROOT")" "$(basename "$RELEASE_ROOT")"
  log "done: $TARBALL ($(du -h "$TARBALL" | cut -f1))"
fi

log "materialize complete"
