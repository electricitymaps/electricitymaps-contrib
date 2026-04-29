#!/usr/bin/env python3

"""
Probe the ENTSO-E Transparency Platform for borders that publish A09
("Finalised Schedule" / day-ahead scheduled commercial exchanges).

The Transparency Platform has no "list-borders" endpoint, so discovery is
done by issuing one A09 query per candidate (in_Domain, out_Domain) pair
and observing whether the response is a Publication_MarketDocument with
TimeSeries (=> data) or an Acknowledgement_MarketDocument with
"No matching data found" (=> nothing on this border).

Defaults probe the Nordic bidding zones plus their direct neighbours.
Override with --zones / --neighbours to widen or narrow the sweep.

Usage:
    ENTSOE_TOKEN=... python scripts/probe_entsoe_a09_borders.py
    python scripts/probe_entsoe_a09_borders.py --target-date 2026-04-22
    python scripts/probe_entsoe_a09_borders.py --zones DK-DK1 DK-DK2 --neighbours DE-LU NL
"""

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import combinations

import re

from requests import Session

from electricitymap.contrib.parsers.ENTSOE import (
    ENTSOE_DOMAIN_MAPPINGS,
    ENTSOE_EXCHANGE_DOMAIN_OVERRIDE,
    query_exchange_forecast,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException

DEFAULT_ZONES = [
    "AX",
    "DK-DK1",
    "DK-DK2",
    "FI",
    "NO-NO1",
    "NO-NO2",
    "NO-NO3",
    "NO-NO4",
    "NO-NO5",
    "SE-SE1",
    "SE-SE2",
    "SE-SE3",
    "SE-SE4",
]

DEFAULT_NEIGHBOURS = ["DE-LU", "DE", "GB", "NL", "PL", "LT", "EE", "RU"]


@dataclass
class ProbeResult:
    zone_a: str
    zone_b: str
    direction: str  # "A->B" or "B->A"
    in_domain: str
    out_domain: str
    status: str  # "DATA", "EMPTY", "NONE", "ERROR"
    detail: str = ""


def domains_for(z1: str, z2: str) -> tuple[str, str]:
    """Resolve EIC domains for an EM zone pair, honouring exchange overrides.

    Returns (in_Domain, out_Domain) where in_Domain corresponds to z1 and
    out_Domain to z2.
    """
    key = f"{z1}->{z2}"
    rev = f"{z2}->{z1}"
    if key in ENTSOE_EXCHANGE_DOMAIN_OVERRIDE:
        a, b = ENTSOE_EXCHANGE_DOMAIN_OVERRIDE[key]
        return a, b
    if rev in ENTSOE_EXCHANGE_DOMAIN_OVERRIDE:
        a, b = ENTSOE_EXCHANGE_DOMAIN_OVERRIDE[rev]
        return b, a
    return ENTSOE_DOMAIN_MAPPINGS[z1], ENTSOE_DOMAIN_MAPPINGS[z2]


_TIMESERIES_OPEN_TAG = re.compile(r"<TimeSeries\b", re.IGNORECASE)


def has_timeseries(xml: str | None) -> bool:
    """Whether the XML body contains at least one TimeSeries element."""
    if not xml:
        return False
    return _TIMESERIES_OPEN_TAG.search(xml) is not None


def probe(
    z1: str,
    z2: str,
    session: Session,
    target_datetime: datetime,
) -> list[ProbeResult]:
    """Probe both directions of the (z1, z2) border for A09 data."""
    try:
        in_d, out_d = domains_for(z1, z2)
    except KeyError as e:
        return [
            ProbeResult(z1, z2, "->", "", "", "ERROR", f"unknown zone: {e}")
        ]

    results: list[ProbeResult] = []
    for direction, (a, b) in (("A->B", (in_d, out_d)), ("B->A", (out_d, in_d))):
        try:
            xml = query_exchange_forecast(
                a, b, session=session, target_datetime=target_datetime
            )
            if has_timeseries(xml):
                results.append(ProbeResult(z1, z2, direction, a, b, "DATA"))
            else:
                results.append(ProbeResult(z1, z2, direction, a, b, "EMPTY"))
        except ParserException as e:
            msg = str(e).strip() or "ParserException"
            status = "NONE" if "No matching data found" in msg else "ERROR"
            results.append(ProbeResult(z1, z2, direction, a, b, status, msg))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zones",
        nargs="+",
        default=DEFAULT_ZONES,
        help="EM zone keys to probe pairwise (default: Nordic bidding zones).",
    )
    parser.add_argument(
        "--neighbours",
        nargs="+",
        default=DEFAULT_NEIGHBOURS,
        help="External zones to probe against each --zones entry.",
    )
    parser.add_argument(
        "--target-date",
        help="UTC date (YYYY-MM-DD) to probe. Defaults to yesterday — A09 is "
        "published day-ahead so a recent past day gives the highest hit rate.",
    )
    parser.add_argument(
        "--include-internal",
        action="store_true",
        default=True,
        help="Probe pairs within --zones (default: on).",
    )
    parser.add_argument(
        "--no-internal", dest="include_internal", action="store_false"
    )
    parser.add_argument(
        "--include-external",
        action="store_true",
        default=True,
        help="Probe pairs between --zones and --neighbours (default: on).",
    )
    parser.add_argument(
        "--no-external", dest="include_external", action="store_false"
    )
    return parser.parse_args()


def resolve_target_datetime(s: str | None) -> datetime:
    if s is None:
        # A09 is day-ahead, so probing the previous full day at 00:00 UTC
        # gives the highest hit rate where the border actually publishes.
        today_utc = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return today_utc - timedelta(days=1)
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def main() -> int:
    args = parse_args()
    target_dt = resolve_target_datetime(args.target_date)

    pairs: list[tuple[str, str]] = []
    if args.include_internal:
        pairs.extend(combinations(args.zones, 2))
    if args.include_external:
        pairs.extend((z, n) for z in args.zones for n in args.neighbours)

    print(
        f"# Probing A09 (scheduled day-ahead exchanges) for {len(pairs)} "
        f"border(s) at {target_dt.isoformat()}",
        file=sys.stderr,
    )
    print("zone_a\tzone_b\tdirection\tstatus\tdetail")

    session = Session()
    summary: dict[str, int] = {"DATA": 0, "EMPTY": 0, "NONE": 0, "ERROR": 0}
    borders_with_data: set[tuple[str, str]] = set()

    for z1, z2 in pairs:
        for r in probe(z1, z2, session, target_dt):
            summary[r.status] = summary.get(r.status, 0) + 1
            if r.status == "DATA":
                a, b = sorted((r.zone_a, r.zone_b))
                borders_with_data.add((a, b))
            print(
                f"{r.zone_a}\t{r.zone_b}\t{r.direction}\t{r.status}\t{r.detail}"
            )

    print(
        f"\n# Summary: {summary}\n"
        f"# Borders with at least one direction publishing A09: "
        f"{len(borders_with_data)}",
        file=sys.stderr,
    )
    for a, b in sorted(borders_with_data):
        print(f"# DATA: {a} <-> {b}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
