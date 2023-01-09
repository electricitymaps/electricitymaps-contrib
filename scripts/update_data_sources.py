""" This script aims at automatically updating the data sources file with sources listed in the zones config. """
import logging
from collections import namedtuple
from copy import copy
from pathlib import Path
from typing import Dict, List, Set

import arrow
import pandas as pd
import yaml

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.joinpath("config").resolve()
EMISSION_FACTORS_SOURCES_FILENAME = (
    Path(__file__).parent.parent.joinpath("EMISSION_FACTORS_SOURCES.md").resolve()
)

MD_CONTENT_HEADER = """
# Emission factors sources

This file describes data sources used for generating the emission factors for all zones.

It only describes zone specific emission factors. Our default emission factors come  from the [IPCC (2014) Fith Assessment Report](https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7) report, and are fully described in our [wiki](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Default-emission-factors).

## Zone specific emission factors

&nbsp;<details><summary>Click to see the full list of sources</summary>

"""


def _find_emission_factor_sources(
    zone_config: dict,
) -> Dict[str, Dict[str, Dict[str, str]]]:
    zone_sources = zone_config.get("sources", {})

    def _get_sources_for_type(_type: str) -> Dict[str, Dict[str, str]]:
        sources = {}
        for mode, ef in zone_config.get("emissionFactors", {}).get(_type, {}).items():
            sources_per_mode = {}
            if isinstance(ef, list):
                for _ef in ef:
                    for s in zone_sources:
                        if s in _ef.get("source"):
                            sources_per_mode[s] = zone_sources[s].get("link")
            else:
                for s in zone_sources:
                    if s in ef.get("source"):
                        sources_per_mode[s] = zone_sources[s].get("link")
            if sources_per_mode != {}:
                sources[mode] = sources_per_mode
        return sources

    sources = {
        "direct": _get_sources_for_type("direct"),
        "lifecycle": _get_sources_for_type("lifecycle"),
    }
    if sources["direct"] == {}:
        del sources["direct"]
    if sources["lifecycle"] == {}:
        del sources["lifecycle"]
    return sources


def read_zone_config(zone_key: str) -> dict:
    with open(CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml")) as f:
        return yaml.safe_load(f)


def update_data_sources() -> None:
    all_emission_factor_sources = {}

    for zone_key in sorted(CONFIG_DIR.joinpath("zones").glob("*.yaml")):
        zone_key = zone_key.stem
        zone_config = read_zone_config(zone_key)
        all_emission_factor_sources[zone_key] = _find_emission_factor_sources(
            zone_config
        )

    # Filter out empty sources
    all_emission_factor_sources = {
        k: v
        for k, v in all_emission_factor_sources.items()
        if v.get("direct", {}) != {} or v.get("lifecycle", {}) != {}
    }

    md_content = copy(MD_CONTENT_HEADER)

    for zone_key, sources in all_emission_factor_sources.items():
        zone_content = f"""
* {zone_key}
        """
        if "direct" in sources:
            zone_content += """
  * Direct emission factors
            """
            for mode, mode_sources in sources["direct"].items():
                zone_content += f"""
    * {mode}
                """
                for source, link in mode_sources.items():
                    # We must be careful to not add ";" in the sources
                    for i, _s in enumerate(source.split("; ")):
                        zone_content += f"""
      * [{_s}]({link.split(', ')[i]})
                """
        if "lifecycle" in sources:
            zone_content += """
  * Lifecycle emission factors
            """
            for mode, mode_sources in sources["lifecycle"].items():
                zone_content += f"""
    * {mode}
                """
                for source, link in mode_sources.items():
                    # We must be careful to not add ";" in the sources
                    for i, _s in enumerate(source.split("; ")):
                        zone_content += f"""
      * [{_s}]({link.split(', ')[i]})
                """
        md_content += zone_content

    md_content += """

    &nbsp;</details>
    """

    with open(EMISSION_FACTORS_SOURCES_FILENAME, "w") as f:
        f.write(md_content)


if __name__ == "__main__":
    update_data_sources()
