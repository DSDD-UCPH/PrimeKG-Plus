from bs4 import BeautifulSoup
import pandas as pd

input_path = '../data/drugbank/full database.xml'
output_path = '../data/vocab/drugbank_atc_codes.csv'

rows = []

with open(input_path, 'r') as f:
    soup = BeautifulSoup(f, 'xml')
    for drug in soup.find_all('drug'):
        primary_id = drug.find('drugbank-id', {'primary': 'true'})
        if primary_id is None:
            primary_id = drug.find('drugbank-id')
        if primary_id is None:
            continue
        drugbank_id = primary_id.text.strip()
        atc_codes = drug.find_all('atc-code')
        for atc in atc_codes:
            code = atc.get('code')
            if code:
                rows.append(
                    {'atc_code': code.strip(),
                     'parent_key': drugbank_id}
                )

df = pd.DataFrame(rows).drop_duplicates()
df.to_csv(output_path, index=False)
