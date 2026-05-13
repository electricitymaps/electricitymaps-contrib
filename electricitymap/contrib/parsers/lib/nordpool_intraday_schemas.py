"""Pydantic v1 contract models for Nord Pool intraday ContractStatistics.

Strict mode (`extra='forbid'`): unknown fields raise ValidationError. The caller
(feeder-electricity in the EM monorepo) wires this into a Sentry alert.

Empirical drift catalog informing this schema:
  see notes/2026-05-11-nordpool-intraday-discovery/findings.md §2-§3 in the
  electricitymaps monorepo.
"""

from __future__ import annotations

from datetime import datetime

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
    contractOpenTime: datetime | None = None
    contractCloseTime: datetime | None = None
    highPrice: float | None = None
    lowPrice: float | None = None
    openPrice: float | None = None
    openTradeTime: datetime | None = None
    closePrice: float | None = None
    closeTradeTime: datetime | None = None
    averagePrice: float | None = None
    averagePriceLast1H: float | None = None
    averagePriceLast3H: float | None = None
    volume: float | None = None
    buyVolume: float | None = None
    sellVolume: float | None = None


class ContractStatisticsAreaResult(_StrictModel):
    priceUnit: str
    contracts: list[ContractStatistic]
    deliveryArea: str
    deliveryDateCET: str
    status: str
    volumeUnit: str
    updatedAt: datetime


class ContractStatisticsResponse(BaseModel):
    __root__: list[ContractStatisticsAreaResult]


STATS_AREAS: tuple[str, ...] = ("GER", "50Hz", "AMP", "TTG", "TBW")
