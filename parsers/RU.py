#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
from functools import reduce

import arrow
import pandas as pd
import requests

# RU-1: European and Uralian Market Zone (Price Zone 1)
# RU-2: Siberian Market Zone (Price Zone 2)
# RU-AS: Russia East Power System (2nd synchronous zone)
# Handling of hours: data at t on API side corresponds to
# production / consumption from t to t+1

# http://br.so-ups.ru is not available outside Russia (sometimes?), use a reverse proxy in Russia
HOST = "https://858127-cc16935.tmweb.ru"
BASE_EXCHANGE_URL = f"${HOST}/webapi/api/flowDiagramm/GetData?"

MAP_GENERATION_1 = {
    "P_AES": "nuclear",
    "P_GES": "hydro",
    "P_GRES": "unknown",
    "P_TES": "unknown",
    "P_BS": "unknown",
    "P_REN": "solar",
}
MAP_GENERATION_2 = {"aes_gen": "nuclear", "ges_gen": "hydro", "P_tes": "unknown"}

exchange_ids = {
    "RU-AS->CN": 764,
    "RU->MN": 276,
    "RU-2->MN": 276,
    "RU->KZ": 785,
    "RU-1->KZ": 2394,
    "RU-2->KZ": 344,
    "RU-2->RU-1": 139,
    "RU->GE": 752,
    "RU-1->GE": 752,
    "AZ->RU": 598,
    "AZ->RU-1": 598,
    "BY->RU": 321,
    "BY->RU-1": 321,
    "RU->FI": 187,
    "RU-1->FI": 187,
    "RU-KGD->LT": 212,
    "RU-1->UA-CR": 5688,
    "UA->RU-1": 880,
}

# Each exchange is contained in a div tag with a "data-id" attribute that is unique.


tz = "Europe/Moscow"


def fetch_production(
    zone_key="RU", session=None, target_datetime=None, logger=None
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    if zone_key == "RU":
        # Get data for all zones
        dfs = {}
        for subzone_key in ["RU-1", "RU-2", "RU-AS"]:
            data = fetch_production(subzone_key, session, target_datetime, logger)
            df = pd.DataFrame(data).set_index("datetime")
            df_prod = df["production"].apply(pd.Series).fillna(0)

            # Set a 30 minutes frequency
            if subzone_key in ["RU-1", "RU-2"]:
                df_30m_index = df_prod.index.union(
                    df_prod.index + pd.Timedelta(minutes=30)
                )
                df_prod = df_prod.reindex(df_30m_index).ffill()

            dfs[subzone_key] = df_prod

        # Compute the sum
        df_prod = reduce(lambda x, y: x + y, dfs.values()).dropna()

        # Format to dict
        df_prod = df_prod.apply(dict, axis=1).reset_index(name="production")
        df_prod["zoneKey"] = "RU"
        df_prod["storage"] = [{} for i in range(len(df_prod))]
        df_prod["source"] = "so-ups.ru"
        data = df_prod.to_dict("records")
        for row in data:
            row["datetime"] = row["datetime"].to_pydatetime()

        return data

    elif zone_key == "RU-1" or zone_key == "RU-2":
        return fetch_production_1st_synchronous_zone(zone_key, session, target_datetime)
    elif zone_key == "RU-AS":
        return fetch_production_2nd_synchronous_zone(zone_key, session, target_datetime)
    else:
        raise NotImplementedError("This parser is not able to parse given zone")


def fetch_production_1st_synchronous_zone(
    zone_key="RU-1", session=None, target_datetime=None
) -> list:
    zone_key_price_zone_mapper = {
        "RU-1": 1,
        "RU-2": 2,
    }
    if zone_key not in zone_key_price_zone_mapper:
        raise NotImplementedError("This parser is not able to parse given zone")

    if target_datetime:
        target_datetime_tz = arrow.get(target_datetime).to(tz)
    else:
        target_datetime_tz = arrow.now(tz)
    # Query at t gives production from t to t+1
    # I need to shift 1 to get the last value at t
    datetime_to_fetch = target_datetime_tz.shift(hours=-1)
    date = datetime_to_fetch.format("YYYY.MM.DD")

    r = session or requests.session()

    price_zone = zone_key_price_zone_mapper[zone_key]
    base_url = "{}/webapi/api/CommonInfo/PowerGeneration?priceZone[]={}".format(
        HOST, price_zone
    )
    url = base_url + "&startDate={date}&endDate={date}".format(date=date)

    response = r.get(url, verify=False)
    json_content = json.loads(response.text)
    dataset = json_content[0]["m_Item2"]

    data = []
    for datapoint in dataset:
        row = {
            "zoneKey": zone_key,
            "production": {},
            "storage": {},
            "source": "so-ups.ru",
        }

        for k, production_type in MAP_GENERATION_1.items():
            if k in datapoint:
                gen_value = float(datapoint[k]) if datapoint[k] else 0.0
                row["production"][production_type] = (
                    row["production"].get(production_type, 0.0) + gen_value
                )
            else:
                row["production"][production_type] = row["production"].get(
                    production_type, 0.0
                )

        # Date
        hour = "%02d" % (int(datapoint["INTERVAL"]))
        datetime = arrow.get("%s %s" % (date, hour), "YYYY.MM.DD HH", tzinfo=tz)
        row["datetime"] = datetime.datetime
        last_dt = arrow.now(tz).shift(hours=-1).datetime

        # Drop datapoints in the future
        if row["datetime"] > last_dt:
            continue

        # Default values
        row["production"]["biomass"] = None
        row["production"]["geothermal"] = None

        data.append(row)

    return data


def fetch_production_2nd_synchronous_zone(
    zone_key="RU-AS", session=None, target_datetime=None
) -> dict:
    if zone_key != "RU-AS":
        raise NotImplementedError("This parser is not able to parse given zone")

    if target_datetime:
        target_datetime_tz = arrow.get(target_datetime).to(tz)
    else:
        target_datetime_tz = arrow.now(tz)
    # Here we should shift 30 minutes but it would be inconsistent with 1st zone
    datetime_to_fetch = target_datetime_tz.shift(hours=-1)
    date = datetime_to_fetch.format("YYYY.MM.DD")

    r = session or requests.session()

    url = "{}/webapi/api/CommonInfo/GenEquipOptions_Z2?oesTerritory[]=540000&startDate={}".format(
        HOST, date
    )

    response = r.get(url, verify=False)
    json_content = json.loads(response.text)
    dataset = json_content[0]["m_Item2"]

    data = []
    for datapoint in dataset:
        row = {
            "zoneKey": zone_key,
            "production": {},
            "storage": {},
            "source": "so-ups.ru",
        }

        for k, production_type in MAP_GENERATION_2.items():
            if k in datapoint:
                gen_value = float(datapoint[k]) if datapoint[k] else 0.0
                row["production"][production_type] = (
                    row["production"].get(production_type, 0.0) + gen_value
                )
            else:
                row["production"][production_type] = row["production"].get(
                    production_type, 0.0
                )

        # Date
        hour = datapoint["fHour"]

        if len(hour) == 1:
            hour = "0" + hour

        datetime = arrow.get("%s %s" % (date, hour), "YYYY.MM.DD HH", tzinfo=tz)
        row["datetime"] = datetime.datetime
        last_dt = arrow.now(tz).shift(minutes=-30).datetime

        # Drop datapoints in the future
        if row["datetime"] > last_dt:
            continue

        # Default values
        row["production"]["biomass"] = None
        row["production"]["geothermal"] = None
        row["production"]["solar"] = None

        data.append(row)

    return data


def response_checker(json_content) -> bool:
    flow_values = json_content["Flows"]

    if not flow_values:
        return False

    non_zero = False
    for item in flow_values:
        if item["Id"] in list(exchange_ids.values()):
            if item["NumValue"] == 0.0:
                continue
            else:
                non_zero = True
                break

    return non_zero


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> list:
    """Requests the last known power exchange (in MW) between two zones."""
    if target_datetime:
        today = arrow.get(target_datetime, "YYYYMMDD")
    else:
        today = arrow.utcnow()

    date = today.format("YYYY-MM-DD")
    r = session or requests.session()
    DATE = "Date={}".format(date)

    exchange_urls = []
    if target_datetime:
        for hour in range(0, 24):
            url = BASE_EXCHANGE_URL + DATE + "&Hour={}".format(hour)
            exchange_urls.append((url, hour))
    else:
        # Only fetch last 2 hours when not fetching historical data.
        for shift in range(0, 2):
            hour = today.shift(hours=-shift).format("HH")
            url = BASE_EXCHANGE_URL + DATE + "&Hour={}".format(hour)
            exchange_urls.append((url, int(hour)))

    datapoints = []
    for url, hour in exchange_urls:
        response = r.get(url, verify=False)
        json_content = json.loads(response.text)

        if response_checker(json_content):
            datapoints.append((json_content["Flows"], hour))
        else:
            # data not yet available for this hour
            continue

    sortedcodes = "->".join(sorted([zone_key1, zone_key2]))
    reversesortedcodes = "->".join(sorted([zone_key1, zone_key2], reverse=True))

    if sortedcodes in exchange_ids.keys():
        exchange_id = exchange_ids[sortedcodes]
        direction = 1
    elif reversesortedcodes in exchange_ids.keys():
        exchange_id = exchange_ids[reversesortedcodes]
        direction = -1
    else:
        raise NotImplementedError("This exchange pair is not implemented.")

    data = []
    for datapoint, hour in datapoints:
        try:
            exchange = [item for item in datapoint if item["Id"] == exchange_id][0]
            flow = exchange.get("NumValue") * direction
        except KeyError:
            # flow is unknown or not available
            flow = None

        dt = today.replace(hour=hour).floor("hour").datetime

        exchange = {
            "sortedZoneKeys": sortedcodes,
            "datetime": dt,
            "netFlow": flow,
            "source": "so-ups.ru",
        }

        data.append(exchange)

    return data


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_production(RU-1) ->")
    print(fetch_production("RU-1"))
    print("fetch_production(RU-2) ->")
    print(fetch_production("RU-2"))
    print("fetch_production(RU-AS) ->")
    print(fetch_production("RU-AS"))
    print("fetch_exchange(CN, RU-AS) ->")
    print(fetch_exchange("CN", "RU-AS"))
    print("fetch_exchange(MN, RU) ->")
    print(fetch_exchange("MN", "RU"))
    print("fetch_exchange(MN, RU-2) ->")
    print(fetch_exchange("MN", "RU-2"))
    print("fetch_exchange(KZ, RU) ->")
    print(fetch_exchange("KZ", "RU"))
    print("fetch_exchange(KZ, RU-1) ->")
    print(fetch_exchange("KZ", "RU-1"))
    print("fetch_exchange(KZ, RU-2) ->")
    print(fetch_exchange("KZ", "RU-2"))
    print("fetch_exchange(GE, RU) ->")
    print(fetch_exchange("GE", "RU"))
    print("fetch_exchange(GE, RU-1) ->")
    print(fetch_exchange("GE", "RU-1"))
    print("fetch_exchange(AZ, RU) ->")
    print(fetch_exchange("AZ", "RU"))
    print("fetch_exchange(AZ, RU-1) ->")
    print(fetch_exchange("AZ", "RU-1"))
    print("fetch_exchange(BY, RU) ->")
    print(fetch_exchange("BY", "RU"))
    print("fetch_exchange(BY, RU-1) ->")
    print(fetch_exchange("BY", "RU-1"))
    print("fetch_exchange(RU-1, UA-CR) ->")
    print(fetch_exchange("RU-1", "UA-CR"))
    print("fetch_exchange(RU-1, UA) ->")
    print(fetch_exchange("RU-1", "UA"))
    print("fetch_exchange(RU-1, RU-2) ->")
    print(fetch_exchange("RU-1", "RU-2"))
