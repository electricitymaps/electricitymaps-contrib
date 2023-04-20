from abc import ABC, abstractmethod
from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.libs.models.events import (
    Event,
    EventObservation,
    Exchange,
    Price,
    ProductionBreakdown,
    ProductionMix,
    StorageMix,
    TotalConsumption,
    TotalProduction,
)


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
        observation: EventObservation = EventObservation.measured,
    ):
        event = Exchange.create(
            self.logger, zoneKey, datetime, source, value, observation
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
        observation: EventObservation = EventObservation.measured,
    ):
        event = ProductionBreakdown.create(
            self.logger, zoneKey, datetime, source, production, storage, observation
        )
        if event:
            self.events.append(event)


class TotalProductionList(EventList):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        observation: EventObservation = EventObservation.measured,
    ):
        event = TotalProduction.create(
            self.logger, zoneKey, datetime, source, value, observation
        )
        if event:
            self.events.append(event)


class TotalConsumptionList(EventList):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float,
        observation: EventObservation = EventObservation.measured,
    ):
        event = TotalConsumption.create(
            self.logger, zoneKey, datetime, source, consumption, observation
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
        observation: EventObservation = EventObservation.measured,
    ):
        event = Price.create(
            self.logger, zoneKey, datetime, source, price, currency, observation
        )
        if event:
            self.events.append(event)
