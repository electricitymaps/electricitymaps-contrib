"""Regression tests for NL's ``_fetch_dk1_exchange`` helper.

These tests pin down the anti-churn behaviour of the helper that fixes a
data-churn bug: ``DK.fetch_exchange`` returns a single *calendar day* of 5-min
data keyed off ``target_datetime``'s date, while NL's other inputs use a rolling
``[target-1d, target]`` window. By fetching *both* the current and previous
calendar day and averaging the 5-min flows to the hour, every hour in NL's
rolling window is built from a complete set of 5-min points regardless of which
day a refetch targets, so the derived hourly value no longer flip-flops between
refetches.

The tests are pure unit tests: ``DK.fetch_exchange`` is monkeypatched with a
fake that mimics the real calendar-day behaviour, so no HTTP is performed.
"""

from datetime import datetime, timedelta, timezone

import pytest

from electricitymap.contrib.parsers import NL

UTC = timezone.utc

# A concrete UTC date for "day D", deliberately away from any DST boundary.
D = datetime(2024, 3, 12, tzinfo=UTC)

# The sorted zone-key pair NL produces for the NL<->DK-DK1 exchange.
SORTED_ZONE_KEYS = "DK-DK1->NL"
SOURCE = "energidataservice.dk"


def _ramp_net_flow(point: datetime) -> float:
    """A deterministic ``netFlow`` ramp keyed purely off the clock time.

    The value is a function of the *absolute* UTC time only, so a given 5-min
    timestamp produces the same flow no matter which calendar-day fetch returned
    it. Within any hour the 12 points carry the minutes {0, 5, ..., 55}, whose
    mean is 27.5; the hour component contributes ``hour * 100``. Hence the hourly
    mean for hour ``h`` is exactly ``h * 100 + 27.5``.
    """
    return point.hour * 100 + point.minute


def _expected_hourly_mean(hour: datetime) -> float:
    """The exact hourly mean implied by ``_ramp_net_flow`` for a given hour."""
    return round(hour.hour * 100 + 27.5, 3)


def _build_fake_fetch_exchange(calls: list[datetime]):
    """Build a fake ``DK.fetch_exchange`` that mimics real calendar-day behaviour.

    Each invocation records its ``target_datetime`` and returns 5-min exchange
    points spanning the *whole calendar day* of that ``target_datetime`` (00:00
    through 23:55 UTC), exactly like the real DK parser (``start=target.date()``,
    ``end=target.date()+1d``).
    """

    def fake_fetch_exchange(zone_key1, zone_key2, session, target_datetime, logger):  # noqa: ANN001 - matches DK.fetch_exchange signature loosely
        calls.append(target_datetime)
        day_start = target_datetime.astimezone(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        points = []
        # 12 points per hour * 24 hours = 288 five-minute points.
        for step in range(0, 24 * 60, 5):
            point = day_start + timedelta(minutes=step)
            points.append(
                {
                    "datetime": point,
                    "netFlow": _ramp_net_flow(point),
                    "sortedZoneKeys": SORTED_ZONE_KEYS,
                    "source": SOURCE,
                    "sourceType": "measured",
                }
            )
        return points

    return fake_fetch_exchange


@pytest.fixture
def dk_calls(monkeypatch):
    """Patch ``NL.DK.fetch_exchange`` with the fake and expose recorded calls."""
    calls: list[datetime] = []
    monkeypatch.setattr(NL.DK, "fetch_exchange", _build_fake_fetch_exchange(calls))
    return calls


def _run(target_datetime, session=None, logger=None):
    return NL._fetch_dk1_exchange(
        zone_key="NL",
        session=session,
        target_datetime=target_datetime,
        logger=logger or NL.getLogger("test_NL"),
    )


def test_fetches_both_current_and_previous_day(dk_calls):
    """It fetches DK-DK1 for both ``target`` and ``target - 1 day``."""
    target = D.replace(hour=12)

    _run(target)

    assert len(dk_calls) == 2
    assert set(dk_calls) == {target, target - timedelta(days=1)}


def test_covers_previous_day_hours_the_regression(dk_calls):
    """Hours on day D-1 are present even when targeting noon of day D.

    This is the hour the OLD single-day fetch (which only covered day D) would
    have missed, producing the churn.
    """
    target = D.replace(hour=12)

    df = _run(target)

    prev_day_hour = (D - timedelta(days=1)).replace(hour=18)
    hours = set(df["datetime"])
    assert prev_day_hour in hours, (
        f"expected {prev_day_hour} to be covered; a single-day fetch of {target.date()} "
        "would NOT have covered any hour on the previous day"
    )

    # Sanity check that a single-day fetch of D indeed would not cover D-1 18:00:
    # every point returned for target=D lands on D's date, never D-1.
    single_day_calls: list[datetime] = []
    single_day_points = _build_fake_fetch_exchange(single_day_calls)(
        "DK-DK1", "NL", None, target, None
    )
    assert all(p["datetime"].date() == target.date() for p in single_day_points)


def test_hourly_value_is_stable_across_alignment(dk_calls):
    """The hourly netFlow for a settled hour is identical across refetch alignments.

    This is the core anti-churn property: a settled hour well inside the overlap
    must produce the same hourly mean whether the refetch targets ``D 12:00`` or
    ``(D-1) 23:00``.
    """
    settled_hour = (D - timedelta(days=1)).replace(hour=18)

    df_from_day_d = _run(D.replace(hour=12))
    df_from_prev_day = _run((D - timedelta(days=1)).replace(hour=23))

    value_d = df_from_day_d.loc[
        df_from_day_d["datetime"] == settled_hour, "netFlow"
    ].iloc[0]
    value_prev = df_from_prev_day.loc[
        df_from_prev_day["datetime"] == settled_hour, "netFlow"
    ].iloc[0]

    assert value_d == value_prev


def test_hourly_value_equals_mean_of_twelve_five_minute_points(dk_calls):
    """An hour's value equals the rounded mean of its twelve 5-min points."""
    target = D.replace(hour=12)

    df = _run(target)

    settled_hour = (D - timedelta(days=1)).replace(hour=18)
    value = df.loc[df["datetime"] == settled_hour, "netFlow"].iloc[0]

    # Ramp mean for hour 18 == 18*100 + mean(0,5,...,55) == 1800 + 27.5 == 1827.5
    assert value == _expected_hourly_mean(settled_hour)
    assert value == 1827.5

    # And the carried-through metadata columns survive the aggregation.
    row = df.loc[df["datetime"] == settled_hour].iloc[0]
    assert row["sortedZoneKeys"] == SORTED_ZONE_KEYS
    assert row["source"] == SOURCE
