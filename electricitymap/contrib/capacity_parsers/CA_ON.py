from datetime import datetime

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

MODE_MAPPING = {
    "Nuclear": "nuclear",
    "Hydroelectric": "hydro",
    "Gas/Oil": "gas",
    "Wind": "wind",
    "Biofuel": "biomass",
    "Solar": "solar",
}


def fetch_production_capacity(zone_key: ZoneKey, target_datetime: datetime):
    url = f"https://www.ieso.ca/-/media/Files/IESO/Document-Library/planning-forecasts/reliability-outlook/ReliabilityOutlookTables_{target_datetime.strftime('%Y%b')}.ashx"
    r: Response = Session().get(url)
    if r.status_code == 200:
        df = pd.read_excel(r.url, sheet_name="Table 4.1", header=4, skipfooter=3)
        df = df.rename(
            columns={"Fuel Type": "mode", "Total Installed Capacity\n(MW)": "value"}
        )
        df = df[["mode", "value"]]
        df["mode"] = df["mode"].apply(lambda x: MODE_MAPPING[x])
        capacity = {}
        for idx, data in df.iterrows():
            capacity[data["mode"]] = {
                "datetime": target_datetime.strftime("%Y-%m-%d"),
                "value": round(data["value"], 2),
                "source": "ieso.ca",
            }
        print(
            f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{capacity}"
        )
        return capacity
    else:
        raise ValueError(
            f"Failed to fetch capacity data for IESO at {target_datetime.strftime('%Y-%m')}"
        )
