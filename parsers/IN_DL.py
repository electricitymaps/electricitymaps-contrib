#!/usr/bin/env python3

from requests import Session

from .lib import IN, web, zonekey

plants = {
    "CCGT-Bawana": "Gas",
    "DMSWSL-Dsidc": "G2E",
    "EDWPL-Gazipur": "G2E",
    "GT": "Gas",
    "Pragati": "Gas",
    "TOWMP-Okhla": "G2E",
}


def fetch_consumption(
    zone_key="IN-DL", session=None, target_datetime=None, logger=None
) -> dict:
    """Fetch Delhi consumption"""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    zonekey.assert_zone_key(zone_key, "IN-DL")
    html = web.get_response_soup(
        zone_key, "http://www.delhisldc.org/Redirect.aspx", session
    )

    india_date_time = IN.read_datetime_from_span_id(
        html, "DynamicData1_LblDate", "DD-MMM-YYYY hh:mm:ss A"
    )

    demand_value = IN.read_value_from_span_id(html, "DynamicData1_LblLoad")

    data = {
        "zoneKey": zone_key,
        "datetime": india_date_time.datetime,
        "consumption": demand_value,
        "source": "delhisldc.org",
    }

    return data


def fetch_production(
    zone_key="IN-DL", session=None, target_datetime=None, logger=None
) -> dict:
    """Fetch Delhi production"""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    energy = {"Gas": 0, "G2E": 0, "Coal": 0}

    zonekey.assert_zone_key(zone_key, "IN-DL")

    html = web.get_response_soup(
        zone_key, "http://www.delhisldc.org/Redirect.aspx?Loc=0804", session
    )

    india_date_string = IN.read_text_from_span_id(html, "ContentPlaceHolder3_ddgenco")
    india_date_time = IN.read_datetime_with_only_time(india_date_string, "HH:mm:ss")

    prod_table = html.find("table", {"id": "ContentPlaceHolder3_dgenco"})
    prod_rows = prod_table.findAll("tr")

    for plant in range(1, len(plants) + 1):
        energy[plants[read_name(prod_rows[plant])]] += read_value(prod_rows[plant])

    data = {
        "zoneKey": zone_key,
        "datetime": india_date_time.datetime,
        "production": {
            "coal": energy["Coal"],
            "gas": energy["Gas"],
            "biomass": energy["G2E"],
        },
        "source": "delhisldc.org",
    }

    return data


def read_value(row, index=2):
    value = float(row.findAll("td")[index].text)
    return value if value >= 0.0 else 0.0


def read_name(row, index=0):
    return row.findAll("td")[index].text


if __name__ == "__main__":
    session = Session()
    print(fetch_production("IN-DL", session))
    print(fetch_consumption("IN-DL", session))
