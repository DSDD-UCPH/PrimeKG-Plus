# PrimeKG-Plus

**PrimeKG-Plus** is a large-scale biomedical knowledge graph for AI-driven drug discovery, with expanded coverage of rare diseases. It extends [PrimeKG](https://github.com/mims-harvard/PrimeKG) (Chandak et al., *Scientific Data*, 2023) through temporal updates to all source databases, LLM-assisted literature curation from over 800 PubMed articles, and integration of new data sources including OpenTargets, STRING v12, and nSIDES.

PrimeKG-Plus is developed at the [Center for Pharmaceutical Data Science and Education](https://cpdse.dk/), Department of Drug Design and Pharmacology, University of Copenhagen, as part of a Lundbeck Foundation-funded project on drug repurposing for rare diseases.

> **Status:** Manuscript in preparation. Data and scripts will be released upon publication.

---

## Overview

| Property | Value |
|---|---|
| Node types | 10 |
| Relation types | 6 |
| Data sources | 18 |
| Rare disease coverage | Expanded via LLM-assisted PubMed curation |
| Disease ontology | MONDO (with expert-curated grouping) |

### Node types

- Drug
- Disease
- Protein
- Anatomy
- Pathway (Reactome)
- Gene Ontology (GO) term
- Phenotype (HPO)
- Exposure (CTD)
- Biological process

### Relation types and data sources

| Relation type | Connects | Data source |
|---|---|---|
| indicated_for | Drug → Disease | DrugCentral, RepurposedDrug |
| targets | Drug → Protein | DrugBank |
| interacts_with | Protein → Protein | STRING v12, BioGRID |
| associated_with | Disease → Protein | DisGeNET, OpenTargets, HPO, NCBI |
| associated_with | Exposure → Protein / Disease | CTD |
| participates_in | Protein → Pathway | Reactome, NCBI |
| annotated_with | Protein → GO term | GO, Gene2GO, NCBI |
| expresses | Anatomy → Protein | Bgee, Uberon |
| presents_with | Disease → Phenotype | HPO |
| causes_side_effect | Drug → Drug effect | SIDER, nSIDES, DrugBank |
| parent_of | Disease → Disease | MONDO |
| parent_of | Phenotype → Phenotype | HPO |
| parent_of | Pathway → Pathway | Reactome |
| parent_of | Anatomy → Anatomy | Uberon |
| parent_of | GO → GO | Gene Ontology |

### Data sources (18)

DrugBank, DrugCentral, RepurposedDrug, DisGeNET, OpenTargets, STRING v12, BioGRID, Reactome, NCBI Gene, Gene Ontology, Bgee, Uberon, HPO, MONDO, CTD, SIDER, nSIDES, PubMed (LLM-curated, >800 articles)

---

## Key improvements over PrimeKG

- **Temporal updates** to all 20 original source databases
- **Rare disease expansion** via LLM-assisted curation of PubMed literature focused on rare and metabolic diseases
- **New data sources:** OpenTargets (disease-protein associations), STRING v12 (protein-protein interactions), nSIDES (drug side effects)
- **Expert-curated disease grouping** using Bio_ClinicalBERT embeddings (cosine similarity threshold 0.98) with human-in-the-loop review, expanding disease representation from 1,267 to 1,360 disease groups
- **MONDO-based disease ontology** with post-processing split rules for biologically heterogeneous clusters

---

## Usage

> Full data download and construction scripts will be released upon manuscript publication.

The knowledge graph is provided in edge-list format and can be loaded with standard graph libraries:

```python
import pandas as pd

# Load edge list
edges = pd.read_csv('primekg_plus_edges.csv')

# Load node features
nodes = pd.read_csv('primekg_plus_nodes.csv')
```

Compatible with:
- [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/)
- [DGL](https://www.dgl.ai/)
- [NetworkX](https://networkx.org/)

---

## Repository structure

```
PrimeKG-Plus/
├── data/                    # Edge lists and node features (released upon publication)
├── scripts/
│   ├── build/               # Data collection and integration pipeline
│   ├── curation/            # Disease grouping and expert review tools
│   └── analysis/            # Graph statistics and validation
├── notebooks/               # Example usage notebooks
├── LICENSE
└── README.md
```

---

## Citation

If you use PrimeKG-Plus in your research, please cite:

```bibtex
@misc{nguyen2026primekg,
  author    = {Nguyen, Trinh Trung Duong and others},
  title     = {PrimeKG-Plus: A Rare-Disease-Enriched Biomedical Knowledge Graph for AI-Driven Drug Discovery},
  year      = {2026},
  note      = {Manuscript in preparation},
  url       = {https://github.com/DSDD-UCPH/PrimeKG-Plus}
}
```

Please also cite the original PrimeKG:

```bibtex
@article{chandak2023primekg,
  title   = {Building a knowledge graph to enable precision medicine},
  author  = {Chandak, Payal and Huang, Kexin and Zitnik, Marinka},
  journal = {Scientific Data},
  volume  = {10},
  pages   = {67},
  year    = {2023}
}
```

---

## Team

**Principal Investigator:** Trinh Trung Duong Nguyen (University of Copenhagen)

**Contributors:** Nguyen Phuong Thuy (Hanoi Medical University) · Tung Kieu (Aalborg University) · Alexander S. Hauser (University of Copenhagen) · Albert J. Kooistra (University of Copenhagen) · Nguyen Dinh Truong (CUNY School of Medicine)

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

Trinh Trung Duong Nguyen · Department of Drug Design and Pharmacology, University of Copenhagen · [nguyentrinhtrungduong@gmail.com](mailto:nguyentrinhtrungduong@gmail.com)

