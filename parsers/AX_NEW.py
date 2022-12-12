from datetime import datetime
from logging import Logger, getLogger
from typing import Optional
from requests import Response, Session
from bs4 import BeautifulSoup
from re import findall

IFRAME_URL = "https://grafik.kraftnat.ax/grafer/tot_inm_24h_15.php"


def fetch_data(session: Session, logger: Logger):
    """Fetch data from the iFrame."""

    response: Response = session.get(IFRAME_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser").find_all("script")
    time_series = findall(r"data: \[(.*?)\]", str(soup))[0]
    raw_data = findall(r"data:\[(.*?)\]", str(soup))
    data_list = []
    for time, sweden, alink, fossil, gustavs, wind, consumption in zip(
        time_series.split(","),
        raw_data[0].split(","),
        raw_data[1].split(","),
        raw_data[2].split(","),
        raw_data[3].split(","),
        raw_data[4].split(","),
        raw_data[5].split(","),
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


def fetch_production(
    zone_key: str = "AX",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Fetch production from the iFrame."""

    if target_datetime is not None:
        raise NotImplementedError(
            "The datasource currently implemented is only real time"
        )

    data = fetch_data(session, logger)

    return data
