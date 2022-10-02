from datetime import date, datetime
from typing import Callable, Optional, Union

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

Percentage = confloat(ge=0, le=1)


class StrictBaseModel(BaseModel):
    class Config:
        extra = "forbid"


class StrictBaseModelWithAlias(BaseModel):
    class Config:
        extra = "forbid"
        # To allow for both comment and _comment.
        # _source and source
        # _url and url
        # TODO: stick to one of them
        allow_population_by_field_name = True


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


class ParsersBaseModel(StrictBaseModel):
    def get_function(self, type: str) -> Optional[Callable]:
        """Lazy load parser functions.

        This requires the consumer to have install all parser dependencies.

        Returns:
            Optional[Callable]: parser function
        """
        function_str = getattr(self, type)
        if function_str:
            return import_string(f"electricitymap.contrib.parsers.{function_str}")


class Parsers(ParsersBaseModel):
    consumption: Optional[str]
    consumptionForecast: Optional[str]
    generationForecast: Optional[str]
    productionPerModeForecast: Optional[str]
    price: Optional[str]
    production: Optional[str]
    productionPerUnit: Optional[str]


class Delays(StrictBaseModel):
    consumption: Optional[PositiveInt]
    consumptionForecast: Optional[PositiveInt]
    generationForecast: Optional[PositiveInt]
    price: Optional[PositiveInt]
    production: Optional[PositiveInt]
    productionPerModeForecast: Optional[PositiveInt]
    productionPerUnit: Optional[PositiveInt]


class Zone(StrictBaseModelWithAlias):
    bounding_box: Optional[list[Point]]
    capacity: Optional[Capacity]
    comment: Optional[str] = Field(None, alias="_comment")
    contributors: Optional[list[str]]
    delays: Optional[Delays]
    disclaimer: Optional[str]
    flag_file_name: Optional[str]
    parsers: Parsers = Parsers()
    sub_zone_names: Optional[list[str]] = Field(None, alias="subZoneNames")
    timezone: Optional[str]
    key: ZoneKey  # This is not part of zones.json, but added here to enable self referencing
    estimation_method: Optional[str]

    def neighbors(self) -> list[ZoneKey]:
        return ZONE_NEIGHBOURS.get(self.key, [])


class ExchangeParsers(ParsersBaseModel):
    exchange: Optional[str]
    exchangeForecast: Optional[str]


class Exchange(StrictBaseModelWithAlias):
    capacity: Optional[tuple[int, int]]
    comment: Optional[str] = Field(None, alias="_comment")
    lonlat: Optional[tuple[float, float]]
    parsers: Optional[ExchangeParsers]
    rotation: Optional[int]


class PowerOriginRatiosValues(StrictBaseModelWithAlias):
    battery_charge: Optional[Percentage] = Field(None, alias="battery charge")
    battery_discharge: Optional[Percentage] = Field(None, alias="battery discharge")
    biomass: Optional[Percentage]
    coal: Optional[Percentage]
    gas: Optional[Percentage]
    geothermal: Optional[Percentage]
    hydro_discharge: Optional[Percentage] = Field(None, alias="hydro discharge")
    hydro_charge: Optional[Percentage] = Field(None, alias="hydro charge")
    hydro: Optional[Percentage]
    nuclear: Optional[Percentage]
    oil: Optional[Percentage]
    solar: Optional[Percentage]
    unknown: Optional[Percentage]
    wind: Optional[Percentage]

    @root_validator
    @classmethod
    def check_sum(cls, values):
        """Check that the sum of all values is approximately 1."""
        _v = [0 if v is None else v for v in values.values()]
        if abs(sum(_v) - 1) > 0.01:
            raise ValueError(
                f"All values must approximately sum to 1. Sum to {sum(_v)}"
            )
        return values


class PowerOriginRatios(StrictBaseModelWithAlias):
    source: Optional[str] = Field(None, alias="_source")
    comment: Optional[str] = Field(None, alias="_comment")
    url: Optional[Union[str, list[str]]] = Field(None, alias="_url")
    datetime: Optional[Union[date, datetime]]
    value: PowerOriginRatiosValues


class PowerOriginRatiosForZone(StrictBaseModelWithAlias):
    source: Optional[str] = Field(None, alias="_source")
    comment: Optional[str] = Field(None, alias="_comment")
    url: Optional[Union[str, list[str]]] = Field(None, alias="_url")
    power_origin_ratios: Union[list[PowerOriginRatios], PowerOriginRatios] = Field(
        alias="powerOriginRatios"
    )


class FallbackZoneMixes(StrictBaseModelWithAlias):
    defaults: PowerOriginRatiosForZone
    zone_overrides: dict[str, PowerOriginRatiosForZone] = Field(alias="zoneOverrides")


class ModeCategoryContribution(StrictBaseModelWithAlias):
    source: Optional[str] = Field(None, alias="_source")
    comment: Optional[str] = Field(None, alias="_comment")
    url: Optional[Union[str, list[str]]] = Field(None, alias="_url")
    datetime: Optional[Union[datetime, date]]
    value: Optional[Percentage]


class CategoryContribution(StrictBaseModelWithAlias):
    battery_charge: Optional[
        Union[ModeCategoryContribution, list[ModeCategoryContribution]]
    ] = Field(None, alias="battery charge")
    battery_discharge: Optional[
        Union[ModeCategoryContribution, list[ModeCategoryContribution]]
    ] = Field(None, alias="battery discharge")
    biomass: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]
    coal: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]
    gas: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]
    geothermal: Optional[
        Union[ModeCategoryContribution, list[ModeCategoryContribution]]
    ]
    hydro_charge: Optional[
        Union[ModeCategoryContribution, list[ModeCategoryContribution]]
    ] = Field(None, alias="hydro charge")
    hydro_discharge: Optional[
        Union[ModeCategoryContribution, list[ModeCategoryContribution]]
    ] = Field(None, alias="hydro discharge")
    hydro: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]
    nuclear: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]
    oil: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]
    solar: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]
    unknown: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]
    wind: Optional[Union[ModeCategoryContribution, list[ModeCategoryContribution]]]

    @root_validator
    @classmethod
    def check_contributions(cls, values):
        for v in values.values():
            if isinstance(v, list):
                # verify ordered by datetime
                dts = [c.datetime for c in v]
                if dts != sorted(dts):
                    raise ValueError("Contributions must be ordered by datetime")
        return values


class IsLowCarbon(StrictBaseModelWithAlias):
    defaults: CategoryContribution = CategoryContribution()
    zone_overrides: dict[str, CategoryContribution] = Field(alias="zoneOverrides")


class IsRenewable(StrictBaseModelWithAlias):
    defaults: CategoryContribution = CategoryContribution()
    zone_overrides: dict[str, CategoryContribution] = Field(alias="zoneOverrides")


class ModeEmissionFactor(StrictBaseModelWithAlias):
    source: Optional[str] = Field(None, alias="_source")
    comment: Optional[str] = Field(None, alias="_comment")
    url: Optional[Union[str, list[str]]] = Field(None, alias="_url")
    datetime: Optional[Union[date, datetime]]
    value: NonNegativeFloat


class AllModesEmissionFactors(StrictBaseModelWithAlias):
    battery_charge: Optional[
        Union[list[ModeEmissionFactor], ModeEmissionFactor]
    ] = Field(None, alias="battery charge")
    battery_discharge: Optional[
        Union[list[ModeEmissionFactor], ModeEmissionFactor]
    ] = Field(None, alias="battery discharge")
    biomass: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    coal: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    gas: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    geothermal: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    hydro_charge: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]] = Field(
        None, alias="hydro charge"
    )
    hydro_discharge: Optional[
        Union[list[ModeEmissionFactor], ModeEmissionFactor]
    ] = Field(None, alias="hydro discharge")
    hydro: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    nuclear: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    oil: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    solar: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    unknown: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]
    wind: Optional[Union[list[ModeEmissionFactor], ModeEmissionFactor]]

    @root_validator
    @classmethod
    def check_emission_factors(cls, values):
        """
        Check that all emission factors given as list are not empty.
        """
        for v in values.values():
            if isinstance(v, list):
                assert len(v) > 0, "Emission factors must not be an empty list"
        return values


class EmissionFactors(StrictBaseModelWithAlias):
    defaults: AllModesEmissionFactors
    zone_overrides: dict[str, AllModesEmissionFactors] = Field(alias="zoneOverrides")


class CO2eqParameters(StrictBaseModelWithAlias):
    fallback_zone_mixes: FallbackZoneMixes = Field(alias="fallbackZoneMixes")
    is_low_carbon: IsLowCarbon = Field(alias="isLowCarbon")
    is_renewable: IsRenewable = Field(alias="isRenewable")
    emission_factors: EmissionFactors = Field(alias="emissionFactors")


class ConfigModel(StrictBaseModel):
    exchanges: dict[str, Exchange]
    zones: dict[str, Zone]


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
