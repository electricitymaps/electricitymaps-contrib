from collections import namedtuple
import logging
import arrow
import pandas as pd
from copy import deepcopy
from pathlib import Path

import yaml

from electricitymap.contrib.config import CO2EQ_PARAMETERS_DIRECT

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

EMISSION_FACTORS_DIRECT_FILENAME = "2022-08-11 regional emission factors - direct.csv"
EMISSION_FACTORS_UPSTREAM_FILENAME = "2022-08-11 regional emission factors - upstream.csv"

CARBON_FREE_MODES = [
    "nuclear",
    "wind",
    "solar",
    "hydro",
]

EmissionFactorRow = namedtuple("emission_factor_row", ["zone_key", "mode", "emission_factor", "datetime", "source"])

df_direct = pd.read_csv(
    CONFIG_DIR.joinpath(EMISSION_FACTORS_DIRECT_FILENAME))
df_upstream = pd.read_csv(
    CONFIG_DIR.joinpath(EMISSION_FACTORS_UPSTREAM_FILENAME))


def _get_row_direct(row: namedtuple) -> namedtuple:
    _df = df_direct.loc[
        (df_direct["mode"] == row.mode) &
        (df_direct["zone_key"] == row.zone_key)]
    if _df.shape[0] == 0:
        logger.debug(f"[{row.zone_key} | {row.mode}] no direct emissions. Falling back to default.")
        return EmissionFactorRow(
            row.zone_key,
            row.mode,
            CO2EQ_PARAMETERS_DIRECT["emissionFactors"]["defaults"][row.mode]["value"],
            "1900-01-01",
            CO2EQ_PARAMETERS_DIRECT["emissionFactors"]["defaults"][row.mode]["source"]
        )
    elif _df.shape[0] > 1:
        logger.warning(f"[{row.zone_key} | {row.mode}] Direct emissions for appear multiple times.")
    return list(_df.itertuples())[0]

def _get_lifecycle_datetime(row_u: namedtuple, row_d: namedtuple) -> str:
    # Get the latest datetime as the valid one
    return max(arrow.get(row_u.datetime), arrow.get(row_d.datetime)).format("YYYY-MM-DD 00:00:00+00:00")

# Sum per zone_key, per mode to get lifecycle emission factors
_rows_lifecycle = []
for row_upstream in df_upstream.itertuples():
    # If it's a carbon-free mode, we don't expect any direct emissions
    if row_upstream.mode in CARBON_FREE_MODES:
        _rows_lifecycle.append(dict(row_upstream._asdict()))
    else:
        row_direct = _get_row_direct(row_upstream)
        _row_lifecycle = deepcopy(dict(row_upstream._asdict()))
        _row_lifecycle["emission_factor"] += row_direct.emission_factor
        _row_lifecycle["datetime"] = _get_lifecycle_datetime(row_upstream, row_direct)
        _row_lifecycle["source"] = "; ".join([row_upstream.source, row_direct.source])
        _rows_lifecycle.append(_row_lifecycle)

# Remove the artefact `Index` column
df_lifecycle = pd.DataFrame.from_records(_rows_lifecycle).drop(columns=["Index"])
