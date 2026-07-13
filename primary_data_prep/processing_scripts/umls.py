import os
from pathlib import Path

import numpy as np
import pandas as pd

UMLS_DIR = Path('../data/umls')
mrconso = UMLS_DIR / 'MRCONSO.RRF'
if not mrconso.is_file():
    candidates = sorted(UMLS_DIR.glob('**/MRCONSO.RRF'))
    if not candidates:
        raise FileNotFoundError(
            f"Missing MRCONSO.RRF under {UMLS_DIR.resolve()}. "
            "Unzip the UMLS Metathesaurus release and copy META/MRCONSO.RRF to data/umls/MRCONSO.RRF."
        )
    mrconso = candidates[0]

with open(mrconso, 'r') as f:
    data = f.readlines()
data = [x.split('|') for x in data]

columns = ['cui', 'language', 'term_status', 'lui', 'string_type', 'string_identifier', 'is_preferred',
          'aui', 'source_aui', 'source_cui', 'source_descriptor_dui', 'source',
          'source_term_type', 'source_code', 'source_name', 'x1', 'x2', 'x3', 'x4']

df_umls = pd.DataFrame(data, columns=columns)
df_umls = df_umls.query('language=="ENG"')
df_umls.head()

df_umls.to_csv('../data/umls/umls.csv', index=False)
