from collections.abc import Callable
from datetime import date, datetime, timezone
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    NonNegativeFloat,
    PositiveInt,
    confloat,
    root_validator,
    validator,
)
from pydantic.utils import import_string

from electricitymap.contrib.config import (
    CO2EQ_PARAMETERS_DIRECT,
    CO2EQ_PARAMETERS_LIFECYCLE,
    DATA_CENTERS_CONFIG,
    EXCHANGES_CONFIG,
    ZONE_NEIGHBOURS,
    ZONES_CONFIG,
)
from electricitymap.contrib.config.types import Point
from electricitymap.contrib.lib.models.constants import VALID_CURRENCIES
from electricitymap.contrib.lib.types import ZoneKey

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


class ModeCapacity(StrictBaseModelWithAlias):
    source: str | None = Field(None, alias="_source")
    comment: str | None = Field(None, alias="_comment")
    url: str | list[str] | None = Field(None, alias="_url")
    datetime: date | datetime | None
    value: NonNegativeFloat | None


class Capacity(StrictBaseModel):
    # TODO: if zone.json used underscores for keys we didn't need the Field()
    battery_storage: (
        ModeCapacity | list[ModeCapacity] | NonNegativeFloat
    ) | None = Field(None, alias="battery storage")
    biomass: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    coal: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    gas: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    geothermal: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    hydro_storage: (
        ModeCapacity | list[ModeCapacity] | NonNegativeFloat
    ) | None = Field(None, alias="hydro storage")
    hydro: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    nuclear: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    oil: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    solar: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    unknown: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None
    wind: (ModeCapacity | list[ModeCapacity] | NonNegativeFloat) | None


def _get_parser_folder(parser_key: str) -> str:
    return (
        "electricitymap.contrib.capacity_parsers"
        if parser_key == "productionCapacity"
        else "parsers"
    )


class ParsersBaseModel(StrictBaseModel):
    def get_function(self, data_type: str) -> Callable | None:
        """Lazy load parser functions.

        This requires the consumer to have install all parser dependencies.

        Returns:
            Optional[Callable]: parser function
        """
        function_str = getattr(self, data_type)

        if function_str:
            parser_folder = _get_parser_folder(data_type)
            return import_string(f"{parser_folder}.{function_str}")


class Parsers(ParsersBaseModel):
    consumption: str | None
    consumptionForecast: str | None
    generationForecast: str | None
    productionPerModeForecast: str | None
    dayaheadLocationalMarginalPrice: str | None
    realtimeLocationalMarginalPrice: str | None
    price: str | None
    priceIntraday: str | None
    production: str | None
    productionCapacity: str | None
    gridAlerts: str | None


class Source(StrictBaseModel):
    link: str


class Delays(StrictBaseModel):
    consumption: PositiveInt | None
    consumptionForecast: PositiveInt | None
    generationForecast: PositiveInt | None
    price: PositiveInt | None
    production: PositiveInt | None
    productionPerModeForecast: PositiveInt | None


class Zone(StrictBaseModelWithAlias):
    bounding_box: list[Point] | None
    bypass_aggregation_checks: list[ZoneKey] | None = Field(
        [], alias="bypassedSubZones"
    )
    capacity: Capacity | None
    comment: str | None = Field(None, alias="_comment")
    contributors: list[str] | None
    delays: Delays | None
    disclaimer: str | None
    parsers: Parsers = Parsers()
    price_displayed: bool | None
    generation_only: bool | None
    sub_zone_names: list[ZoneKey] | None = Field(None, alias="subZoneNames")
    timezone: str | None
    key: ZoneKey  # This is not part of zones/{zone_key}.yaml, but added here to enable self referencing
    sources: dict[str, Source] | None
    region: str | None
    country: str | None
    zone_name: str | None
    zone_short_name: str | None
    country_name: str | None
    currency: str | None

    @validator("currency")
    def currency_is_valid(cls, v):
        if v and v not in VALID_CURRENCIES:
            raise ValueError(f"Currency {v} is not a valid ISO 4217 currency code")
        return v

    def neighbors(self) -> list[ZoneKey]:
        return ZONE_NEIGHBOURS.get(self.key, [])


class ExchangeParsers(ParsersBaseModel):
    exchange: str | None
    exchangeForecast: str | None


class Exchange(StrictBaseModelWithAlias):
    capacity: tuple[int, int] | None
    comment: str | None = Field(None, alias="_comment")
    lonlat: tuple[float, float] | None
    parsers: ExchangeParsers | None
    rotation: int | None


class PowerOriginRatiosValues(StrictBaseModelWithAlias):
    battery_charge: Percentage | None = Field(None, alias="battery charge")
    battery_discharge: Percentage | None = Field(None, alias="battery discharge")
    biomass: Percentage | None
    coal: Percentage | None
    gas: Percentage | None
    geothermal: Percentage | None
    hydro_discharge: Percentage | None = Field(None, alias="hydro discharge")
    hydro_charge: Percentage | None = Field(None, alias="hydro charge")
    hydro: Percentage | None
    nuclear: Percentage | None
    oil: Percentage | None
    solar: Percentage | None
    unknown: Percentage | None
    wind: Percentage | None

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
    source: str | None = Field(None, alias="_source")
    comment: str | None = Field(None, alias="_comment")
    url: str | list[str] | None = Field(None, alias="_url")
    datetime: date | datetime | None
    value: PowerOriginRatiosValues


class PowerOriginRatiosForZone(StrictBaseModelWithAlias):
    source: str | None = Field(None, alias="_source")
    comment: str | None = Field(None, alias="_comment")
    url: str | list[str] | None = Field(None, alias="_url")
    power_origin_ratios: list[PowerOriginRatios] | PowerOriginRatios = Field(
        alias="powerOriginRatios"
    )


class FallbackZoneMixes(StrictBaseModelWithAlias):
    defaults: PowerOriginRatiosForZone
    zone_overrides: dict[str, PowerOriginRatiosForZone] = Field(alias="zoneOverrides")


class ModeCategoryContribution(StrictBaseModelWithAlias):
    source: str | None = Field(None, alias="_source")
    comment: str | None = Field(None, alias="_comment")
    url: str | list[str] | None = Field(None, alias="_url")
    datetime: datetime | date | None
    value: Percentage | None


class CategoryContribution(StrictBaseModelWithAlias):
    battery_charge: None | (
        ModeCategoryContribution | list[ModeCategoryContribution]
    ) = Field(None, alias="battery charge")
    battery_discharge: None | (
        ModeCategoryContribution | list[ModeCategoryContribution]
    ) = Field(None, alias="battery discharge")
    biomass: ModeCategoryContribution | list[ModeCategoryContribution] | None
    coal: ModeCategoryContribution | list[ModeCategoryContribution] | None
    gas: ModeCategoryContribution | list[ModeCategoryContribution] | None
    geothermal: None | (ModeCategoryContribution | list[ModeCategoryContribution])
    hydro_charge: None | (
        ModeCategoryContribution | list[ModeCategoryContribution]
    ) = Field(None, alias="hydro charge")
    hydro_discharge: None | (
        ModeCategoryContribution | list[ModeCategoryContribution]
    ) = Field(None, alias="hydro discharge")
    hydro: ModeCategoryContribution | list[ModeCategoryContribution] | None
    nuclear: ModeCategoryContribution | list[ModeCategoryContribution] | None
    oil: ModeCategoryContribution | list[ModeCategoryContribution] | None
    solar: ModeCategoryContribution | list[ModeCategoryContribution] | None
    unknown: ModeCategoryContribution | list[ModeCategoryContribution] | None
    wind: ModeCategoryContribution | list[ModeCategoryContribution] | None

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
    source: str | None = Field(None, alias="_source")
    comment: str | None = Field(None, alias="_comment")
    url: str | list[str] | None = Field(None, alias="_url")
    datetime: date | datetime | None
    value: NonNegativeFloat


class AllModesEmissionFactors(StrictBaseModelWithAlias):
    battery_charge: None | (
        list[ModeEmissionFactor] | ModeEmissionFactor
    ) = Field(None, alias="battery charge")
    battery_discharge: None | (
        list[ModeEmissionFactor] | ModeEmissionFactor
    ) = Field(None, alias="battery discharge")
    biomass: list[ModeEmissionFactor] | ModeEmissionFactor | None
    coal: list[ModeEmissionFactor] | ModeEmissionFactor | None
    gas: list[ModeEmissionFactor] | ModeEmissionFactor | None
    geothermal: list[ModeEmissionFactor] | ModeEmissionFactor | None
    hydro_charge: list[ModeEmissionFactor] | ModeEmissionFactor | None = Field(
        None, alias="hydro charge"
    )
    hydro_discharge: None | (
        list[ModeEmissionFactor] | ModeEmissionFactor
    ) = Field(None, alias="hydro discharge")
    hydro: list[ModeEmissionFactor] | ModeEmissionFactor | None
    nuclear: list[ModeEmissionFactor] | ModeEmissionFactor | None
    oil: list[ModeEmissionFactor] | ModeEmissionFactor | None
    solar: list[ModeEmissionFactor] | ModeEmissionFactor | None
    unknown: list[ModeEmissionFactor] | ModeEmissionFactor | None
    wind: list[ModeEmissionFactor] | ModeEmissionFactor | None

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


class DataCenter(StrictBaseModel):
    displayName: str
    lonlat: tuple[float, float] | None
    operationalSince: date | None
    provider: str
    region: str
    source: str
    status: str
    zoneKey: ZoneKey

    @property
    def ID(self) -> str:
        return f"{self.provider}-{self.region}"

    @validator("status")
    def status_exists(cls, v):
        AVAILABLE_STATUSES = ["operational"]
        if v not in AVAILABLE_STATUSES:
            raise ValueError(
                f"Data center status {v} is not one of the allowed statuses: {AVAILABLE_STATUSES}"
            )
        return v

    @validator("zoneKey")
    def zone_key_exists(cls, v):
        if v not in ZONES_CONFIG:
            raise ValueError(
                f"Data center zone key {v} is not one of the allowed zone keys: {ZONES_CONFIG.keys()}"
            )
        return v


class DataCenters(StrictBaseModel):
    data_centers: dict[str, DataCenter]

    # check that the ID for each data center is unique and matches the key in the dataCenters dict
    @validator("data_centers")
    def ids_match_configs(cls, v):
        for dict_ID, data_center in v.items():
            if dict_ID != data_center.ID:
                raise ValueError(
                    f"Data center ID {data_center.ID} does not match the key {dict_ID}"
                )
        return v


class EmissionFactorVariant(Enum):
    """
    Describes where an emission factor (EF) comes from.
    See electricitymap/contrib/config/emission_factors.py::_get_zone_specific_co2eq_parameter_with_metadata
    """

    GLOBAL_EXACT_TIMELESS = "global_exact_timeless"
    GLOBAL_EXACT_TIMELY = "global_exact_timely"
    GLOBAL_FALLBACK_LATEST = "global_fallback_latest"
    GLOBAL_FALLBACK_OLDER = "global_fallback_older"
    GLOBAL_FALLBACK_OLDEST = "global_fallback_oldest"

    ZONE_EXACT_TIMELESS = "zone_exact_timeless"
    ZONE_EXACT_TIMELY = "zone_exact_timely"
    ZONE_FALLBACK_LATEST = "zone_fallback_latest"
    ZONE_FALLBACK_OLDER = "zone_fallback_older"
    ZONE_FALLBACK_OLDEST = "zone_fallback_oldest"


class EmissionFactorMode(Enum):
    BIOMASS = "biomass"
    COAL = "coal"
    GAS = "gas"
    GEOTHERMAL = "geothermal"
    HYDRO = "hydro"
    NUCLEAR = "nuclear"
    OIL = "oil"
    SOLAR = "solar"
    UNKNOWN = "unknown"
    WIND = "wind"
    BATTERY_DISCHARGE = "battery discharge"
    HYDRO_DISCHARGE = "hydro discharge"


class YearZoneModeEmissionFactor(StrictBaseModelWithAlias):
    dt: datetime = Field(..., alias="datetime")
    zone_key: ZoneKey
    mode: EmissionFactorMode
    lifecycle_value: NonNegativeFloat
    lifecycle_source: str
    lifecycle_variant: EmissionFactorVariant
    lifecycle_datetime: datetime | None
    direct_value: NonNegativeFloat
    direct_source: str
    direct_variant: EmissionFactorVariant
    direct_datetime: datetime | None

    @validator("dt", "lifecycle_datetime", "direct_datetime", pre=True)
    def validate_timezone_aware(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v

        if isinstance(v, str):
            v = datetime.fromisoformat(v).replace(tzinfo=timezone.utc)

        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("Datetime must be timezone-aware")

        truncated_to_year = v.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        if v != truncated_to_year:
            raise ValueError("Datetime must be truncated to year.")
        return v


DATA_CENTERS_CONFIG_MODEL = DataCenters(data_centers=DATA_CENTERS_CONFIG)


if __name__ == "__main__":
    print(DATA_CENTERS_CONFIG_MODEL)
