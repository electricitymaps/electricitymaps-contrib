#!/usr/bin/env python3

from datetime import date, datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException

TIMEZONE = ZoneInfo("Asia/Singapore")

# Backend of the charts on https://www.home.emcsg.com/. Given a `fromDate`, each
# dataset covers the 7 days before it. History goes back to 2024.
DATASYNC_URL = "https://www.home.emcsg.com/api/DataSync/Get"
DAILY_GENERATION_SHARE = 9  # daily share (%) of each generator type
HALF_HOURLY_PRICE_DEMAND = 14  # half-hourly USEP ($/MWh) and demand (MW)

SOURCE = "emcsg.com"

"""
Around 95% of Singapore's generation is done with combined-cycle gas turbines.

Resources:

- https://www.ema.gov.sg/Statistics.aspx particularly filtering by "Generation"
The most recent document at time of writing is
https://www.ema.gov.sg/cmsmedia/Publications_and_Statistics/Statistics/27RSU.pdf
It says that between January 2016 and March 2017, non-gas monthly generation breakdown has been 0.7% to 1.4% coal,
0.1% to 1.0% "petroleum products" (excluding an exceptional value of 3.9% in Nov 2016),
and 2.7% to 3.4% "other", which includes among others waste-to-energy and solar.

- Write-up of energy statistics in 2015 and first half of 2016:
https://www.ema.gov.sg/cmsmedia/Publications_and_Statistics/Publications/SES/2016/Singapore%20Energy%20Statistics%202016.pdf
(referred to as "Singapore Energy Statistics 2016" below)
It states among others "In 2015, [natural gas] accounted for about 95% of fuel mix,
comparable with that recorded in 2014. Petroleum products, mainly in the form of diesel and fuel oil,
made up 0.7% of the fuel mix. Other energy products (e.g. municipal waste, coal and biomass)
accounted for 2.9% while the remaining 1.2% was from coal", and that steam turbines in Singapore
"typically run on fuel oil and diesel'

EMC publishes generation shares for "CCGT/COGEN/TRIGEN", "GT", "ST", "IMPORT" and "ESS".
I take the first three to mean combined-cycle gas turbines/co-generation/tri-generation,
single-cycle gas turbines (following the Energy Statistics 2016 pg 24), and steam turbines respectively.
There is no information on fuel for steam turbines.

For Electricity Map, we map CCGT and GT to gas, ST to "unknown" and ESS (energy storage systems) to battery.
IMPORT is left out: imports are not production, and the interconnection to Malaysia is implemented in MY_WM.py.

Shares are only published per day, so the half-hourly production is the half-hourly demand
split by the share of that day. Solar is mostly embedded (behind the meter), so it isn't part of
that demand and is added on top, from EMC's estimate.
"""

TYPE_MAPPINGS = {"CCGT/COGEN/TRIGEN": "gas", "GT": "gas", "ST": "unknown"}


def _fetch_datasets(
    session: Session, value: int, end: date
) -> tuple[list[str], dict[str, list[str]]]:
    """Returns the labels and datasets (label -> values) of the 7 days up to `end` included."""
    from_date = (end + timedelta(days=1)).isoformat()
    response = session.get(
        DATASYNC_URL,
        params={"value": value, "fromDate": from_date, "toDate": from_date},
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    blocks = response.json()["data"]["data"]
    if not blocks:
        raise ParserException("SG.py", f"No data from EMC up to {end}", ZoneKey("SG"))
    return blocks[0]["labels"], {
        dataset["label"]: dataset["data"] for dataset in blocks[0]["datasets"]
    }


def _parse_label(label: str, end: date) -> datetime:
    """Turns labels like "03 Nov" or "03 Nov 00:00-00:30" into the (period start) datetime.

    Labels have no year, so we take the one that puts the label on or before `end`.
    """
    day, month, *period = label.split(" ")
    start = period[0].split("-")[0] if period else "00:00"
    dt = datetime.strptime(f"{day} {month} {end.year} {start}", "%d %b %Y %H:%M")
    if dt.date() > end:
        dt = dt.replace(year=end.year - 1)
    return dt.replace(tzinfo=TIMEZONE)


def _end_date(target_datetime: datetime | None) -> date:
    """The last day to fetch: the target day, or yesterday as today isn't published yet."""
    if target_datetime is None:
        return datetime.now(tz=TIMEZONE).date() - timedelta(days=1)
    return target_datetime.astimezone(TIMEZONE).date()


@refetch_frequency(timedelta(days=7))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("SG"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the half-hourly production mix (in MW) of Singapore for the past week."""
    session = session or Session()
    end = _end_date(target_datetime)

    share_days, shares = _fetch_datasets(session, DAILY_GENERATION_SHARE, end)
    shares_by_day = {
        _parse_label(day, end).date(): {
            gen_type: float(values[i]) / 100 for gen_type, values in shares.items()
        }
        for i, day in enumerate(share_days)
    }
    periods, datasets = _fetch_datasets(session, HALF_HOURLY_PRICE_DEMAND, end)
    # "Solar" is stacked on top of demand on EMC's chart: it is demand plus the estimated
    # (embedded) solar output. It is empty in older data.
    demand_with_solar = datasets.get("Solar") or [None] * len(periods)

    production_breakdowns = ProductionBreakdownList(logger)
    for period, demand, with_solar in zip(
        periods, datasets["Demand"], demand_with_solar, strict=True
    ):
        dt = _parse_label(period, end)
        day_shares = shares_by_day.get(dt.date())
        if day_shares is None or demand is None:
            continue
        demand_mw = float(demand)

        mix = ProductionMix()
        storage = StorageMix()
        for gen_type, share in day_shares.items():
            if gen_type == "IMPORT":
                continue
            if gen_type == "ESS":
                # Discharge is a positive share, storage is positive when charging.
                storage.add_value("battery", -share * demand_mw)
            elif gen_type in TYPE_MAPPINGS:
                mix.add_value(TYPE_MAPPINGS[gen_type], share * demand_mw)
            else:
                logger.warning(
                    f'Singapore has unrecognized generation type "{gen_type}" '
                    f"with production share {share:.2%}"
                )
                mix.add_value("unknown", share * demand_mw)
        if with_solar is not None:
            mix.add_value("solar", float(with_solar) - demand_mw)

        production_breakdowns.append(
            datetime=dt,
            zoneKey=zone_key,
            production=mix,
            storage=storage,
            source=SOURCE,
        )
    return production_breakdowns.to_list()


@refetch_frequency(timedelta(days=7))
def fetch_price(
    zone_key: ZoneKey = ZoneKey("SG"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Requests the half-hourly power prices in Singapore (USEP) for the past week.

    See https://www.nems.emcsg.com/Guide-To-Prices for details of what different prices in the data source mean.
    We use USEP here: "The Uniform Singapore Energy Price (USEP) is the uniform price of energy
    that applies for settlement purposes for all energy injections or withdrawals that are deemed to occur
    at the Singapore hub. It is the weighted-average of the nodal prices at all off-take nodes in each half hour."
    """
    end = _end_date(target_datetime)
    periods, datasets = _fetch_datasets(
        session or Session(), HALF_HOURLY_PRICE_DEMAND, end
    )

    price_list = PriceList(logger)
    for period, price in zip(periods, datasets["USEP"], strict=True):
        if price is None:
            continue
        price_list.append(
            zoneKey=zone_key,
            datetime=_parse_label(period, end),
            currency="SGD",
            price=float(price),
            source=SOURCE,
        )
    return price_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print('fetch_price("SG") ->')
    print(fetch_price("SG"))
