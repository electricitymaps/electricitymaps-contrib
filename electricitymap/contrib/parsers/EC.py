#!/usr/bin/env python3
"""
Ecuador (EC) electricity parser for electricitymaps by alixunderplatz / initiaded March 2026 based on issue #1558.

Source:      CENACE — https://www.cenace.gob.ec/info-operativa/InformacionOperativa.htm
Granularity: 30-minute intervals, current day only
Data:        Plotly.js charts embedded in HTML (binary float64 / bdata)

Production categories:
  hydro    → Hidráulica
  unknown  → Térmica + Gas Natural + Renovable
             (fuel mix and renewable types not distinguishable from this source,
             though a solar peak in the renovable-data is visible during the day,
             as of March 2026)

Note: "Datos preliminares del SCADA, sujetos a revisión y validación."
"""

import base64
import json
import re
import struct
from datetime import date, datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import urllib3
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.types import ZoneKey

# CENACE has an incomplete SSL certificate chain — suppress the warning.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SOURCE = "cenace.gob.ec"
ZONE_KEY = ZoneKey("EC")
URL = "https://www.cenace.gob.ec/info-operativa/InformacionOperativa.htm"
TZ_EC = ZoneInfo("America/Guayaquil")

# Maps the three chart series names from the real-time dashboard to electricitymaps categories.
PRODUCTION_MAPPINGS = {
    "Hidr\u00e1ulica": "hydro",  # Hidráulica
    "T\u00e9rmica": "unknown",  # Térmica   (diesel/fuel oil/gas mix)
    "Renovable": "unknown",  # Renovable (solar + wind, not split further)
}

MONTHS_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


# ── Plotly data decoding ──────────────────────────────────────────────────────


def _decode_bdata(b64: str) -> list:
    """Decode Plotly binary float64 array (base64, dtype f8)."""
    raw = base64.b64decode(b64)
    n = len(raw) // 8
    return list(struct.unpack(f"{n}d", raw[: n * 8]))


def _get_y_values(trace: dict) -> list:
    """Return y-values from a Plotly trace, handling bdata and plain list."""
    if "bdata" in trace:
        return _decode_bdata(trace["bdata"])
    y = trace.get("y", [])
    if isinstance(y, dict) and "bdata" in y:  # nested typed array
        return _decode_bdata(y["bdata"])
    return [float(v) for v in y]


# ── HTML parsing ──────────────────────────────────────────────────────────────


def _parse_traces(html: str) -> dict:
    """
    Find the time-series chart (identified by 'stackgroup') and return all
    series as: { series_name: {"x": ["00:00", ...], "y": [float, ...]} }
    """
    for m in re.finditer(r'Plotly\.newPlot\(\s*"[^"]+"\s*,\s*', html):
        pos = m.end()
        if html[pos] != "[":
            continue
        if '"stackgroup"' not in html[pos : pos + 2000]:
            continue
        traces_data, _ = json.JSONDecoder().raw_decode(html, pos)
        result = {}
        for trace in traces_data:
            name = trace.get("name", "")
            x = list(trace.get("x", []))
            y = _get_y_values(trace)
            if name and x and y:
                result[name] = {"x": x, "y": y}
        return result
    raise ValueError("No time-series chart (stackgroup) found in CENACE HTML")


def _parse_page_date(html: str) -> date:
    """
    Read the date from the CENACE page header, e.g.:
      'Domingo, 22 de marzo de 2026'  →  date(2026, 3, 22)

    More reliable than using the server clock: a server in UTC+1 at 01:00
    would already be on the 23rd while Ecuador (UTC-5) is still on the 22nd.
    Falls back to datetime.now(TZ_EC).date() if parsing fails.
    """
    m = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", html)
    if m:
        month = MONTHS_ES.get(m.group(2).lower())
        if month:
            return date(int(m.group(3)), month, int(m.group(1)))
    return datetime.now(TZ_EC).date()  # fallback


def _str_to_dt(time_str: str, today: date) -> datetime:
    """Convert '13:30' + date from page header → timezone-aware datetime for Ecuador."""
    h, m = map(int, str(time_str).split(":"))
    return datetime(today.year, today.month, today.day, h, m, tzinfo=TZ_EC)


# ── Public parser functions ───────────────────────────────────────────────────


def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Fetch real-time production breakdown for Ecuador (30-min resolution).
    Only current-day data is available. target_datetime is ignored.
    """
    s = session or Session()
    logger.info(f"Fetching Ecuador production from {URL}")

    resp = s.get(URL, timeout=30, verify=False)
    resp.raise_for_status()

    traces = _parse_traces(resp.text)
    today = _parse_page_date(resp.text)
    now_ec = datetime.now(TZ_EC)

    ref = next((v for k, v in traces.items() if k in PRODUCTION_MAPPINGS), None)
    if ref is None:
        raise ValueError("No production data found in CENACE chart")

    production_list = ProductionBreakdownList(logger)

    for i, ts in enumerate(ref["x"]):
        dt = _str_to_dt(ts, today)
        if dt > now_ec:
            break

        mix = ProductionMix()
        for series_name, series_data in traces.items():
            if series_name not in PRODUCTION_MAPPINGS:
                continue
            em_key = PRODUCTION_MAPPINGS[series_name]
            val = float(series_data["y"][i]) if i < len(series_data["y"]) else 0.0
            if val != val:
                continue  # NaN
            val = max(val, 0.0)
            current = getattr(mix, em_key) or 0.0
            setattr(mix, em_key, round(current + val, 3))

        # Skip slot if SCADA has not yet populated any value (all NaN)
        if mix.hydro is None and mix.unknown is None:
            continue

        production_list.append(
            zoneKey=zone_key,
            datetime=dt,
            production=mix,
            source=SOURCE,
        )

    logger.info(f"fetch_production: {len(production_list.events)} datapoints")
    return production_list.to_list()


def fetch_consumption(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Fetch real-time national demand (DEMANDA NACIONAL) for Ecuador.
    """
    s = session or Session()
    logger.info(f"Fetching Ecuador consumption from {URL}")

    resp = s.get(URL, timeout=30, verify=False)
    resp.raise_for_status()

    traces = _parse_traces(resp.text)
    today = _parse_page_date(resp.text)
    now_ec = datetime.now(TZ_EC)

    demand_trace = next((v for k, v in traces.items() if "DEMANDA" in k.upper()), None)
    if demand_trace is None:
        logger.warning("DEMANDA NACIONAL trace not found")
        return []

    consumption_list = TotalConsumptionList(logger)

    for i, ts in enumerate(demand_trace["x"]):
        dt = _str_to_dt(ts, today)
        if dt > now_ec:
            break
        val = float(demand_trace["y"][i])
        if val != val or val <= 0:
            continue
        consumption_list.append(
            zoneKey=zone_key,
            datetime=dt,
            consumption=round(val, 3),
            source=SOURCE,
        )

    logger.info(f"fetch_consumption: {len(consumption_list.events)} datapoints")
    return consumption_list.to_list()


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_consumption() ->")
    print(fetch_consumption())
