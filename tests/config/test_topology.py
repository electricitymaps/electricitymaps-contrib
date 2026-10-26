from datetime import datetime, timezone

from electricitymap.contrib.config.topology import GRID_TOPOLOGY
from electricitymap.contrib.types import ZoneKey

BEFORE_CALABRIA = datetime(2020, 12, 31, 22, 59, tzinfo=timezone.utc)
AFTER_CALABRIA = datetime(2020, 12, 31, 23, tzinfo=timezone.utc)

IT = ZoneKey("IT")
IT_CA = ZoneKey("IT-CA")
IT_SIC = ZoneKey("IT-SIC")
IT_SIC_IT_SO = ZoneKey("IT-SIC->IT-SO")


def test_calabria_split_changes_the_topology():
    before = GRID_TOPOLOGY.at(BEFORE_CALABRIA)
    after = GRID_TOPOLOGY.at(AFTER_CALABRIA)

    assert IT_CA not in before.zones_config
    assert IT_CA not in before.zones_config[IT]["subZoneNames"]
    assert IT_CA not in before.zone_parent
    assert IT_SIC_IT_SO in before.exchanges_config
    assert IT_CA not in before.zone_neighbours[IT_SIC]
    assert "IT-SO" in before.zone_neighbours[IT_SIC]

    assert after.zone_parent[IT_CA] == IT
    assert IT_SIC_IT_SO not in after.exchanges_config
    assert "IT-SO" not in after.zone_neighbours[IT_SIC]
    assert after.zone_neighbours[IT_CA] == ["IT-SIC", "IT-SO"]
    assert IT_CA in after.all_neighbours[IT_SIC]


def test_instants_of_a_period_share_one_snapshot():
    assert GRID_TOPOLOGY.at(AFTER_CALABRIA) is GRID_TOPOLOGY.at(
        datetime(2021, 6, 1, tzinfo=timezone.utc)
    )
