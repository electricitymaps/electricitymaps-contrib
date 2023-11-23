"""
Usage: poetry run capacity_update --zone FR --target_datetime "2022-01-01"
"""

import importlib
from datetime import datetime
from logging import DEBUG, basicConfig, getLogger

import click
from requests import Session

from electricitymap.contrib.config import ZONE_PARENT, ZONES_CONFIG
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.parsers import PARSER_KEY_TO_DICT
from scripts.update_capacity_configuration import (
    update_aggregated_capacity_config,
    update_zone_capacity_config,
)
from scripts.utils import ROOT_PATH, run_shell_command

logger = getLogger(__name__)
basicConfig(level=DEBUG, format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s")


CAPACITY_PARSERS = PARSER_KEY_TO_DICT["productionCapacity"]

# Get productionCapacity source to zones mapping
CAPACITY_PARSER_SOURCE_TO_ZONES = {}
for zone_id, zone_config in ZONES_CONFIG.items():
    if zone_config.get("parsers", {}).get("productionCapacity") is not None:
        source = zone_config.get("parsers", {}).get("productionCapacity").split(".")[0]
        if source in CAPACITY_PARSER_SOURCE_TO_ZONES:
            CAPACITY_PARSER_SOURCE_TO_ZONES[source].append(zone_id)
        else:
            CAPACITY_PARSER_SOURCE_TO_ZONES[source] = [zone_id]


# TODO create source to key mapping eg {"EMBER": [....]}


@click.command()
@click.option("--zone", default=None)
@click.option("--source", default=None)
@click.option("--target_datetime")
@click.option("--update_aggregate", default=False)
def capacity_update(
    zone: ZoneKey,
    source: str,
    target_datetime: str,
    update_aggregate: bool = False,
):
    """Parameters
    ----------
    zone: a two letter zone from the map or a zone group (EIA, ENTSOE, EMBER, IRENA)
    target_datetime: ISO 8601 string, such as 2018-05-30 15:00
    \n
    Examples
    -------
    >>> poetry run capacity_update --zone FR --target_datetime "2022-01-01"
    >>> poetry run capacity_update --source ENTSOE --target_datetime "2022-01-01"
    """
    assert zone is not None or source is not None
    assert not (zone is None and source is None)

    session = Session()
    parsed_target_datetime = None
    if target_datetime is not None:
        parsed_target_datetime = datetime.fromisoformat(target_datetime)
    else:
        raise ValueError("target_datetime must be specified")

    if source is not None:
        if source not in CAPACITY_PARSER_SOURCE_TO_ZONES:
            raise ValueError(f"No capacity parser developed for {source}")
        parser = getattr(
            importlib.import_module(
                f"electricitymap.contrib.capacity_parsers.{source}"
            ),
            "fetch_production_capacity_for_all_zones",
        )
        source_capacity = parser(
            target_datetime=parsed_target_datetime, session=session
        )

        for zone in source_capacity:
            if not source_capacity[zone]:
                print(f"No capacity data for {zone} in {target_datetime}")
            else:
                update_zone_capacity_config(zone, source_capacity[zone])

    elif zone is not None:
        if zone not in CAPACITY_PARSERS:
            raise ValueError(f"No capacity parser developed for {zone}")
        parser = CAPACITY_PARSERS[zone]

        zone_capacity = parser(
            zone_key=zone, target_datetime=parsed_target_datetime, session=session
        )
        if not zone_capacity:
            raise ValueError(f"No capacity data for {zone} in {target_datetime}")
        else:
            update_zone_capacity_config(zone, zone_capacity)

    if eval(update_aggregate):
        zone_parent = ZONE_PARENT[zone]
        update_aggregated_capacity_config(zone_parent)

    print(f"Running prettier...")
    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)
