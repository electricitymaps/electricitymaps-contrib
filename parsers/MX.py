#!/usr/bin/env python3

import datetime
import urllib
from collections import defaultdict
from io import StringIO

import arrow
import pandas
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser, tz

MX_PRODUCTION_URL = (
    "https://www.cenace.gob.mx/SIM/VISTA/REPORTES/EnergiaGenLiqAgregada.aspx"
)
MX_EXCHANGE_URL = "https://www.cenace.gob.mx/Paginas/Publicas/Info/DemandaRegional.aspx"

EXCHANGES = {
    "MX-NO->MX-NW": "IntercambioNTE-NOR",
    "MX-NE->MX-NO": "IntercambioNES-NTE",
    "MX-NE->MX-OR": "IntercambioNES-ORI",
    "MX-OR->MX-PN": "IntercambioORI-PEN",
    "MX-CE->MX-OR": "IntercambioORI-CEL",
    "MX-OC->MX-OR": "IntercambioOCC-ORI",
    "MX-CE->MX-OC": "IntercambioOCC-CEL",
    "MX-NE->MX-OC": "IntercambioNES-OCC",
    "MX-NO->MX-OC": "IntercambioNTE-OCC",
    "MX-NW->MX-OC": "IntercambioNOR-OCC",
    "MX-NO->US-TEX-ERCO": "IntercambioUSA-NTE",
    "MX-NE->US-TEX-ERCO": "IntercambioUSA-NES",
    "BZ->MX-PN": "IntercambioPEN-BEL",
}

MAPPING = {
    "Eolica": "wind",
    "Fotovoltaica": "solar",
    "Biomasa": "biomass",
    "Carboelectrica": "coal",
    "Ciclo Combinado": "gas",
    "Geotermoelectrica": "geothermal",
    "Hidroelectrica": "hydro",
    "Nucleoelectrica": "nuclear",
    "Combustion Interna": "unknown",
    "Termica Convencional": "unknown",
    "Turbo Gas": "gas",
}

# cache where the data for whole months is stored as soon as it has been fetched once
DATA_CACHE = {}


def parse_date(date, hour):
    tzoffset = tz.tzoffset("CST", -3600 * 6)
    dt = datetime.datetime.strptime(date, "%d/%m/%Y")
    dt = dt.replace(hour=int(hour) - 1, tzinfo=tzoffset)
    return dt


def fetch_csv_for_date(dt, session=None):
    """
    Fetches the whole month of the give datetime.
    returns the data as a DataFrame.
    throws an exception data is not available.
    """
    if not session:
        session = requests.session()

    # build the parameters and fill in the requested date
    # TODO find something prettier than string concatenation which works
    # TODO find out whether VIEWSTATE stays valid or needs to be fetched before making the post request
    datestr = dt.strftime("%m/%d/%Y")
    parameters = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": "/wEPDwUKLTM2ODQwNzIwMw9kFgJmD2QWAgIDD2QWAgIBD2QWCAIBD2QWAmYPZBYCAgMPDxYCHgRUZXh0BTNTaXN0ZW1hIGRlIEluZm9ybWFjacOzbiBkZWwgTWVyY2Fkby4gw4FyZWEgUMO6YmxpY2FkZAIFDzwrABEDAA8WBB4LXyFEYXRhQm91bmRnHgtfIUl0ZW1Db3VudGZkARAWABYAFgAMFCsAAGQCCQ9kFgJmD2QWAgIDD2QWAmYPZBYEZg9kFgYCAQ8PFgQFBE1pbkQGAECJX4pw0wgFBE1heEQGAMBI0Tg61wgPFg4eB01pbkRhdGUGAECJX4pw0wgeDFNlbGVjdGVkRGF0ZQYAwEjRODrXCB4HTWF4RGF0ZQYAwEjRODrXCB4VRW5hYmxlRW1iZWRkZWRTY3JpcHRzZx4cRW5hYmxlRW1iZWRkZWRCYXNlU3R5bGVzaGVldGceElJlc29sdmVkUmVuZGVyTW9kZQspclRlbGVyaWsuV2ViLlVJLlJlbmRlck1vZGUsIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMTQuMi43MjQuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNAEeF0VuYWJsZUFqYXhTa2luUmVuZGVyaW5naGQWBGYPFCsACA8WEB8ABRMyMDE5LTA5LTE2LTAwLTAwLTAwHhFFbmFibGVBcmlhU3VwcG9ydGgfBmceDUxhYmVsQ3NzQ2xhc3MFB3JpTGFiZWwfCWgfB2ceBFNraW4FB0RlZmF1bHQfCAsrBAFkFggeBVdpZHRoGwAAAAAAAFlABwAAAB4KUmVzaXplTW9kZQspclRlbGVyaWsuV2ViLlVJLlJlc2l6ZU1vZGUsIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMTQuMi43MjQuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNAAeCENzc0NsYXNzBRFyaVRleHRCb3ggcmlIb3Zlch4EXyFTQgKCAhYIHw0bAAAAAAAAWUAHAAAAHw4LKwUAHw8FEXJpVGV4dEJveCByaUVycm9yHxACggIWCB8NGwAAAAAAAFlABwAAAB8OCysFAB8PBRNyaVRleHRCb3gg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BQtFZGl0SW5kZXhlcxYAARYCFgsPAgYUKwAGPCsABQEAFgQeCERhdGFUeXBlGSsCHgRvaW5kAgI8KwAFAQAWBB8VGSsCHxYCAxQrAAUWAh8WAgRkZGQFBmNvbHVtbhQrAAUWAh8WAgVkZGQFB2NvbHVtbjEUKwAFFgIfFgIGZGRkBQdjb2x1bW4yPCsABQEAFgQfFRkrAh8WAgdkZRQrAAALKXlUZWxlcmlrLldlYi5VSS5HcmlkQ2hpbGRMb2FkTW9kZSwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAxNC4yLjcyNC40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0ATwrAAcACyl0VGVsZXJpay5XZWIuVUkuR3JpZEVkaXRNb2RlLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDE0LjIuNzI0LjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQBZGQWDB8BZx4USXNCb3VuZFRvRm9yd2FyZE9ubHloHgVfcWVsdBkpZ1N5c3RlbS5EYXRhLkRhdGFSb3dWaWV3LCBTeXN0ZW0uRGF0YSwgVmVyc2lvbj00LjAuMC4wLCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPWI3N2E1YzU2MTkzNGUwODkeCERhdGFLZXlzFgAeBV8hQ0lTFwAfAgIBZGYWBGYPFCsAA2RkZGQCAQ8WBRQrAAIPFgwfAWcfF2gfGBkrCR8ZFgAfGhcAHwICAWQXAwULXyFJdGVtQ291bnQCAQUIXyFQQ291bnRkBQZfIURTSUMCARYCHgNfc2UWAh4CX2NmZBYGZGRkZGRkFgJnZxYCZg9kFghmD2QWAmYPZBYQZg8PFgQfAAUGJm5ic3A7HgdWaXNpYmxlaGRkAgEPDxYEHwAFBiZuYnNwOx8daGRkAgIPDxYCHwAFEU1lcyBkZSBPcGVyYWNpw7NuZGQCAw8PFgIfAAUcTm8uIGRlIExpcXVpZGFjacOzbiBBc29jaWFkYWRkAgQPDxYCHwAFA0NzdmRkAgUPDxYCHwAFA1BkZmRkAgYPDxYCHwAFBEh0bWxkZAIHDw8WAh8ABRVGZWNoYSBkZSBQdWJsaWNhY2nDs25kZAIBDw8WAh8daGQWAmYPZBYQZg8PFgIfAAUGJm5ic3A7ZGQCAQ8PFgIfAAUGJm5ic3A7ZGQCAg8PFgIfAAUGJm5ic3A7ZGQCAw8PFgIfAAUGJm5ic3A7ZGQCBA8PFgIfAAUGJm5ic3A7ZGQCBQ8PFgIfAAUGJm5ic3A7ZGQCBg8PFgIfAAUGJm5ic3A7ZGQCBw8PFgIfAAUGJm5ic3A7ZGQCAg8PFgIeBF9paWgFATBkFhBmDw8WAh8daGRkAgEPDxYEHwAFBiZuYnNwOx8daGRkAgIPDxYCHwAFD1NlcHRpZW1icmUgMjAxOWRkAgMPDxYCHwAFATBkZAIED2QWAmYPDxYEHg1BbHRlcm5hdGVUZXh0ZR4HVG9vbFRpcGVkZAIFD2QWAmYPDxYEHx9lHyBlZGQCBg9kFgJmDw8WBB8fZR8gZWRkAgcPDxYCHwAFGTE0LzEwLzIwMTkgMDU6MDA6MDEgYS4gbS5kZAIDD2QWAmYPDxYCHx1oZGQCCw8PFggfB2cfCWgfCAsrBAEfBmdkFgRmDw8WBh8JaB8GZx8ICysEAWRkAgEPFCsAAhQrAAIUKwACDxYOHwdnHhNFbmFibGVFbWJlZGRlZFNraW5zZx8JaB4URW5hYmxlUm91bmRlZENvcm5lcnNnHg1FbmFibGVTaGFkb3dzaB8GZx8ICysEAWRkZGRkGAIFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYMBSdjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJEZlY2hhQ29uc3VsdGEFJmN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkRmVjaGFJbmljaWFsBSRjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJEZlY2hhRmluYWwFK2N0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkRGVzY2FyZ2FyUmVwb3J0ZXMFKmN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkR3JpZFJhZFJlc3VsdGFkbwVAY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRHcmlkUmFkUmVzdWx0YWRvJGN0bDAwJGN0bDA0JGdiY2NvbHVtbgVBY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRHcmlkUmFkUmVzdWx0YWRvJGN0bDAwJGN0bDA0JGdiY2NvbHVtbjEFQWN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkR3JpZFJhZFJlc3VsdGFkbyRjdGwwMCRjdGwwNCRnYmNjb2x1bW4yBSVjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJE5vdGlmQXZpc29zBS5jdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJE5vdGlmQXZpc29zJFhtbFBhbmVsBS9jdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJE5vdGlmQXZpc29zJFRpdGxlTWVudQUoY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRidG5DZXJyYXJQYW5lbAUfY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRjdGwwMA88KwAMAQhmZHAKRKrT54JyF09yAgRL16DIn42vcyspzOtg86mdF/6Z",
        "__VIEWSTATEGENERATOR": "5B6503FA",
        "__EVENTVALIDATION": "/wEdABPIFpMnlAgkSZvMhE+vOQYa0gsvRcXibJrviW3Dmsx0G+jYKkdCU41GOhiZPOlFyBecIegvepvm5r48BtByTWSkIC/PSPgmtogq3vXUp+YNvsMPaGT0F8ZMY05tsTP7KXY5p77wXhhk2nxxmhBw8yYO6yoq09PpCPpnHhKGI5XXqN0NAXFS9Kcv7U1TgXuCACxTET4yjIt6nVt9qCHIyzbla16U6SvCvrhBDl88f4l+A2AwM+Efhx0eY7z5UUNUDwDoCL/OENuuNNFPCRAmSpT1/nxKmb/ucFs0tCWRV4G4iLScixGy8IhVeNkOJJPR8q4msGM8DGO6o6g/gMszmMRrbD50rXo0f8u6b2IB+RzVpsHxVceaRLBN56ddyVdqKV1RL0jZlTtb1Prpo6YdA7cH301O2Ez19CJOtDoyAWUZ982dVJTM6fLOsQokHcEDIxQ=",
        "ctl00_ContentPlaceHolder1_FechaConsulta_ClientState": '{"minDateStr":"'
        + datestr
        + '+0:0:0","maxDateStr":"'
        + datestr
        + '+0:0:0"}',
        "ctl00$ContentPlaceHolder1$GridRadResultado$ctl00$ctl04$gbccolumn.x": "10",
        "ctl00$ContentPlaceHolder1$GridRadResultado$ctl00$ctl04$gbccolumn.y": "9",
    }

    # urlencode the data in the weird form which is expected by the API
    # plus signs MUST be contained in the date strings but MAY NOT be contained in the VIEWSTATE...
    data = urllib.parse.urlencode(parameters, quote_via=urllib.parse.quote).replace(
        "%2B0", "+0"
    )

    response = session.post(
        MX_PRODUCTION_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()

    # API returns normally status 200 but content type text/html when data is missing
    if (
        "Content-Type" not in response.headers
        or response.headers["Content-Type"] != "application/octet-stream"
    ):
        raise Exception(
            "Error while fetching csv for date {}: No CSV was returned by the API. Probably the data for this date has not yet been published.".format(
                datestr
            )
        )

    # skip non-csv data, the header starts with "Sistema"
    csv_str = response.text
    csv_str = csv_str[csv_str.find('"Sistema"') :]

    return pd.read_csv(
        StringIO(csv_str), parse_dates={"instante": [1, 2]}, date_parser=parse_date
    )


def convert_production(series):
    aggregated = {
        "biomass": 0.0,
        "coal": 0.0,
        "gas": 0.0,
        "hydro": 0.0,
        "nuclear": 0.0,
        "oil": 0.0,
        "solar": 0.0,
        "wind": 0.0,
        "geothermal": 0.0,
        "unknown": 0.0,
    }

    for name, val in series.iteritems():
        name = name.strip()
        if isinstance(val, float) or isinstance(val, int):
            target = MAPPING.get(name, "unknown")  # default to unknown
            aggregated[target] += val

    return aggregated


def fetch_production(zone_key, session=None, target_datetime=None, logger=None):
    if zone_key != "MX":
        raise ValueError(
            "MX parser cannot fetch production for zone {}".format(zone_key)
        )

    if target_datetime is None:
        raise ValueError(
            "Parser only supports fetching historical production data, please specify a terget_datetime in the past"
        )

    # retrieve data for the month either from the cache or fetch it
    cache_key = target_datetime.strftime("%Y-%m")
    if cache_key in DATA_CACHE:
        df = DATA_CACHE[cache_key]
    else:
        df = fetch_csv_for_date(target_datetime, session=session)
        DATA_CACHE[cache_key] = df

    data = []
    for idx, series in df.iterrows():
        data.append(
            {
                "zoneKey": zone_key,
                "datetime": series["instante"].to_pydatetime(),
                "production": convert_production(series),
                "source": "cenace.gob.mx",
            }
        )
    return data


def fetch_MX_exchange(sorted_zone_keys, s) -> float:
    """Finds current flow between two Mexican control areas."""

    req = s.get(MX_EXCHANGE_URL)
    soup = BeautifulSoup(req.text, "html.parser")
    exchange_div = soup.find("div", attrs={"id": EXCHANGES[sorted_zone_keys]})
    val = exchange_div.text

    # cenace html uses unicode hyphens instead of minus signs and , as thousand separator
    trantab = str.maketrans({chr(8208): chr(45), ",": ""})

    val = val.translate(trantab)
    flow = float(val)

    if sorted_zone_keys in ["BZ->MX-PN", "MX-CE->MX-OR", "MX-CE->MX-OC"]:
        # reversal needed for these zones due to EM ordering
        flow = -1 * flow

    return flow


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys not in EXCHANGES:
        raise NotImplementedError(
            "Exchange pair not supported: {}".format(sorted_zone_keys)
        )

    s = session or requests.Session()

    netflow = fetch_MX_exchange(sorted_zone_keys, s)

    data = {
        "sortedZoneKeys": sorted_zone_keys,
        "datetime": arrow.now("America/Tijuana").datetime,
        "netFlow": netflow,
        "source": "cenace.gob.mx",
    }

    return data


if __name__ == "__main__":
    print(
        fetch_production(
            "MX", target_datetime=datetime.datetime(year=2019, month=7, day=1)
        )
    )
    print("fetch_exchange(MX-NO, MX-NW)")
    print(fetch_exchange("MX-NO", "MX-NW"))
    print("fetch_exchange(MX-OR, MX-PN)")
    print(fetch_exchange("MX-OR", "MX-PN"))
    print("fetch_exchange(MX-NE, MX-OC)")
    print(fetch_exchange("MX-NE", "MX-OC"))
    print("fetch_exchange(MX-NE, MX-NO)")
    print(fetch_exchange("MX-NE", "MX-NO"))
    print("fetch_exchange(MX-OC, MX-OR)")
    print(fetch_exchange("MX-OC", "MX-OR"))
    print("fetch_exchange(MX-NE, US-TEX-ERCO)")
    print(fetch_exchange("MX-NE", "US-TEX-ERCO"))
    print("fetch_exchange(MX-CE, MX-OC)")
    print(fetch_exchange("MX-CE", "MX-OC"))
    print("fetch_exchange(MX-PN, BZ)")
    print(fetch_exchange("MX-PN", "BZ"))
    print("fetch_exchange(MX-NO, MX-OC)")
    print(fetch_exchange("MX-NO", "MX-OC"))
    print("fetch_exchange(MX-NO, US-TEX-ERCO)")
    print(fetch_exchange("MX-NO", "US-TEX-ERCO"))
    print("fetch_exchange(MX-NE, MX-OR)")
    print(fetch_exchange("MX-NE", "MX-OR"))
    print("fetch_exchange(MX-CE, MX-OR)")
    print(fetch_exchange("MX-CE", "MX-OR"))
