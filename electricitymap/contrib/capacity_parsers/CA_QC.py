from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

"""Disclaimer: only valid for real-time data, historical capacity is not available"""

MODE_MAPPING = {
    "Run-of-river": "hydro",
    "Reservoir": "hydro",
    "Gas-fired turbines": "gas",
    "Diesel": "oil",
    "Churchill Falls generating station â\x80\x94 Churchill Falls (Labrador) Corporation Limiteda": "hydro",
    "39\xa0wind farms operated by independent power producersb": "wind",
    "7\xa0biomass and 3\xa0biogas cogeneration plants operated by independent power producersc": "biomass",
    "5\xa0small hydropower plants operated by independent power producersb": "hydro",
    "Other suppliersd": "unknown",
}


def fetch_production_capacity(zone_key: ZoneKey, target_datetime: datetime) -> dict:
    r: Response = Session().get(
        "https://www.hydroquebec.com/generation/generating-stations.html"
    )
    soup = BeautifulSoup(r.text, "html.parser")
    all_capacity = []

    tables = soup.find_all("table")
    for table in tables:
        all_rows = table.find_all("tr")
        table_headers = [th.string for th in all_rows[0].find_all("th")]

        for row in all_rows:
            if len(row.find_all("td")):
                td = row.find_all("td")
                if "Watersheds" in table_headers:
                    pp_capacity = {
                        "mode": td[3].string,
                        "value": int(td[4].string.replace(",", "")),
                    }
                else:
                    pp_capacity = {
                        "mode": td[1].string,
                        "value": int(td[2].string.replace(",", "")),
                    }
                all_capacity.append(pp_capacity)

    table_others = soup.find_all("ul", attrs={"class": "hq-liste-donnees"})[0]

    all_rows = table_others.find_all("li")
    for row in all_rows[1:]:
        pp_capacity = {
            "mode": row.find("span", attrs={"class": "txt"}).text.strip(),
            "value": int(
                row.find("span", attrs={"class": "nbr"}).string[:-3].replace(",", "")
            ),
        }
        all_capacity.append(pp_capacity)
    capacity_dict = {}
    for item in all_capacity:
        mode = MODE_MAPPING[item["mode"]]
        if mode in capacity_dict:
            capacity_dict[mode]["value"] += item["value"]
        else:
            capacity_dict[mode] = {
                "datetime": datetime.now().strftime("%Y-01-01"),
                "value": item["value"],
                "source": "hydroquebec.com",
            }

    if capacity_dict:
        print(
            f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n {capacity_dict}"
        )
        return dict(sorted(capacity_dict.items()))
    else:
        raise ValueError(
            f"CA_QC: No capacity data available for {target_datetime.date()}"
        )


if __name__ == "__main__":
    fetch_production_capacity("CA-QC", datetime.now())
