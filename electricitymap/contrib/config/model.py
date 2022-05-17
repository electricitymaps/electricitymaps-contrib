from datetime import date, datetime
from typing import Callable, Dict, List, Optional, Tuple, Union

from pydantic import (
    BaseModel,
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    confloat,
    root_validator,
)
from pydantic.utils import import_string

from electricitymap.contrib.config import (
    CO2EQ_PARAMETERS_DIRECT,
    CO2EQ_PARAMETERS_LIFECYCLE,
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
    battery_storage: Optional[NonNegativeInt] = Field(None, alias="battery storage")
    biomass: Optional[NonNegativeInt]
    coal: Optional[NonNegativeInt]
    gas: Optional[NonNegativeInt]
    geothermal: Optional[NonNegativeInt]
    hydro_storage: Optional[NonNegativeInt] = Field(None, alias="hydro storage")
    hydro: Optional[NonNegativeInt]
    nuclear: Optional[NonNegativeInt]
    oil: Optional[NonNegativeInt]
    solar: Optional[NonNegativeInt]
    unknown: Optional[NonNegativeInt]
    wind: Optional[NonNegativeInt]


class Parsers(StrictBaseModel):
    consumption: Optional[str]
    consumptionForecast: Optional[str]
    generationForecast: Optional[str]
    productionPerModeForecast: Optional[str]
    price: Optional[str]
    production: Optional[str]
    productionPerUnit: Optional[str]

    def get_function(self, type: str) -> Optional[Callable]:
        """Lazy load parser functions.

        This requires the consumer to have install all parser dependencies.

        Returns:
            Optional[Callable]: parser function
        """
        function_str = getattr(self, type)
        if function_str:
            return import_string(f"electricitymap.contrib.parsers.{function_str}")


class Delays(StrictBaseModel):
    consumption: Optional[PositiveInt]
    consumptionForecast: Optional[PositiveInt]
    generationForecast: Optional[PositiveInt]
    price: Optional[PositiveInt]
    production: Optional[PositiveInt]
    productionPerModeForecast: Optional[PositiveInt]
    productionPerUnit: Optional[PositiveInt]


class Zone(StrictBaseModel):
    bounding_box: Optional[List[Point]]
    capacity: Optional[Capacity]
    comment: Optional[str] = Field(None, alias="_comment")
    contributors: Optional[List[str]]
    delays: Optional[Delays]
    disclaimer: Optional[str]
    flag_file_name: Optional[str]
    parsers: Parsers = Parsers()
    sub_zone_names: Optional[List[str]] = Field(None, alias="subZoneNames")
    timezone: Optional[str]
    key: ZoneKey  # This is not part of zones.json, but added here to enable self referencing

    def neighbors(self) -> List[ZoneKey]:
        return ZONE_NEIGHBOURS.get(self.key, [])

    class Config:
        # To allow for both comment and _comment.
        # TODO: stick to one of them
        allow_population_by_field_name = True


class ExchangeParsers(StrictBaseModel):
    exchange: Optional[str]
    exchangeForecast: Optional[str]


class Exchange(StrictBaseModel):
    capacity: Optional[Tuple[int, int]]
    comment: Optional[str] = Field(None, alias="_comment")
    lonlat: Optional[Tuple[float, float]]
    parsers: Optional[ExchangeParsers]
    rotation: Optional[int]

    class Config:
        # To allow for both comment and _comment.
        # TODO: stick to one of them
        allow_population_by_field_name = True


class PowerOriginRatiosValues(StrictBaseModel):
    battery_charge: Optional[confloat(ge=0, le=1)] = Field(
        None, alias="battery charge"
    )
    battery_discharge: Optional[confloat(ge=0, le=1)] = Field(
        None, alias="battery discharge"
    )
    biomass: Optional[confloat(ge=0, le=1)]
    coal: Optional[confloat(ge=0, le=1)]
    gas: Optional[confloat(ge=0, le=1)]
    geothermal: Optional[confloat(ge=0, le=1)]
    hydro_discharge: Optional[confloat(ge=0, le=1)] = Field(
        None, alias="hydro discharge"
    )
    hydro_charge: Optional[confloat(ge=0, le=1)] = Field(
        None, alias="hydro charge"
    )
    hydro: Optional[confloat(ge=0, le=1)]
    nuclear: Optional[confloat(ge=0, le=1)]
    oil: Optional[confloat(ge=0, le=1)]
    solar: Optional[confloat(ge=0, le=1)]
    unknown: Optional[confloat(ge=0, le=1)]
    wind: Optional[confloat(ge=0, le=1)]

    class Config:
        allow_population_by_field_name = True

    @root_validator
    def check_sum(cls, values):
        """Check that the sum of all values is approximately 1."""
        _v = [0 if v is None else v for v in values.values()]
        if abs(sum(_v) - 1) > 0.01:
            raise ValueError(
                f"All values must approximately sum to 1. Sum to {sum(_v)}"
            )
        return values


class PowerOriginRatios(StrictBaseModel):
    source: Optional[str] = Field(None, alias="_source")
    comment: Optional[str] = Field(None, alias="_comment")
    url: Optional[Union[str, List[str]]] = Field(None, alias="_url")
    datetime: Optional[Union[date, datetime]]
    value: PowerOriginRatiosValues

    class Config:
        # To allow for both comment and _comment + source and _source + url and _url.
        # TODO: stick to one of them
        allow_population_by_field_name = True


class PowerOriginRatiosForZone(StrictBaseModel):
    source: Optional[str] = Field(None, alias="_source")
    comment: Optional[str] = Field(None, alias="_comment")
    url: Optional[Union[str, List[str]]] = Field(None, alias="_url")
    power_origin_ratios: Union[List[PowerOriginRatios], PowerOriginRatios] = Field(
        alias="powerOriginRatios"
    )

    class Config:
        # To allow for both comment and _comment + source and _source + url and _url.
        # TODO: stick to one of them
        allow_population_by_field_name = True


class FallbackZoneMixes(StrictBaseModel):
    defaults: PowerOriginRatiosForZone
    zone_overrides: Dict[str, PowerOriginRatiosForZone] = Field(alias="zoneOverrides")

    class Config:
        allow_population_by_field_name = True


class ModeCategoryContribution(StrictBaseModel):
    source: Optional[str] = Field(None, alias="_source")
    comment: Optional[str] = Field(None, alias="_comment")
    url: Optional[Union[str, List[str]]] = Field(None, alias="_url")
    datetime: Optional[Union[datetime, date]]
    value: Optional[confloat(ge=0, le=1)]

    class Config:
        # To allow for both comment and _comment + source and _source.
        # TODO: stick to one of them
        allow_population_by_field_name = True


class CategoryContribution(StrictBaseModel):
    battery_charge: Optional[
        Union[ModeCategoryContribution, List[ModeCategoryContribution]]
    ] = Field(None, alias="battery charge")
    battery_discharge: Optional[
        Union[ModeCategoryContribution, List[ModeCategoryContribution]]
    ] = Field(None, alias="battery discharge")
    biomass: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]
    coal: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]
    gas: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]
    geothermal: Optional[
        Union[ModeCategoryContribution, List[ModeCategoryContribution]]
    ]
    hydro_charge: Optional[
        Union[ModeCategoryContribution, List[ModeCategoryContribution]]
    ] = Field(None, alias="hydro charge")
    hydro_discharge: Optional[
        Union[ModeCategoryContribution, List[ModeCategoryContribution]]
    ] = Field(None, alias="hydro discharge")
    hydro: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]
    nuclear: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]
    oil: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]
    solar: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]
    unknown: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]
    wind: Optional[Union[ModeCategoryContribution, List[ModeCategoryContribution]]]

    class Config:
        allow_population_by_field_name = True


class IsLowCarbon(StrictBaseModel):
    defaults: CategoryContribution = CategoryContribution()
    zone_overrides: Dict[str, CategoryContribution] = Field(alias="zoneOverrides")

    class Config:
        allow_population_by_field_name = True


class IsRenewable(StrictBaseModel):
    defaults: CategoryContribution = CategoryContribution()
    zone_overrides: Dict[str, CategoryContribution] = Field(alias="zoneOverrides")

    class Config:
        allow_population_by_field_name = True


class ModeEmissionFactor(StrictBaseModel):
    source: Optional[str] = Field(None, alias="_source")
    comment: Optional[str] = Field(None, alias="_comment")
    url: Optional[Union[str, List[str]]] = Field(None, alias="_url")
    datetime: Optional[Union[date, datetime]]
    value: NonNegativeFloat

    class Config:
        # To allow for both comment and _comment + source and _source + url and _url.
        # TODO: stick to one of them
        allow_population_by_field_name = True


class AllModesEmissionFactors(StrictBaseModel):
    battery_charge: Optional[
        Union[List[ModeEmissionFactor], ModeEmissionFactor]
    ] = Field(None, alias="battery charge")
    battery_discharge: Optional[
        Union[List[ModeEmissionFactor], ModeEmissionFactor]
    ] = Field(None, alias="battery discharge")
    biomass: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    coal: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    gas: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    geothermal: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    hydro_charge: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]] = Field(
        None, alias="hydro charge"
    )
    hydro_discharge: Optional[
        Union[List[ModeEmissionFactor], ModeEmissionFactor]
    ] = Field(None, alias="hydro discharge")
    hydro: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    nuclear: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    oil: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    solar: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    unknown: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]
    wind: Optional[Union[List[ModeEmissionFactor], ModeEmissionFactor]]

    class Config:
        allow_population_by_field_name = True


class EmissionFactors(StrictBaseModel):
    defaults: AllModesEmissionFactors
    zone_overrides: Dict[str, AllModesEmissionFactors] = Field(alias="zoneOverrides")

    class Config:
        allow_population_by_field_name = True


class CO2eqParameters(StrictBaseModel):
    fallback_zone_mixes: FallbackZoneMixes = Field(alias="fallbackZoneMixes")
    is_low_carbon: IsLowCarbon = Field(alias="isLowCarbon")
    is_renewable: IsRenewable = Field(alias="isRenewable")
    emission_factors: EmissionFactors = Field(alias="emissionFactors")

    class Config:
        allow_population_by_field_name = True


class ConfigModel(StrictBaseModel):
    exchanges: Dict[str, Exchange]
    zones: Dict[str, Zone]


# The co2eq parameters config model is separated as it does not respect the
# format: [zone_key]: [config for zone]
# NOTE: Possibility to parse the co2eq config to make it available as [zone_key]: [co2eq params]
class CO2eqConfigModel(StrictBaseModel):
    direct: CO2eqParameters
    lifecycle: CO2eqParameters


def _load_config_model() -> ConfigModel:
    for zone_key, zone in ZONES_CONFIG.items():
        zone["key"] = zone_key

    return ConfigModel(exchanges=EXCHANGES_CONFIG, zones=ZONES_CONFIG)


CONFIG_MODEL = _load_config_model()
CO2EQ_CONFIG_MODEL = CO2eqConfigModel(
    direct=CO2EQ_PARAMETERS_DIRECT, lifecycle=CO2EQ_PARAMETERS_LIFECYCLE
)
