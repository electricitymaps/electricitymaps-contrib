from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import PriceList
from electricitymap.contrib.types import ZoneKey

ZONE_KEY = ZoneKey("ID")
TZ = ZoneInfo("Asia/Jakarta")
SOURCE = "pln.co.id"

# ESDM established this rate for October-December 2020, reducing the previous
# IDR 1,467/kWh low-voltage tariff to IDR 1,444.70/kWh for customers including
# R-1/TR households with 1,300 VA and 2,200 VA connections:
# https://www.esdm.go.id/id/media-center/arsip-berita/menteri-esdm-tetapkan-tarif-listrik-pelanggan-tegangan-rendah-nonsubsidi-turun
# The official PLN tariff adjustment for July-September 2026 confirms that the
# R-1/TR 1,300 VA and 2,200 VA residential tariff remains unchanged:
# https://www.pln.co.id/webapi/media/file/webkorp/asset/1fa2814b-6ffd-459b-ac16-d46e515a0b3b.pdf
# Electricity Maps prices are expressed per MWh.
RESIDENTIAL_TARIFF_IDR_PER_MWH = 1_444.70 * 1_000
TARIFF_EFFECTIVE_AT = datetime(2020, 10, 1, tzinfo=TZ)


def fetch_price(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Return PLN's latest known non-subsidized residential electricity tariff."""
    if target_datetime is None:
        target_datetime = datetime.now(tz=TZ)
    elif target_datetime.tzinfo is None:
        raise ValueError("target_datetime must be timezone-aware")
    else:
        target_datetime = target_datetime.astimezone(TZ)

    if target_datetime < TARIFF_EFFECTIVE_AT:
        raise NotImplementedError(
            "Indonesia price data is not available before 2020-10-01"
        )

    prices = PriceList(logger=logger)
    prices.append(
        zoneKey=zone_key,
        datetime=target_datetime.replace(minute=0, second=0, microsecond=0),
        source=SOURCE,
        price=RESIDENTIAL_TARIFF_IDR_PER_MWH,
        currency="IDR",
    )
    return prices.to_list()
