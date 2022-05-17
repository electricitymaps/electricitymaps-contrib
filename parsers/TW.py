#!/usr/bin/env python3
from datetime import timedelta

import arrow
import dateutil
import pandas as pd
import requests

from parsers.lib.config import refetch_frequency


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key="TW", session=None, target_datetime=None, logger=None
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    url = "http://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary.txt"
    s = session or requests.Session()
    response = s.get(url)
    data = response.json()

    dumpDate = data[""]
    prodData = data["aaData"]

    tz = "Asia/Taipei"
    dumpDate = arrow.get(dumpDate, "YYYY-MM-DD HH:mm").replace(
        tzinfo=dateutil.tz.gettz(tz)
    )

    objData = pd.DataFrame(prodData)

    columns = [
        "fueltype",
        "additional_1",
        "name",
        "capacity",
        "output",
        "percentage",
        "additional_2",
    ]
    assert len(objData.iloc[0]) == len(columns), "number of input columns changed"
    objData.columns = columns

    objData["fueltype"] = objData.fueltype.str.split("(").str[1]
    objData["fueltype"] = objData.fueltype.str.split(")").str[0]
    objData.loc[:, ["capacity", "output"]] = objData[["capacity", "output"]].apply(
        pd.to_numeric, errors="coerce"
    )
    assert (
        not objData.capacity.isna().all()
    ), "capacity data is entirely NaN - input column order may have changed"
    assert (
        not objData.output.isna().all()
    ), "output data is entirely NaN - input column order may have changed"

    objData.drop(
        columns=["additional_1", "name", "additional_2", "percentage"],
        axis=1,
        inplace=True,
    )
    # summing because items in returned object are for each power plant and operational units
    production = pd.DataFrame(objData.groupby("fueltype").sum())
    production.columns = ["capacity", "output"]

    # check output values coincide with total capacity by fuel type
    check_values = production.output <= production.capacity
    assert check_values.loc[
        ~check_values.index.isin(["Co-Gen"])
    ].all(), "output > capacity"  # HACK: Co-Gen capacity is underestimated

    coal_capacity = (
        production.loc["Coal"].capacity + production.loc["IPP-Coal"].capacity
    )
    gas_capacity = production.loc["LNG"].capacity + production.loc["IPP-LNG"].capacity
    oil_capacity = production.loc["Oil"].capacity + production.loc["Diesel"].capacity

    coal_production = production.loc["Coal"].output + production.loc["IPP-Coal"].output
    gas_production = production.loc["LNG"].output + production.loc["IPP-LNG"].output
    oil_production = production.loc["Oil"].output + production.loc["Diesel"].output

    # For storage, note that load will be negative, and generation positive.
    # We require the opposite

    returndata = {
        "zoneKey": zone_key,
        "datetime": dumpDate.datetime,
        "production": {
            "coal": coal_production,
            "gas": gas_production,
            "oil": oil_production,
            "hydro": production.loc["Hydro"].output,
            "nuclear": production.loc["Nuclear"].output,
            "solar": production.loc["Solar"].output,
            "wind": production.loc["Wind"].output,
            "unknown": production.loc["Co-Gen"].output,
        },
        "capacity": {
            "coal": coal_capacity,
            "gas": gas_capacity,
            "oil": oil_capacity,
            "hydro": production.loc["Hydro"].capacity,
            "hydro storage": production.loc["Pumping Gen"].capacity,
            "nuclear": production.loc["Nuclear"].capacity,
            "solar": production.loc["Solar"].capacity,
            "wind": production.loc["Wind"].capacity,
            "unknown": production.loc["Co-Gen"].capacity,
        },
        "storage": {
            "hydro": -1 * production.loc["Pumping Load"].output
            - production.loc["Pumping Gen"].output
        },
        "source": "taipower.com.tw",
    }

    return returndata


if __name__ == "__main__":
    print(fetch_production())
