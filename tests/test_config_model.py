import unittest

from electricitymap.contrib.config.model import CO2EQ_CONFIG_MODEL, CONFIG_MODEL


class ConfigModelTestcase(unittest.TestCase):
    def test_pydantic_model(self):
        self.assertIn("DK-BHM->SE-SE4", CONFIG_MODEL.exchanges.keys())
        self.assertIn("US-NW-PSCO", CONFIG_MODEL.zones.keys())
        self.assertIsNotNone(
            CONFIG_MODEL.zones["US-NW-PSCO"].parsers.get_function("production")
        )

    # Add well-known sources that don't require config-based references here
    GLOBAL_SOURCE_REFERENCES = {
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
    }

    def test_zone_sources(self):
        for _, model in CO2EQ_CONFIG_MODEL:
            if not model.emission_factors:
                continue
            if not model.emission_factors.zone_overrides:
                continue
            for zone_key, zone_modes in model.emission_factors.zone_overrides.items():
                for mode, estimate in zone_modes or ():
                    if estimate is None:
                        continue
                    estimates = estimate if isinstance(estimate, list) else [estimate]
                    for estimate in estimates:
                        self.assertIsNotNone(
                            estimate.source,
                            msg=f"Source is required for {mode} in {zone_key}",
                        )
                        for source in estimate.source.split(";"):
                            source = source.strip()
                            if source.startswith("assumes"):
                                continue
                            if source.startswith("Electricity Maps"):
                                continue
                            if source in self.GLOBAL_SOURCE_REFERENCES:
                                continue
                            self.assertIn(source, CONFIG_MODEL.zones[zone_key].sources)


if __name__ == "__main__":
    unittest.main(buffer=True)
