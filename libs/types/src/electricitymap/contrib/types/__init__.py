"""Electricity Maps type definitions."""

from enum import Enum
from typing import NewType

ZoneKey = NewType("ZoneKey", str)
"""
ZoneKey is used throughout the code to identify zones.
These are uppercase with 1-3 parts separated by dashes,
where the first part is a two-letter country code,
e.g. "AU", "AU-TAS", "AU-TAS-CBI".
"""

Point = NewType("Point", tuple[float, float])
"""
Point represents a geographic coordinate as (longitude, latitude).
For example, the point (150.47, -33.48) represents 150.47°E, 33.48°S.
"""

BoundingBox = NewType("BoundingBox", list[Point])
"""
BoundingBox indicate a geographic area of a zone.
An example bounding box looks like: [[140.46, -39.64], [150.47, -33.48]],
representing a box with corners at 140.46°E, 39.64°S and 150.47°E, 33.48°S.
"""


class ParserDataType(Enum):
    CONSUMPTION = "consumption"
    CONSUMPTION_FORECAST = "consumptionForecast"
    DAYAHEAD_LOCATIONAL_MARGINAL_PRICE = "dayaheadLocationalMarginalPrice"
    EXCHANGE_FORECAST = "exchangeForecast"
    EXCHANGE = "exchange"
    GENERATION_FORECAST = "generationForecast"
    PRICE = "price"
    PRICE_INTRADAY = "priceIntraday"
    PRODUCTION = "production"
    PRODUCTION_PER_MODE_FORECAST = "productionPerModeForecast"
    REALTIME_LOCATIONAL_MARGINAL_PRICE = "realtimeLocationalMarginalPrice"
    # TODO: Double check if we should keep them here?
    PRODUCTION_CAPACITY = "productionCapacity"
    GRID_ALERTS = "gridAlerts"

    def __str__(self) -> str:
        return self.value


ALL_DATA_TYPES = [dt.value for dt in ParserDataType]
EXCHANGE_DATA_TYPES = [ParserDataType.EXCHANGE, ParserDataType.EXCHANGE_FORECAST]
LMP_DATA_TYPES = [
    ParserDataType.REALTIME_LOCATIONAL_MARGINAL_PRICE,
    ParserDataType.DAYAHEAD_LOCATIONAL_MARGINAL_PRICE,
]

__all__: list[str] = [
    "ZoneKey",
    "Point",
    "BoundingBox",
    "ParserDataType",
    "ALL_DATA_TYPES",
    "EXCHANGE_DATA_TYPES",
    "LMP_DATA_TYPES",
]
