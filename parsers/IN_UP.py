import json
from ast import literal_eval

import arrow
from requests import Session

from .lib import web

URL = "http://www.upsldc.org/real-time-data"


def fetch_data(zone_key="IN-UP", session=None):

    time_now = arrow.now(tz="Asia/Kolkata")

    HTML_PARAMS = {
        "p_p_id": "upgenerationsummary_WAR_UPSLDCDynamicDisplayportlet",
        "p_p_lifecycle": 2,
        "p_p_state": "normal",
        "p_p_mode": "view",
        "p_p_resource_id": "realtimedata",
        "p_p_cacheability": "cacheLevelPage",
        "p_p_col_id": "column-1",
        "p_p_col_count": 1,
        "_upgenerationsummary_WAR_UPSLDCDynamicDisplayportlet_time": time_now,
        "_upgenerationsummary_WAR_UPSLDCDynamicDisplayportlet_cmd": "realtimedata",
    }

    KEY_MAP = {
        "total hydro generation": "hydro",
        "total thermal up generation": "unknown",
        "cogen-sent out": "unknown",
        "solar generation": "solar",
        "total up load/demand": "demand",
    }

    response_objects = literal_eval(
        web.get_response_with_params(
            zone_key,
            URL,
            session,
            params=HTML_PARAMS,
        ).text.lower()
    )
    india_date = arrow.get(
        json.loads(list(response_objects[1].values())[0])["time_val"],
        "M/D/YYYY h:m",
        tzinfo="Asia/Kolkata",
    )

    value_map = {
        "date": india_date.datetime,
        "production": {
            "solar": None,
            "hydro": None,
            "geothermal": None,
            "wind": None,
            "gas": None,
            "coal": None,
            "unknown": None,
        },
        "consumption": {"demand": None},
    }

    for obj in response_objects:
        val = json.loads(list(obj.values())[0])
        if "point_desc" in val and val["point_desc"] in KEY_MAP:
            if KEY_MAP[val["point_desc"]] == "demand":
                value_map["consumption"]["demand"] = float(val["point_val"])
            else:
                check = value_map["production"][KEY_MAP[val["point_desc"]]]
                if check is None:
                    value_map["production"][KEY_MAP[val["point_desc"]]] = float(
                        val["point_val"]
                    )
                else:
                    value_map["production"][KEY_MAP[val["point_desc"]]] += float(
                        val["point_val"]
                    )

    return value_map


def fetch_production(zone_key, session=None, target_datetime=None, logger=None):
    """Get production data of Uttar Pradesh."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    value_map = fetch_data(zone_key, session)

    data = {
        "zoneKey": zone_key,
        "datetime": value_map.get("date"),
        "production": value_map.get("production"),
        "storage": {"hydro": None},
        "source": "upsldc.org",
    }

    return data


def fetch_consumption(zone_key, session=None, target_datetime=None, logger=None):
    """Get consumption data of Uttar Pradesh."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    value_map = fetch_data(zone_key, session)

    data = {
        "zoneKey": zone_key,
        "datetime": value_map.get("date"),
        "consumption": value_map["consumption"].get("demand"),
        "source": "upsldc.org",
    }

    return data


if __name__ == "__main__":
    session = Session()
    print(fetch_production("IN-UP", session))
    print(fetch_consumption("IN-UP", session))
