"""Resolve curated literature entities to PrimeKG-Plus nodes.

Principle: a curated **CUI is valid**; integration maps it to the PrimeKG node id
for the entity type (MONDO, HPO, NCBI, DrugBank, GO, …).

Resolution order (matches FINAL-* mapping notebooks):
  1. exact / normalized string match against ``nodes.csv``
  2. ``entity*_suggested_name`` / ``second_search_suggested_name`` fallback
  3. UMLS CUI → ontology id via PrimeKG xref tables + UMLS Metathesaurus atoms
  4. HGNC symbol fallback for genes when UMLS has HGNC but not NCBI
  5. UMLS canonical / synonym names → exact match on ontology term vocab + nodes.csv
  6. create literature node when CUI maps to a canonical ontology id not yet in KG
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

CUI_PATTERN = re.compile(r"C\d{5,7}")

GO_ENTITY_TYPES = frozenset(
    {"biological_process", "cellular_component", "molecular function", "molecular_function"}
)
GENE_ENTITY_TYPES = frozenset({"protein/gene", "gene/protein"})

# Curated entity_type → (PrimeKG node_type, allowed node_source values)
ENTITY_TYPE_TO_NODE: dict[str, tuple[str, frozenset[str]]] = {
    "disease": ("disease", frozenset({"MONDO", "MONDO_grouped"})),
    "phenotype": ("effect/phenotype", frozenset({"HPO"})),
    "pathology": ("effect/phenotype", frozenset({"HPO"})),
    "protein/gene": ("gene/protein", frozenset({"NCBI"})),
    "gene/protein": ("gene/protein", frozenset({"NCBI"})),
    "biological_process": ("biological process", frozenset({"GO"})),
    "cellular_component": ("cellular component", frozenset({"GO"})),
    "molecular function": ("molecular function", frozenset({"GO"})),
    "molecular_function": ("molecular function", frozenset({"GO"})),
    "drug": ("drug", frozenset({"DrugBank"})),
    "anatomy": ("anatomy", frozenset({"UBERON"})),
    "pathway": ("pathway", frozenset({"REACTOME"})),
    "exposure": ("exposure", frozenset({"CTD"})),
}

# UMLS ``source`` values tried per entity type (in order).
UMLS_SOURCES_BY_ENTITY: dict[str, tuple[str, ...]] = {
    "disease": ("MONDO", "OMIM", "ORPHANET"),
    "phenotype": ("HPO",),
    "pathology": ("HPO",),
    "protein/gene": ("NCBI",),
    "gene/protein": ("NCBI",),
    "drug": ("DRUGBANK",),
    "biological_process": ("GO",),
    "cellular_component": ("GO",),
    "molecular function": ("GO",),
    "molecular_function": ("GO",),
    "anatomy": ("UBERON", "FMA"),
    "pathway": ("REACTOME",),
}

# node_source used when creating a missing ontology node.
CREATE_NODE_SOURCE: dict[str, str] = {
    "disease": "MONDO",
    "phenotype": "HPO",
    "pathology": "HPO",
    "drug": "DrugBank",
    "biological_process": "GO",
    "cellular_component": "GO",
    "molecular function": "GO",
    "molecular_function": "GO",
    "anatomy": "UBERON",
}

UMLS_INDEX_SOURCES = frozenset(
    {
        "NCBI",
        "HGNC",
        "DRUGBANK",
        "GO",
        "HPO",
        "MONDO",
        "UBERON",
        "REACTOME",
        "OMIM",
        "FMA",
        "ORPHANET",
    }
)

# UMLS sources whose ``source_name`` values are collected for CUI → name → ontology lookup.
UMLS_NAME_SOURCES = frozenset(
    {
        "MTH",
        "MSH",
        "NCI",
        "SNOMEDCT_US",
        "HPO",
        "MONDO",
        "DRUGBANK",
        "HGNC",
        "GO",
        "OMIM",
        "NCBI",
    }
)


@dataclass(frozen=True)
class UmlsAtom:
    source: str
    code: str
    name: str


def norm_name(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def parse_cuis(status: Any) -> list[str]:
    if status is None or (isinstance(status, float) and pd.isna(status)):
        return []
    text = str(status).strip()
    if not text or text == "in_kg" or text == "invalid":
        return []
    return CUI_PATTERN.findall(text)


def normalize_hp_id(oid: str) -> str:
    oid = str(oid).strip()
    if oid.upper().startswith("HP:"):
        oid = oid[3:]
    if oid.isdigit():
        return str(int(oid))
    return oid


def normalize_go_id(oid: str) -> str:
    oid = str(oid).strip()
    if oid.upper().startswith("GO:"):
        oid = oid[3:]
    if oid.isdigit():
        return str(int(oid))
    return oid


def normalize_uberon_id(oid: str) -> str:
    oid = str(oid).strip()
    if oid.upper().startswith("UBERON:"):
        oid = oid[7:]
    if oid.isdigit():
        return str(int(oid))
    return oid


def normalize_mondo_id(oid: str) -> str:
    oid = str(oid).strip()
    if oid.upper().startswith("MONDO:"):
        oid = oid[6:]
    return oid


def normalize_node_id(oid: str, entity_type: str) -> str:
    """Normalize ontology ids to match ``nodes.csv`` conventions."""
    et = entity_type.strip()
    if et in ("phenotype", "pathology"):
        return normalize_hp_id(oid)
    if et in GO_ENTITY_TYPES:
        return normalize_go_id(oid)
    if et == "anatomy":
        return normalize_uberon_id(oid)
    if et == "disease":
        return normalize_mondo_id(oid)
    if et in GENE_ENTITY_TYPES and str(oid).isdigit():
        return str(int(oid))
    if et == "drug":
        return str(oid).strip().upper()
    return str(oid).strip()


@dataclass(frozen=True)
class ResolvedNode:
    node_id: str
    node_type: str
    node_name: str
    node_source: str
    method: str


class EntityResolver:
    def __init__(self, nodes: pd.DataFrame, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
        self._by_key: dict[tuple[str, str, str], dict[str, str]] = {}
        self.new_nodes: list[dict[str, str]] = []

        for row in nodes.itertuples(index=False):
            self._register_node(
                {
                    "node_id": str(row.node_id),
                    "node_type": str(row.node_type),
                    "node_name": str(row.node_name),
                    "node_source": str(row.node_source),
                }
            )

        self._cui_to_mondo = self._load_cui_to_mondo(data_dir)
        self._cui_to_hp = self._load_cui_to_hp(data_dir)
        self._mondo_terms = self._load_mondo_terms(data_dir)
        self._hp_terms = self._load_hp_terms(data_dir)
        self._go_terms = self._load_go_terms(data_dir)
        self._drugbank_terms = self._load_drugbank_terms(data_dir)
        self._uberon_terms = self._load_uberon_terms(data_dir)
        self._hp_id_by_name = self._index_terms_by_name(self._hp_terms, normalize_hp_id)
        self._mondo_id_by_name = self._index_terms_by_name(self._mondo_terms, normalize_mondo_id)
        self._go_id_by_name = self._index_terms_by_name(self._go_terms, normalize_go_id)
        self._uberon_id_by_name = self._index_terms_by_name(self._uberon_terms, normalize_uberon_id)
        self._drug_id_by_name = self._load_drug_name_index(data_dir)

        self._umls_index: dict[str, list[UmlsAtom]] | None = None
        self._cui_atom_names: dict[str, set[str]] | None = None
        self._canonical_names: dict[str, str] | None = None
        self._umls_path = self._find_umls_csv(data_dir)

    def _register_node(self, rec: dict[str, str]) -> None:
        self._by_name[norm_name(rec["node_name"])].append(rec)
        self._by_key[(rec["node_id"], rec["node_type"], rec["node_source"])] = rec

    @staticmethod
    def _find_terms_file(data_dir: Path, subdir: str, basename: str) -> Path | None:
        folder = data_dir / subdir
        dated = sorted(folder.glob(f"*-{basename}"), reverse=True)
        if dated:
            return dated[0]
        plain = folder / basename
        return plain if plain.exists() else None

    @staticmethod
    def _find_umls_csv(data_dir: Path) -> Path | None:
        umls_dir = data_dir / "umls"
        for name in ("umls_2025AB.csv", "umls.csv"):
            p = umls_dir / name
            if p.exists():
                return p
        return None

    @staticmethod
    def _find_canonical_names_csv(data_dir: Path) -> Path | None:
        for rel in (
            "umls/embedding_pool_2025AB/umls_2025ab_canonical_name_per_cui.csv",
            "umls/umls_2025ab_canonical_name_per_cui.csv",
        ):
            p = data_dir / rel
            if p.exists():
                return p
        return None

    @staticmethod
    def _index_terms_by_name(
        terms: dict[str, dict[str, str]],
        norm_id_fn,
    ) -> dict[str, list[str]]:
        out: dict[str, list[str]] = defaultdict(list)
        seen: set[tuple[str, str]] = set()
        for oid, rec in terms.items():
            if rec.get("is_obsolete") in {"true", "1", "yes"}:
                continue
            n = norm_name(rec.get("name", ""))
            if not n:
                continue
            nid = norm_id_fn(oid)
            key = (n, nid)
            if key not in seen:
                seen.add(key)
                out[n].append(nid)
        return dict(out)

    @staticmethod
    def _load_drug_name_index(data_dir: Path) -> dict[str, list[str]]:
        path = EntityResolver._find_terms_file(data_dir, "vocab", "drugbank_vocabulary.csv")
        if not path:
            path = data_dir / "drugbank" / "drugbank vocabulary.csv"
        if not path.exists():
            return {}
        df = pd.read_csv(path, dtype=str).fillna("")
        col_id = "DrugBank ID" if "DrugBank ID" in df.columns else df.columns[0]
        col_name = "Common name" if "Common name" in df.columns else df.columns[2]
        syn_col = "Synonyms" if "Synonyms" in df.columns else None
        out: dict[str, list[str]] = defaultdict(list)
        seen: set[tuple[str, str]] = set()
        for _, r in df.iterrows():
            dbid = str(r[col_id]).strip().upper()
            if not dbid:
                continue
            names = [str(r[col_name]).strip()]
            if syn_col:
                names.extend(str(r[syn_col]).split("|"))
            for raw in names:
                n = norm_name(raw)
                if not n:
                    continue
                key = (n, dbid)
                if key not in seen:
                    seen.add(key)
                    out[n].append(dbid)
        return dict(out)

    @staticmethod
    def _load_cui_to_mondo(data_dir: Path) -> dict[str, str]:
        out: dict[str, str] = {}
        vocab = data_dir / "vocab/20260510-umls_mondo_no_multi_mapping_v2.csv"
        if vocab.exists():
            df = pd.read_csv(vocab, dtype=str)
            for _, r in df.iterrows():
                out[str(r["umls_id"])] = normalize_mondo_id(str(r["mondo_id"]))
        mondo_ref = data_dir / "mondo/20251124-mondo_references.csv"
        if mondo_ref.exists():
            df = pd.read_csv(mondo_ref, dtype=str)
            umls = df[df["ontology"] == "UMLS"]
            for _, r in umls.iterrows():
                out.setdefault(str(r["ontology_id"]), normalize_mondo_id(str(r["mondo_id"])))
        return out

    @staticmethod
    def _load_cui_to_hp(data_dir: Path) -> dict[str, str]:
        out: dict[str, str] = {}
        hp_ref = data_dir / "hpo/20251124-hp_references.csv"
        if hp_ref.exists():
            df = pd.read_csv(hp_ref, dtype=str)
            umls = df[df["ontology"] == "UMLS"]
            for _, r in umls.iterrows():
                out[str(r["ontology_id"])] = normalize_hp_id(str(r["hp_id"]))
        return out

    @staticmethod
    def _load_mondo_terms(data_dir: Path) -> dict[str, dict[str, str]]:
        path = EntityResolver._find_terms_file(data_dir, "mondo", "mondo_terms.csv")
        if not path:
            return {}
        df = pd.read_csv(path, dtype=str).fillna("")
        return {
            str(r["id"]): {"name": str(r["name"]), "is_obsolete": str(r["is_obsolete"]).lower()}
            for _, r in df.iterrows()
        }

    @staticmethod
    def _load_hp_terms(data_dir: Path) -> dict[str, dict[str, str]]:
        path = EntityResolver._find_terms_file(data_dir, "hpo", "hp_terms.csv")
        if not path:
            return {}
        df = pd.read_csv(path, dtype=str).fillna("")
        out: dict[str, dict[str, str]] = {}
        for _, r in df.iterrows():
            rec = {"name": str(r["name"]), "is_obsolete": str(r["is_obsolete"]).lower()}
            out[str(r["id"])] = rec
            if str(r["id"]).isdigit():
                out.setdefault(normalize_hp_id(str(r["id"])), rec)
        return out

    @staticmethod
    def _load_go_terms(data_dir: Path) -> dict[str, dict[str, str]]:
        path = EntityResolver._find_terms_file(data_dir, "go", "go_terms_info.csv")
        if not path:
            return {}
        df = pd.read_csv(path, dtype=str).fillna("")
        out: dict[str, dict[str, str]] = {}
        for _, r in df.iterrows():
            gid = normalize_go_id(str(r["go_term_id"]))
            out[gid] = {"name": str(r["go_term_name"]), "is_obsolete": "false"}
        return out

    @staticmethod
    def _load_drugbank_terms(data_dir: Path) -> dict[str, dict[str, str]]:
        path = EntityResolver._find_terms_file(data_dir, "vocab", "drugbank_vocabulary.csv")
        if not path:
            path = data_dir / "drugbank" / "drugbank vocabulary.csv"
        if not path.exists():
            return {}
        df = pd.read_csv(path, dtype=str).fillna("")
        col_id = "DrugBank ID" if "DrugBank ID" in df.columns else df.columns[0]
        col_name = "Common name" if "Common name" in df.columns else df.columns[2]
        return {
            str(r[col_id]).upper(): {"name": str(r[col_name]), "is_obsolete": "false"}
            for _, r in df.iterrows()
        }

    @staticmethod
    def _load_uberon_terms(data_dir: Path) -> dict[str, dict[str, str]]:
        path = EntityResolver._find_terms_file(data_dir, "uberon", "uberon_terms.csv")
        if not path:
            return {}
        df = pd.read_csv(path, dtype=str).fillna("")
        id_col = "id" if "id" in df.columns else df.columns[0]
        name_col = "name" if "name" in df.columns else df.columns[1]
        obs_col = "is_obsolete" if "is_obsolete" in df.columns else None
        out: dict[str, dict[str, str]] = {}
        for _, r in df.iterrows():
            uid = normalize_uberon_id(str(r[id_col]))
            obs = str(r[obs_col]).lower() if obs_col else "false"
            out[uid] = {"name": str(r[name_col]), "is_obsolete": obs}
        return out

    def _ensure_umls_index(self) -> None:
        if self._umls_index is not None:
            return
        self._umls_index = {}
        self._cui_atom_names = defaultdict(set)
        if not self._umls_path:
            return
        scan_sources = UMLS_INDEX_SOURCES | UMLS_NAME_SOURCES
        for chunk in pd.read_csv(
            self._umls_path,
            usecols=["cui", "source", "source_code", "source_name"],
            dtype=str,
            chunksize=1_000_000,
        ):
            sub = chunk[chunk["source"].isin(scan_sources)]
            for r in sub.itertuples(index=False):
                if r.source in UMLS_INDEX_SOURCES:
                    atom = UmlsAtom(str(r.source), str(r.source_code), str(r.source_name))
                    self._umls_index.setdefault(r.cui, []).append(atom)
                    if r.source == "HPO" and r.source_code:
                        self._cui_to_hp.setdefault(r.cui, normalize_hp_id(r.source_code))
                    if r.source == "MONDO" and r.source_code:
                        self._cui_to_mondo.setdefault(r.cui, normalize_mondo_id(r.source_code))
                if r.source in UMLS_NAME_SOURCES and r.source_name:
                    self._cui_atom_names[r.cui].add(str(r.source_name).strip())

    def _ensure_canonical_names(self) -> None:
        if self._canonical_names is not None:
            return
        path = self._find_canonical_names_csv(self._data_dir)
        if not path:
            self._canonical_names = {}
            return
        df = pd.read_csv(path, dtype=str, usecols=["cui", "canonical_name"]).fillna("")
        self._canonical_names = {
            str(r.cui): str(r.canonical_name).strip()
            for r in df.itertuples(index=False)
            if str(r.canonical_name).strip()
        }

    def _umls_atoms(self, cui: str) -> list[UmlsAtom]:
        self._ensure_umls_index()
        return self._umls_index.get(cui, []) if self._umls_index else []

    def _pick_by_type(self, hits: list[dict[str, str]], entity_type: str) -> dict[str, str] | None:
        if not hits:
            return None
        spec = ENTITY_TYPE_TO_NODE.get(entity_type.strip())
        if spec:
            want_type, want_sources = spec
            typed = [h for h in hits if h["node_type"] == want_type and h["node_source"] in want_sources]
            if typed:
                return typed[0]
        return hits[0]

    def _lookup_existing(self, node_id: str, entity_type: str) -> ResolvedNode | None:
        spec = ENTITY_TYPE_TO_NODE.get(entity_type.strip())
        if not spec:
            return None
        want_type, want_sources = spec
        for src in want_sources:
            node = self._by_key.get((node_id, want_type, src))
            if node:
                return ResolvedNode(
                    node_id=node["node_id"],
                    node_type=node["node_type"],
                    node_name=node["node_name"],
                    node_source=node["node_source"],
                    method="cui",
                )
        return None

    @staticmethod
    def _atom_to_node_id(atom: UmlsAtom, entity_type: str) -> str | None:
        et = entity_type.strip()
        src, code = atom.source, atom.code.strip()
        if not code or code.upper() == "NOCODE":
            return None
        if src == "NCBI" and et in GENE_ENTITY_TYPES and code.isdigit():
            return str(int(code))
        if src == "DRUGBANK" and et == "drug" and code.upper().startswith("DB"):
            return code.upper()
        if src == "GO" and et in GO_ENTITY_TYPES:
            return normalize_go_id(code)
        if src == "HPO" and et in ("phenotype", "pathology"):
            return normalize_hp_id(code)
        if src == "UBERON" and et == "anatomy":
            return normalize_uberon_id(code)
        if src == "FMA" and et == "anatomy" and code.isdigit():
            return str(int(code))
        if src == "REACTOME" and et == "pathway" and code.startswith("R-"):
            return code
        if src == "MONDO" and et == "disease":
            return normalize_mondo_id(code)
        return None

    @staticmethod
    def _gene_symbols_from_atoms(atoms: list[UmlsAtom]) -> list[str]:
        symbols: list[str] = []
        seen: set[str] = set()
        for atom in atoms:
            if atom.source not in {"HGNC", "NCI"}:
                continue
            name = atom.name.strip()
            m = re.match(r"^([A-Z0-9]{2,15})\s+gene\b", name, re.I)
            if m:
                sym = m.group(1).upper()
                if sym not in seen:
                    symbols.append(sym)
                    seen.add(sym)
            m = re.match(r"^([A-Z0-9]{2,15})(?:\s*,|\s+$)", name)
            if m:
                sym = m.group(1).upper()
                if sym not in seen and sym not in {"GENE", "NOS", "BTS", "JNCL"}:
                    symbols.append(sym)
                    seen.add(sym)
        return symbols

    def _legacy_oid_for_cui(self, cui: str, entity_type: str) -> str | None:
        et = entity_type.strip()
        if et == "disease":
            return self._cui_to_mondo.get(cui)
        if et in ("phenotype", "pathology"):
            return self._cui_to_hp.get(cui)
        return None

    def _iter_cui_node_ids(self, cuis: list[str], entity_type: str) -> list[tuple[str, str]]:
        """Yield (node_id, sub_method) candidates in priority order."""
        et = entity_type.strip()
        out: list[tuple[str, str]] = []
        seen: set[str] = set()

        def add(node_id: str | None, method: str) -> None:
            if node_id and node_id not in seen:
                seen.add(node_id)
                out.append((node_id, method))

        preferred_sources = UMLS_SOURCES_BY_ENTITY.get(et, ())

        for cui in cuis:
            oid = self._legacy_oid_for_cui(cui, et)
            if oid:
                add(normalize_node_id(oid, et), "cui_xref")

            atoms = self._umls_atoms(cui)
            for src in preferred_sources:
                for atom in atoms:
                    if atom.source != src:
                        continue
                    add(self._atom_to_node_id(atom, et), f"cui_{src.lower()}")

            if et in GENE_ENTITY_TYPES:
                for sym in self._gene_symbols_from_atoms([a for a in atoms if a.source == "HGNC"]):
                    hit = self._resolve_by_name(sym, et, "cui_hgnc")
                    if hit:
                        add(hit.node_id, "cui_hgnc")

        return out

    def _resolve_by_cui(self, cuis: list[str], entity_type: str) -> ResolvedNode | None:
        if not ENTITY_TYPE_TO_NODE.get(entity_type.strip()):
            return None
        self._ensure_umls_index()
        for node_id, sub_method in self._iter_cui_node_ids(cuis, entity_type):
            hit = self._lookup_existing(node_id, entity_type)
            if hit:
                return ResolvedNode(hit.node_id, hit.node_type, hit.node_name, hit.node_source, sub_method)
        return None

    def _ontology_term(self, oid: str, entity_type: str) -> dict[str, str] | None:
        et = entity_type.strip()
        oid = str(oid).strip()
        if et == "disease":
            return self._mondo_terms.get(normalize_mondo_id(oid))
        if et in ("phenotype", "pathology"):
            return self._hp_terms.get(oid) or self._hp_terms.get(normalize_hp_id(oid))
        if et in GO_ENTITY_TYPES:
            return self._go_terms.get(normalize_go_id(oid))
        if et == "drug":
            return self._drugbank_terms.get(oid.upper())
        if et == "anatomy":
            return self._uberon_terms.get(normalize_uberon_id(oid))
        return None

    def _create_from_cui(self, cuis: list[str], entity_type: str, fallback_name: str) -> ResolvedNode | None:
        et = entity_type.strip()
        if et not in CREATE_NODE_SOURCE:
            return None
        spec = ENTITY_TYPE_TO_NODE.get(et)
        if not spec:
            return None
        want_type = spec[0]
        node_source = CREATE_NODE_SOURCE[et]

        self._ensure_umls_index()
        for node_id, sub_method in self._iter_cui_node_ids(cuis, et):
            existing = self._lookup_existing(node_id, et)
            if existing:
                return ResolvedNode(
                    existing.node_id,
                    existing.node_type,
                    existing.node_name,
                    existing.node_source,
                    sub_method,
                )

            term = self._ontology_term(node_id, et)
            if not term or term.get("is_obsolete") in {"true", "1", "yes"}:
                continue

            node_name = term.get("name") or fallback_name.strip()
            if not node_name:
                continue

            rec = {
                "node_id": node_id,
                "node_type": want_type,
                "node_name": node_name,
                "node_source": node_source,
            }
            self._register_node(rec)
            self.new_nodes.append(rec)
            return ResolvedNode(node_id, want_type, node_name, node_source, "new_cui")

        return None

    def _names_for_cuis(self, cuis: list[str]) -> list[str]:
        self._ensure_umls_index()
        self._ensure_canonical_names()
        ordered: list[str] = []
        seen: set[str] = set()

        def add(raw: str) -> None:
            text = str(raw or "").strip()
            if not text:
                return
            key = norm_name(text)
            if key in seen:
                return
            seen.add(key)
            ordered.append(text)

        for cui in cuis:
            if self._canonical_names:
                add(self._canonical_names.get(cui, ""))
            if self._cui_atom_names:
                for atom_name in self._cui_atom_names.get(cui, ()):
                    add(atom_name)
        return ordered

    def _ontology_ids_for_name(self, entity_type: str, name: str) -> list[str]:
        n = norm_name(name)
        if not n:
            return []
        et = entity_type.strip()
        if et == "disease":
            return list(dict.fromkeys(self._mondo_id_by_name.get(n, [])))
        if et in ("phenotype", "pathology"):
            return list(dict.fromkeys(self._hp_id_by_name.get(n, [])))
        if et in GO_ENTITY_TYPES:
            return list(dict.fromkeys(self._go_id_by_name.get(n, [])))
        if et == "drug":
            return list(dict.fromkeys(self._drug_id_by_name.get(n, [])))
        if et == "anatomy":
            return list(dict.fromkeys(self._uberon_id_by_name.get(n, [])))
        return []

    def _resolve_by_cui_term_names(self, cuis: list[str], entity_type: str) -> ResolvedNode | None:
        if not ENTITY_TYPE_TO_NODE.get(entity_type.strip()):
            return None
        et = entity_type.strip()
        for name in self._names_for_cuis(cuis):
            hit = self._resolve_by_name(name, et, "cui_umls_name")
            if hit:
                return hit
            if et in GENE_ENTITY_TYPES:
                fake_atoms = [UmlsAtom("HGNC", "", name)]
                for sym in self._gene_symbols_from_atoms(fake_atoms):
                    hit = self._resolve_by_name(sym, et, "cui_umls_gene")
                    if hit:
                        return hit
            for oid in self._ontology_ids_for_name(et, name):
                hit = self._lookup_existing(oid, et)
                if hit:
                    return ResolvedNode(hit.node_id, hit.node_type, hit.node_name, hit.node_source, "cui_term_name")
        return None

    def _create_from_cui_term_names(
        self,
        cuis: list[str],
        entity_type: str,
        fallback_name: str,
    ) -> ResolvedNode | None:
        et = entity_type.strip()
        if et not in CREATE_NODE_SOURCE:
            return None
        spec = ENTITY_TYPE_TO_NODE.get(et)
        if not spec:
            return None
        want_type = spec[0]
        node_source = CREATE_NODE_SOURCE[et]

        for name in self._names_for_cuis(cuis):
            for oid in self._ontology_ids_for_name(et, name):
                existing = self._lookup_existing(oid, et)
                if existing:
                    return ResolvedNode(
                        existing.node_id,
                        existing.node_type,
                        existing.node_name,
                        existing.node_source,
                        "cui_term_name",
                    )
                term = self._ontology_term(oid, et)
                if not term or term.get("is_obsolete") in {"true", "1", "yes"}:
                    continue
                node_name = term.get("name") or fallback_name.strip() or name.strip()
                if not node_name:
                    continue
                rec = {
                    "node_id": oid,
                    "node_type": want_type,
                    "node_name": node_name,
                    "node_source": node_source,
                }
                self._register_node(rec)
                self.new_nodes.append(rec)
                return ResolvedNode(oid, want_type, node_name, node_source, "new_cui_term_name")
        return None

    def _resolve_by_name(self, name: Any, entity_type: str, method: str) -> ResolvedNode | None:
        hits = self._by_name.get(norm_name(name), [])
        picked = self._pick_by_type(hits, entity_type)
        if not picked:
            return None
        return ResolvedNode(
            node_id=picked["node_id"],
            node_type=picked["node_type"],
            node_name=picked["node_name"],
            node_source=picked["node_source"],
            method=method,
        )

    def resolve(
        self,
        entity_name: Any,
        entity_status: Any,
        entity_type: Any,
        suggested_name: Any = None,
        second_search_suggested: Any = None,
        expert_cui: Any = None,
    ) -> ResolvedNode | None:
        return self.resolve_or_create(
            entity_name,
            entity_status,
            entity_type,
            suggested_name=suggested_name,
            second_search_suggested=second_search_suggested,
            expert_cui=expert_cui,
            allow_create=False,
        )

    def resolve_or_create(
        self,
        entity_name: Any,
        entity_status: Any,
        entity_type: Any,
        suggested_name: Any = None,
        second_search_suggested: Any = None,
        expert_cui: Any = None,
        allow_create: bool = True,
    ) -> ResolvedNode | None:
        etype = str(entity_type or "").strip()
        if not etype:
            return None

        fallback_name = str(entity_name or suggested_name or second_search_suggested or "").strip()

        for candidate, method in (
            (entity_name, "name"),
            (suggested_name, "suggested_name"),
            (second_search_suggested, "second_search_suggested_name"),
        ):
            hit = self._resolve_by_name(candidate, etype, method)
            if hit:
                return hit

        expert_cuis = parse_cuis(expert_cui)
        if expert_cuis:
            hit = self._resolve_by_cui(expert_cuis, etype)
            if hit:
                return ResolvedNode(hit.node_id, hit.node_type, hit.node_name, hit.node_source, "expert_cui")
            if allow_create:
                created = self._create_from_cui(expert_cuis, etype, fallback_name)
                if created:
                    return created
            hit = self._resolve_by_cui_term_names(expert_cuis, etype)
            if hit:
                return hit
            if allow_create:
                created = self._create_from_cui_term_names(expert_cuis, etype, fallback_name)
                if created:
                    return created

        status_cuis = parse_cuis(entity_status)
        if status_cuis:
            hit = self._resolve_by_cui(status_cuis, etype)
            if hit:
                return hit
            if allow_create:
                created = self._create_from_cui(status_cuis, etype, fallback_name)
                if created:
                    return created
            hit = self._resolve_by_cui_term_names(status_cuis, etype)
            if hit:
                return hit
            if allow_create:
                created = self._create_from_cui_term_names(status_cuis, etype, fallback_name)
                if created:
                    return created

        if str(entity_status or "").strip() == "in_kg":
            for candidate in (entity_name, suggested_name, second_search_suggested):
                hits = self._by_name.get(norm_name(candidate), [])
                if len(hits) == 1:
                    h = hits[0]
                    return ResolvedNode(h["node_id"], h["node_type"], h["node_name"], h["node_source"], "name_loose")
                picked = self._pick_by_type(hits, etype)
                if picked:
                    return ResolvedNode(
                        picked["node_id"],
                        picked["node_type"],
                        picked["node_name"],
                        picked["node_source"],
                        "name_loose",
                    )

        return None

    def extend_nodes(self, base_nodes: pd.DataFrame) -> pd.DataFrame:
        """Append literature-created nodes with new ``node_index`` values."""
        if not self.new_nodes:
            return base_nodes
        next_idx = int(base_nodes["node_index"].max()) + 1
        rows = []
        for rec in self.new_nodes:
            rows.append(
                {
                    "node_index": next_idx,
                    "node_id": rec["node_id"],
                    "node_type": rec["node_type"],
                    "node_name": rec["node_name"],
                    "node_source": rec["node_source"],
                }
            )
            next_idx += 1
        return pd.concat([base_nodes, pd.DataFrame(rows)], ignore_index=True)
