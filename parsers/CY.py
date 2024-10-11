#!/usr/bin/env python3

import sys
from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

# BeautifulSoup is used to parse HTML
from bs4 import BeautifulSoup
from requests import Session

REALTIME_SOURCE = "https://tsoc.org.cy/electrical-system/total-daily-system-generation-on-the-transmission-system/"
HISTORICAL_SOURCE = "https://tsoc.org.cy/electrical-system/archive-total-daily-system-generation-on-the-transmission-system/?startdt={}&enddt=%2B1days"

TIMEZONE = ZoneInfo("Asia/Nicosia")


class CyprusParser:
    CAPACITY_KEYS = {
        "Συμβατική Εγκατεστημένη Ισχύς": "oil",
        "Αιολική Εγκατεστημένη Ισχύς": "wind",
        "Φωτοβολταϊκή Εγκατεστημένη Ισχύς": "solar",
        "Εγκατεστημένη Ισχύς Βιομάζας": "biomass",
    }

    session: Session
    logger: Logger

    def __init__(self, session, logger: Logger = getLogger(__name__)):
        self.session = session
        self.logger = logger

    def warn(self, text: str) -> None:
        self.logger.warning(text, extra={"key": "CY"})

    def parse_capacity(self, html) -> dict:
        capacity = {}
        table = html.find(id="production_graph_static_data2")
        for tr in table.find_all("tr"):
            values = [td.string for td in tr.find_all("td")]
            key = self.CAPACITY_KEYS.get(values[0])
            if key:
                capacity[key] = float(values[1])
        return capacity

    def parse_production(self, html, capacity: dict) -> list:
        data = []
        table = html.find(id="production_graph_data")
        columns = [th.string for th in table.find_all("th")]
        biomass_estimate = 0.0
        for tr in table.tbody.find_all("tr"):
            values = [td.string for td in tr.find_all("td")]
            if None in values or "" in values:
                break
            production = {}
            datum = {
                "zoneKey": "CY",
                "production": production,
                "capacity": capacity,
                "storage": {},
                "source": "tsoc.org.cy",
            }
            for col, val in zip(columns, values, strict=True):
                if col == "Timestamp":
                    datum["datetime"] = datetime.fromisoformat(val).replace(
                        tzinfo=TIMEZONE
                    )
                elif col == "Αιολική Παραγωγή":
                    production["wind"] = float(val)
                elif col == "Συμβατική Παραγωγή":
                    production["oil"] = float(val)
                elif col == "Εκτίμηση Διεσπαρμένης Παραγωγής":
                    # Because solar is explicitly listed as "Solar PV" (so no thermal with energy storage)
                    # and there is no sunlight between 10pm and 3am (https://www.timeanddate.com/sun/cyprus/nicosia),
                    # we use the nightly biomass+solar generation reported to determine the portion of biomass+solar
                    # which constitutes biomass.
                    value = float(val)
                    hour = datum["datetime"].hour
                    if hour < 3 or hour >= 22:
                        biomass_estimate = value
                    production["biomass"] = biomass_estimate
                    production["solar"] = max(value - biomass_estimate, 0.0)
            data.append(datum)
        return data

    def fetch_production(self, target_datetime: datetime | None) -> list:
        if target_datetime is None:
            url = REALTIME_SOURCE
        else:
            # convert target datetime to local datetime
            url_date = target_datetime.astimezone(TIMEZONE).strftime("%d-%m-%Y")
            url = HISTORICAL_SOURCE.format(url_date)

        res = self.session.get(url)
        assert (
            res.status_code == 200
        ), f"CY parser: GET {url} returned {res.status_code}"

        html = BeautifulSoup(res.text, "lxml")

        # Capacity is only available if we fetch data from realtime url
        capacity = self.parse_capacity(html) if url is REALTIME_SOURCE else {}
        data = self.parse_production(html, capacity)

        if len(data) == 0:
            self.warn("No production data returned for Cyprus")
        return data


def fetch_production(
    zone_key: str = "CY",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given country."""
    assert zone_key == "CY"

    parser = CyprusParser(session or Session(), logger)
    return parser.fetch_production(target_datetime)


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    target_datetime = None
    if len(sys.argv) == 4:
        target_datetime = datetime(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))

    print("fetch_production() ->")
    fetched_production = fetch_production(target_datetime=target_datetime)
    if isinstance(fetched_production, list):
        for datum in fetched_production:
            print(datum)
