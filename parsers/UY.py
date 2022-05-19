#!/usr/bin/python3

import re

import arrow
import dateutil
import requests

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup

tz = "America/Montevideo"

MAP_GENERATION = {
    "Hidráulica": "hydro",
    "Eólica": "wind",
    "Fotovoltaica": "solar",
    "Biomasa": "biomass",
    "Térmica": "oil",
}
INV_MAP_GENERATION = dict([(v, k) for (k, v) in MAP_GENERATION.items()])

SALTO_GRANDE_URL = "http://www.cammesa.com/uflujpot.nsf/FlujoW?OpenAgent&Tensiones y Flujos de Potencia&"


def get_salto_grande(session) -> float:
    """Finds the current generation from the Salto Grande Dam that is allocated to Uruguay."""

    current_time = arrow.now("UTC-3")
    if current_time.minute < 30:
        # Data for current hour seems to be available after 30mins.
        current_time = current_time.shift(hours=-1)
    lookup_time = current_time.floor("hour").format("DD/MM/YYYY HH:mm")

    s = session or requests.Session()
    url = SALTO_GRANDE_URL + lookup_time
    response = s.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    tie = soup.find("div", style="position:absolute; top:143; left:597")
    generation = float(tie.text)

    return generation


def parse_page(session):
    r = session or requests.session()
    url = "https://apps.ute.com.uy/SgePublico/ConsPotenciaGeneracionArbolXFuente.aspx"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    datefield = soup.find(
        "span", attrs={"id": "ctl00_ContentPlaceHolder1_lblUltFecScada"}
    )
    datestr = re.findall("\d\d/\d\d/\d\d\d\d \d+:\d\d", str(datefield.contents[0]))[0]
    date = arrow.get(datestr, "DD/MM/YYYY h:mm").replace(tzinfo=dateutil.tz.gettz(tz))

    table = soup.find(
        "table", attrs={"id": "ctl00_ContentPlaceHolder1_gridPotenciasNivel1"}
    )

    obj = {"datetime": date.datetime}

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not len(tds):
            continue

        key = tds[0].find_all("b")
        # Go back one level up if the b tag is not there
        if not len(key):
            key = tds[0].find_all("font")
        k = key[0].contents[0]

        value = tds[1].find_all("b")
        # Go back one level up if the b tag is not there
        if not len(value):
            value = tds[1].find_all("font")
        v_str = value[0].contents[0]
        if v_str.find(",") > -1 and v_str.find(".") > -1:
            # there can be values like "1.012,5"
            v_str = v_str.replace(".", "")
            v_str = v_str.replace(",", ".")
        else:
            # just replace decimal separator, like "125,2"
            v_str = v_str.replace(",", ".")
        v = float(v_str)

        # solar reports -0.1 at night, make it at least 0
        v = max(v, 0)

        obj[k] = v

    # https://github.com/tmrowco/electricitymap/issues/1325#issuecomment-380453296
    salto_grande = get_salto_grande(session)
    obj["Hidráulica"] = obj.get("Hidráulica", 0.0) + salto_grande

    return obj


def fetch_production(
    zone_key="UY", session=None, target_datetime=None, logger=None
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    obj = parse_page(session)

    data = {
        "zoneKey": zone_key,
        "datetime": obj["datetime"],
        "production": dict(
            [(k, obj[INV_MAP_GENERATION[k]]) for k in INV_MAP_GENERATION.keys()]
        ),
        "source": "ute.com.uy",
    }

    return data


def fetch_exchange(
    zone_key1="UY", zone_key2="BR-S", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two countries."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    # set comparison
    if {zone_key1, zone_key2} != {"UY", "BR"}:
        return None

    obj = parse_page(session)
    netFlow = obj["Interconexión con Brasil"]  # this represents BR->UY (imports)
    if zone_key1 != "BR":
        netFlow *= -1

    data = {
        "sortedZoneKeys": "->".join(sorted([zone_key1, zone_key2])),
        "datetime": obj["datetime"],
        "netFlow": netFlow,
        "source": "ute.com.uy",
    }

    return data


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(UY, BR) ->")
    print(fetch_exchange("UY", "BR"))
