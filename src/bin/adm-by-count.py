#!/usr/bin/env python

"""Get DSProv annotated admissions by note count per admission.

"""

from typing import List, Tuple
from pathlib import Path
import pandas as pd
from zensols.mimic import HospitalAdmission, Corpus, ApplicationFactory


def main():
    ds_prov_home: Path = Path('~/view/uic/thesis/view/dsprov/').expanduser()
    corpus: Corpus = ApplicationFactory.get_corpus()
    df: pd.DataFrame = pd.read_csv(ds_prov_home / 'results/csv/match.csv')
    rows: List[Tuple] = []
    for hid in df['hadm_id'].drop_duplicates():
        adm: HospitalAdmission = corpus.get_hospital_adm_by_id(hid)
        rows.append((hid, len(adm)))
    df = pd.DataFrame(rows, columns='hadm_id count'.split())
    df = df.sort_values('count', ascending=True).reset_index(drop=True)
    print(df)


if (__name__ == '__main__'):
    main()
