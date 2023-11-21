import json
import re
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

EGAT_GENERATION_URL = "https://www.sothailand.com/sysgen/ws/sysgen"
EGAT_URL = "www.egat.co.th"
MEA_BASEPRICE_URL = "https://www.mea.or.th/en/profile/109/111"
MEA_FT_URL = "https://www.mea.or.th/content/detail/2985/2987/474"
MEA_URL = "www.mea.or.th"
TZ = ZoneInfo("Asia/Bangkok")


def _as_localtime(dt: datetime) -> datetime:
    """
    If there is no datetime given, returns the current datetime with timezone.
    Otherwise, it interprets the datetime as the representation of local time
    since the API server supposes the local timezone instead of UTC.
    """
    if dt is None:
        return datetime.now(tz=TZ)
    return dt.astimezone(TZ)


def _seconds_to_time(target_datetime: datetime, seconds_in_day: int) -> datetime:
    """Convert a given seconds integer to a datetime value."""
    today = target_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    dt = today + timedelta(seconds=seconds_in_day)
    return dt


def _fetch_data(
    session: Session, target_datetime: datetime, data_type: str
) -> list[dict]:
    """Fetch actual or planning generation data from the EGAT API endpoint."""
    url = f"{EGAT_GENERATION_URL}/{data_type}"
    if target_datetime is None:
        target_datetime = _as_localtime(datetime.now())

    if data_type == "actual":
        params = {"name": "SYSTEM_GEN(MW)", "day": target_datetime.strftime("%d-%m-%Y")}
    elif data_type == "plan":
        params = {"day": target_datetime.strftime("%d-%m-%Y")}
    else:
        raise ParserException("TH.py", f"unexpected data_type: {data_type}", "TZ")

    # This API returns a list of 2-elements list
    # Example: [[0, 12345], [60, 12345.6], ...]
    # - The first integer is the seconds number since 00:00 am (i.e. 900 == 00:15 am)
    # - The second integer is the total generation (MW)
    raw_text = session.post(url, data=params).text

    # Fix programming error of the returned value.
    # This API server returns a invalid string if the list is empty.
    # e.g. {"id":"","name":"","day":"","timeStart":0,list:[],"count":0}
    raw_text = raw_text.replace(",list:", ',"list":')

    raw_data = json.loads(raw_text)["list"]

    data = []
    for item in raw_data:
        # The data structure of `item` is inconsistent.
        # If there is temperature data is available, `item` is 3-tuple.
        # Otherwise, it returns 2-tuple. So we cannot simply iterate `raw_data`.
        seconds_in_day = item[0]
        generation = item[1]

        dt = _seconds_to_time(target_datetime, seconds_in_day)
        data.append(
            {
                "datetime": dt,
                "generation": generation,
            }
        )

    return data


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "TH",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    session = session or Session()
    """Request the last known production mix (in MW) of a given country."""
    data = _fetch_data(session, _as_localtime(target_datetime), "actual")

    production = []
    for item in data:
        production.append(
            {
                "zoneKey": zone_key,
                "datetime": item["datetime"],
                # All mapped to 'unknown' because there is no available breakdown.
                "production": {"unknown": item["generation"]},
                "source": EGAT_URL,
            }
        )
    return production


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "TH",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """
    Gets consumption for a specified zone.

    We use the same value as the production for now.
    But it would be better to include exchanged electricity data if available.
    """
    session = session or Session()
    production = fetch_production(
        session=session, target_datetime=_as_localtime(target_datetime)
    )
    consumption = []
    for item in production:
        item["consumption"] = item["production"]["unknown"]
        del item["production"]
        consumption.append(item)
    return consumption


@refetch_frequency(timedelta(days=1))
def fetch_generation_forecast(
    zone_key: str = "TH",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Gets generation forecast for specified zone."""
    session = session or Session()
    data = _fetch_data(session, _as_localtime(target_datetime), "plan")

    production = []
    for item in data:
        production.append(
            {
                "zoneKey": zone_key,
                "datetime": item["datetime"],
                # All mapped to unknown as there is no available breakdown
                "production": {"unknown": item["generation"]},
                "source": EGAT_URL,
            }
        )
    return production


def fetch_price(
    zone_key: str = "TH",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """
    Fetch the base tariff data from the MEA (Unit in THB). This is then added up with
    Float Time (Ft) rate from another MEA's webpage (Unit in Satang (THB/100)).

    The Thai MEA/PEA Electicity Fee calculation are as follows:
    AmountDue = (BasePrice** + FtRate) * UnitAmountInKWh
    ActualDue = (AmountDue * 7%VAT) + FixedServiceFee

    * Time-of-Use (TOU) rate is uncommon and thus left unimplemented.
    **While actual BasePrice is done in a progressive manner, For Electricity Maps -
      we use "AmountDue" at 1MWh calculated at the highest pricing bracket for simplification.
    """
    session = session or Session()
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    # Fetch price from MEA table.
    # `price_base` is 'Over 400 kWh (up from 401st)' from Table 1.1
    with session.get(MEA_BASEPRICE_URL) as response:
        soup_base = BeautifulSoup(response.content, "lxml")

    if response.status_code != 200:
        raise ParserException(
            parser="TH.py",
            message=f"{MEA_BASEPRICE_URL} returned {response.status_code}",
            zone_key=zone_key,
        )

    unit_price_table = soup_base.find_all("table")[1]
    price_base = unit_price_table.find_all("td")[19].text

    # Available Ft pricing history dated back as far as September 2535 B.E. (1992 C.E.)
    # `price_ft` slot's is 0+(month number), additional +13 is needed if that slot is " "
    # For 2023 multi-Ft rates, we assumed the household rate.
    with session.get(MEA_FT_URL) as response:
        soup_ft = BeautifulSoup(response.content, "lxml")

    if response.status_code != 200:
        raise ParserException(
            parser="TH.py",
            message=f"{MEA_FT_URL} returned {response.status_code}",
            zone_key=zone_key,
        )

    ft_rate_table = soup_ft.find_all("table")[1]
    curr_ft_month = _as_localtime(datetime.now()).month
    price_ft = ft_rate_table.find_all("td")[curr_ft_month].text

    if price_ft == "\xa0":
        price_ft = ft_rate_table.find_all("td")[curr_ft_month + 13].text
    if "\n" in price_ft:
        price_ft = re.findall(r"\d+\.\d+", price_ft)[0]

    return {
        "zoneKey": zone_key,
        "currency": "THB",
        "datetime": _as_localtime(datetime.now()),
        "price": float(price_base) * 1000 + float(price_ft) * 10,
        "source": MEA_URL,
    }


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_consumption() ->")
    print(fetch_consumption())

    print("fetch_generation_forecast() ->")
    print(fetch_generation_forecast())

    print("fetch_price() ->")
    print(fetch_price())
