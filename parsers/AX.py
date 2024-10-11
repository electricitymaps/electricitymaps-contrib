from datetime import datetime, timedelta
from logging import Logger, getLogger
from re import findall
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

from .lib.exceptions import ParserException

IFRAME_URL = "https://grafik.kraftnat.ax/grafer/tot_inm_24h_15.php"
TIME_ZONE = ZoneInfo("Europe/Mariehamn")
SOURCE = "kraftnat.ax"


def fetch_data(session: Session, logger: Logger):
    """Fetch data from the iFrame."""

    response: Response = session.get(IFRAME_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser").find_all("script")
    result_time_series = findall(r"data: \[(.*?)\]", str(soup))
    if len(result_time_series) != 3:
        raise ParserException(
            "AX.py",
            "Did not find the expected amount of results. Check if the website has changed.",
        )
    time_series: list = result_time_series[0].split(",")
    raw_data: list[str] = findall(r"data:\[(.*?)\]", str(soup))
    if len(raw_data) != 6:
        raise ParserException(
            "AX.py",
            "The raw data did not match the expected format. Check if the website has changed.",
        )
    for raw in raw_data:
        if len(raw.split(",")) != len(time_series):
            raise ParserException(
                "AX.py",
                "The raw data did not match the length of the the time series. Check if the website has changed.",
            )
    data_list = []
    for time, sweden, alink, fossil, gustavs, wind, consumption in zip(
        time_series,
        raw_data[0].split(","),
        raw_data[1].split(","),
        raw_data[2].split(","),
        raw_data[3].split(","),
        raw_data[4].split(","),
        raw_data[5].split(","),
        strict=True,
    ):
        data_list.append(
            {
                "time": str(time.replace('"', "")),
                "sweden": float(sweden),
                "alink": float(alink),
                "fossil": float(fossil),
                "gustavs": float(gustavs),
                "wind": float(wind),
                "consumption": float(consumption),
            }
        )
    return data_list


def formatted_data(
    zone_key: ZoneKey | None,
    zone_key1: ZoneKey | None,
    zone_key2: ZoneKey | None,
    session: Session,
    logger: Logger,
    data_type: str,
):
    """Format data to Electricity Map standards."""
    data_list = fetch_data(session, logger)
    data_list.reverse()
    date_time = datetime.now(TIME_ZONE)
    date = date_time.replace(
        hour=int(data_list[0]["time"].split(":")[0]),
        minute=int(data_list[0]["time"].split(":")[1]),
        second=0,
        microsecond=0,
    )
    if date > date_time:
        date = date - timedelta(days=1)
    exchanges = ExchangeList(logger)
    production_breakdowns = ProductionBreakdownList(logger)
    consumption = TotalConsumptionList(logger)
    for data in data_list:
        corrected_date = date - timedelta(minutes=15 * data_list.index(data))
        if data_type == "production" and zone_key is not None:
            production_mix = ProductionMix(wind=data["wind"], oil=data["fossil"])
            production_breakdowns.append(
                datetime=corrected_date,
                production=production_mix,
                source=SOURCE,
                zoneKey=zone_key,
            )
        elif data_type == "consumption" and zone_key is not None:
            consumption.append(
                datetime=corrected_date,
                consumption=data["consumption"],
                source=SOURCE,
                zoneKey=zone_key,
            )
        elif data_type == "exchange":
            if zone_key1 == ZoneKey("AX") and zone_key2 == ZoneKey("SE-SE3"):
                exchanges.append(
                    datetime=corrected_date,
                    netFlow=data["sweden"] * -1,
                    source=SOURCE,
                    zoneKey=ZoneKey("AX->SE-SE3"),
                )
            elif zone_key1 == ZoneKey("AX") and zone_key2 == ZoneKey("FI"):
                exchanges.append(
                    datetime=corrected_date,
                    netFlow=round(data["alink"] + data["gustavs"], 2) * -1,
                    source=SOURCE,
                    zoneKey=ZoneKey("AX->FI"),
                )
            else:
                raise ParserException(
                    "AX.py",
                    "This parser can only fetch data between Åland <-> Sweden and Åland <-> Finland",
                )
        else:
            raise ParserException(
                "AX.py",
                "The datasource currently implemented is only for production, consumption and exchange data",
                zone_key,
            )

    if data_type == "production":
        return production_breakdowns.to_list()
    elif data_type == "consumption":
        return consumption.to_list()
    elif data_type == "exchange":
        return exchanges.to_list()
    else:
        raise ParserException(
            "AX.py",
            "The datasource currently implemented is only for production, consumption and exchange data",
            zone_key,
        )


def fetch_production(
    zone_key: ZoneKey = ZoneKey("AX"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Fetch production data."""

    if target_datetime is not None:
        raise ParserException(
            "AX.py", "The datasource currently implemented is only for real time data"
        )

    return formatted_data(
        zone_key=zone_key,
        zone_key1=None,
        zone_key2=None,
        session=session,
        logger=logger,
        data_type="production",
    )


def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("AX"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Fetch consumption data."""

    if target_datetime is not None:
        raise ParserException(
            "AX.py", "The datasource currently implemented is only for real time data"
        )

    return formatted_data(
        zone_key=zone_key,
        zone_key1=None,
        zone_key2=None,
        session=session,
        logger=logger,
        data_type="consumption",
    )


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Fetch exchange data."""

    if target_datetime is not None:
        raise ParserException(
            "AX.py", "The datasource currently implemented is only for real time data"
        )

    return formatted_data(
        zone_key=None,
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
        logger=logger,
        data_type="exchange",
    )
