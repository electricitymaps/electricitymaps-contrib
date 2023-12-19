#!/usr/bin/env python3
"""
Usage: poetry run test_parser FR production
"""

import pprint
import time
from collections.abc import Callable
from datetime import datetime, timezone
from logging import DEBUG, basicConfig, getLogger
from typing import Any

import click

from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.parsers import PARSER_KEY_TO_DICT
from parsers.lib.quality import (
    ValidationError,
    validate_consumption,
    validate_exchange,
    validate_production,
)

logger = getLogger(__name__)
basicConfig(level=DEBUG, format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s")


@click.command()
@click.argument("zone")
@click.argument("data-type", default="")
@click.option("--target_datetime", default=None, show_default=True)
def test_parser(zone: ZoneKey, data_type: str, target_datetime: str | None):
    """
    Parameters
    ----------
    zone: a two letter zone from the map
    data_type: in ['production', 'exchangeForecast', 'production', 'exchange',
      'price', 'consumption', 'generationForecast', 'consumptionForecast', 'productionPerModeForecast]
    target_datetime: ISO 8601 string, such as 2018-05-30 15:00
    \n
    Examples
    -------
    >>> poetry run test_parser FR
    >>> poetry run test_parser FR production
    >>> poetry run test_parser "NO-NO3->SE" exchange
    >>> poetry run test_parser GE production --target_datetime="2022-04-10 15:00"

    """
    if data_type == "productionCapacity":
        raise ValueError(
            "productionCapacity is not supported by this script. Please use `poetry run update_capacity` instead."
        )
    parsed_target_datetime = None
    if target_datetime is not None:
        parsed_target_datetime = datetime.fromisoformat(target_datetime)
    start = time.time()

    if not data_type:
        data_type = "exchange" if "->" in zone else "production"

    parser: Callable[..., list[dict[str, Any]] | dict[str, Any]] = PARSER_KEY_TO_DICT[
        data_type
    ][zone]

    if data_type in ["exchange", "exchangeForecast"]:
        args = zone.split("->")
    else:
        args = [zone]
    res = parser(
        *args, target_datetime=parsed_target_datetime, logger=getLogger(__name__)
    )

    if not res:
        raise ValueError(f"Error: parser returned nothing ({res})")

    elapsed_time = time.time() - start
    if isinstance(res, list | tuple):
        res_list = list(res)
    else:
        res_list = [res]

    try:
        dts = [e["datetime"] for e in res_list]
    except KeyError:
        raise ValueError(
            f"Parser output lacks `datetime` key for at least some of the output. Full output: \n\n{res}\n"
        )

    assert all(
        [type(e["datetime"]) is datetime for e in res_list]
    ), "Datetimes must be returned as native datetime.datetime objects"

    assert (
        any(
            [
                e["datetime"].tzinfo is None
                or e["datetime"].tzinfo.utcoffset(e["datetime"]) is None
                for e in res_list
            ]
        )
        is False
    ), "Datetimes must be timezone aware"

    last_dt = datetime.fromisoformat(f"{max(dts)}").astimezone(timezone.utc)
    first_dt = datetime.fromisoformat(f"{min(dts)}").astimezone(timezone.utc)
    max_dt_warning = ""
    if not target_datetime:
        now_string = datetime.now(timezone.utc).isoformat(timespec="seconds")
        max_dt_warning = (
            f" :( >2h from now !!! (now={now_string} UTC)"
            if (datetime.now(timezone.utc) - last_dt).total_seconds() > 2 * 3600
            else f" -- OK, <2h from now :) (now={now_string} UTC)"
        )

    print("Parser result:")
    pp = pprint.PrettyPrinter(width=120)
    pp.pprint(res)
    print(
        "\n".join(
            [
                "---------------------",
                f"took {elapsed_time:.2f}s",
                f"min returned datetime: {first_dt} UTC",
                f"max returned datetime: {last_dt} UTC {max_dt_warning}",
            ]
        )
    )

    if isinstance(res, dict):
        res = [res]
    for event in res:
        try:
            if data_type == "production":
                validate_production(event, zone)
            elif data_type == "consumption":
                validate_consumption(event, zone)
            elif data_type == "exchange":
                validate_exchange(event, zone)
        except ValidationError as e:
            logger.warning(f"Validation failed @ {event['datetime']}: {e}")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    print(test_parser())
