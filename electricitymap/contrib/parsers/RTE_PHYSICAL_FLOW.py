"""Parser for the RTE (French TSO) Physical Flow API, covering the French borders.

API: https://data.rte-france.com/catalog/-/api/consumption/Physical-Flow/v1.0
It needs an application on data.rte-france.com: set `RTE_PHYSICAL_FLOW_CLIENT_ID` and
`RTE_PHYSICAL_FLOW_CLIENT_SECRET` to its client ID and secret.

The API publishes one value per direction every 15 minutes, stamped with the interval
start. Its `end_date` reads one hour later, but averaging four consecutive values gives
the hourly ENTSO-E figure, so each point is stored as lasting one step (15 minutes, or
an hour for the older hourly data). Each interval carries both directions of a border,
one of them 0; an interval missing a direction is dropped. Values are stored exactly
as published: no averaging, no resampling, no filling of the intervals RTE skips (the
API has a recurring gap, at times a couple of hours).

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
from itertools import pairwise
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import ExchangeList
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.session import DEFAULT_RETRY, mount_retry
from electricitymap.contrib.parsers.lib.utils import get_token, to_utc

PARSER = "RTE_PHYSICAL_FLOW.py"
SOURCE = "rte-france.com"

TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
PHYSICAL_FLOW_URL = (
    "https://digital.iservices.rte-france.com/open_api/physical_flow/v1/physical_flows"
)
REQUEST_TIMEOUT = 60
# The token lasts an hour. Renew it this long before it expires.
TOKEN_EXPIRY_MARGIN = timedelta(minutes=5)

# Also retry the OAuth token POST on transient errors.
RETRY = DEFAULT_RETRY.new(allowed_methods=["GET", "POST"])

PARIS = ZoneInfo("Europe/Paris")
REFETCH_FREQUENCY = timedelta(days=1)

# ASCII EIC codes: the dashes in the API's Swagger enum are mangled.
FR_EIC = "10YFR-RTE------C"
# No DE: RTE's only German code (10YCB-GERMANY--8) reads about 16% below the flows the
# German TSOs report to ENTSO-E, in both directions, so DE->FR stays on ENTSO-E.
BORDER_EICS: dict[str, str] = {
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
    # The API has nothing past now, and refuses a window without a whole day in it.
    target = min(to_utc(target_datetime).astimezone(PARIS), now)
    # Subtract in UTC: wall-clock arithmetic in Paris loses an hour across DST.
    start = _paris_midnight(
        (target.astimezone(UTC) - REFETCH_FREQUENCY).astimezone(PARIS).date()
    )
    # The API refuses an end_date beyond the coming midnight.
    end = min(
        _paris_midnight(target.date() + timedelta(days=1)),
        _paris_midnight(now.date() + timedelta(days=1)),
    )
    return start, end


def _query_physical_flows(
    session: Session, border_eic: str, start: datetime, end: datetime
) -> list[dict]:
    def get():
        return session.get(
            PHYSICAL_FLOW_URL,
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "country_eic_code": border_eic,
            },
            headers={"Authorization": f"Bearer {_get_access_token(session)}"},
            timeout=REQUEST_TIMEOUT,
        )

    response = get()
    if response.status_code == 401:
        # The cached token was revoked or expired early: get a new one, once.
        _token_cache.clear()
        response = get()
    if not response.ok:
        # RTE explains refusals in the body, e.g. PHYSIFLOW_PHFLO_F04.
        raise ParserException(
            PARSER,
            f"Physical flow request failed with HTTP {response.status_code}: "
            f"{response.text[:500]}",
        )
    if response.status_code == 204 or not response.content:
        return []
    return response.json().get("physical_flows", [])


def _direction_exchanges(
    values: list[dict], net_sign: int, sorted_zone_keys: ZoneKey, logger: Logger
) -> ExchangeList:
    """One direction's points as signed net flows along sorted_zone_keys.

    Each point ends one step after its start, the step being the smallest spacing
    between the direction's starts (RTE's own `end_date` reads an hour later).
    """
    starts = sorted(
        {datetime.fromisoformat(v["start_date"]).astimezone(UTC) for v in values}
    )
    step = min((b - a for a, b in pairwise(starts)), default=None)

    exchanges = ExchangeList(logger)
    for value in values:
        # A null value leaves this direction without the interval, and the merge
        # then drops it.
        if value.get("value") is None:
            continue
        start = datetime.fromisoformat(value["start_date"]).astimezone(UTC)
        end = datetime.fromisoformat(value["end_date"]).astimezone(UTC)
        exchanges.append(
            zoneKey=sorted_zone_keys,
            datetime=start,
            end_datetime=end if step is None else min(start + step, end),
            netFlow=net_sign * value["value"],
            source=SOURCE,
        )
    return exchanges


def _net_flows(
    physical_flows: list[dict], sorted_zone_keys: ZoneKey, logger: Logger
) -> ExchangeList:
    """Net flow along sorted_zone_keys: the first zone's sending minus the second's.

    An interval only one direction covers is dropped, with a single warning.
    """
    first, second = sorted_zone_keys.split("->")
    values_by_sender: dict[str, list[dict]] = {first: [], second: []}
    for flow in physical_flows:
        sender = EIC_TO_ZONE.get(flow["sender_country_eic_code"])
        receiver = EIC_TO_ZONE.get(flow["receiver_country_eic_code"])
        if {sender, receiver} == {first, second}:
            values_by_sender[sender].extend(flow["values"])

    return ExchangeList.merge_exchanges(
        [
            _direction_exchanges(values_by_sender[first], 1, sorted_zone_keys, logger),
            _direction_exchanges(
                values_by_sender[second], -1, sorted_zone_keys, logger
            ),
        ],
        logger,
        drop_non_matching_datetimes=True,
    )


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

    session = mount_retry(session or Session(), RETRY)
    start, end = _query_window(target_datetime)
    net_flows = _net_flows(
        _query_physical_flows(session, BORDER_EICS[other], start, end),
        sorted_zone_keys,
        logger,
    )
    if len(net_flows) == 0:
        logger.warning(
            {
                "message": "RTE physical flow returned no data",
                "zone_key": sorted_zone_keys,
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
        )
    return net_flows.to_list()


if __name__ == "__main__":
    for key in ("BE", "CH", "ES", "IT-NO"):
        pair = sorted(["FR", key])
        print(fetch_exchange(ZoneKey(pair[0]), ZoneKey(pair[1]))[-2:])
