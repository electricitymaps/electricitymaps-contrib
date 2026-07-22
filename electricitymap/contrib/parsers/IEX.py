"""Indian Energy Exchange (IEX) Day-Ahead Market price parser.

Data: unconstrained DAM market clearing price (MCP) from IEX's public
provisional DAM page (15-minute blocks, ₹/MWh):
  https://iexrtmprice.com/view-dam-provisional-mcv-and-mcp-data/
Linked from the official IEX DAM market snapshot:
  https://www.iexindia.com/market-data/day-ahead-market/market-snapshot

Attribution uses the IEX root domain ``iexindia.com`` (project convention:
root URL of the datasource, not the provisional page host).

The provisional page exposes the latest cleared delivery day only.
Historical backfill is out of scope for this endpoint; see
https://github.com/electricitymaps/electricitymaps-contrib/issues/8796
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import PriceList
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

TZ = ZoneInfo("Asia/Kolkata")
# Root domain of the Indian Energy Exchange (see Event.source docs).
SOURCE = "iexindia.com"
CURRENCY = "INR"
PARSER = "IEX.py"

# Provisional unconstrained DAM MCP/MCV table (public, no auth).
# Host is iexrtmprice.com; brand/attribution remains iexindia.com.
DAM_PROVISIONAL_URL = "https://iexrtmprice.com/view-dam-provisional-mcv-and-mcp-data/"
_REQUEST_HEADERS = {
    "User-Agent": "electricitymaps-contrib/IEX-parser (+https://github.com/electricitymaps/electricitymaps-contrib)",
    "Accept": "text/html,application/xhtml+xml",
}

# e.g. "00:00 - 00:15", "23:45 - 24:00"
_TIME_BLOCK_RE = re.compile(
    r"^(?P<sh>\d{1,2}):(?P<sm>\d{2})\s*-\s*(?P<eh>\d{1,2}):(?P<em>\d{2})$"
)
_DATE_RE = re.compile(r"(\d{2})-(\d{2})-(\d{4})")


def _parse_delivery_date(text: str) -> date:
    match = _DATE_RE.search(text)
    if not match:
        raise ParserException(
            PARSER,
            f"Could not parse delivery date from: {text!r}",
        )
    day, month, year = (int(match.group(i)) for i in range(1, 4))
    return date(year, month, day)


def _block_bounds(delivery_date: date, time_block: str) -> tuple[datetime, datetime]:
    """Return (start, end) datetimes in Asia/Kolkata for a DAM time block."""
    match = _TIME_BLOCK_RE.match(time_block.strip())
    if not match:
        raise ValueError(f"Unrecognised time block: {time_block!r}")

    sh, sm = int(match.group("sh")), int(match.group("sm"))
    eh, em = int(match.group("eh")), int(match.group("em"))

    start = datetime(
        delivery_date.year,
        delivery_date.month,
        delivery_date.day,
        sh,
        sm,
        tzinfo=TZ,
    )
    if eh == 24 and em == 0:
        end = datetime(
            delivery_date.year,
            delivery_date.month,
            delivery_date.day,
            tzinfo=TZ,
        ) + timedelta(days=1)
    else:
        end = datetime(
            delivery_date.year,
            delivery_date.month,
            delivery_date.day,
            eh,
            em,
            tzinfo=TZ,
        )
    return start, end


def _parse_dam_html(
    html: str, logger: Logger
) -> tuple[date, list[tuple[datetime, datetime, float]]]:
    """Parse provisional DAM HTML into (delivery_date, [(start, end, price), ...])."""
    soup = BeautifulSoup(html, "html.parser")

    heading = soup.find("h1")
    if heading is None:
        raise ParserException(PARSER, "Missing <h1> with delivery date on DAM page")
    delivery_date = _parse_delivery_date(heading.get_text(" ", strip=True))

    table = soup.find("table")
    if table is None:
        raise ParserException(PARSER, "Missing DAM price table")

    rows: list[tuple[datetime, datetime, float]] = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(strip=True) for c in tr.find_all("td")]
        if len(cells) < 2:
            continue
        time_block, mcp_raw = cells[0], cells[1]
        if not _TIME_BLOCK_RE.match(time_block):
            # Skip header leftovers / Max / Average / Sum summary rows.
            continue
        if not mcp_raw or mcp_raw in {"-", "NA", "N/A"}:
            logger.warning("Skipping DAM block %s with empty MCP", time_block)
            continue
        try:
            price = float(mcp_raw.replace(",", ""))
        except ValueError:
            logger.warning(
                "Skipping DAM block %s with non-numeric MCP %r", time_block, mcp_raw
            )
            continue
        start, end = _block_bounds(delivery_date, time_block)
        rows.append((start, end, price))

    if not rows:
        raise ParserException(PARSER, "No DAM time-block rows found in HTML")

    return delivery_date, rows


def _fetch_dam_html(session: Session) -> str:
    response: Response = session.get(
        DAM_PROVISIONAL_URL, timeout=30, headers=_REQUEST_HEADERS
    )
    if not response.ok:
        raise ParserException(
            PARSER,
            f"{DAM_PROVISIONAL_URL} returned HTTP {response.status_code}",
        )
    return response.text


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: ZoneKey = ZoneKey("IN"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Fetch IEX unconstrained Day-Ahead Market clearing prices (₹/MWh).

    The public provisional endpoint only exposes the latest cleared delivery
    day. Historical `target_datetime` queries that do not match that day raise
    ``ParserException``.
    """
    session = session or Session()
    html = _fetch_dam_html(session)
    delivery_date, rows = _parse_dam_html(html, logger)

    if target_datetime is not None:
        if target_datetime.tzinfo is None:
            raise ParserException(
                PARSER,
                "target_datetime must be timezone-aware",
                zone_key,
            )
        requested = target_datetime.astimezone(TZ).date()
        if requested != delivery_date:
            raise ParserException(
                PARSER,
                (
                    f"Historical DAM prices are not available from the provisional "
                    f"endpoint (requested {requested.isoformat()}, page has "
                    f"{delivery_date.isoformat()}). See issue #8796 for backfill."
                ),
                zone_key,
            )

    price_list = PriceList(logger)
    for start, end, price in rows:
        # Cleared day-ahead MCP for the delivery day — often >24h ahead of
        # fetch time, so use published (ex-ante market result), not measured.
        price_list.append(
            zoneKey=zone_key,
            datetime=start,
            end_datetime=end,
            price=price,
            currency=CURRENCY,
            source=SOURCE,
            sourceType=EventSourceType.published,
        )
    return price_list.to_list()


if __name__ == "__main__":
    print("fetch_price() ->")
    print(fetch_price())
