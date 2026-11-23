"""Parser for the RTE (French TSO) Physical Flow API, covering the French borders.

API: https://data.rte-france.com/catalog/-/api/consumption/Physical-Flow/v1.0
It needs an application on data.rte-france.com: set `RTE_PHYSICAL_FLOW_CLIENT_ID` and
`RTE_PHYSICAL_FLOW_CLIENT_SECRET` to its client ID and secret.

The API publishes one value per direction every 15 minutes, stamped with the interval
start (its `end_date` reads one hour later, but averaging four consecutive values gives
the hourly ENTSO-E figure). Each interval carries both directions of a border, one of
them 0. Points are stored exactly as published: no averaging, no resampling, no filling
of the intervals RTE skips (the API has a recurring gap, at times a couple of hours).

Window rules, found by probing the API:
- It returns only the Paris-local days that fall entirely inside [start_date, end_date].
- `end_date` can be at most the coming Paris midnight (`PHYSIFLOW_PHFLO_F04` beyond).
- A window holding no whole day is refused (`PHYSIFLOW_PHFLO_F05`).
The parser therefore asks for the Paris days that hold the 24 hours up to the target
(the feeder expects `[target - refetch frequency, target]`) and the feeder drops the rest.
The API serves data back to 2015: hourly until spring 2023, 15-minute since. A window
longer than about a year is refused (`PHYSIFLOW_PHFLO_F03`).
"""

from datetime import UTC, date, datetime, time, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import ExchangeList
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.session import mount_retry
from electricitymap.contrib.parsers.lib.utils import get_token

PARSER = "RTE_PHYSICAL_FLOW.py"
SOURCE = "rte-france.com"

TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
PHYSICAL_FLOW_URL = (
    "https://digital.iservices.rte-france.com/open_api/physical_flow/v1/physical_flows"
)
REQUEST_TIMEOUT = 60
# The token lasts an hour. Renew it this long before it expires.
TOKEN_EXPIRY_MARGIN = timedelta(minutes=5)

PARIS = ZoneInfo("Europe/Paris")
REFETCH_FREQUENCY = timedelta(days=1)

# ASCII EIC codes: the dashes in the API's Swagger enum are mangled.
FR_EIC = "10YFR-RTE------C"
BORDER_EICS: dict[str, str] = {
    "DE": "10YCB-GERMANY--8",
    "BE": "10YBE----------2",
    "CH": "10YCH-SWISSGRIDZ",
    "ES": "10YES-REE------0",
    "IT-NO": "10YIT-GRTN-----B",
}
EIC_TO_ZONE: dict[str, str] = {eic: zone for zone, eic in BORDER_EICS.items()}
EIC_TO_ZONE[FR_EIC] = "FR"

# One token per process: the feeder refetches every border in a single run.
_token_cache: dict[str, object] = {}


def _get_access_token(session: Session) -> str:
    expires_at = _token_cache.get("expires_at")
    if isinstance(expires_at, datetime) and datetime.now(UTC) < expires_at:
        return str(_token_cache["access_token"])

    response = session.post(
        TOKEN_URL,
        auth=(
            get_token("RTE_PHYSICAL_FLOW_CLIENT_ID"),
            get_token("RTE_PHYSICAL_FLOW_CLIENT_SECRET"),
        ),
        timeout=REQUEST_TIMEOUT,
    )
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Token request failed with HTTP {response.status_code}: "
            f"{response.text[:500]}",
        )
    payload = response.json()
    lifetime = timedelta(seconds=int(payload.get("expires_in", 3600)))
    _token_cache["access_token"] = payload["access_token"]
    _token_cache["expires_at"] = datetime.now(UTC) + lifetime - TOKEN_EXPIRY_MARGIN
    return payload["access_token"]


def _paris_midnight(day: date) -> datetime:
    return datetime.combine(day, time(), tzinfo=PARIS)


def _query_window(target_datetime: datetime | None) -> tuple[datetime, datetime]:
    """The Paris days holding the 24 hours up to the target, as the feeder expects."""
    now = datetime.now(PARIS)
    target = (target_datetime or now).astimezone(PARIS)
    start = _paris_midnight((target - REFETCH_FREQUENCY).date())
    # The API refuses an end_date beyond the coming midnight.
    end = min(
        _paris_midnight(target.date() + timedelta(days=1)),
        _paris_midnight(now.date() + timedelta(days=1)),
    )
    return start, end


def _query_physical_flows(
    session: Session, border_eic: str, start: datetime, end: datetime
) -> list[dict]:
    response = session.get(
        PHYSICAL_FLOW_URL,
        params={
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "country_eic_code": border_eic,
        },
        headers={"Authorization": f"Bearer {_get_access_token(session)}"},
        timeout=REQUEST_TIMEOUT,
    )
    if not response.ok:
        # RTE explains refusals in the body, e.g. PHYSIFLOW_PHFLO_F04.
        raise ParserException(
            PARSER,
            f"Physical flow request failed with HTTP {response.status_code}: "
            f"{response.text[:500]}",
        )
    return response.json().get("physical_flows", [])


def _net_flows(
    physical_flows: list[dict], zone_key1: str, zone_key2: str, logger: Logger
) -> dict[datetime, float]:
    """Net flow zone_key1 -> zone_key2 per interval start (UTC), in MW."""
    sent: dict[datetime, dict[str, float]] = {}
    for flow in physical_flows:
        sender = EIC_TO_ZONE.get(flow["sender_country_eic_code"])
        receiver = EIC_TO_ZONE.get(flow["receiver_country_eic_code"])
        if {sender, receiver} != {zone_key1, zone_key2}:
            continue
        for point in flow["values"]:
            start = datetime.fromisoformat(point["start_date"]).astimezone(UTC)
            sent.setdefault(start, {})[sender] = point["value"]

    net_flows: dict[datetime, float] = {}
    for start, by_sender in sorted(sent.items()):
        if len(by_sender) != 2:
            logger.warning(
                {
                    "message": "RTE physical flow interval lacks one direction, skipped",
                    "zone_key": f"{zone_key1}->{zone_key2}",
                    "datetime": start.isoformat(),
                }
            )
            continue
        net_flows[start] = by_sender[zone_key1] - by_sender[zone_key2]
    return net_flows


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    zones = set(sorted_zone_keys.split("->"))
    others = zones - {"FR"}
    if "FR" not in zones or len(others) != 1 or others.isdisjoint(BORDER_EICS):
        raise ParserException(
            PARSER,
            f"{sorted_zone_keys} is not a supported border. Supported: "
            f"{sorted(f'FR<->{zone}' for zone in BORDER_EICS)}",
            sorted_zone_keys,
        )
    (other,) = others
    first, second = sorted_zone_keys.split("->")

    session = mount_retry(session or Session())
    start, end = _query_window(target_datetime)
    net_flows = _net_flows(
        _query_physical_flows(session, BORDER_EICS[other], start, end),
        first,
        second,
        logger,
    )
    if not net_flows:
        logger.warning(
            {
                "message": "RTE physical flow returned no data",
                "zone_key": sorted_zone_keys,
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
        )

    exchanges = ExchangeList(logger)
    for datetime_utc, net_flow in net_flows.items():
        exchanges.append(
            zoneKey=sorted_zone_keys,
            datetime=datetime_utc,
            netFlow=net_flow,
            source=SOURCE,
        )
    return exchanges.to_list()


if __name__ == "__main__":
    for key in ("BE", "CH", "DE", "ES", "IT-NO"):
        pair = sorted(["FR", key])
        print(fetch_exchange(ZoneKey(pair[0]), ZoneKey(pair[1]))[-2:])
