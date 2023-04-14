import datetime
from abc import ABC
from typing import Dict

from electricitymap.contrib.libs.models.constants import VALID_CURRENCIES
from pydantic import BaseModel, validator

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG, ZoneKey
from electricitymap.contrib.config.constants import PRODUCTION_MODES, STORAGE_MODES


class Datapoint(BaseModel, ABC):
    zoneKey: ZoneKey
    datetime: datetime
    source: dict
    forecasted: bool
    estimated: bool
    consolidated: bool

    @validator("zoneKey")
    def _validate_zone_key(self):
        if self.zoneKey not in ZONES_CONFIG:
            raise ValueError(f"Unknown zone: {self.zoneKey}")


class Exchange(Datapoint):
    value: float

    @validator("zoneKey")
    def _validate_zone_key(self):
        if "->" not in self.zoneKey:
            raise ValueError(f"Not an exchange key: {self.zoneKey}")
        zone_keys = self.zoneKey.split("->")
        if zone_keys != sorted(zone_keys):
            raise ValueError(f"Exchange key not sorted: {self.zoneKey}")
        if self.zoneKey not in EXCHANGES_CONFIG:
            raise ValueError(f"Unknown zone: {self.zoneKey}")


class Generation(Datapoint):
    value: float

    @validator("value")
    def _validate_value(self):
        if self.value < 0:
            raise ValueError(f"Generation cannot be negative: {self.value}")


class ProductionBreakdown(Datapoint):
    production: Dict[str, float]
    storage: Dict[str, float]

    @validator("production")
    def _validate_production(self):
        production_modes = set(self.production.keys())
        if not production_modes.issubset(PRODUCTION_MODES):
            raise ValueError(
                f"Unknown production mode: {production_modes - set(PRODUCTION_MODES)}"
            )

    @validator("storage")
    def _validate_storage(self):
        storage_modes = set(self.storage.keys())
        if not set(storage_modes).issubset(STORAGE_MODES):
            raise ValueError(
                f"Unknown storage mode: {storage_modes - set(STORAGE_MODES)}"
            )


class Consumption(Datapoint):
    consumption: float

    @validator("consumption")
    def _validate_consumption(self):
        if self.consumption < 0:
            raise ValueError(f"Consumption cannot be negative: {self.consumption}")


class Price(Datapoint):
    price: float
    currency: str
