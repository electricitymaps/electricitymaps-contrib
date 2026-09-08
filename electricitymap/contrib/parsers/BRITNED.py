#!/usr/bin/env python3

"""
Parser for the BritNed Empire auction platform.

Endpoint: https://api.empire.britned.com
Spec: https://github.com/britned/empire-platform-api (`openapi.yaml`)
Auth: none. The `/v1/public/*` paths carry no `security` requirement, and BritNed
publishes auction schedules, results and aggregated nominations without an account.

BritNed (the GB<->NL interconnector, operated by BritNed Development Limited) is the
one GB border that is neither implicitly coupled nor auctioned through JAO today. It
runs its own explicit auctions — long term, day ahead and intraday — on Empire.

It did not always. JAO ran the daily auctions for the corridors `BDL-GB-NL` /
`BDL-NL-GB` (BDL for BritNed Development Limited, the same prefix Empire uses in
`displayId`) up to and including the **2023-09-17** market day, after which BritNed
moved allocation onto Empire. `getauctions` still knows the corridor names and still
serves that pre-cutover history, but returns "No Data found" for every horizon from
2023-10 onward. So `JAO_Auctions.py` cannot serve current data for this border and
deliberately omits it — while a backfill reaching before the cutover would need JAO,
not this parser.

Things this API does differently from JAO's Auction API:

1. Capacities are in **kW**, not MW. A 1000 MW cable reports 1016000.
2. Day-ahead auctions are *not* on `/v1/public/auctions` — that lists long-term
   products only. They live under `/v1/public/allocated-auctions`, which is also
   where the history sits.
3. Each direction is a separate auction object with its own id, so a delivery day is
   two auctions (`borderDirection` `GB_NL` and `NL_GB`) and needs two detail calls.
4. Both `limit` and `offset` are mandatory on list endpoints; omitting either is a
   400, not a default.
5. Timestamps are UTC with a `Z` suffix, which `datetime.fromisoformat` cannot parse
   before Python 3.11 — see `_parse_empire_datetime`.
6. There is a per-MTU field called `atc`, and it is **not** the one to read — it is
   measurably 0 on this border because BritNed sells its whole capability long-term
   and resells whatever comes back un-nominated. The day-ahead capacity is `finalOc`.
   `_auction_mtu_capacity` explains the allocation mechanism behind that.

Currently wired (day-ahead horizon):
- fetch_auction_atc_day_ahead  ->  per-MTU offered capacity in both directions
"""

from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import ExchangeAtcList
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.session import mount_retry
from electricitymap.contrib.types import AtcType

PARSER = "BRITNED.py"
SOURCE = "britned.com"
BASE_URL = "https://api.empire.britned.com"
REQUEST_TIMEOUT_SECONDS = 30

# The only border this platform serves. Empire is BritNed's own system, so unlike the
# JAO parsers there is no mapping table to grow — a second border here would mean a
# second interconnector had adopted Empire, which would need its own review.
BRITNED_EXCHANGE_KEY = ZoneKey("GB->NL")

# `borderDirection` values, expressed against the sorted zone key "GB->NL": GB_NL is
# capacity for flow out of zone1 (export), NL_GB is capacity into zone1 (import).
DIRECTION_EXPORT = "GB_NL"
DIRECTION_IMPORT = "NL_GB"

# `limit` is capped at 100 by the spec. A day is two auctions, so one page covers the
# fetch window comfortably; the parser still pages properly rather than relying on it.
PAGE_LIMIT = 100

# One list call plus two detail calls per delivery day, so the window trades request
# count against backfill speed. A week keeps a single refetch under ~15 requests.
BRITNED_MAX_FETCH_DAYS = 7

# Empire publishes hourly products today but the spec allows 15- and 30-minute MTUs,
# and European markets are moving that way. Derive the event duration from the
# auction's own `allocationMtuSize` rather than assuming an hour.
MTU_SIZE_TO_DURATION: dict[str, timedelta] = {
    "MTU_15_MINS": timedelta(minutes=15),
    "MTU_30_MINS": timedelta(minutes=30),
    "MTU_60_MINS": timedelta(minutes=60),
}

KW_PER_MW = 1000


def _parse_empire_datetime(value: str) -> datetime:
    """Parse an Empire timestamp ("2026-08-27T22:00:00Z") as tz-aware UTC.

    `datetime.fromisoformat` only learned to accept the "Z" suffix in Python 3.11 and
    this repo targets 3.10, so the suffix is normalised first.
    """
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_utc(dt: datetime) -> str:
    """Format a tz-aware datetime the way Empire's MTU query parameters expect."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _target_window(
    target_datetime: datetime | None,
    days: int = BRITNED_MAX_FETCH_DAYS,
) -> tuple[datetime, datetime]:
    """Return the UTC window to request for `target_datetime`.

    The delivery-period filter matches on *overlap*, not containment: an auction is
    returned whenever its delivery period intersects the window, so a window an hour
    long inside a market day still returns that day's auctions. Touching only at a
    boundary does not count — the comparison is half-open.

    That is what makes plain UTC midnight a safe lower bound here. BritNed market days
    run CET/CEST midnight to midnight, i.e. they *start* at 22:00 UTC (summer) or 23:00
    UTC (winter) on the preceding calendar day, so under a containment filter a
    midnight bound would clip the target day's own auction entirely. Under overlap it
    does not, because midnight falls strictly inside that period. Verified against the
    live API rather than assumed — an earlier version of this parser reached back an
    extra day to defend against the containment reading, which was unnecessary and
    silently pulled in the previous market day too.
    """
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)
    elif target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    day_start = datetime.combine(
        target_datetime.astimezone(timezone.utc).date(),
        time.min,
        tzinfo=timezone.utc,
    )
    return day_start, day_start + timedelta(days=days)


def _query_empire(
    session: Session,
    path: str,
    params: dict | None,
    logger: Logger,
) -> dict:
    """GET a public Empire endpoint and return the decoded body."""
    url = f"{BASE_URL}{path}"
    logger.debug("Querying Empire", extra={"path": path, "params": params})
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    if not response.ok:
        raise ParserException(
            parser=PARSER,
            message=f"{path}: HTTP {response.status_code} {response.text[:200]}",
            zone_key=BRITNED_EXCHANGE_KEY,
        )
    return response.json() or {}


def _list_day_ahead_auctions(
    session: Session,
    from_utc: datetime,
    to_utc: datetime,
    logger: Logger,
) -> list[dict]:
    """List every day-ahead auction whose delivery period sits inside the window.

    Returns both directions, one object per direction per delivery day. An empty list
    is a routine answer — BritNed can cancel a day-ahead auction on a cable outage —
    so it must not be treated as an error.
    """
    auctions: list[dict] = []
    offset = 0
    while True:
        body = _query_empire(
            session,
            "/v1/public/allocated-auctions",
            {
                "sortBy": "DELIVERY_PERIOD_START_ASC",
                "limit": PAGE_LIMIT,
                "offset": offset,
                "timescales": "DAY_AHEAD",
                "deliveryPeriodStart": _format_utc(from_utc),
                "deliveryPeriodEnd": _format_utc(to_utc),
            },
            logger,
        )
        entries = body.get("entries") or []
        auctions.extend(entries)
        total = body.get("totalCount") or 0
        # Guard on the page being empty as well as on the count: a short page would
        # otherwise loop forever if `totalCount` ever disagreed with what is served.
        if not entries or len(auctions) >= total:
            return auctions
        offset += len(entries)


def _auction_mtu_capacity(
    auction: dict, logger: Logger
) -> dict[datetime, tuple[datetime, float]]:
    """Map each MTU of one auction to its (end, offered capacity in MW).

    We read `finalOc`. Empire also publishes a field literally called `atc`, and that
    one is wrong for us — the reason is the allocation mechanism, so it is worth
    setting out rather than leaving as a rule to memorise.

    BritNed sells almost its entire capability on long-term products, months or years
    before delivery. Holders of those long-term rights must declare, at the long-term
    nomination deadline, whether they actually intend to use them. Whatever they do not
    nominate is handed back and resold in the day-ahead auction (UIoSI / UIoLI — Use It
    Or Sell It / Lose It). In practice most of it comes back: nearly everything BritNed
    auctions day-ahead is recycled long-term capacity, not capacity that was withheld
    from the long-term timeframe in the first place.

    Empire's four per-MTU fields sit at two different points in that sequence:

      atc                  NTC - TRM - *all* long-term allocations   (pre-nomination)
      preliminaryOc        OC reserved at auction creation, before returns are known
      unNominatedCapacity  long-term rights handed back at the nomination deadline
      finalOc              preliminaryOc + unNominatedCapacity        (post-nomination)

    So both `atc` and `finalOc` are ATC — they differ in whether long-term rights that
    were allocated but then *returned* still count as allocated. `atc` stops the
    subtraction before the nomination deadline and therefore reads 0 whenever the cable
    was fully sold long-term, which here is always: measured 0 in **720 of 720 MTUs**
    sampled across 2024-03 to 2026-08. Using it would report a permanently closed
    border while every field validated cleanly. `finalOc` continues the subtraction
    past the deadline, netting off only the long-term capacity actually nominated, and
    is therefore the capacity genuinely available to the day-ahead timeframe. The
    identity `finalOc == preliminaryOc + unNominatedCapacity` held in 720/720 of that
    same sample.

    Two independent checks that `finalOc` is the right quantity, which matter more than
    the argument above:

    - It reconciles with a second source. ENTSOE's day-ahead NTC for GB->NL publishes
      1016-1046 MW (symmetric), and `(export + import) / 2` over the same hours is
      1016-1046 MW. The half-sum reconstructs the published NTC exactly.
    - It is the same construct `JAO_Auctions.py` stores (`offeredCapacity`), so this
      border stays comparable with the other `atcDayAhead` borders instead of being an
      outlier.

    The consequence for consumers, and why the raw directional value must not be used
    as a bound: because returned rights reconstitute the cable, a single direction can
    exceed the cable's own rating. Single-direction `finalOc` ranged 559-1511 MW and
    exceeded the border's 1000 MW config capacity in 525 of 720 MTUs, while the
    half-sum stayed in that tight 1016-1046 MW band (median 1032) for all 360 paired
    MTUs. The envelope is `(export + import) / 2`; see the fetcher docstring and
    DAT-477.

    Caveat: `atc` being 0 is an observation over 2.5 years, not a guarantee. Were
    BritNed to start withholding capacity from long-term products it would go positive,
    and whether `preliminaryOc` still subsumes it would need rechecking.
    """
    mtu_size = auction.get("allocationMtuSize")
    duration = MTU_SIZE_TO_DURATION.get(mtu_size) if mtu_size else None
    if duration is None:
        logger.error(
            f"Empire auction {auction.get('displayId')} has unknown "
            f"allocationMtuSize {mtu_size!r}; skipping it"
        )
        return {}

    capacity_by_datetime: dict[datetime, tuple[datetime, float]] = {}
    for mtu in auction.get("mtus") or []:
        offered = mtu.get("finalOc")
        if offered is None:
            continue
        start = _parse_empire_datetime(mtu["mtu"])
        capacity_by_datetime[start] = (start + duration, offered / KW_PER_MW)
    return capacity_by_datetime


@refetch_frequency(timedelta(days=BRITNED_MAX_FETCH_DAYS))
def fetch_auction_atc_day_ahead(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Day-ahead ATC for GB<->NL from the BritNed Empire platform.

    **Which quantity this returns.** Empire publishes a per-MTU field called `atc` and
    another called `finalOc`. Both are ATC; they differ in where the subtraction stops.
    BritNed sells almost its whole capability on long-term products, and holders must
    declare at the long-term nomination deadline whether they will actually use those
    rights — whatever they do not nominate is handed back and resold day-ahead
    (UIoSI / UIoLI). `atc` subtracts *all* long-term allocations, so it stops before
    that deadline and reads 0 whenever the cable was fully sold long-term, which on
    this border is always (0 in 720 of 720 MTUs sampled 2024-03 to 2026-08). `finalOc`
    subtracts only the long-term capacity actually nominated, so it is the capacity
    genuinely available to the day-ahead timeframe. We return `finalOc`, in MW.
    `_auction_mtu_capacity` carries the full field breakdown and the measurements.

    Tagged AtcType.EXPLICIT_AUCTION. Neither direction bounds physical flow on its
    own: BritNed sells directional rights that buyers nominate, and the two directions
    are cross-netted, so each published value already embeds whatever the opposite
    direction has committed. Measured on delivery day 2026-08-29, the two directions
    sum to 2032-2076 MW on a ~1000 MW cable and the GB->NL value alone reaches 1146 MW
    — above the cable's own rating — while the half-sum tracks the rating. Consumers
    must use `(export + import) / 2` as the envelope, exactly as for the cross-netted
    JAO corridors; see DAT-477.
    """
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    if sorted_zone_keys != BRITNED_EXCHANGE_KEY:
        raise ParserException(
            parser=PARSER,
            message=(
                f"BritNed Empire only serves {BRITNED_EXCHANGE_KEY}, "
                f"got {sorted_zone_keys}"
            ),
            zone_key=sorted_zone_keys,
        )

    from_utc, to_utc = _target_window(target_datetime)
    session = mount_retry(session or Session())

    export_by_dt: dict[datetime, tuple[datetime, float]] = {}
    import_by_dt: dict[datetime, tuple[datetime, float]] = {}
    for auction in _list_day_ahead_auctions(session, from_utc, to_utc, logger):
        direction = auction.get("borderDirection")
        if direction == DIRECTION_EXPORT:
            accumulator = export_by_dt
        elif direction == DIRECTION_IMPORT:
            accumulator = import_by_dt
        else:
            logger.error(
                f"Empire auction {auction.get('displayId')} has unexpected "
                f"borderDirection {direction!r}; skipping it"
            )
            continue
        detail = _query_empire(
            session, f"/v1/public/auctions/day-ahead/{auction['id']}", None, logger
        )
        accumulator.update(_auction_mtu_capacity(detail, logger))

    capacities = ExchangeAtcList(logger)
    for dt in sorted(set(export_by_dt) | set(import_by_dt)):
        export = export_by_dt.get(dt)
        import_ = import_by_dt.get(dt)
        # One direction can be missing when only that auction was cancelled, so take
        # the end from whichever side is present rather than assuming both are. `dt`
        # comes from the union of the two maps, so at least one is always set.
        present = export or import_
        if present is None:
            continue
        end_datetime = present[0]
        capacities.append(
            zoneKey=sorted_zone_keys,
            datetime=dt,
            end_datetime=end_datetime,
            source=SOURCE,
            capacityExport=export[1] if export else None,
            capacityImport=import_[1] if import_ else None,
            atcType=AtcType.EXPLICIT_AUCTION,
        )
    return capacities.to_list()


if __name__ == "__main__":
    from pprint import pprint

    pprint(fetch_auction_atc_day_ahead(ZoneKey("GB"), ZoneKey("NL")))
