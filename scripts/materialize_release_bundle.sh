#!/usr/bin/env bash
# Materialize PrimeKG-Plus_release for Zenodo/GitHub upload:
# - Replace symlinks with real file copies
# - Copy curated literature CSVs into dataset/literature_curation/curated/
# - Copy supplementary tables into dataset/supplementary_tables/
#
# Usage:
#   ./scripts/materialize_release_bundle.sh
#   ./scripts/materialize_release_bundle.sh --tarball   # also create ../zenodo_bundle.tar.gz
#
# Environment overrides:
#   PRIMEKG_ROOT      default: ../PrimeKG (sibling of release folder)
#   CURATION_ROOT     default: ../THUY_DATA_CURATION
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
# PrimeKG-Plus_release lives inside the PrimeKG repo (not in a nested PrimeKG/PrimeKG folder).
PRIMEKG_ROOT="${PRIMEKG_ROOT:-$PARENT_DIR}"
CURATION_ROOT="${CURATION_ROOT:-$(cd "$PARENT_DIR/.." && pwd)/THUY_DATA_CURATION}"
VALIDATION_ROOT="${VALIDATION_ROOT:-$PARENT_DIR/PrimeKG-Plus_validation}"
KG_DIR="$PRIMEKG_ROOT/datasets/data/kg"
DATAVERSE="$PRIMEKG_ROOT/dataverse_files"

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

copy_curated() {
  local curated_dir="$RELEASE_ROOT/dataset/literature_curation/curated"
  mkdir -p "$curated_dir"
  [[ -d "$CURATION_ROOT" ]] || die "CURATION_ROOT not found: $CURATION_ROOT"

  # name|source path (bash 3.2 compatible — macOS /bin/bash has no declare -A)
  local pairs=(
    "Canavan_final.csv|$CURATION_ROOT/20260508-Canavan_final.csv"
    "Batten_final.csv|$CURATION_ROOT/20260508-Batten_final.csv"
    "NPC_final.csv|$CURATION_ROOT/20260508-NMP_final.csv"
    "Tay-Sachs_final.csv|$CURATION_ROOT/20260521-Tay-Sachs_final.csv"
    "Canavan_additional.csv|$CURATION_ROOT/Post curation/merged_expert_v2/Canavan_additional_relations_v2.csv"
    "Batten_additional.csv|$CURATION_ROOT/Post curation/merged_expert_v2/Batten_additional_relations_v2.csv"
    "NPC_additional.csv|$CURATION_ROOT/Post curation/merged_expert_v2/NPC_additional_relations_v2.csv"
    "Tay-Sachs_additional.csv|$CURATION_ROOT/Post curation/merged_expert_v2/Tay-Sachs_additional_relations_v2.csv"
  )

  local pair name src
  for pair in "${pairs[@]}"; do
    name="${pair%%|*}"
    src="${pair#*|}"
    [[ -f "$src" ]] || die "missing curated source: $src"
    if [[ -L "$curated_dir/$name" || -e "$curated_dir/$name" ]]; then
      rm -f "$curated_dir/$name"
    fi
    cp -f "$src" "$curated_dir/${name}.tmp"
    mv -f "$curated_dir/${name}.tmp" "$curated_dir/$name"
    log "curated: $name"
  done
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

log "RELEASE_ROOT=$RELEASE_ROOT"
log "PRIMEKG_ROOT=$PRIMEKG_ROOT"
[[ -d "$KG_DIR" ]] || die "KG build dir not found: $KG_DIR"

# Main graph files (symlinks on author machine)
materialize_path "dataset/primekg_plus.csv"
materialize_path "dataset/nodes.csv"
materialize_path "dataset/edges.csv"
materialize_path "dataset/baseline/no_dup_kg.csv"

# Auxiliary pipeline artifacts
for f in kg_raw.csv kg_giant.csv kg_grouped.csv kg_grouped_diseases_bert_map.csv 20260616_dup_name_group_fixes.csv; do
  materialize_path "dataset/auxillary/$f"
done

# Literature graph (dated files; symlinks primekg_plus_rd*.csv point here)
materialize_path "dataset/literature_curation/20260529-primekg_plus_rd.csv"
materialize_path "dataset/literature_curation/20260529-primekg_plus_rd_nodes.csv"
materialize_path "dataset/literature_curation/20260529-primekg_plus_rd_edges.csv"

# Refresh convenience symlinks after materializing dated files
(
  cd "$RELEASE_ROOT/dataset/literature_curation"
  ln -sf 20260529-primekg_plus_rd.csv primekg_plus_rd.csv
  ln -sf 20260529-primekg_plus_rd_nodes.csv primekg_plus_rd_nodes.csv
  ln -sf 20260529-primekg_plus_rd_edges.csv primekg_plus_rd_edges.csv
)

copy_curated
copy_supplementary_tables

if [[ "$MAKE_TARBALL" == "1" ]]; then
  # Write outside RELEASE_ROOT — tar cannot pack a folder that contains the output archive.
  TARBALL="${TARBALL:-$PARENT_DIR/zenodo_bundle.tar.gz}"
  log "creating $TARBALL (excludes .ipynb_checkpoints, __pycache__, large source_prep inputs)"
  tar -czf "$TARBALL" \
    --exclude='.ipynb_checkpoints' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='zenodo_bundle.tar.gz' \
    --exclude='source_prep/sider_nsides/inputs' \
    --exclude='source_prep/repurposed_drug/inputs' \
    -C "$(dirname "$RELEASE_ROOT")" "$(basename "$RELEASE_ROOT")"
  log "done: $TARBALL ($(du -h "$TARBALL" | cut -f1))"
fi

log "materialize complete"
