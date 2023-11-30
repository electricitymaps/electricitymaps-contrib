"""
Usage: poetry run capacity_update --zone FR --target_datetime "2022-01-01"
"""

from datetime import datetime
from logging import DEBUG, basicConfig, getLogger

import click
from requests import Session

from electricitymap.contrib.lib.types import ZoneKey
from scripts.update_capacity_configuration import update_source, update_zone
from scripts.utils import ROOT_PATH, run_shell_command

logger = getLogger(__name__)
basicConfig(level=DEBUG, format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s")


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
    assert zone is not None or source is not None, "Either zone or source must be set"
    assert not (zone is None and source is None), "Zone and source cannot be both set"

    session = Session()
    update_aggregate = eval(update_aggregate)
    parsed_target_datetime = None
    if target_datetime is None:
        raise ValueError("target_datetime must be specified")
    parsed_target_datetime = datetime.fromisoformat(target_datetime)

    if source is not None:
        update_source(source, parsed_target_datetime, session)
    else:
        update_zone(zone, parsed_target_datetime, session, update_aggregate)

    print("Running prettier...")
    run_shell_command("web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)
