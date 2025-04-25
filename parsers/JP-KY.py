#!/usr/bin/env python3
import io
import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd

# The request library is used to fetch content through HTTP
from requests import Session, get

from parsers import occtonet

TIMEZONE = ZoneInfo("Asia/Tokyo")


def fetch_production(
    zone_key: str = "JP-KY",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict | list:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = {
        "zoneKey": zone_key,
        "datetime": None,
        "production": {
            "biomass": 0,
            "coal": 0,
            "gas": 0,
            "hydro": None,
            "nuclear": None,
            "oil": 0,
            "solar": None,
            "wind": None,
            "geothermal": None,
            "unknown": 0,
        },
        "storage": {},
        "source": "www.kyuden.co.jp",
    }

    # url for consumption and solar
    url = f"https://www.kyuden.co.jp/td_power_usages/csv/juyo-hourly-{datetime.now(tz=TIMEZONE).strftime('%Y%m%d')}.csv"
    response = get(url)
    content = response.text

    # Filter out the irrelevant data
    start_idx = content.rfind("DATE,TIME")
    if start_idx == -1:
        logger.error(
            "Could not find time series data section in solar and consumption CSV"
        )
        return []
    time_series_section = content[start_idx:]
    df = pd.read_csv(io.StringIO(time_series_section))

    # Translate column names to english
    df.columns = ["DATE", "TIME", "consumption", "solar"]

    last_complete_row = df.dropna().iloc[-1]

    dt = datetime.strptime(
        f"{last_complete_row['DATE']} {last_complete_row['TIME']}", "%Y/%m/%d %H:%M"
    )
    dt = dt.replace(tzinfo=TIMEZONE)
    data["datetime"] = dt

    # Get values in MW - convert from 10000 kW to MW
    consumption = last_complete_row["consumption"].astype(float) * 10
    solar = last_complete_row["solar"].astype(float) * 10

    # add two nuclear power plants at Sendai and Genkai
    sendai_url = (
        "http://www.kyuden.co.jp/php/nuclear/sendai/rename.php?"
        "A=s_power.fdat&B=ncp_state.fdat&_=1520532401043"
    )
    genkai_url = (
        "http://www.kyuden.co.jp/php/nuclear/genkai/rename.php?"
        "A=g_power.fdat&B=ncp_state.fdat&_=1520532904073"
    )

    sendai_raw_text = get(sendai_url).text
    genkai_raw_text = get(genkai_url).text

    regex = r"(?<=gouki=)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*" + r"(?:[eE][-+]?\d+)?(?=&)"
    sendai_values = re.findall(regex, sendai_raw_text)
    genkai_values = re.findall(regex, genkai_raw_text)

    sendai_total = sum(map(float, sendai_values))
    genkai_total = sum(map(float, genkai_values))

    nuclear = sendai_total + genkai_total
    # convert from 万kW to MW
    nuclear *= 10

    # add the exchange JP-CG->JP-KY
    exchanges = occtonet.fetch_exchange("JP-KY", "JP-CG")
    # find the nearest exchanges in time to consumption timestamp
    nearest_exchanges = sorted(
        exchanges, key=lambda exchange: abs(exchange["datetime"] - dt)
    )
    # take the nearest exchange
    exchange = nearest_exchanges[0]
    # check that consumption and exchange timestamps are within a 15 minute window
    if abs(dt - exchange["datetime"]).seconds <= 900:
        generation = consumption - exchange["netFlow"]
        unknown = generation - nuclear - solar
        data["production"]["solar"] = solar
        data["production"]["nuclear"] = nuclear
        data["production"]["unknown"] = unknown

        return data
    else:
        return []


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
