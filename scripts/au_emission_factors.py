"""Compute generation-weighted Australian direct emission factors from NGER data.

The input reports total generation, including a station's own consumption, rather
than electricity sent out. Results are gross-generation factors, not overrides
for the net-generation factors used by Electricity Maps.
"""

import csv
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

SCOPE_1_COLUMN = "Total scope 1 emissions \n(t CO2-e)"
GENERATION_COLUMN = "Electricity production (MWh)"

# NEM states map to the zones used by OPENNEM; the ACT is part of NSW1.
# WA and NT have several grids: do not assign NWIS, Mt Isa or off-grid plants
# to a zone solely from their state. AU-WA covers SWIS; AU-NT covers DKIS.
GRID_STATE_TO_ZONE = {
    ("NEM", "ACT"): "AU-NSW",
    ("NEM", "NSW"): "AU-NSW",
    ("NEM", "QLD"): "AU-QLD",
    ("NEM", "SA"): "AU-SA",
    ("NEM", "TAS"): "AU-TAS",
    ("NEM", "VIC"): "AU-VIC",
    ("SWIS", "WA"): "AU-WA",
    ("DKIS", "NT"): "AU-NT",
}
FUEL_TO_MODE = {
    "Black Coal": "coal",
    "Brown Coal": "coal",
    "Gas": "gas",
    "Coal Seam Methane": "gas",
    "Waste Coal Mine Gas": "gas",
    "Ethane": "gas",
    "Diesel": "oil",
    "Kerosene": "oil",
}


@dataclass
class EmissionFactor:
    zone: str
    mode: str
    generation_mwh: float = 0
    emissions_tco2e: float = 0
    reporting_records: int = 0

    @property
    def direct_gco2e_per_kwh(self) -> float:
        # 1 tonne/MWh = 1,000 g/kWh. Do not average the rounded intensity column.
        return 1000 * self.emissions_tco2e / self.generation_mwh


def _number(value: str) -> float:
    result = float(value.replace(",", ""))
    if not isfinite(result) or result < 0:
        raise ValueError(f"Expected a finite, non-negative NGER value, got {value!r}")
    return result


def calculate_factors(rows: list[dict[str, str]]) -> list[EmissionFactor]:
    """Aggregate reported scope 1 tonnes and gross MWh by zone and fossil mode.

    Only the explicitly documented duplicate Callide C report is removed.
    Different records for a same-named station (e.g. Moranbah) are retained:
    successive operators may report different parts of a reporting year.
    """
    totals: dict[tuple[str, str], EmissionFactor] = {}
    callide_reports: list[dict[str, str]] = []
    for row in rows:
        if row["Type"] != "F" or row["Grid connected"] != "On":
            continue
        zone = GRID_STATE_TO_ZONE.get((row["Grid"], row["State"]))
        mode = FUEL_TO_MODE.get(row["Primary fuel"])
        if zone is None or mode is None:
            continue
        generation = _number(row[GENERATION_COLUMN])
        emissions = _number(row[SCOPE_1_COLUMN])
        if generation == 0:
            # No per-kWh intensity can be inferred for a non-producing station.
            continue
        if row["Facility name"] == "Callide C Power Station":
            callide_reports.append(row)
            if len(callide_reports) > 1:
                first = callide_reports[0]
                if (
                    {first["Reporting entity"], row["Reporting entity"]}
                    != {"C S ENERGY LIMITED", "IG POWER HOLDINGS LIMITED"}
                    or any(
                        first[key] != row[key]
                        for key in (
                            "State",
                            "Grid",
                            "Primary fuel",
                            GENERATION_COLUMN,
                            SCOPE_1_COLUMN,
                        )
                    )
                    or len(callide_reports) > 2
                ):
                    raise ValueError(
                        "Unexpected Callide C reports: review deduplication"
                    )
                continue
        key = (zone, mode)
        if key not in totals:
            totals[key] = EmissionFactor(zone=zone, mode=mode)
        totals[key].generation_mwh += generation
        totals[key].emissions_tco2e += emissions
        totals[key].reporting_records += 1
    return [totals[key] for key in sorted(totals)]


def read_nger(path: Path) -> list[dict[str, str]]:
    # The CER download uses Windows-1252 (including an en dash in facility names).
    with path.open(encoding="cp1252", newline="") as source:
        return list(csv.DictReader(source))


def write_factors(factors: list[EmissionFactor], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(
            [
                "zone",
                "mode",
                "reporting_records",
                "gross_generation_mwh",
                "scope_1_emissions_tco2e",
                "direct_gco2e_per_kwh",
            ]
        )
        for factor in factors:
            writer.writerow(
                [
                    factor.zone,
                    factor.mode,
                    factor.reporting_records,
                    f"{factor.generation_mwh:.0f}",
                    f"{factor.emissions_tco2e:.0f}",
                    f"{factor.direct_gco2e_per_kwh:.2f}",
                ]
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CER designated-facility CSV")
    parser.add_argument("output", type=Path, help="Calculated direct factors CSV")
    args = parser.parse_args()
    write_factors(calculate_factors(read_nger(args.input)), args.output)
