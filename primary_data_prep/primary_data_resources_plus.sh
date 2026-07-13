#!/usr/bin/env bash
# PrimeKG-Plus primary data retrieval and processing
#
# Self-contained fork of PrimeKG datasets/primary_data_resources.sh.
# Processing scripts live in primary_data_prep/processing_scripts/ (no PrimeKG repo required).
#
# Usage:
#   cd primary_data_prep
#   bash primary_data_resources_plus.sh
#
# Override output directory:
#   PRIMARY_DATA_DIR=/path/to/data bash primary_data_resources_plus.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIMARY_PREP_ROOT="$SCRIPT_DIR"
DATA_DIR="${PRIMARY_DATA_DIR:-$PRIMARY_PREP_ROOT/data}"
PROC_DIR="$PRIMARY_PREP_ROOT/processing_scripts"

run_py() {
  (cd "$PROC_DIR" && python "$1")
}

echo "Primary data directory: $DATA_DIR"
mkdir -p "$DATA_DIR"/{bgee,ctd,disgenet,drugbank,vocab,drugcentral,ncbigene,go,hpo,mondo,reactome,uberon,umls,ppi,sider,repurposed_drug}
mkdir -p "$DATA_DIR/disgenet/OpenTarget"

ADDITIONAL_SOURCE="$(cd "$PRIMARY_PREP_ROOT/.." && pwd)/additional_data_source"

copy_if_missing() {
  local src="$1" dst="$2"
  if [[ -f "$src" && ! -f "$dst" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "Seeded $(basename "$dst") from additional_data_source bundle"
  fi
}

# ── HGNC gene names + Entrez↔UniProt map ─────────────────────────────────────
echo "Downloading HGNC gene names..."
curl -fsSL \
  "https://www.genenames.org/cgi-bin/download/custom?col=gd_app_sym&col=gd_app_name&col=gd_pub_acc_ids&col=gd_pub_refseq_ids&col=gd_pub_eg_id&col=md_eg_id&col=md_prot_id&col=md_mim_id&status=Approved&hgnc_dbtag=on&order_by=gd_app_sym_sort&format=text&submit=submit" \
  -o "$DATA_DIR/vocab/gene_names.csv"

echo "Downloading HGNC Entrez↔UniProt map..."
curl -fsSL \
  "https://www.genenames.org/cgi-bin/download/custom?col=md_eg_id&col=md_prot_id&status=Approved&hgnc_dbtag=on&order_by=gd_app_sym_sort&format=text&submit=submit" \
  -o "$DATA_DIR/vocab/gene_map.csv"

# ── BGEE ───────────────────────────────────────────────────────────────────────
echo "Downloading and processing BGEE..."
curl -fsSL https://www.bgee.org/ftp/current/download/calls/expr_calls/Homo_sapiens_expr_advanced.tsv.gz \
  -o "$DATA_DIR/bgee/Homo_sapiens_expr_advanced.tsv.gz"
gunzip -f "$DATA_DIR/bgee/Homo_sapiens_expr_advanced.tsv.gz"
run_py bgee.py

# ── CTD exposures ──────────────────────────────────────────────────────────────
echo "Downloading and processing CTD exposure events..."
curl -fsSL https://ctdbase.org/reports/CTD_exposure_events.csv.gz \
  -o "$DATA_DIR/ctd/CTD_exposure_events.csv.gz"
gunzip -f "$DATA_DIR/ctd/CTD_exposure_events.csv.gz"
run_py ctd.py

# ── DisGeNET (manual) ────────────────────────────────────────────────────────
echo ""
echo "DisGeNET: download manually from https://www.disgenet.org/"
echo "  Place the authors-curated associations file at:"
echo "    $DATA_DIR/disgenet/Authors-curated_gene_disease_associations.tsv"
echo "  (Notebook 01 expects this filename, not the bulk curated export.)"
echo ""

# ── DrugBank (manual, licensed) ────────────────────────────────────────────────
echo "DrugBank (licensed): set DRUGBANK_SRC to a folder containing downloaded archives, then re-run."
echo "  Expected files in DRUGBANK_SRC:"
echo "    drugbank_all_full_database.xml.zip"
echo "    drugbank_all_carrier_polypeptide_ids.csv.zip"
echo "    drugbank_all_enzyme_polypeptide_ids.csv.zip"
echo "    drugbank_all_target_polypeptide_ids.csv.zip"
echo "    drugbank_all_transporter_polypeptide_ids.csv.zip"
echo "    drugbank_all_drugbank_vocabulary.csv.zip"
echo ""

if [[ -n "${DRUGBANK_SRC:-}" && -d "$DRUGBANK_SRC" ]]; then
  echo "Processing DrugBank from DRUGBANK_SRC=$DRUGBANK_SRC"

  cp "$DRUGBANK_SRC/drugbank_all_full_database.xml.zip" "$DATA_DIR/drugbank/"
  unzip -o "$DATA_DIR/drugbank/drugbank_all_full_database.xml.zip" -d "$DATA_DIR/drugbank"
  rm -f "$DATA_DIR/drugbank/drugbank_all_full_database.xml.zip"

  for kind in carrier enzyme target transporter; do
    zip="drugbank_all_${kind}_polypeptide_ids.csv.zip"
    cp "$DRUGBANK_SRC/$zip" "$DATA_DIR/drugbank/"
    unzip -o "$DATA_DIR/drugbank/$zip" -d "$DATA_DIR/drugbank/drugbank_all_${kind}_polypeptide_ids.csv"
    rm -f "$DATA_DIR/drugbank/$zip"
  done

  cp "$DRUGBANK_SRC/drugbank_all_drugbank_vocabulary.csv.zip" "$DATA_DIR/vocab/"
  unzip -o "$DATA_DIR/vocab/drugbank_all_drugbank_vocabulary.csv.zip" -d "$DATA_DIR/vocab/"
  if [[ -f "$DATA_DIR/vocab/drugbank vocabulary.csv" ]]; then
    mv "$DATA_DIR/vocab/drugbank vocabulary.csv" "$DATA_DIR/vocab/drugbank_vocabulary.csv"
  fi
  rm -f "$DATA_DIR/vocab/drugbank_all_drugbank_vocabulary.csv.zip"

  run_py drugbank_atc.py
  run_py drugbank_drug_protein.py
  run_py drugbank_drug_drug.py
else
  echo "Skipping DrugBank processing (DRUGBANK_SRC not set)."
fi

# ── DrugCentral (manual) ───────────────────────────────────────────────────────
echo ""
echo "DrugCentral: manual PostgreSQL import required."
echo "  1. Download a DrugCentral SQL dump to $DATA_DIR/drugcentral/"
echo "  2. Load with psql and export indication/contraindication/off-label edges"
echo "  3. Clean SNOMED concept columns and save as:"
echo "       $DATA_DIR/drugcentral/drug_disease_cleaned.csv"
echo "  SQL templates: $PROC_DIR/drugcentral_queries.txt"
echo ""

# ── Entrez Gene → GO ───────────────────────────────────────────────────────────
echo "Downloading and processing NCBI gene2go..."
curl -fsSL https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz -o "$DATA_DIR/ncbigene/gene2go.gz"
gunzip -f "$DATA_DIR/ncbigene/gene2go.gz"
run_py ncbigene.py

# ── Gene Ontology ──────────────────────────────────────────────────────────────
echo "Downloading and processing GO..."
curl -fsSL http://purl.obolibrary.org/obo/go/go-basic.obo -o "$DATA_DIR/go/go-basic.obo"
run_py go.py

# ── HPO ────────────────────────────────────────────────────────────────────────
echo "Downloading and processing HPO..."
curl -fsSL http://purl.obolibrary.org/obo/hp.obo -o "$DATA_DIR/hpo/hp.obo"
run_py hpo.py
curl -fsSL http://purl.obolibrary.org/obo/hp/hpoa/phenotype.hpoa -o "$DATA_DIR/hpo/phenotype.hpoa"
run_py hpoa.py

# ── MONDO ──────────────────────────────────────────────────────────────────────
echo "Downloading and processing MONDO..."
curl -fsSL http://purl.obolibrary.org/obo/MONDO.obo -o "$DATA_DIR/mondo/mondo.obo"
run_py mondo.py

# ── Reactome ───────────────────────────────────────────────────────────────────
echo "Downloading and processing Reactome..."
curl -fsSL https://reactome.org/download/current/ReactomePathways.txt -o "$DATA_DIR/reactome/ReactomePathways.txt"
curl -fsSL https://reactome.org/download/current/ReactomePathwaysRelation.txt -o "$DATA_DIR/reactome/ReactomePathwaysRelation.txt"
curl -fsSL https://reactome.org/download/current/NCBI2Reactome.txt -o "$DATA_DIR/reactome/NCBI2Reactome.txt"
run_py reactome.py

# ── UBERON ─────────────────────────────────────────────────────────────────────
echo "Downloading and processing UBERON..."
curl -fsSL http://purl.obolibrary.org/obo/uberon/ext.obo -o "$DATA_DIR/uberon/ext.obo"
run_py uberon.py

# ── UMLS (manual, licensed) ────────────────────────────────────────────────────
echo ""
echo "UMLS (licensed): set UMLS_SRC to a folder containing the Metathesaurus zip, then re-run."
echo "  Example: export UMLS_SRC=/path/to/umls-download"
echo ""

if [[ -n "${UMLS_SRC:-}" && -d "$UMLS_SRC" ]]; then
  echo "Processing UMLS from UMLS_SRC=$UMLS_SRC"
  zip="$(ls "$UMLS_SRC"/umls-*-metathesaurus-full.zip 2>/dev/null | head -1 || true)"
  if [[ -z "$zip" ]]; then
    echo "ERROR: no umls-*-metathesaurus-full.zip found in $UMLS_SRC" >&2
    exit 1
  fi
  cp "$zip" "$DATA_DIR/umls/"
  unzip -o "$DATA_DIR/umls/$(basename "$zip")" -d "$DATA_DIR/umls/"
  found="$(find "$DATA_DIR/umls" -name MRCONSO.RRF | head -1)"
  cp "$found" "$DATA_DIR/umls/MRCONSO.RRF"
  run_py umls.py
  run_py map_umls_mondo.py
else
  echo "Skipping UMLS processing (UMLS_SRC not set)."
fi

echo ""
echo "UMLS↔MONDO bijective vocabulary (PrimeKG-Plus build):"
echo "  Notebook 01 uses vocab/umls_mondo_bijective.csv (one preferred CUI per MONDO)."
echo "  map_umls_mondo.py only writes the multi-mapping vocab/umls_mondo.csv."
echo "  Build the bijective file with Monarch API + UMLS term status (see SI Section E),"
echo "  or copy a pre-built umls_mondo_bijective.csv into $DATA_DIR/vocab/."
echo ""

# ── PPI (manual) ───────────────────────────────────────────────────────────────
echo "Protein–protein interactions:"
echo "  Place merged human PPI edges at:"
echo "    $DATA_DIR/ppi/protein_protein.csv"
echo "  (PrimeKG-Plus does not ship a PPI merge script; see SI Section E.)"
echo ""

# ── Additional sources (bundled outputs → primary_data_prep/data/) ─────────────────
copy_if_missing \
  "$ADDITIONAL_SOURCE/opentarget/outputs/OpenTarget_disease_protein_associations.csv" \
  "$DATA_DIR/disgenet/OpenTarget/OpenTarget_disease_protein_associations.csv"
copy_if_missing \
  "$ADDITIONAL_SOURCE/repurposed_drug/outputs/RepurposedDrug_Indication.csv" \
  "$DATA_DIR/repurposed_drug/RepurposedDrug_Indication.csv"
copy_if_missing \
  "$ADDITIONAL_SOURCE/sider_nsides/outputs/sider_with_nsides.csv" \
  "$DATA_DIR/sider/sider_with_nsides.csv"

echo ""
echo "Additional sources (Open Targets, RepurposeDrugs, SIDER+nSIDES):"
echo "  Notebooks write directly to primary_data_prep/data/. Re-run to refresh:"
echo "    additional_data_source/opentarget/process_opentarget.ipynb"
echo "    additional_data_source/repurposed_drug/process_repurposed_drug.ipynb"
echo "    additional_data_source/sider_nsides/build_sider.py"
echo "    additional_data_source/sider_nsides/process_sider_nsides.ipynb"
echo ""
echo "Done. Notebook 01 reads PRIMARY_DATA_DIR=$DATA_DIR by default."
