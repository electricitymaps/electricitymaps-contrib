
import json
from datetime import datetime

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

"""Disclaimer: only valid for real-time data, historical capacity is not available"""

MODE_MAPPING = {"Gas": "gas", "Water": "hydro", "Coal": "coal", "Solar": "solar"}


def fetch_production_capacity(zone_key:ZoneKey, target_datetime: datetime) -> dict:
    url = "https://www.gso.org.my/SystemData/PowerStation.aspx/GetDataSource"

    headers = {
        "Content-Type": "application/json",
        "Origin": "https://www.gso.org.my",
        "Referer": "https://www.gso.org.my/SystemData/PowerStation.aspx",
    }

    r: Response = Session().post(url, headers=headers)

    if r.status_code == 200:
        data = pd.DataFrame(json.loads(r.json()["d"]))
        data = data[["PPAExpiry", "Fuel", "Capacity (MW)"]]
        data = data.rename(
            columns={
                "PPAExpiry": "expiry_datetime",
                "Fuel": "mode",
                "Capacity (MW)": "value",
            }
        )
        data["mode"] = data["mode"].apply(lambda x: x.strip())
        data["mode"] = data["mode"].apply(lambda x: MODE_MAPPING[x])
        data["expiry_datetime"] = data["expiry_datetime"].apply(
            lambda x: pd.to_datetime(x).replace(day=31, month=12)
        )

        filtered_data = data.loc[data["expiry_datetime"] > target_datetime]
        filtered_data = filtered_data.groupby(["mode"])[["value"]].sum().reset_index()

        capacity_dict = {}
        for idx, data in filtered_data.iterrows():
            capacity_dict[data["mode"]] = {
                "value": data["value"],
                "source": "gso.org.my",
                "datetime": target_datetime.strftime("%Y-%m-%d"),
            }
        print(f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{capacity_dict}")
        return capacity_dict
    else:
        raise ValueError(
            f"Failed to fetch capacity data for GSO at {target_datetime.strftime('%Y-%m')}"
        )

if __name__ == "__main__":
    fetch_production_capacity("MY-WM", datetime(2023,1,1))