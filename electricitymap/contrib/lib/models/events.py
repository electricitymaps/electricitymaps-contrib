# pylint: disable=no-member
import datetime as dt
import math
from abc import ABC, abstractmethod
from collections.abc import Set
from datetime import datetime, timedelta, timezone
from enum import Enum
from logging import Logger
from typing import Any

import pandas as pd
from pydantic import BaseModel, PrivateAttr, ValidationError, validator

from electricitymap.contrib.config import (
    EXCHANGES_CONFIG,
    RETIRED_ZONES_CONFIG,
    ZONES_CONFIG,
)
from electricitymap.contrib.lib.models.constants import VALID_CURRENCIES
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import ProductionModes, StorageModes

LOWER_DATETIME_BOUND = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _is_naive(t: dt.datetime) -> bool:
    """Determines if a datetime object is naive."""
    return t.tzinfo is None or t.tzinfo.utcoffset(t) is None


def _none_safe_round(value: float | None, precision: int = 6) -> float | None:
    """
    Rounds a value to the provided precision.
    If the value is None, it is returned as is.
    The default precision is 6 decimal places, which gives us a precision of 1 W.
    """
    return None if value is None or math.isnan(value) else round(value, precision)


class Mix(BaseModel, ABC):
    def add_value(
        self,
        mode: str,
        value: float | None,
    ) -> None:
        """
        Adds the provided value to the existing value of the provided mode.
        This is useful if there are multiple production modes in the source
        that maps to the same Electricity Maps production mode.
        """
        existing_value: float | None = getattr(self, mode)
        if value is not None and math.isnan(value):
            value = None
        if existing_value is not None:
            value = 0 if value is None else value
            self.__setattr__(mode, existing_value + value)
        else:
            self.__setattr__(mode, value)

    @classmethod
    def merge(cls, mixes: list["Mix"]) -> "Mix":
        raise NotImplementedError()

    @classmethod
    def _update(cls, mix: "Mix", new_mix: "Mix") -> "Mix":
        raise NotImplementedError()

    def __setattr__(self, name: str, value: float | None) -> None:
        """
        Overriding the setattr method to raise an error if the mode is unknown.
        """
        # 6 decimal places gives us a precision of 1 W.
        super().__setattr__(name, _none_safe_round(value))

    def __setitem__(self, key: str, value: float | None) -> None:
        """
        Allows to set the value of a mode using the bracket notation.
        """
        self.__setattr__(key, value)


class ProductionMix(Mix):
    """
    Contains the production mix for a zone at a given time.
    All values should be positives, otherwise they will be set to None
    and a warning will be logged.
    All values are in MW.
    """

    # We use a private attribute to keep track of the modes that have been set to None.
    _corrected_negative_values: set = PrivateAttr(set())
    biomass: float | None = None
    coal: float | None = None
    gas: float | None = None
    geothermal: float | None = None
    hydro: float | None = None
    nuclear: float | None = None
    oil: float | None = None
    solar: float | None = None
    unknown: float | None = None
    wind: float | None = None

    def __init__(self, **data: Any):
        """
        Overriding the constructor to check for negative values and set them to None.
        This method also keeps track of the modes that have been corrected.
        Note: This method does NOT allow to set negative values to zero for self consumption.
        As we want self consumption to be set to zero, on a fine grained level with the `add_value` method.
        """
        super().__init__(**data)
        for attr, value in data.items():
            if value is not None and value < 0:
                self._corrected_negative_values.add(attr)
                value = None
            # Ensure that the value is rounded to 6 decimal places and set to None if it is NaN.
            self.__setattr__(attr, value)

    def dict(  # noqa: A003
        self,
        *,
        include: set | dict | None = None,
        exclude: set | dict | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        keep_corrected_negative_values: bool = False,
    ) -> dict[str, Any]:
        """Overriding the dict method to add the corrected negative values as Nones."""
        production_mix = super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        if keep_corrected_negative_values:
            for corrected_negative_mode in self._corrected_negative_values:
                if corrected_negative_mode not in production_mix:
                    production_mix[corrected_negative_mode] = None
        return production_mix

    def __setattr__(
        self,
        name: str,
        value: float | None,
    ) -> None:
        """
        Overriding the setattr method to check that the name is a valid production mode
        and to check for negative values and set them to None.
        This method also keeps track of the modes that have been corrected.
        """
        if name not in ProductionModes.values():
            raise AttributeError(f"Unknown production mode: {name}")
        if value is not None and value < 0:
            self._corrected_negative_values.add(name)
            value = None
        return super().__setattr__(name, value)

    def _correct_negative_value(
        self, mode: str, value: float | None, correct_negative_with_zero: bool
    ) -> float | None:
        """
        Corrects a negative value by setting it to None or 0.
        This method also keeps track of the modes that have been corrected.
        """
        if value is not None and value < 0:
            self._corrected_negative_values.add(mode)
            return 0 if correct_negative_with_zero else None
        return value

    def add_value(
        self,
        mode: str,
        value: float | None,
        correct_negative_with_zero: bool = False,
    ) -> None:
        """Adds the provided value to the existing value of the provided mode. Negative values are set to None by default.
        If correct_negative_with_zero is set to True, negative values will be set to 0 instead of None.
        This method keeps track of modes that have been corrected.
        """
        value = self._correct_negative_value(mode, value, correct_negative_with_zero)
        super().add_value(mode, value)

    @property
    def has_corrected_negative_values(self) -> bool:
        return len(self._corrected_negative_values) > 0

    @property
    def corrected_negative_modes(self) -> Set[str]:
        return self._corrected_negative_values

    @classmethod
    def merge(cls, production_mixes: list["ProductionMix"]) -> "ProductionMix":
        """
        Merge a list of production mixes into a single production mix.
        The values are summed. Negative values have been set to None or 0.
        Therefore merging cannot result in a lower production value.
        """
        merged_production_mix = cls()
        for production_mix in production_mixes:
            # Process all set production modes
            for mode in ProductionModes.values():
                if mode in production_mix.__fields_set__:
                    merged_production_mix.add_value(mode, getattr(production_mix, mode))

            # Update corrected negative values
            merged_production_mix._corrected_negative_values.update(
                production_mix.corrected_negative_modes
            )
        return merged_production_mix

    @classmethod
    def _update(
        cls,
        production_mix: "ProductionMix | None",
        new_production_mix: "ProductionMix | None",
    ) -> "ProductionMix | None":
        """Update the production mix of a zone at a given time."""
        if production_mix is None:
            return new_production_mix
        elif new_production_mix is not None:
            for mode, value in new_production_mix:
                if value is not None:
                    production_mix[mode] = value
        return production_mix


class StorageMix(Mix):
    """
    Contains the storage mix for a zone at a given time.
    All values are in MW.
    Values can be both positive (when storing energy) or negative (when the storage is discharged).
    """

    battery: float | None = None
    hydro: float | None = None

    def __init__(self, **data: Any):
        """
        Overriding the constructor to check for NaN values and set them to None.
        """
        super().__init__(**data)
        for attr, value in data.items():
            self.__setattr__(attr, value)

    def __setattr__(self, name: str, value: float | None) -> None:
        """
        Overriding the setattr method to raise an error if the mode is unknown.
        """
        if name not in StorageModes.values():
            raise AttributeError(f"Unknown storage mode: {name}")
        return super().__setattr__(name, value)

    @classmethod
    def merge(cls, storage_mixes: list["StorageMix"]) -> "StorageMix":
        """
        Merge a list of storage mixes into a single storage mix.
        The values are summed.
        """
        merged_storage_mix = cls()
        for storage_mix in storage_mixes:
            for mode in StorageModes.values():
                if mode in storage_mix.__fields_set__:
                    merged_storage_mix.add_value(mode, getattr(storage_mix, mode))

        return merged_storage_mix

    @classmethod
    def _update(
        cls, storage_mix: "StorageMix | None", new_storage_mix: "StorageMix | None"
    ) -> "StorageMix | None":
        """Update the storage mix of a zone at a given time."""
        if storage_mix is None:
            return new_storage_mix
        elif new_storage_mix is not None:
            for mode, value in new_storage_mix:
                if value is not None:
                    storage_mix[mode] = value
        return storage_mix


class EventSourceType(str, Enum):
    measured = "measured"
    forecasted = "forecasted"
    estimated = "estimated"


class Event(BaseModel, ABC):
    """
    An abstract class representing all types of electricity events that can occur in a zone.
    sourceType: How was the event observed.
    Should be set to forecasted if the point is a forecast provided by a datasource.
    Should be set to estimated if the point is an estimate or data that has not been consolidated yet by the datasource.
    zoneKey: The zone key of the zone the event is happening in.
    datetime: The datetime of the event.
    source: The source of the event.
    We currently use the root url of the datasource. Ex: edf.fr
    """

    # The order of the attributes matters for the validation.
    # As the validators are called in the order of the attributes, we need to make sure that the sourceType is validated before the datetime.
    sourceType: EventSourceType = EventSourceType.measured
    zoneKey: ZoneKey
    datetime: datetime
    source: str

    @validator("zoneKey")
    def _validate_zone_key(cls, v):
        if v not in ZONES_CONFIG and v not in RETIRED_ZONES_CONFIG:
            raise ValueError(f"Unknown zone: {v}")
        return v

    @validator("datetime")
    def _validate_datetime(cls, v: dt.datetime, values: dict[str, Any]) -> dt.datetime:
        if _is_naive(v):
            raise ValueError(f"Missing timezone: {v}")
        if v < LOWER_DATETIME_BOUND:
            raise ValueError(f"Date is before 2000, this is not plausible: {v}")
        if values.get(
            "sourceType", EventSourceType.measured
        ) != EventSourceType.forecasted and v.astimezone(timezone.utc) > datetime.now(
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
    def to_dict(self) -> dict[str, Any]:
        """As part of a backwards compatibility, the points will be converted to a dict before being sent to the database."""
        pass


class AggregatableEvent(Event):
    """
    An abstract class representing all types of electricity events that can be aggregated.
    """

    @staticmethod
    def _unique_zone_key(df_view: pd.DataFrame) -> ZoneKey:
        zone_key = df_view["zoneKey"].unique()
        if len(zone_key) > 1:
            raise ValueError(f"Cannot merge events from different zones: {zone_key}")
        return zone_key[0]

    @staticmethod
    def _sources(df_view: pd.DataFrame) -> str:
        sources = df_view["source"].unique()
        flattened_sources = [
            source.strip() for sublist in sources for source in sublist.split(",")
        ]
        unique_sources = sorted(set(flattened_sources))
        return ", ".join(unique_sources)

    @staticmethod
    def _unique_source_type(df_view: pd.DataFrame) -> EventSourceType:
        source_type = df_view["sourceType"].unique()
        if len(source_type) > 1:
            raise ValueError(
                f"Cannot merge events from different source types: {source_type}"
            )
        return source_type[0]

    @staticmethod
    def _unique_datetime(df_view: pd.DataFrame) -> datetime:
        target_datetime = df_view.datetime.unique()
        if len(target_datetime) > 1:
            raise ValueError(
                f"Cannot merge events from different datetimes: {target_datetime}"
            )
        return target_datetime[0].to_pydatetime()

    @staticmethod
    def _aggregated_fields(
        df_view: pd.DataFrame,
    ) -> tuple[ZoneKey, str, EventSourceType, datetime]:
        return (
            AggregatableEvent._unique_zone_key(df_view),
            AggregatableEvent._sources(df_view),
            AggregatableEvent._unique_source_type(df_view),
            AggregatableEvent._unique_datetime(df_view),
        )

    @staticmethod
    @abstractmethod
    def aggregate(events: list["AggregatableEvent"]) -> "AggregatableEvent":
        """Aggregate a list of events into a single event."""
        pass


class Exchange(Event):
    """
    An event class representing the net exchange between two zones.
    netFlow: The net flow of electricity between the two zones.
    It should be positive if the zoneKey on the left of the arrow is exporting electricity to the zoneKey on the right of the arrow.
    Negative otherwise.
    """

    netFlow: float | None

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

    @validator("netFlow")
    def _validate_value(cls, v: float | None):
        if v is None:
            raise ValueError(f"Exchange cannot be None: {v}")
        if math.isnan(v):
            raise ValueError(f"Exchange cannot be NaN: {v}")
        # TODO in the future those checks should be performed in the data quality layer.
        if abs(v) > 100000:
            raise ValueError(f"Exchange is implausibly high, above 100GW: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        netFlow: float | None,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> "Exchange | None":
        try:
            return Exchange(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                netFlow=_none_safe_round(netFlow),
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(
                f"Error(s) creating exchange Event {datetime}: {e}",
                extra={
                    "zoneKey": zoneKey,
                    "datetime": datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "kind": "exchange",
                },
            )

    @staticmethod
    def _update(event: "Exchange", new_event: "Exchange") -> "Exchange":
        """Update the net exchange between two zones."""
        if event.zoneKey != new_event.zoneKey:
            raise ValueError(
                f"Cannot update events from different zones: {event.zoneKey} and {new_event.zoneKey}"
            )
        if event.datetime != new_event.datetime:
            raise ValueError(
                f"Cannot update events from different datetimes: {event.datetime} and {new_event.datetime}"
            )
        if event.source != new_event.source:
            raise ValueError(
                f"Cannot update events from different sources: {event.source} and {new_event.source}"
            )
        if event.sourceType != new_event.sourceType:
            raise ValueError(
                f"Cannot update events from different source types: {event.sourceType} and {new_event.sourceType}"
            )
        return Exchange(
            zoneKey=event.zoneKey,
            datetime=event.datetime,
            source=event.source,
            netFlow=new_event.netFlow,  # Exchange values can never be none so a new valid value will always be provided.
            sourceType=event.sourceType,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "datetime": self.datetime,
            "sortedZoneKeys": self.zoneKey,
            "netFlow": self.netFlow,
            "source": self.source,
            "sourceType": self.sourceType,
        }


class TotalProduction(Event):
    """Represents the total production of a zone at a given time. The value is in MW."""

    value: float | None

    @validator("value")
    def _validate_value(cls, v: float | None):
        if v is None:
            raise ValueError(f"Total production cannot be None: {v}")
        if math.isnan(v):
            raise ValueError(f"Exchange cannot be NaN: {v}")
        if v < 0:
            raise ValueError(f"Total production cannot be negative: {v}")
        # TODO in the future those checks should be performed in the data quality layer.
        if v > 500000:
            raise ValueError(f"Total production is implausibly high, above 500GW: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float | None,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> "TotalProduction | None":
        try:
            return TotalProduction(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                value=_none_safe_round(value),
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(
                f"Error(s) creating total production Event {datetime}: {e}",
                extra={
                    "zoneKey": zoneKey,
                    "datetime": datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "kind": "production",
                },
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "generation": self.value,
            "source": self.source,
            "sourceType": self.sourceType,
        }


class ProductionBreakdown(AggregatableEvent):
    production: ProductionMix | None = None
    storage: StorageMix | None = None
    """
    An event representing the production and storage breakdown of a zone at a given time.
    If a production mix is supplied it should not be fully empty.
    """

    @validator("production")
    def _validate_production_mix(cls, v):
        if (
            v is not None
            and not v.has_corrected_negative_values
            and all(value is None or math.isnan(value) for value in v.dict().values())
        ):
            raise ValueError("Mix is completely empty")
        return v

    @validator("storage")
    def _validate_storage_mix(cls, v):
        if v is not None and all(
            value is None or math.isnan(value) for value in v.dict().values()
        ):
            return None
        return v

    def get_value(self, mode: str) -> float | None:
        """Returns the value of the provided mode this can be production or storage.
        To retrieve the value of a storage mode, the mode should be suffixed with storage.
        Ex: retrive hydro production: get_value("hydro")
        Ex: retrive hydro storage: get_value("hydro storage")
        """
        if "storage" in mode:
            if self.storage is None:
                return None
            # This naming is the same as the capacity naming in the config.
            return getattr(self.storage, mode.split(" ")[0])
        if self.production is None:
            return None
        return getattr(self.production, mode)

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        production: ProductionMix | None = None,
        storage: StorageMix | None = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> "ProductionBreakdown | None":
        try:
            # Log warning if production has been corrected.
            if production is not None and production.has_corrected_negative_values:
                logger.debug(
                    f"Negative production values were detected: {production._corrected_negative_values}.\
                    They have been set to None."
                )
            return ProductionBreakdown(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                production=production,
                storage=storage,
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(
                f"Error(s) creating production breakdown Event {datetime}: {e}",
                extra={
                    "zoneKey": zoneKey,
                    "datetime": datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "kind": "production breakdown",
                },
            )

    @staticmethod
    def aggregate(events: list["ProductionBreakdown"]) -> "ProductionBreakdown":
        """Merge ProductionBreakdown events into one."""
        if len(events) == 0:
            raise ValueError("Cannot aggregate empty list of events")
        df_view = pd.DataFrame.from_records(
            [
                {
                    "zoneKey": event.zoneKey,
                    "datetime": event.datetime,
                    "source": event.source,
                    "sourceType": event.sourceType,
                    "data": event,
                }
                for event in events
            ]
        )
        (
            zoneKey,
            sources,
            source_type,
            target_datetime,
        ) = ProductionBreakdown._aggregated_fields(df_view)

        production_mix = ProductionMix.merge(
            [event.production for event in events if event.production is not None]
        )
        storage_mix = StorageMix.merge(
            [event.storage for event in events if event.storage is not None]
        )
        return ProductionBreakdown(
            zoneKey=zoneKey,
            datetime=target_datetime,
            source=sources,
            production=production_mix,
            storage=storage_mix,
            sourceType=source_type,
        )

    @staticmethod
    def _update(
        event: "ProductionBreakdown", new_event: "ProductionBreakdown"
    ) -> "ProductionBreakdown":
        """Update the production and storage breakdown of a zone at a given time."""
        if event.zoneKey != new_event.zoneKey:
            raise ValueError(
                f"Cannot update events from different zones: {event.zoneKey} and {new_event.zoneKey}"
            )
        if event.datetime != new_event.datetime:
            raise ValueError(
                f"Cannot update events from different datetimes: {event.datetime} and {new_event.datetime}"
            )
        if event.sourceType != new_event.sourceType:
            raise ValueError(
                f"Cannot update events from different source types: {event.sourceType} and {new_event.sourceType}"
            )
        production_mix = ProductionMix._update(event.production, new_event.production)
        storage_mix = StorageMix._update(event.storage, new_event.storage)
        source = ", ".join(
            set(event.source.split(", ")) | set(new_event.source.split(", "))
        )
        return ProductionBreakdown(
            zoneKey=event.zoneKey,
            datetime=event.datetime,
            source=source,
            production=production_mix,
            storage=storage_mix,
            sourceType=event.sourceType,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "production": self.production.dict(
                exclude_unset=True, keep_corrected_negative_values=True
            )
            if self.production
            else {},
            "storage": self.storage.dict(exclude_unset=True) if self.storage else {},
            "source": self.source,
            "sourceType": self.sourceType,
            "correctedModes": []
            if self.production is None
            else list(map(str, self.production._corrected_negative_values)),
        }


class TotalConsumption(Event):
    """Reprensent the total consumption of a zone. The total consumption is expressed in MW."""

    consumption: float | None

    @validator("consumption")
    def _validate_consumption(cls, v: float):
        if v is None:
            raise ValueError(f"Total consumption cannot be None: {v}")
        if math.isnan(v):
            raise ValueError(f"Exchange cannot be NaN: {v}")
        if v < 0:
            raise ValueError(f"Total consumption cannot be negative: {v}")
        # TODO in the future those checks should be performed in the data quality layer.
        if v > 500000:
            raise ValueError(f"Total consumption is implausibly high, above 500GW: {v}")
        if v == 0:
            raise ValueError(f"Total consumption cannot be 0 MW: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float | None,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> "TotalConsumption | None":
        try:
            return TotalConsumption(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                consumption=_none_safe_round(consumption),
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(
                f"Error(s) creating total consumption Event {datetime}: {e}",
                extra={
                    "zoneKey": zoneKey,
                    "datetime": datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "kind": "consumption",
                },
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "consumption": self.consumption,
            "source": self.source,
            "sourceType": self.sourceType,
        }


class Price(Event):
    price: float | None
    currency: str

    @validator("currency")
    def _validate_currency(cls, v: str) -> str:
        if v not in VALID_CURRENCIES:
            raise ValueError(f"Unknown currency: {v}")
        return v

    @validator("datetime")
    def _validate_datetime(cls, v: dt.datetime) -> datetime:
        """Prices are given for the day ahead, so we should allow them to be in the future."""
        if _is_naive(v):
            raise ValueError(f"Missing timezone: {v}")
        if v < LOWER_DATETIME_BOUND:
            raise ValueError(f"Date is before 2000, this is not plausible: {v}")
        return v

    @validator("price")
    def _validate_price(cls, v: float | None) -> float:
        """Prices can be negative but not None, so we should only check for None values"""
        if v is None:
            raise ValueError(f"Price cannot be None: {v}")
        if math.isnan(v):
            raise ValueError(f"Price cannot be NaN: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float | None,
        currency: str,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> "Price | None":
        try:
            return Price(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                price=price,
                currency=currency,
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(
                f"Error(s) creating price Event {datetime}: {e}",
                extra={
                    "zoneKey": zoneKey,
                    "datetime": datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "kind": "price",
                },
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "currency": self.currency,
            "price": self.price,
            "source": self.source,
            "sourceType": self.sourceType,
        }


class LocationalMarginalPrice(Price):
    node: str

    @validator("node")
    def _validate_node(cls, v: str) -> str:
        clean_value = v.strip()
        if not clean_value:
            raise ValueError(f"Node cannot be an invalid string: {v}")
        if clean_value != v:
            raise ValueError(f"Node should not contain leading or trailing spaces: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float | None,
        currency: str,
        node: str,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> "LocationalMarginalPrice | None":
        try:
            return LocationalMarginalPrice(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                price=price,
                currency=currency,
                node=node,
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(
                f"Error(s) creating Locational Marginal Price Event {datetime}: {e}",
                extra={
                    "zoneKey": zoneKey,
                    "datetime": datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "kind": "Locational Marginal Price",
                },
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "currency": self.currency,
            "price": self.price,
            "node": self.node,
            "source": self.source,
            "sourceType": self.sourceType,
        }
