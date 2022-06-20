import os

import pandas as pd


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", f"{name}.csv")
    df = pd.read_csv(path, index_col="datetime", parse_dates=True)
    df = df.apply(pd.to_numeric, errors="coerce")
    return df
