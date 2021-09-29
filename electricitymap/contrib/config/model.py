from __future__ import annotations

import json
from typing import Callable

from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt
from pydantic.utils import import_string

from electricitymap.contrib.config import (
    EXCHANGES_CONFIG,
    ZONE_NEIGHBOURS,
    ZONES_CONFIG,
    Point,
    ZoneKey,
)

# NOTE: we could cast Point to a NamedTuple with x/y accessors


class StrictBaseModel(BaseModel):
    class Config:
        extra = "forbid"


class Capacity(StrictBaseModel):
    # TODO: if zone.json used underscores for keys we didn't need the Field()
    battery_storage: NonNegativeInt | None = Field(None, alias="battery storage")
    biomass: NonNegativeInt | None
    coal: NonNegativeInt | None
    gas: NonNegativeInt | None
    geothermal: NonNegativeInt | None
    hydro_storage: NonNegativeInt | None = Field(None, alias="hydro storage")
    hydro: NonNegativeInt | None
    nuclear: NonNegativeInt | None
    oil: NonNegativeInt | None
    solar: NonNegativeInt | None
    unknown: NonNegativeInt | None
    wind: NonNegativeInt | None


class Parsers(StrictBaseModel):
    consumption: str | None
    consumptionForecast: str | None
    generationForecast: str | None
    productionPerModeForecast: str | None
    price: str | None
    production: str | None
    productionPerUnit: str | None

    def get_function(self, type: str) -> Callable | None:
        """Lazy load parser functions.
        This requires the consumer to have install all parser dependencies.
        """
        function_str = getattr(self, type)
        if function_str:
            return import_string(f"electricitymap.contrib.parsers.{function_str}")


class Delays(StrictBaseModel):
    consumption: PositiveInt | None
    consumptionForecast: PositiveInt | None
    generationForecast: PositiveInt | None
    price: PositiveInt | None
    production: PositiveInt | None
    productionPerModeForecast: PositiveInt | None
    productionPerUnit: PositiveInt | None


class Zone(StrictBaseModel):
    bounding_box: list[Point] | None
    capacity: Capacity | None
    comment: str | None = Field(None, alias="_comment")
    contributors: list[str] | None
    delays: Delays | None
    disclaimer: str | None
    flag_file_name: str | None
    parsers: Parsers = Parsers()
    sub_zone_names: list[str] | None = Field(None, alias="subZoneNames")
    timezone: str | None
    key: ZoneKey  # This is not part of zones.json, but added here to enable self referencing

    def neighbors(self) -> list[ZoneKey]:
        return ZONE_NEIGHBOURS.get(self.key, [])

    class Config:
        # To allow for both comment and _comment.
        # TODO: stick to one of them
        allow_population_by_field_name = True


class ExchangeParsers(StrictBaseModel):
    exchange: str | None
    exchangeForecast: str | None


class Exchange(StrictBaseModel):
    capacity: tuple[int, int] | None
    comment: str | None = Field(None, alias="_comment")
    lonlat: tuple[float, float] | None
    parsers: ExchangeParsers | None
    rotation: int | None

    class Config:
        # To allow for both comment and _comment.
        # TODO: stick to one of them
        allow_population_by_field_name = True


class ConfigModel(StrictBaseModel):
    exchanges: dict[str, Exchange]
    zones: dict[str, Zone]
    # TODO: maybe extend with config/co2eq_parameters.json


def _load_config_model() -> ConfigModel:
    for zone_key, zone in ZONES_CONFIG.items():
        zone["key"] = zone_key

    return ConfigModel(exchanges=EXCHANGES_CONFIG, zones=ZONES_CONFIG)


CONFIG_MODEL = _load_config_model()
