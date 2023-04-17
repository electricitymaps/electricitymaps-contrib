import datetime
from abc import ABC
from logging import Logger
from typing import Any, Dict, Optional

from pydantic import BaseModel, root_validator, validator

from electricitymap.config.libs.loggers.parser_logger import ParserLoggerAdapter
from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG, ZoneKey
from electricitymap.contrib.config.constants import PRODUCTION_MODES, STORAGE_MODES
from electricitymap.contrib.libs.models.constants import VALID_CURRENCIES

LOWER_DATETIME_BOUND = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)

class ProductionMix(BaseModel):
    biomass: Optional[float]
    coal: Optional[float]
    gas: Optional[float]
    geothermal: Optional[float]
    hydro: Optional[float]
    nuclear: Optional[float]
    oil: Optional[float]
    solar: Optional[float]
    unknown: Optional[float]
    wind: Optional[float]
    @root_validator
    def _validate_production_mix(cls, values: Dict[str, Optional[float]]):
        if all(v is None for v in values.values()):
            raise ValueError("Production mix is completely empty")
    @validator("*")
    def _validate_production_mix_values(cls, v: Optional[float]):
        if v is not None and v < 0:
            raise ValueError(f"Production mix cannot be negative: {v}")
        return v

class StorageMix(BaseModel):
    battery: Optional[float]
    hydro: Optional[float]
    @root_validator
    def _validate_production_mix(cls, values: Dict[str, Optional[float]]):
        if all(v is None for v in values.values()):
            raise ValueError("Production mix is completely empty")





class Datapoint(BaseModel, ABC):
    zoneKey: ZoneKey
    datetime: datetime
    source: dict
    forecasted: bool = False

    @validator("zoneKey")
    def _validate_zone_key(cls, v):
        if v not in ZONES_CONFIG:
            raise ValueError(f"Unknown zone: {v}")
        return v
    @validator("datetime")
    def _validate_datetime(cls, v, values: Dict[str, Any]):
        if v.tzinfo is None:
            raise ValueError(f"Missing timezone: {v}")
        if v < LOWER_DATETIME_BOUND:
            raise ValueError(f"Date is before 2000, this is not plausible: {v}")
        if not values.get("forecasted", False) and v > datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1):
            raise ValueError(f"Date is in the future and this is not a forecasted point : {v}")
        return v
    @staticmethod
    def create(zone_key: ZoneKey, datetime: datetime, source: dict, forecasted: bool = False) -> "Datapoint":
        pass


class Exchange(Datapoint):
    value: float

    @validator("zoneKey")
    def _validate_zone_key(cls, v: str):
        if "->" not in v:
            raise ValueError(f"Not an exchange key: {v}")
        zone_keys = v.split("->")
        if zone_keys != sorted(zone_keys):
            raise ValueError(f"Exchange key not sorted: {v}")
        if v not in EXCHANGES_CONFIG:
            raise ValueError(f"Unknown zone: {v}")
        return v
    @validator("value")
    def _validate_value(cls, v: float):
        if abs(v) > 100000:
            raise ValueError(f"Exchange is implausibly high, above 100GW: {v}")
        return v
    @staticmethod
    def create(zone_key: ZoneKey, datetime: datetime, source: dict, value: float, forecasted: bool = False, logger: ParserLoggerAdapter = None) -> Optional["Exchange"]:
        try:
            return Exchange(zoneKey=zone_key, datetime=datetime, source=source, value=value, forecasted=forecasted)
        except ValueError as e:
            logger.error(f"Error creating exchange datapoint {datetime}: {e}")



class Generation(Datapoint):
    value: float

    @validator("value")
    def _validate_value(cls, v: float):
        if v < 0:
            raise ValueError(f"Generation cannot be negative: {v}")
        if v > 500000:
            raise ValueError(f"Generation is implausibly high, above 500GW: {v}")
        return v


class ProductionBreakdown(Datapoint):
    production: ProductionMix
    storage: Optional[StorageMix]


class Consumption(Datapoint):
    consumption: float

    @validator("consumption")
    def _validate_consumption(cls, v: float):
        if v < 0:
            raise ValueError(f"Consumption cannot be negative: {v}")
        if v > 500000:
            raise ValueError(f"Consumption is implausibly high, above 500GW: {v}")


class Price(Datapoint):
    price: float
    currency: str
    @validator("currency")
    def _validate_currency(cls, v: str):
        if v not in VALID_CURRENCIES:
            raise ValueError(f"Unknown currency: {v}")
        return v
