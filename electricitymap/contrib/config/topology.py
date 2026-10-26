"""Grid topology as of a point in time.

Zones and exchanges can declare lifespans (see `lifespan.py`), so the set of zones,
their parent/sub-zone relations and the exchanges between them change over time.
The topology only changes on lifespan bounds, so history is split into periods
between consecutive bounds and each period's topology is built once, on first use.
"""

from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cache
from itertools import chain
from typing import Any

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG
from electricitymap.contrib.config.lifespan import is_active, lifespan_instants
from electricitymap.contrib.config.zones import (
    generate_all_neighbours,
    generate_zone_neighbours,
    zone_parents,
)
from electricitymap.contrib.types import ZoneKey

_BEGINNING_OF_TIME = datetime.min.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class GridSnapshot:
    """The zones and exchanges active during one period, with the relations
    derived from them. Snapshots are cached and shared between callers, so their
    contents must not be mutated."""

    zones_config: dict[ZoneKey, Any]
    exchanges_config: dict[ZoneKey, Any]
    zone_parent: dict[ZoneKey, ZoneKey]
    zone_neighbours: dict[ZoneKey, list[ZoneKey]]
    all_neighbours: dict[ZoneKey, list[ZoneKey]]


class GridTopology:
    """Resolves the grid topology of a set of zone and exchange configs at any
    point in time.

    A lookup costs a binary search over the lifespan bounds, and each period's
    snapshot is built at most once.
    """

    def __init__(
        self,
        zones_config: dict[ZoneKey, Any],
        exchanges_config: dict[ZoneKey, Any],
    ):
        self._zones_config = zones_config
        self._exchanges_config = exchanges_config
        bounds = {
            instant
            for config in chain(zones_config.values(), exchanges_config.values())
            for instant in lifespan_instants(config)
            if instant is not None
        }
        self._period_starts = sorted(bounds)
        self._snapshot_of_period = cache(self._build_snapshot)

    def at(self, at: datetime) -> GridSnapshot:
        """Returns the topology at the given aware datetime."""
        if at.tzinfo is None or at.tzinfo.utcoffset(at) is None:
            raise ValueError(f"Datetime must be timezone-aware, got {at!r}")
        return self._snapshot_of_period(bisect_right(self._period_starts, at))

    def _build_snapshot(self, period: int) -> GridSnapshot:
        # Every instant of a period shares the same topology, so its start
        # stands for the whole period.
        start = self._period_starts[period - 1] if period > 0 else _BEGINNING_OF_TIME

        zones_config = {
            zone_key: self._zone_config_at(config, start)
            for zone_key, config in self._zones_config.items()
            if is_active(config, start)
        }
        # The config model guarantees an exchange is only active while both its
        # zones are, so its own lifespan is enough.
        exchanges_config = {
            exchange_key: config
            for exchange_key, config in self._exchanges_config.items()
            if is_active(config, start)
        }
        return GridSnapshot(
            zones_config=zones_config,
            exchanges_config=exchanges_config,
            zone_parent=zone_parents(zones_config),
            zone_neighbours=generate_zone_neighbours(zones_config, exchanges_config),
            all_neighbours=generate_all_neighbours(exchanges_config),
        )

    def _zone_config_at(
        self, zone_config: dict[str, Any], at: datetime
    ) -> dict[str, Any]:
        """Returns a copy of the zone config listing only the sub-zones active at `at`."""
        zone_config = dict(zone_config)
        if "subZoneNames" in zone_config:
            zone_config["subZoneNames"] = [
                name
                for name in zone_config["subZoneNames"]
                if is_active(self._zones_config.get(name, {}), at)
            ]
        return zone_config


GRID_TOPOLOGY = GridTopology(ZONES_CONFIG, EXCHANGES_CONFIG)
