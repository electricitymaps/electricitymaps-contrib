"""Lifespans of config entities (zones and exchanges).

An entity config may declare `active_from` (inclusive) and `active_to` (exclusive)
as ISO 8601 dates. A bound takes effect at midnight in the entity's `timezone`,
matching market reforms that start on a local delivery day, so an entity with a
bound must declare a timezone. A missing bound leaves that side open, so an entity
without either is active over all of history.
"""

from datetime import date, datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo


def parse_lifespan_bound(value: str | date | None) -> date | None:
    """Parses an `active_from`/`active_to` value into a date.

    Raises a ValueError on datetimes, as a lifespan bound is a whole local day.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        raise ValueError(f"Lifespan bound must be a date, got datetime {value!r}")
    return date.fromisoformat(value) if isinstance(value, str) else value


def start_of_local_day(day: date, timezone_name: str) -> datetime:
    """Returns the UTC instant at which the day starts in the given IANA timezone."""
    local_midnight = datetime.combine(day, time.min, tzinfo=ZoneInfo(timezone_name))
    return local_midnight.astimezone(timezone.utc)


def lifespan_instants(
    entity_config: dict[str, Any],
) -> tuple[datetime | None, datetime | None]:
    """Returns the UTC instants at which an entity config's lifespan starts and ends.

    Raises a ValueError when a bound is set without a `timezone`, as a date only
    maps to an instant within a timezone.
    """
    active_from = parse_lifespan_bound(entity_config.get("active_from"))
    active_to = parse_lifespan_bound(entity_config.get("active_to"))
    if active_from is None and active_to is None:
        return None, None
    timezone_name = entity_config.get("timezone")
    if timezone_name is None:
        raise ValueError("active_from and active_to require a timezone")
    return (
        start_of_local_day(active_from, timezone_name) if active_from else None,
        start_of_local_day(active_to, timezone_name) if active_to else None,
    )


def is_active(entity_config: dict[str, Any], at: datetime) -> bool:
    """Returns whether an entity config is active at the given aware datetime."""
    active_from, active_to = lifespan_instants(entity_config)
    return (active_from is None or active_from <= at) and (
        active_to is None or at < active_to
    )
