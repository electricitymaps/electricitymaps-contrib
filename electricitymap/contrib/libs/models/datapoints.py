from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, root_validator, validator

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG, ZoneKey
from electricitymap.contrib.libs.models.constants import VALID_CURRENCIES

LOWER_DATETIME_BOUND = datetime(2000, 1, 1, tzinfo=timezone.utc)


class Mix(BaseModel, ABC):
    @root_validator
    def _validate_mix(cls, values: Dict[str, Optional[float]]):
        if all(v is None for v in values.values()):
            raise ValueError("Mix is completely empty")


class ProductionMix(Mix):
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


class StorageMix(Mix):
    battery: Optional[float]
    hydro: Optional[float]


class Datapoint(BaseModel, ABC):
    zoneKey: ZoneKey
    datetime: datetime
    source: str
    forecasted: bool = False
    # TODO estimated: bool = False,

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
        if not values.get("forecasted", False) and v > datetime.now(
            timezone.utc
        ) + timedelta(days=1):
            raise ValueError(
                f"Date is in the future and this is not a forecasted point : {v}"
            )
        return v

    @staticmethod
    @abstractmethod
    def create(*args, **kwargs) -> "Datapoint":
        """To avoid having one datapoint failure crashing the whole parser, we use a factory method to create the datapoint."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """As part of a backwards compatibility, the points will be converted to a dict before being sent to the database."""
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
    def create(
        logger: Logger,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        forecasted: bool = False,
    ) -> Optional["Exchange"]:
        try:
            return Exchange(
                zoneKey=zone_key,
                datetime=datetime,
                source=source,
                value=value,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(f"Error creating exchange datapoint {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "sortedZoneKeys": self.zoneKey,
            "netFlow": self.value,
            "source": self.source,
        }


class Generation(Datapoint):
    value: float

    @validator("value")
    def _validate_value(cls, v: float):
        if v < 0:
            raise ValueError(f"Generation cannot be negative: {v}")
        if v > 500000:
            raise ValueError(f"Generation is implausibly high, above 500GW: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        forecasted: bool = False,
    ) -> Optional["Generation"]:
        try:
            return Generation(
                zoneKey=zone_key,
                datetime=datetime,
                source=source,
                value=value,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(f"Error creating generation datapoint {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "generation": self.value,
            "source": self.source,
        }


class ProductionBreakdown(Datapoint):
    production: ProductionMix
    storage: Optional[StorageMix]

    @staticmethod
    def create(
        logger: Logger,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        production: ProductionMix,
        storage: Optional[StorageMix] = None,
        forecasted: bool = False,
    ) -> Optional["ProductionBreakdown"]:
        try:
            # Correct negative production values.
            for key, value in production.dict().items():
                if value is not None and value < 0:
                    production.__setattr__(key, None)
                    logger.warning(
                        f"Production value for {key} is negative.\
                              This value is set to None."
                    )
            return ProductionBreakdown(
                zoneKey=zone_key,
                datetime=datetime,
                source=source,
                production=production,
                storage=storage,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(
                f"Error creating production breakdown datapoint {datetime}: {e}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "production": self.production.dict(),
            "storage": self.storage.dict() if self.storage else None,
            "source": self.source,
        }


class Consumption(Datapoint):
    consumption: float

    @validator("consumption")
    def _validate_consumption(cls, v: float):
        if v < 0:
            raise ValueError(f"Consumption cannot be negative: {v}")
        if v > 500000:
            raise ValueError(f"Consumption is implausibly high, above 500GW: {v}")

    @staticmethod
    def create(
        logger: Logger,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float,
        forecasted: bool = False,
    ) -> Optional["Consumption"]:
        try:
            return Consumption(
                zoneKey=zone_key,
                datetime=datetime,
                source=source,
                consumption=consumption,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(
                f"Error creating consumption datapoint {datetime}: {e}",
                extra={
                    "zone_key": zone_key,
                    "datetime": datetime,
                    "kind": "consumption",
                },
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "consumption": self.consumption,
            "source": self.source,
        }


class Price(Datapoint):
    price: float
    currency: str

    @validator("currency")
    def _validate_currency(cls, v: str):
        if v not in VALID_CURRENCIES:
            raise ValueError(f"Unknown currency: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        price: float,
        currency: str,
        forecasted: bool = False,
    ) -> Optional["Price"]:
        try:
            return Price(
                zoneKey=zone_key,
                datetime=datetime,
                source=source,
                price=price,
                currency=currency,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(f"Error creating price datapoint {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "currency": self.currency,
            "price": self.price,
            "source": self.source,
        }


class DatapointList(ABC):
    """A wrapper around datapoints lists."""

    logger: Logger
    datapoints: List[Datapoint]

    def __init__(self, logger: Logger):
        self.datapoints = list()
        self.logger = logger

    @abstractmethod
    def append(self, **kwargs):
        """Handles creation of datapoints and adding it to the batch."""
        # TODO Handle one day the creation of mixed batches.
        pass

    def to_list(self) -> List[Dict[str, Any]]:
        return [datapoint.to_dict() for datapoint in self.datapoints]


class ExchangeList(DatapointList):
    def append(
        self,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        forecasted: bool = False,
    ):
        datapoint = Exchange.create(
            self.logger, zone_key, datetime, source, value, forecasted
        )
        if datapoint:
            self.datapoints.append(datapoint)


class ProductionMixList(DatapointList):
    def append(
        self,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        production: ProductionMix,
        storage: Optional[StorageMix] = None,
        forecasted: bool = False,
    ):
        datapoint = ProductionBreakdown.create(
            self.logger, zone_key, datetime, source, production, storage, forecasted
        )
        if datapoint:
            self.datapoints.append(datapoint)


class GenerationList(DatapointList):
    def append(
        self,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        forecasted: bool = False,
    ):
        datapoint = Generation.create(
            self.logger, zone_key, datetime, source, value, forecasted
        )
        if datapoint:
            self.datapoints.append(datapoint)


class ConsumptionList(DatapointList):
    def append(
        self,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float,
        forecasted: bool = False,
    ):
        datapoint = Consumption.create(
            self.logger, zone_key, datetime, source, consumption, forecasted
        )
        if datapoint:
            self.datapoints.append(datapoint)


class PriceList(DatapointList):
    def append(
        self,
        zone_key: ZoneKey,
        datetime: datetime,
        source: str,
        price: float,
        currency: str,
        forecasted: bool = False,
    ):
        datapoint = Price.create(
            self.logger, zone_key, datetime, source, price, currency, forecasted
        )
        if datapoint:
            self.datapoints.append(datapoint)
