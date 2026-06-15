from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from itertools import pairwise
from logging import Logger
from operator import itemgetter
from typing import Any, Generic, TypeVar

import pandas as pd

from electricitymap.contrib.lib.models.events import (
    Event,
    EventSourceType,
    Exchange,
    ExchangeAtc,
    ExchangeCapacity,
    GridAlert,
    GridAlertType,
    IntradayContractStatistics,
    LocationalMarginalPrice,
    Price,
    ProductionBreakdown,
    ProductionMix,
    StorageMix,
    TotalConsumption,
    TotalProduction,
)
from electricitymap.contrib.types import AtcType, ZoneKey

EventType = TypeVar("EventType", bound="Event")


class EventList(ABC, Generic[EventType]):
    """
    A wrapper around Events lists.
    Events are indexed by datetimes.
    """

    logger: Logger
    events: list[EventType]

    def __init__(self, logger: Logger):
        self.events = []
        self.logger = logger

    def __len__(self):
        return len(self.events)

    def __contains__(self, datetime) -> bool:
        return any(event.datetime == datetime for event in self.events)

    def __setitem__(self, datetime, event: EventType):
        self.events[self.events.index(self[datetime])] = event

    def __add__(self, other: "EventList") -> "EventList":
        new_list = self.__class__(self.logger)
        new_list.events = self.events + other.events
        return new_list

    def __getitem__(self, datetime) -> EventType:
        return next(event for event in self.events if event.datetime == datetime)

    def __iter__(self):
        return iter(self.events)

    @abstractmethod
    def append(self, **kwargs):
        """Handles creation of events and adding it to the batch."""
        # TODO Handle one day the creation of mixed batches.
        pass

    def to_list(self) -> list[dict[str, Any]]:
        return sorted(
            [event.to_dict() for event in self.events], key=itemgetter("datetime")
        )

    @property
    def dataframe(self) -> pd.DataFrame:
        """Gives the dataframe representation of the events, indexed by datetime."""
        return pd.DataFrame.from_records(
            [
                {
                    "datetime": event.datetime,
                    "zoneKey": event.zoneKey,
                    "source": event.source,
                    "sourceType": event.sourceType,
                    "data": event,
                }
                for event in self.events
                if len(self.events) > 0
            ]
        ).set_index("datetime")


class AggregatableEventList(EventList[EventType], ABC, Generic[EventType]):
    """An abstract class to supercharge event lists with aggregation capabilities."""

    @classmethod
    def is_completely_empty(
        cls, ungrouped_events: Sequence["AggregatableEventList"], logger: Logger
    ) -> bool:
        """Checks if the lists to be merged have any data."""
        if len(ungrouped_events) == 0:
            return True
        if all(len(event_list.events) == 0 for event_list in ungrouped_events):
            logger.warning(f"All {cls.__name__} are empty.")
            return True
        return False

    @classmethod
    def get_zone_source_type(
        cls,
        events: pd.DataFrame,
    ) -> tuple[ZoneKey, str, EventSourceType]:
        """
        Given a concatenated dataframe of events, return the unique zone, the aggregated sources and the unique source type.
        Raises an error if there are multiple zones or source types.
        It assumes that zoneKey, source and sourceType are present in the dataframe's columns.
        """
        return (
            AggregatableEventList._get_unique_zone(events),
            AggregatableEventList._get_aggregated_sources(events),
            AggregatableEventList._get_unique_source_type(events),
        )

    @classmethod
    def _get_unique_zone(cls, events: pd.DataFrame) -> ZoneKey:
        """
        Given a concatenated dataframe of events, return the unique zone.
        Raises an error if there are multiple zones.
        It assumes that `zoneKey` is present in the dataframe's columns.
        """
        zones = events["zoneKey"].unique()
        if len(zones) != 1:
            raise ValueError(
                f"Trying to merge {cls.__name__} from multiple zones \
                , got {len(zones)}: {', '.join(zones)}"
            )
        return zones[0]

    @classmethod
    def _get_aggregated_sources(cls, events: pd.DataFrame) -> str:
        """
        Given a concatenated dataframe of events, return the aggregated sources.
        It assumes that `source` is present in the dataframe's columns.
        """
        sources = events["source"].unique()
        sources = ", ".join(sources)
        return sources

    @classmethod
    def _get_unique_source_type(cls, events: pd.DataFrame) -> EventSourceType:
        """
        Given a concatenated dataframe of events, return the unique source type.
        Raises an error if there are multiple source types.
        It assumes that `sourceType` is present in the dataframe's columns.
        """
        source_types = events["sourceType"].unique()
        if len(source_types) != 1:
            raise ValueError(
                f"Trying to merge {cls.__name__} from multiple source types \
                , got {len(source_types)}: {', '.join(source_types)}"
            )
        return source_types[0]


class NonOverlappingEventList(EventList[EventType], ABC, Generic[EventType]):
    """An EventList representing a single time series, where at most one event
    should cover any given instant.

    Mixed into list types whose events must not overlap (exchanges, production,
    consumption, prices, exchange capacity). `to_list()` resolves events whose
    `[datetime, end_datetime)` intervals intersect by clamping the earlier
    event's end to the later event's start. Events sharing the exact same
    `datetime` cannot be clamped, so they are kept as-is; both cases log a
    warning — a data imperfection should degrade the output, not crash the
    whole fetch. Lists that legitimately hold several events per datetime —
    e.g. locational marginal prices keyed by node, or grid alerts — do NOT use
    this mixin.
    """

    def to_list(self) -> list[dict[str, Any]]:
        return self._resolve_overlaps(super().to_list())

    def _resolve_overlaps(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Clamps overlapping `[datetime, end_datetime)` intervals in place.

        `events` is sorted by start (`datetime`); a pair overlaps when the
        earlier event's `end_datetime` is strictly after the later event's
        `datetime`. Events without an `end_datetime` are treated as
        instantaneous points at `datetime`. Because the events are
        start-sorted, checking consecutive pairs is enough to catch any
        overlap. Clamping always leaves a positive duration, as the earlier
        event starts strictly before the later one.
        """
        for previous, current in pairwise(events):
            if previous["datetime"] == current["datetime"]:
                self.logger.warning(
                    f"{type(self).__name__} has two events sharing datetime "
                    f"{current['datetime']}; keeping both."
                )
                continue
            previous_end = previous["end_datetime"]
            if previous_end is not None and previous_end > current["datetime"]:
                self.logger.warning(
                    f"{type(self).__name__} interval ending {previous_end} "
                    f"overlaps the event starting {current['datetime']}; "
                    f"clamping its end to {current['datetime']}."
                )
                previous["end_datetime"] = current["datetime"]
        return events


class ExchangeList(NonOverlappingEventList[Exchange], AggregatableEventList[Exchange]):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        netFlow: float | None,
        *,
        end_datetime: datetime | None = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = Exchange.create(
            self.logger, zoneKey, datetime, end_datetime, source, netFlow, sourceType
        )
        if event:
            self.events.append(event)

    @staticmethod
    def merge_exchanges(
        ungrouped_exchanges: list["ExchangeList"], logger: Logger
    ) -> "ExchangeList":
        """
        Given multiple parser outputs, sum the netflows of corresponding datetimes
        to create a unique exchange list. Sources will be aggregated in a
        comma-separated string. Ex: "entsoe, eia".
        """
        exchanges = ExchangeList(logger)
        if ExchangeList.is_completely_empty(ungrouped_exchanges, logger):
            return exchanges

        # Create a dataframe for each parser output, then flatten the exchanges.
        exchange_dfs = [
            pd.json_normalize(exchanges.to_list()).set_index("datetime")
            for exchanges in ungrouped_exchanges
            if len(exchanges.events) > 0
        ]

        exchange_df = pd.concat(exchange_dfs)
        exchange_df = exchange_df.rename(columns={"sortedZoneKeys": "zoneKey"})
        zone_key, sources, source_type = ExchangeList.get_zone_source_type(exchange_df)

        end_datetimes = None
        if "end_datetime" in exchange_df.columns:
            # When sources disagree (e.g. one reports 15-minute and another
            # hourly intervals), keep the earliest end: it is deterministic and
            # the finest resolution cannot overlap the next merged point.
            end_datetimes = exchange_df.groupby(level="datetime")["end_datetime"].min()

        exchange_df = exchange_df.groupby(level="datetime", dropna=False).sum(
            numeric_only=True,
        )
        for dt, row in exchange_df.iterrows():
            end_datetime = None
            if end_datetimes is not None:
                val = end_datetimes.get(dt)
                if not pd.isna(val):
                    end_datetime = val.to_pydatetime()

            exchanges.append(
                zoneKey=zone_key,
                datetime=dt.to_pydatetime(),
                source=sources,
                netFlow=row["netFlow"],
                end_datetime=end_datetime,
                sourceType=source_type,
            )

        return exchanges

    @staticmethod
    def update_exchanges(
        exchanges: "ExchangeList", new_exchanges: "ExchangeList", logger: Logger
    ) -> "ExchangeList":
        """Given a new batch of exchanges, update the existing ones."""
        if len(new_exchanges) == 0:
            return exchanges
        elif len(exchanges) == 0:
            return new_exchanges

        for new_event in new_exchanges.events:
            if new_event.datetime in exchanges:
                existing_event = exchanges[new_event.datetime]
                updated_event = Exchange._update(existing_event, new_event)
                exchanges[new_event.datetime] = updated_event
            else:
                exchanges.append(
                    new_event.zoneKey,
                    new_event.datetime,
                    new_event.source,
                    new_event.netFlow,
                    end_datetime=new_event.end_datetime,
                    sourceType=new_event.sourceType,
                )

        return exchanges


class ExchangeCapacityList(NonOverlappingEventList[ExchangeCapacity]):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        capacityExport: float | None,
        capacityImport: float | None,
        *,
        end_datetime: datetime | None = None,
        sourceType: EventSourceType = EventSourceType.published,
    ):
        event = ExchangeCapacity.create(
            self.logger,
            zoneKey,
            datetime,
            end_datetime,
            source,
            capacityExport,
            capacityImport,
            sourceType,
        )
        if event:
            self.events.append(event)


class ExchangeAtcList(EventList[ExchangeAtc]):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        capacityExport: float | None,
        capacityImport: float | None,
        atcType: AtcType,
        *,
        end_datetime: datetime | None = None,
        sourceType: EventSourceType = EventSourceType.published,
    ):
        event = ExchangeAtc.create(
            self.logger,
            zoneKey,
            datetime,
            end_datetime,
            source,
            capacityExport,
            capacityImport,
            atcType,
            sourceType,
        )
        if event:
            self.events.append(event)


class ProductionBreakdownList(
    NonOverlappingEventList[ProductionBreakdown],
    AggregatableEventList[ProductionBreakdown],
):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        *,
        end_datetime: datetime | None = None,
        production: ProductionMix | None = None,
        storage: StorageMix | None = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = ProductionBreakdown.create(
            self.logger,
            zoneKey,
            datetime,
            end_datetime,
            source,
            production,
            storage,
            sourceType,
        )
        if event:
            self.events.append(event)

    @staticmethod
    def merge_production_breakdowns(
        ungrouped_production_breakdowns: list["ProductionBreakdownList"],
        logger: Logger,
        matching_timestamps_only: bool = False,
    ) -> "ProductionBreakdownList":
        """
        Given multiple parser outputs, sum the production and storage
        of corresponding datetimes to create a unique production breakdown list.
        Sources will be aggregated in a comma-separated string. Ex: "entsoe, eia".
        There should be only one zone in the list of production breakdowns.
        Matching timestamps only will only keep the timestamps where all the production breakdowns have data.
        """
        production_breakdowns = ProductionBreakdownList(logger)
        if ProductionBreakdownList.is_completely_empty(
            ungrouped_production_breakdowns, logger
        ):
            return production_breakdowns
        len_ungrouped_production_breakdowns = len(ungrouped_production_breakdowns)
        df = pd.concat(
            [
                production_breakdowns.dataframe
                for production_breakdowns in ungrouped_production_breakdowns
                if len(production_breakdowns.events) > 0
            ]
        )
        _, _, _ = ProductionBreakdownList.get_zone_source_type(df)

        df = df.drop(columns=["source", "sourceType", "zoneKey"])
        df = df.groupby(level=0, dropna=False)["data"].apply(list)
        if matching_timestamps_only:
            logger.info(
                f"Filtering production breakdowns to keep \
                only the timestamps where all the production breakdowns \
                have data, {len(df[df.apply(lambda x: len(x) != len_ungrouped_production_breakdowns)])}\
                points where discarded."
            )
            df = df[df.apply(lambda x: len(x) == len_ungrouped_production_breakdowns)]
        for row in df:
            prod = ProductionBreakdown.aggregate(row)
            production_breakdowns.events.append(prod)
        return production_breakdowns

    @staticmethod
    def update_production_breakdowns(
        production_breakdowns: "ProductionBreakdownList",
        new_production_breakdowns: "ProductionBreakdownList",
        logger: Logger,
        matching_timestamps_only: bool = False,
    ) -> "ProductionBreakdownList":
        """
        Given a new batch of production breakdowns, update the existing ones.

        Params:
        - production_breakdowns: The existing production breakdowns to be updated.
        - new_production_breakdowns: The new batch of production breakdowns.
        - logger: The logger object used for logging information.
        - matching_timestamps_only: Flag indicating whether to update only the events with matching timestamps from both the production breakdowns.
        """

        if len(new_production_breakdowns) == 0:
            return production_breakdowns
        elif len(production_breakdowns) == 0:
            return new_production_breakdowns

        updated_production_breakdowns = ProductionBreakdownList(logger)

        if matching_timestamps_only:
            diff = abs(len(new_production_breakdowns) - len(production_breakdowns))
            logger.info(
                f"Filtering production breakdowns to keep only the events where both the production breakdowns have matching datetimes, {diff} events where discarded."
            )

        for new_event in new_production_breakdowns.events:
            if new_event.datetime in production_breakdowns:
                existing_event = production_breakdowns[new_event.datetime]
                updated_event = ProductionBreakdown._update(existing_event, new_event)
                updated_production_breakdowns.append(
                    updated_event.zoneKey,
                    updated_event.datetime,
                    updated_event.source,
                    end_datetime=updated_event.end_datetime,
                    production=updated_event.production,
                    storage=updated_event.storage,
                    sourceType=updated_event.sourceType,
                )
            elif matching_timestamps_only is False:
                updated_production_breakdowns.append(
                    new_event.zoneKey,
                    new_event.datetime,
                    new_event.source,
                    end_datetime=new_event.end_datetime,
                    production=new_event.production,
                    storage=new_event.storage,
                    sourceType=new_event.sourceType,
                )

        if matching_timestamps_only is False:
            for existing_event in production_breakdowns.events:
                if existing_event.datetime not in new_production_breakdowns:
                    updated_production_breakdowns.append(
                        existing_event.zoneKey,
                        existing_event.datetime,
                        existing_event.source,
                        end_datetime=existing_event.end_datetime,
                        production=existing_event.production,
                        storage=existing_event.storage,
                        sourceType=existing_event.sourceType,
                    )

        return updated_production_breakdowns


class TotalProductionList(
    NonOverlappingEventList[TotalProduction], AggregatableEventList[TotalProduction]
):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float | None,
        *,
        end_datetime: datetime | None = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = TotalProduction.create(
            self.logger, zoneKey, datetime, end_datetime, source, value, sourceType
        )
        if event:
            self.events.append(event)

    @staticmethod
    def merge_total_production_lists(
        ungrouped_production_lists: list["TotalProductionList"],
        logger: Logger,
    ) -> "TotalProductionList":
        """
        Given multiple parser outputs, sum the production of corresponding datetimes
        to create a unique production list. Sources will be aggregated in a
        comma-separated string. Ex: "entsoe, eia".
        """
        production_list = TotalProductionList(logger)
        if TotalProductionList.is_completely_empty(ungrouped_production_lists, logger):
            return production_list

        # Create a dataframe for each parser output, then flatten the production.
        production_dfs = [
            pd.json_normalize(production.to_list()).set_index("datetime")
            for production in ungrouped_production_lists
            if len(production.events) > 0
        ]

        production_df = pd.concat(production_dfs)

        zone_key, sources, source_type = TotalProductionList.get_zone_source_type(
            production_df
        )

        end_datetimes = None
        if "end_datetime" in production_df.columns:
            # When sources disagree, keep the earliest end (see merge_exchanges).
            end_datetimes = production_df.groupby(level="datetime")[
                "end_datetime"
            ].min()

        production_df = production_df.groupby(level="datetime", dropna=False).sum(
            numeric_only=True
        )
        for dt, row in production_df.iterrows():
            end_datetime = None
            if end_datetimes is not None:
                val = end_datetimes.get(dt)
                if not pd.isna(val):
                    end_datetime = val.to_pydatetime()

            production_list.append(
                zoneKey=zone_key,
                datetime=dt.to_pydatetime(),
                source=sources,
                value=row["value"],
                end_datetime=end_datetime,
                sourceType=source_type,
            )

        return production_list


class TotalConsumptionList(
    NonOverlappingEventList[TotalConsumption], AggregatableEventList[TotalConsumption]
):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float | None,
        *,
        end_datetime: datetime | None = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = TotalConsumption.create(
            self.logger,
            zoneKey,
            datetime,
            end_datetime,
            source,
            consumption,
            sourceType,
        )
        if event:
            self.events.append(event)

    @staticmethod
    def merge_consumption_lists(
        ungrouped_consumption_lists: list["TotalConsumptionList"],
        logger: Logger,
    ) -> "TotalConsumptionList":
        """
        Given multiple parser outputs, sum the consumption of corresponding datetimes
        to create a unique consumption list. Sources will be aggregated in a
        comma-separated string. Ex: "entsoe, eia".
        """
        consumption_list = TotalConsumptionList(logger)
        if TotalConsumptionList.is_completely_empty(
            ungrouped_consumption_lists, logger
        ):
            return consumption_list

        # Create a dataframe for each parser output, then flatten the consumption.
        consumption_dfs = [
            pd.json_normalize(consumption.to_list()).set_index("datetime")
            for consumption in ungrouped_consumption_lists
            if len(consumption.events) > 0
        ]

        consumption_df = pd.concat(consumption_dfs)

        zone_key, sources, source_type = TotalConsumptionList.get_zone_source_type(
            consumption_df
        )

        end_datetimes = None
        if "end_datetime" in consumption_df.columns:
            # When sources disagree, keep the earliest end (see merge_exchanges).
            end_datetimes = consumption_df.groupby(level="datetime")[
                "end_datetime"
            ].min()

        consumption_df = consumption_df.groupby(level="datetime", dropna=False).sum(
            numeric_only=True
        )
        for dt, row in consumption_df.iterrows():
            end_datetime = None
            if end_datetimes is not None:
                val = end_datetimes.get(dt)
                if not pd.isna(val):
                    end_datetime = val.to_pydatetime()

            consumption_list.append(
                zoneKey=zone_key,
                datetime=dt.to_pydatetime(),
                source=sources,
                consumption=row["consumption"],
                end_datetime=end_datetime,
                sourceType=source_type,
            )

        return consumption_list


class PriceList(NonOverlappingEventList[Price]):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float | None,
        currency: str,
        *,
        end_datetime: datetime | None = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = Price.create(
            self.logger,
            zoneKey,
            datetime,
            end_datetime,
            source,
            price,
            currency,
            sourceType,
        )
        if event:
            self.events.append(event)


class LocationalMarginalPriceList(EventList[LocationalMarginalPrice]):
    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float | None,
        currency: str,
        node: str,
        *,
        end_datetime: datetime | None = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = LocationalMarginalPrice.create(
            self.logger,
            zoneKey,
            datetime,
            end_datetime,
            source,
            price,
            currency,
            node,
            sourceType,
        )
        if event:
            self.events.append(event)


class GridAlertList(EventList[GridAlert]):
    def append(
        self,
        zoneKey: ZoneKey,
        locationRegion: str | None,
        source: str,
        alertType: GridAlertType,
        message: str,
        issuedTime: datetime,
        startTime: datetime | None,
        endTime: datetime | None,
    ):
        event = GridAlert.create(
            self.logger,
            zoneKey,
            locationRegion,
            source,
            alertType,
            message,
            issuedTime,
            startTime,
            endTime,
        )
        if event:
            self.events.append(event)


class IntradayContractStatisticsList(EventList[IntradayContractStatistics]):
    def append(  # type: ignore[override]
        self,
        zoneKey: ZoneKey,
        area: str,
        apiUpdatedAt: datetime,
        currency: str,
        priceUnitRaw: str,
        deliveryStart: datetime,
        deliveryEnd: datetime,
        contractId: str,
        contractName: str,
        contractOpenTime: datetime | None,
        contractCloseTime: datetime | None,
        isLocalContract: bool,
        vwap: float | None,
        vwap1hBeforeClose: float | None,
        vwap3hBeforeClose: float | None,
        openPrice: float | None,
        closePrice: float | None,
        highPrice: float | None,
        lowPrice: float | None,
        openTradeTime: datetime | None,
        closeTradeTime: datetime | None,
        volume: float | None,
        buyVolume: float | None,
        sellVolume: float | None,
        source: str,
        sourceType: EventSourceType = EventSourceType.published,
    ):
        event = IntradayContractStatistics.create(
            logger=self.logger,
            zoneKey=zoneKey,
            area=area,
            apiUpdatedAt=apiUpdatedAt,
            currency=currency,
            priceUnitRaw=priceUnitRaw,
            deliveryStart=deliveryStart,
            deliveryEnd=deliveryEnd,
            contractId=contractId,
            contractName=contractName,
            contractOpenTime=contractOpenTime,
            contractCloseTime=contractCloseTime,
            isLocalContract=isLocalContract,
            vwap=vwap,
            vwap1hBeforeClose=vwap1hBeforeClose,
            vwap3hBeforeClose=vwap3hBeforeClose,
            openPrice=openPrice,
            closePrice=closePrice,
            highPrice=highPrice,
            lowPrice=lowPrice,
            openTradeTime=openTradeTime,
            closeTradeTime=closeTradeTime,
            volume=volume,
            buyVolume=buyVolume,
            sellVolume=sellVolume,
            source=source,
            sourceType=sourceType,
        )
        if event:
            self.events.append(event)

    def to_list(self) -> list[dict[str, Any]]:
        """Sort by (deliveryStart, area, contractId) instead of 'datetime' key."""
        return sorted(
            [event.to_dict() for event in self.events],
            key=lambda d: (d["deliveryStart"], d["area"], d["contractId"]),
        )
