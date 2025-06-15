#!/usr/bin/env python

import pandas as pd


def main():
    df: pd.DataFrame = pd.read_excel(
        'corpus/generated-sents.xlsx',
        index_col=0,
        header=1)
    df.columns = map(lambda s: s.replace(' ', '_'), df.columns)
    #dfn = df.select_dtypes(include='number')
    #print(df.columns)
    dfn = df['original_score general_score medical_terms_score'.split()]
    #print(dfn)
    dfn = dfn[dfn['medical_terms_score'].map(type) != str]  # one value has a comment
    # physicians told no annotation needed if a 5
    dfn = dfn.fillna(5)
    print(dfn.describe())
    print(dfn[dfn['original_score'] >= 4].describe())


if (__name__ == '__main__'):
    main()
