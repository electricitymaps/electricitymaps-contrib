# Australian direct emission factors

Open [AU_emission_factors.ipynb](AU_emission_factors.ipynb) for the methodology,
source selection, zone mappings, results and limitations for the 2024–25 NGER
reporting year. The notebook uses the same calculation as the tested Python
module, with no additional runtime dependencies beyond `uv sync --extra parsers`.
A Jupyter frontend with a kernel using that environment is needed to open and run
the notebook interactively.

From the repository root, reproduce the published CSV without Jupyter:

```sh
uv run python -m scripts.au_emission_factors \
  notebooks/au_emission_factors/nger_2024_25.csv \
  /tmp/au-emission-factors.csv
diff notebooks/au_emission_factors/results.csv /tmp/au-emission-factors.csv
uv run pytest tests/test_au_emission_factors.py
```

The output uses **scope 1 tonnes divided by gross electricity generation**,
weighted by generation within each zone and fossil-fuel mode. Deployment requires
reconciling gross generation with the generation basis of the production parsers
and adding the appropriate upstream emissions for lifecycle factors. No live zone
configuration is changed by this calculation.

## Data provenance

`nger_2024_25.csv` is the unchanged [official CER CSV](https://cer.gov.au/document/greenhouse-and-energy-information-designated-generation-facility-2024-25-0)
linked from the [2024–25 publication](https://cer.gov.au/markets/reports-and-data/nger-reporting-data-and-registers/electricity-sector-emissions-and-generation-data-2024-25),
retrieved on 29 October 2026. It is encoded in Windows-1252 and has SHA-256:

```text
cf29fbdbc46a802fe1c925b31aa0c4ad5b747af429c54f259f96745b9a73a648
```

Licensed from the Clean Energy Regulator, Commonwealth of Australia under a
[Creative Commons Attribution 4.0 licence](https://creativecommons.org/licenses/by/4.0/).
`results.csv` is derived from that data. The [CER copyright policy](https://cer.gov.au/about-us/our-policies/copyright)
describes reuse and attribution.
