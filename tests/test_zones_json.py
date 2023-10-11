"""Tests for ZONE_CONFIG, config loaded from config/zones/*.yaml."""

import json
import unittest

from electricitymap.contrib.config import ZONES_CONFIG


class ZonesJsonTestcase(unittest.TestCase):
    # Add well-known sources that don't require config-based references here
    GLOBAL_SOURCE_REFERENCES = {
        "2018 average estimated from https://www.hops.hr/page-file/oEvvKj779KAhmQg10Gezt2/temeljni-podaci/Temeljni%20podaci%202018.pdf",
        "2020 average by Electricity Maps. See disclaimer",
        "BEIS 2021",
        "CEA 2022",
        "EIA 2020/BEIS 2021",
        "Enerdata 2022",
        "EU-ETS 2021",
        "EU-ETS, ENTSO-E 2021",
        "Guatemala AMM 2021-2022",
        "IEA 2019",
        "IEA 2020",
        'Oberschelp, Christopher, et al. "Global emission hotspots of coal power generation."',
        "Tidal (IPCC 2014)",
        "https://www.iea.org/data-and-statistics/charts/electricity-generation-mix-in-mexico-1-jan-30-sep-2019-and-2020",
    }

    def test_bounding_boxes(self):
        for zone, values in ZONES_CONFIG.items():
            bbox = values.get("bounding_box")
            if bbox:
                self.assertLess(bbox[0][0], bbox[1][0])
                self.assertLess(bbox[0][1], bbox[1][1])

    def test_sub_zones(self):
        zone_keys = set(ZONES_CONFIG.keys())
        for zone, values in ZONES_CONFIG.items():
            sub_zones = values.get("subZoneNames", [])
            for sub_zone in sub_zones:
                self.assertIn(sub_zone, zone_keys)

    def test_zone_sources(self):
        for _, config in ZONES_CONFIG.items():
            top_level_sources = config.get("sources", {}).keys()
            for _, production_modes in config.get("emissionFactors", {}).items():
                for production_mode, estimate in production_modes.items():
                    estimates = estimate if isinstance(estimate, list) else [estimate]
                    for estimate in estimates:
                        source_list = estimate.get("source")
                        if source_list is None:
                            continue
                        for source in source_list.split(";"):
                            source = source.strip()
                            if source.startswith("assumes"):
                                continue
                            if source.startswith("Electricity Maps"):
                                continue
                            if source in self.GLOBAL_SOURCE_REFERENCES:
                                continue
                            self.assertIn(source, top_level_sources)

    def test_zones_from_geometries_exist(self):
        world_geometries = json.load(open("web/geo/world.geojson"))
        world_geometries_zone_keys = set()
        for ft in world_geometries["features"]:
            world_geometries_zone_keys.add(ft["properties"]["zoneName"])
        all_zone_keys = set(ZONES_CONFIG.keys())
        non_existing_zone_keys = sorted(world_geometries_zone_keys - all_zone_keys)
        assert (
            len(non_existing_zone_keys) == 0
        ), f"{non_existing_zone_keys} are defined in world.geojson but not in zones/*.yaml"


if __name__ == "__main__":
    unittest.main(buffer=True)
