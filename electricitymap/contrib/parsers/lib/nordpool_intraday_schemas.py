"""Pydantic v1 contract models for Nord Pool intraday ContractStatistics.

Strict mode (`extra='forbid'`): unknown fields raise ValidationError. The caller
(feeder-electricity in the EM monorepo) wires this into a Sentry alert.

Empirical drift catalog informing this schema:
  see notes/2026-05-11-nordpool-intraday-discovery/findings.md §2-§3 in the
  electricitymaps monorepo.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class _StrictModel(BaseModel):
    class Config:
        extra = "forbid"


class ContractStatistic(_StrictModel):
    deliveryStart: datetime
    deliveryEnd: datetime
    isLocalContract: bool
    contractId: str
    contractName: str
    contractOpenTime: Optional[datetime] = None
    contractCloseTime: Optional[datetime] = None
    highPrice: Optional[float] = None
    lowPrice: Optional[float] = None
    openPrice: Optional[float] = None
    openTradeTime: Optional[datetime] = None
    closePrice: Optional[float] = None
    closeTradeTime: Optional[datetime] = None
    averagePrice: Optional[float] = None
    averagePriceLast1H: Optional[float] = None
    averagePriceLast3H: Optional[float] = None
    volume: Optional[float] = None
    buyVolume: Optional[float] = None
    sellVolume: Optional[float] = None


class ContractStatisticsAreaResult(_StrictModel):
    priceUnit: str
    contracts: List[ContractStatistic]
    deliveryArea: str
    deliveryDateCET: str
    status: str
    volumeUnit: str
    updatedAt: datetime


class ContractStatisticsResponse(BaseModel):
    __root__: List[ContractStatisticsAreaResult]


STATS_AREAS: tuple = ("GER", "50Hz", "AMP", "TTG", "TBW")
