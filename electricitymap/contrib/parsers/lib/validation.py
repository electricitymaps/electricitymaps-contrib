"""Centralised validation function for all parsers."""

from logging import Logger, getLogger
from typing import Any


def validate_exchange(
    datapoint: dict, logger: Logger = getLogger(__name__)
) -> dict[str, Any] | None:
    """
    Validates a production datapoint based on given constraints.
    If the datapoint is found to be invalid then None is returned.
    """
    exchange: float = datapoint["netFlow"]
    if exchange is None:
        logger.warning(
            "{}: expected exchange cannot be null".format(
                datapoint["sortedZoneKeys"],
            ),
            extra={"key": datapoint["sortedZoneKeys"]},
        )
        return
    return datapoint
