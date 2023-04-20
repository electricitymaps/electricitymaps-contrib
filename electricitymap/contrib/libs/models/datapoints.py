from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG, ZoneKey
from electricitymap.contrib.libs.models.constants import VALID_CURRENCIES

LOWER_DATETIME_BOUND = datetime(2000, 1, 1, tzinfo=timezone.utc)


class ProductionMix(BaseModel):
    """
    Containts the production mix for a zone at a given time.
    All values are in MW.
    """
    biomass: Optional[float] = None
    coal: Optional[float] = None
    gas: Optional[float] = None
    geothermal: Optional[float] = None
    hydro: Optional[float] = None
    nuclear: Optional[float] = None
    oil: Optional[float] = None
    solar: Optional[float] = None
    unknown: Optional[float] = None
    wind: Optional[float] = None

    def set_value(self, mode: str, value: float) -> None:
        """
        Sets the value of a production mode.
        This can be used if the Production has been initialized empty
        and is being filled in a loop.
        """
        self.__setattr__(mode, value)

class StorageMix(BaseModel):
    """
    Containts the storage mix for a zone at a given time.
    All values are in MW.
    """
    battery: Optional[float] = None
    hydro: Optional[float] = None


class Event(BaseModel, ABC):
    """
    An abstract class representing all types of electricity events that can occur in a zone.
    forecasted: Whether the point is a forecasted point or not.
    Should be set to True if the point is a forecast provided by a datasource.
    zoneKey: The zone key of the zone the event is happening in.
    datetime: The datetime of the event.
    source: The source of the event.
    We currentlu use the root url of the datasource. Ex: edf.fr
    """
    forecasted: bool = False
    zoneKey: ZoneKey
    datetime: datetime
    source: str
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
                f"Date is in the future and this is not a forecasted point: {v}"
            )
        return v

    @staticmethod
    @abstractmethod
    def create(*args, **kwargs) -> "Event":
        """To avoid having one Event failure crashing the whole parser, we use a factory method to create the Event."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """As part of a backwards compatibility, the points will be converted to a dict before being sent to the database."""
        pass


class Exchange(Event):
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
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        forecasted: bool = False,
    ) -> Optional["Exchange"]:
        try:
            return Exchange(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                value=value,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(f"Error creating exchange Event {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "sortedZoneKeys": self.zoneKey,
            "netFlow": self.value,
            "source": self.source,
        }


class Generation(Event):
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
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        forecasted: bool = False,
    ) -> Optional["Generation"]:
        try:
            return Generation(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                value=value,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(f"Error creating generation Event {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "generation": self.value,
            "source": self.source,
        }


class ProductionBreakdown(Event):
    production: ProductionMix
    storage: Optional[StorageMix] = None

    @validator("production", "storage")
    def _validate_mix(cls, v):
        if v is not None:
            if all(value is None for value in v.dict().values()):
                raise ValueError("Mix is completely empty")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
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
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                production=production,
                storage=storage,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(
                f"Error creating production breakdown Event {datetime}: {e}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "production": self.production.dict(exclude_none=True),
            "storage": self.storage.dict(exclude_none=True) if self.storage else None,
            "source": self.source,
        }


class Consumption(Event):
    consumption: float

    @validator("consumption")
    def _validate_consumption(cls, v: float):
        if v < 0:
            raise ValueError(f"Consumption cannot be negative: {v}")
        if v > 500000:
            raise ValueError(f"Consumption is implausibly high, above 500GW: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float,
        forecasted: bool = False,
    ) -> Optional["Consumption"]:
        try:
            return Consumption(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                consumption=consumption,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(
                f"Error creating consumption Event {datetime}: {e}",
                extra={
                    "zoneKey": zoneKey,
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


class Price(Event):
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
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float,
        currency: str,
        forecasted: bool = False,
    ) -> Optional["Price"]:
        try:
            return Price(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                price=price,
                currency=currency,
                forecasted=forecasted,
            )
        except ValueError as e:
            logger.error(f"Error creating price Event {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "currency": self.currency,
            "price": self.price,
            "source": self.source,
        }


class EventList(ABC):
    """A wrapper around Events lists."""

    logger: Logger
    events: List[Event]

    def __init__(self, logger: Logger):
        self.events = list()
        self.logger = logger

    @abstractmethod
    def append(self, **kwargs):
        """Handles creation of events and adding it to the batch."""
        # TODO Handle one day the creation of mixed batches.
        pass

    def to_list(self) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in self.events]


class ExchangeList(EventList):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        forecasted: bool = False,
    ):
        event = Exchange.create(
            self.logger, zoneKey, datetime, source, value, forecasted
        )
        if event:
            self.events.append(event)


class ProductionBreakdownList(EventList):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        production: ProductionMix,
        storage: Optional[StorageMix] = None,
        forecasted: bool = False,
    ):
        event = ProductionBreakdown.create(
            self.logger, zoneKey, datetime, source, production, storage, forecasted
        )
        if event:
            self.events.append(event)


class GenerationList(EventList):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        forecasted: bool = False,
    ):
        event = Generation.create(
            self.logger, zoneKey, datetime, source, value, forecasted
        )
        if event:
            self.events.append(event)


class ConsumptionList(EventList):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float,
        forecasted: bool = False,
    ):
        event = Consumption.create(
            self.logger, zoneKey, datetime, source, consumption, forecasted
        )
        if event:
            self.events.append(event)


class PriceList(EventList):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float,
        currency: str,
        forecasted: bool = False,
    ):
        event = Price.create(
            self.logger, zoneKey, datetime, source, price, currency, forecasted
        )
        if event:
            self.events.append(event)
