from abc import ABC, abstractmethod
from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from electricitymap.contrib.lib.models.events import (
    Event,
    EventSourceType,
    Exchange,
    Price,
    ProductionBreakdown,
    ProductionMix,
    StorageMix,
    TotalConsumption,
    TotalProduction,
)
from electricitymap.contrib.lib.types import ZoneKey


class EventList(ABC):
    """A wrapper around Events lists."""

    logger: Logger
    events: List[Event]

    def __init__(self, logger: Logger):
        self.events = []
        self.logger = logger

    @abstractmethod
    def append(self, **kwargs):
        """Handles creation of events and adding it to the batch."""
        # TODO Handle one day the creation of mixed batches.
        pass

    def to_list(self) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in self.events]


class ExchangeList(EventList):
    events: List[Exchange]

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        netFlow: float,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = Exchange.create(
            self.logger, zoneKey, datetime, source, netFlow, sourceType
        )
        if event:
            self.events.append(event)


class ProductionBreakdownList(EventList):
    events: List[ProductionBreakdown]

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        production: Optional[ProductionMix] = None,
        storage: Optional[StorageMix] = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = ProductionBreakdown.create(
            self.logger, zoneKey, datetime, source, production, storage, sourceType
        )
        if event:
            self.events.append(event)

    @staticmethod
    def merge_production_breakdowns(
        ungrouped_production_breakdowns: List["ProductionBreakdownList"],
        logger: Logger,
    ) -> "ProductionBreakdownList":
        """
        Given multiple parser outputs, sum the production and storage
        of corresponding datetimes to create a unique production breakdown list.
        Sources will be aggregated in a comma-separated string. Ex: "entsoe, eia".
        There should be only one zone in the list of production breakdowns.
        """
        if len(ungrouped_production_breakdowns) == 0:
            return ProductionBreakdownList(logger)
        if all(
            len(breakdowns.events) == 0
            for breakdowns in ungrouped_production_breakdowns
        ):
            logger.warning("All production breakdowns are empty.")
            return ProductionBreakdownList(logger)

        # Create a dataframe for each parser output, then flatten the power mixes.
        prod_and_storage_dfs = [
            pd.json_normalize(breakdowns.to_list()).set_index("datetime")
            for breakdowns in ungrouped_production_breakdowns
            if len(breakdowns.events) > 0
        ]
        df = pd.concat(prod_and_storage_dfs)
        sources = df["source"].unique()
        sources = ", ".join(sources)
        zones = df["zoneKey"].unique()
        if len(zones) != 1:
            raise ValueError(
                f"Trying to merge production outputs from multiple zones \
                , got {len(zones)}: {', '.join(zones)}"
            )
        source_types = df["sourceType"].unique()
        if len(source_types) != 1:
            raise ValueError(
                f"Trying to merge production outputs from multiple source types \
                , got {len(source_types)}: {', '.join(source_types)}"
            )

        def aggregate(value: pd.Series) -> Union[List[str], Optional[float]]:
            """An internal aggregation function taking care of corrected modes."""
            if value.name == "corrected_modes":
                aggregated_modes = set()
                for corrected_modes in value:
                    if corrected_modes is not None:
                        aggregated_modes.update(set(corrected_modes))
                return list(aggregated_modes)
            if value.isnull().all():
                # We don't want to return a zero if all are None or NaN.
                return None
            return value.sum()

        df = df.drop(columns=["source", "sourceType", "zoneKey"])
        df = df.groupby(level=0, dropna=False).agg(aggregate)
        result = ProductionBreakdownList(logger)
        for row in df.iterrows():
            production_mix = ProductionMix()
            storage_mix = StorageMix()
            for key, value in row[1].items():
                if str(key).startswith("production.") or str(key).startswith(
                    "storage."
                ):
                    # NaN values can arise from the aggregation. We want to keep them as None.
                    # We do this at the last step to avoid changing the object type of the dataframe.
                    if value is not None and np.isnan(value):
                        value = None
                    # The key is in the form of "production.<mode>" or "storage.<mode>"
                    prefix, mode = key.split(".")  # type: ignore
                    if prefix == "production":
                        if mode in row[1]["correctedModes"]:
                            # This is just to mark this mode as corrected, the value is not used.
                            production_mix.set_value(mode, -1)
                        production_mix.set_value(mode, value)
                    elif prefix == "storage":
                        storage_mix.set_value(mode, value)
            result.append(
                zones[0],
                row[0].to_pydatetime(),  # type: ignore
                sources,
                production_mix,
                storage_mix,
                source_types[0],
            )
        return result


class TotalProductionList(EventList):
    events: List[TotalProduction]

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = TotalProduction.create(
            self.logger, zoneKey, datetime, source, value, sourceType
        )
        if event:
            self.events.append(event)


class TotalConsumptionList(EventList):
    events: List[TotalConsumption]

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = TotalConsumption.create(
            self.logger, zoneKey, datetime, source, consumption, sourceType
        )
        if event:
            self.events.append(event)


class PriceList(EventList):
    events: List[Price]

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float,
        currency: str,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = Price.create(
            self.logger, zoneKey, datetime, source, price, currency, sourceType
        )
        if event:
            self.events.append(event)
