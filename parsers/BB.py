from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

# The request library is used to fetch content through HTTP
import requests
from requests import Session
from requests.auth import AuthBase

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

SOURCE = "energy.gov.bb"
base_url = "https://dataservices.acelerex.com/api"


class JwtPublicAuth(AuthBase):
    def __init__(self):
        self.token = None

    def __call__(self, r):
        if self.token is None:
            self.token = self.get_token()
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r

    def get_token(self) -> str:
        url = base_url + "/authentication"
        response = requests.post(
            url, json={"dashboardId": "barbados", "strategy": "jwt-public"}
        )
        return response.json()["accessToken"]


def session_with_auth(session: Session) -> Session:
    if session.auth is None:
        session.auth = JwtPublicAuth()
    return session


def parse_operational_data(response_json) -> tuple[list[str], list[list[str]]]:
    header, *table = (x for x in response_json["data"][0]["data"]["data"] if len(x) > 1)
    return header, table


def fetch_operational_data(
    zone_key,
    session: Session,
    target_datetime: datetime | None,
    logger: Logger,
) -> pd.DataFrame:
    session = session_with_auth(session)

    params = {"name": "operational-data", "$sort[created_at]": -1}

    header = None
    table = None

    if target_datetime is None:
        data = session.get(base_url + "/barbados/uploads", params=params).json()
        header, table = parse_operational_data(data)
    elif target_datetime > datetime(year=2023, month=2, day=27):
        expected_date = target_datetime.astimezone(
            ZoneInfo("America/Barbados")
        ).strftime("%Y-%m-%d")

        for i in range(10):
            url_date = (
                (target_datetime + timedelta(days=i))
                .astimezone(ZoneInfo("America/Barbados"))
                .strftime("%Y-%m-%d")
            )
            params["created_at[$lt]"] = url_date
            data = session.get(base_url + "/barbados/uploads", params=params).json()
            header, table = parse_operational_data(data)
            if table[0][0][:10] == expected_date:
                break
            if table[0][0][:10] > expected_date:
                raise ParserException("BB.py", "Date not found", zone_key)
    else:
        raise ParserException(
            "BB.py",
            "This parser is not yet able to parse dates before 2023-02-27",
            zone_key,
        )

    if table is None or header is None:
        raise ParserException("BB.py", "No data found", zone_key)

    operational_data = pd.DataFrame(
        table,
        columns=header,
    )
    columns = [
        "24 hr monitored solar production",
        "24 hr monitored wind production",
        "24 hr storage charging",
        "24 hr storage discharging",
        "24 hr fossil production",
        "24 hr Net demand",
        "24 hr Curtailment",
    ]
    for columm in columns:
        operational_data[columm] = pd.to_numeric(operational_data[columm])
    return operational_data


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("BB"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    operational_data = fetch_operational_data(
        zone_key, session, target_datetime, logger
    )

    production_list = ProductionBreakdownList(logger=logger)

    for _index, row in operational_data.iterrows():
        production_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(row["datetime"]),
            production=ProductionMix(
                solar=row["24 hr monitored solar production"],
                wind=row["24 hr monitored wind production"],
                oil=row["24 hr fossil production"],
            ),
            storage=StorageMix(
                battery=(
                    row["24 hr storage discharging"] + row["24 hr storage charging"]
                )
                * -1
            ),
            source=SOURCE,
        )
    return production_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict[str, Any] | list[dict[str, Any]]:
    operational_data = fetch_operational_data(
        zone_key, session, target_datetime, logger
    )

    consumption_list = TotalConsumptionList(logger=logger)

    for _index, row in operational_data.iterrows():
        consumption_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(row["datetime"]),
            consumption=row["24 hr Net demand"],
            source=SOURCE,
        )
    return consumption_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Maps backend, but handy for testing."""

    print("fetch_production(XX) ->")
    print(fetch_production(ZoneKey("BB")))
    fetch_production(ZoneKey("BB"), target_datetime=datetime(2024, 2, 2))
    print("fetch_consumption(XX) ->")
    print(fetch_consumption(ZoneKey("BB")))
