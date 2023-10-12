import unittest

from electricitymap.contrib.config.model import CONFIG_MODEL


class ConfigModelTestcase(unittest.TestCase):
    def test_pydantic_model(self):
        self.assertIn("DK-BHM->SE-SE4", CONFIG_MODEL.exchanges.keys())
        self.assertIn("US-NW-PSCO", CONFIG_MODEL.zones.keys())
        self.assertIsNotNone(
            CONFIG_MODEL.zones["US-NW-PSCO"].parsers.get_function("production")
        )

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

    def test_zone_sources(self):
        for _, zone in CONFIG_MODEL.zones.items():
            for _, production_mode in zone.emission_factors or ():
                for _, estimate in production_mode or ():
                    if estimate is None:
                        continue
                    estimates = estimate if isinstance(estimate, list) else [estimate]
                    for estimate in estimates:
                        source_list = estimate.source
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
                            self.assertIn(source, zone.sources)


if __name__ == "__main__":
    unittest.main(buffer=True)
