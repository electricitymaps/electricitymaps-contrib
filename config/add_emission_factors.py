import logging
from collections import namedtuple
from copy import deepcopy
from pathlib import Path

import arrow
import pandas as pd
import yaml

from electricitymap.contrib.config import CO2EQ_PARAMETERS_DIRECT

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

EMISSION_FACTORS_DIRECT_FILENAME = "2022-08-11 regional emission factors - direct.csv"
EMISSION_FACTORS_UPSTREAM_FILENAME = (
    "2022-08-11 regional emission factors - upstream.csv"
)

CARBON_FREE_MODES = [
    "nuclear",
    "wind",
    "solar",
    "hydro",
]

EmissionFactorRow = namedtuple(
    "emission_factor_row", ["zone_key", "mode", "emission_factor", "datetime", "source"]
)

df_direct = pd.read_csv(CONFIG_DIR.joinpath(EMISSION_FACTORS_DIRECT_FILENAME))
df_upstream = pd.read_csv(CONFIG_DIR.joinpath(EMISSION_FACTORS_UPSTREAM_FILENAME))


def _get_row_direct(row: namedtuple) -> namedtuple:
    _df = df_direct.loc[
        (df_direct["mode"] == row.mode) & (df_direct["zone_key"] == row.zone_key)
    ]
    if _df.shape[0] == 0:
        logger.debug(
            f"[{row.zone_key} | {row.mode}] no direct emissions. Falling back to default."
        )
        return EmissionFactorRow(
            row.zone_key,
            row.mode,
            CO2EQ_PARAMETERS_DIRECT["emissionFactors"]["defaults"][row.mode]["value"],
            "1900-01-01",
            CO2EQ_PARAMETERS_DIRECT["emissionFactors"]["defaults"][row.mode]["source"],
        )
    elif _df.shape[0] > 1:
        logger.warning(
            f"[{row.zone_key} | {row.mode}] Direct emissions appear multiple times."
        )
    return list(_df.itertuples())[0]


def _get_lifecycle_datetime(row_u: namedtuple, row_d: namedtuple) -> str:
    # Get the latest datetime as the valid one
    return max(arrow.get(row_u.datetime), arrow.get(row_d.datetime)).format(
        "YYYY-MM-DD"
    )


# Sum per zone_key, per mode to get lifecycle emission factors
_rows_lifecycle = []
for row_upstream in df_upstream.itertuples():
    # If it's a carbon-free mode, we don't expect any direct emissions
    if row_upstream.mode in CARBON_FREE_MODES:
        _rows_lifecycle.append(dict(row_upstream._asdict()))
    else:
        row_direct = _get_row_direct(row_upstream)
        if row_upstream.zone_key == "AX":
            breakpoint()
        _row_lifecycle = deepcopy(dict(row_upstream._asdict()))
        _row_lifecycle["emission_factor"] += row_direct.emission_factor
        _row_lifecycle["datetime"] = _get_lifecycle_datetime(row_upstream, row_direct)
        _row_lifecycle["source"] = "; ".join([row_upstream.source, row_direct.source])
        _rows_lifecycle.append(_row_lifecycle)

# Remove the artefact `Index` column
df_lifecycle = pd.DataFrame.from_records(_rows_lifecycle).drop(columns=["Index"])


def read_zone_config(zone_key: str) -> dict:
    with open(CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml")) as f:
        return yaml.safe_load(f)


def update_zone_config(ef: pd.DataFrame, ef_type: str) -> None:
    assert ef_type in ["direct", "lifecycle"]
    for row in ef.itertuples():
        zone_config = read_zone_config(row.zone_key)
        _ef = zone_config.get("emissionFactors", {}).get(ef_type, {})
        # Can be undefined, a dict or a list of dicts
        if (_ef.get(row.mode) is None) or (isinstance(_ef.get(row.mode), dict)):
            _ef[row.mode] = {
                "value": row.emission_factor,
                "source": row.source,
                "datetime": row.datetime,
            }
        elif isinstance(_ef.get(row.mode), list):
            _ef[row.mode].append(
                {
                    "value": row.emission_factor,
                    "source": row.source,
                    "datetime": row.datetime,
                }
            )
        zone_config["emissionFactors"] = {
            **zone_config.get("emissionFactors", {}),
            ef_type: _ef,
        }

        with open(CONFIG_DIR.joinpath(f"zones/{row.zone_key}.yaml"), "w") as f:
            yaml.dump(zone_config, f, default_flow_style=False)


# Write direct emission factors
update_zone_config(df_direct, "direct")
logger.debug("👍🏻 Direct emission factors written.")

# Write lifecycle emission factors
update_zone_config(df_lifecycle, "lifecycle")
logger.debug("👍🏻 Lifecycle emission factors written.")
