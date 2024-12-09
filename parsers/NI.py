from datetime import datetime, time, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

TIMEZONE = ZoneInfo("America/Managua")

PRICE_URL = (
    "http://www.cndc.org.ni/consultas/infoRelevanteSIN/consultaCostoMarginal.php"
)


PRODUCTION_TYPE_TO_PRODUCTION_MODE = {
    "EOLICA": "wind",
    "GEOTERMICA": "geothermal",
    "BIOMASA": "biomass",
    "HIDROELECTRICA": "hydro",
    "SOLAR": "solar",
    "TERMICA": "oil",
    # "MER" is imports and exports
}

ZONE_KEYS_TO_INTERCONNECTION = {
    "CR->NI": ["amy", "lvg"],
    "HN->NI": ["snd", "leon"],
}


def extract_text(full_text: str, start_text: str, end_text: str | None = None):
    start = full_text.find(start_text)

    if start == -1:
        return full_text

    start += len(start_text)

    if not end_text:
        return full_text[start:]

    end = full_text.find(end_text, start)

    if end == -1:
        return full_text[start:]
    else:
        return full_text[start:end]


def fetch_production(
    zone_key: str = "NI",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of Nicaragua."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    url = "https://www.cndc.org.ni/graficos/consultarGeneracionPorTipo"

    response = requests.get(url)
    if not response.ok:
        raise ParserException(
            f"Exception when fetching production error code for {zone_key}: {response.status_code}: {response.text}",
        )

    response_payload = response.json().get("GeneracionTipo")
    response_df = pd.DataFrame(response_payload).set_index("fecha_hora")

    production_breakdown_list = ProductionBreakdownList(logger)

    for idx in response_df.index.unique():
        production_mix = ProductionMix()
        time = datetime.strptime(idx, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TIMEZONE)

        for _, item in response_df.loc[idx].iterrows():
            production_type = item.get("tipo")
            production_mode = PRODUCTION_TYPE_TO_PRODUCTION_MODE.get(production_type)

            if production_mode is None:
                continue

            value = float(item.get("valor"))
            production_mix.add_value(production_mode, value)

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=time,
            source="cndc.org.ni",
            production=production_mix,
        )

    return production_breakdown_list.to_list()


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    url = "https://www.cndc.org.ni/Inicio/ConsultarTipoGeneracion"

    response = requests.get(url)
    if not response.ok:
        raise ParserException(
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
        )

    response_payload = response.json().get("interconexion")[0]
    time = datetime.strptime(
        response.json().get("tipoGeneracion")[0].get("fecha_hora"), "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=TIMEZONE)

    # Cross-comparing regional data on https://www.enteoperador.org/flujos-regionales-en-tiempo-real/
    # and NI data (both fairly real-time), we can see that negative is import to NI, and positive is export from NI.

    # Because in both possible sorted_zone_key values (HN->NI and CR->NI) NI is second,
    # we expect netFlow to be positive when NI is importing, and negative when NI is exporting.
    # So multiply value reported by the MAP_URL by -1.

    if sorted_zone_keys in ZONE_KEYS_TO_INTERCONNECTION:
        interchange_list = [
            float(response_payload.get(con).replace(",", "."))
            for con in ZONE_KEYS_TO_INTERCONNECTION.get(sorted_zone_keys)
        ]

        flow = -1 * sum(interchange_list)

    else:
        raise NotImplementedError("This exchange pair is not implemented")

    exchange_list = ExchangeList(logger)
    exchange_list.append(
        zoneKey=ZoneKey(sorted_zone_keys),
        datetime=time,
        netFlow=flow,
        source="cndc.org.ni",
    )
    return exchange_list.to_list()


def fetch_price(
    zone_key: str = "NI",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the most recent known power prices in Nicaragua grid."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or Session()
    response = requests_obj.get(PRICE_URL)
    response.encoding = "utf-8"
    prices_html = response.text

    now_local_time = datetime.now(TIMEZONE)
    midnight_local_time = datetime.combine(
        now_local_time, time(), tzinfo=TIMEZONE
    )  # truncate to day

    hours_text = prices_html.split("<br />")

    for hour_data in hours_text:
        if not hour_data:
            # there is usually an empty item at the end of the list, ignore it
            continue

        # hour_data is like "Hora 13:&nbsp;&nbsp;   84.72"
        hour = int(extract_text(hour_data, "Hora ", ":"))
        price = float(extract_text(hour_data, "&nbsp;   ").replace(",", "."))

        price_date = midnight_local_time + timedelta(hours=hour)
        if price_date > now_local_time:
            # data for previous day is also included
            price_date = price_date - timedelta(days=1)

    price_list = PriceList(logger)
    price_list.append(
        zoneKey=ZoneKey(zone_key),
        datetime=price_date,
        price=price,
        currency="USD",
        source="cndc.org.ni",
    )
    return price_list.to_list()
