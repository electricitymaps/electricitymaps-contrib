# Capacity update process <a name="#top"></a>

## Table of contents

- [Context](#context)
- [Capacity source](#capacity_sources)
- [Capacity update process](#capacity_update_process)
  - [When should capacity data be updated?](#when_to_update)
  - [Format of the capacity configuration](#format)
  - [Opening a PR](#PR)
  - [The zone capacity can be updated automatically](#automatic_update)
  - [The zone capacity is updated manually](#manual_update)
- [Technical requirements for adding a new data source](#technical_requirements)
- [Building a new capacity parser](#building_a_parser)

## Context <a name="#context"></a>

In an effort to increase the quality of the data published on our app or API, we have started a whole initiative to enable us to track outliers in the source data. You can find more information on this [wiki page](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Capacity-update-process).

## Capacity sources <a name="capacity_sources"></a>

[(back to top)](#top)

Of all electricity data available, capacity is probably the least consistent (e.g. different reporting standards, different update frequencies, accessibility). A review of available capacity data was done in order to manage the number of different data sources used for capacity and to ensure that the capacity data has been reviewed and has an overall consistent quality level.

The main organisations that published capacity data are:

- **[EIA](https://www.eia.gov/electricity/data/eia860/)**: The EIA publishes generator-level specific information about existing and planned generators and associated environmental equipment at electric power plants with 1 megawatt or greater of combined nameplate capacity. This data is available in the EIA API and can be aggregated by balancing authority.
- **[EMBER](https://ember-climate.org/)**: EMBER aggregates data from different sources:
  - IRENA for non-fossil generation,
  - Global Energy Monitor for coal and gas generation,
  - World Resource Institue, although this datbase is incomplete is can be used to verify information from the other sources.
- **[ENTSO-e](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)**: Net generation capacity is published on an annual basis on the ENTSO-e Transparency platform. This will be the prefered data source for European zones as the capacity breakdown is more detailed.
- **[IRENA](https://www.irena.org/Data/Downloads/IRENASTAT)**: For most countries and technologies, the data reflects the capacity installed and connected at the end of the calendar year. Data has been obtained from a variety of sources, including an IRENA questionnaire, official national statistics, industry association reports, other reports and news articles.

In the case of countries divided in subzones, capacity data is collected directly from the main data source. This is the case for Brasil, Australia or Spain for instance.

## Capacity update process <a name="capacity_update_process"></a>

[(back to top)](#top)

There are two ways of updating capacity configuration files:

- The zone has a capacity parser
- The update must be done manually.

### When should capacity data be updated? <a name="when_to_update"></a>

[(back to top)](#top)

Depending on the source, capacity data can be updated at a more or less regular frequency.

In the case of EMBER, IRENA and ENTSO-e, capacity data is updated once a year with data for the previous year. This update usually happens in the third quarter of the year (June to September of Y+1). The capacity for these zones should therefore be updated **once per year**.

The EIA updates their capacity dataset on a monthly basis so updates can happen **every semester or every quarter**.

We would like to update the capacity data for **all zones** once per year, around the 3rd quarter. This can be done more for capacity that are updated every month or quarter but it is not absolutely required.

### Format of the capacity configuration <a name="format"></a>

[(back to top)](#top)

The capacity configuration should include the date from which the value is valid.

For a chosen mode, a data point needs to include the following fields:

- **value**: the installed capacity for the chosen mode,
- **datetime**: from this date forward, the value is considered to be the most up-to-date
- **source**: the data source

This format will enable us to track the evolution of capacity across different zones over time such as the increase of renewables or phase out of fossil power plants.

Looking at the example of DK-DK1 mentioned above, the capacity configuration format would be the following:

```
capacity
├── wind
    ├── datetime: "2023-01-01"
    ├── source: "ENTSOE"
    └── value: 5233
```

### Opening a PR <a name="PR"></a>

[(back to top)](#top)

Before opening a PR to update capacity data, you should check the following:

- **Do not update all capacities at once!** Smaller PRs will help us make sure that no error slips through the cracks. We recommend updated a few zones at once or by group of zones (EIA, ENTSOE, EMBER, IRENA etc.)
- **The new data points are consistent with the previous ones.** Big breaks in trends are rare for capacity data. You should check whether the variation between two data points is realistic. We expect that renewable capacity will increase in the coming years and fossil capacity to decrease,so these are patterns to look out for.
- **Reference main changes in the PR description**. If you spot a major change in values, please mention it and verify it. This will make the reviewer's job easier!

### The zone capacity can be updated automatically <a name="automatic_update"></a>

[(back to top)](#top)

For some zones, we have developed capacity parsers which collect the data automatically.

The update of capacity configurations can be done in the `contrib` repo using `poetry run capacity_parser`.

The `capacity_parser` function has the following arguments:
| Argument | Description |
|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --zone | A specific zone (e.g. DK-DK1) |
| --source | A group of zones. The capacity update will run for all the zones that have capacity from this data source. The groups of zones are: EIA, EMBER, ENTSOE, IRENA, ONS, OPENNEM, REE |
| --target_datetime | Date for the capacity data (e.g. "2023-01-01") |

Here is a list of examples:

```{python}
poetry run capacity_parser --zone DK-DK1 --target_datetime "2023-01-01"
```

```{python}
poetry run capacity_parser --source EIA --target_datetime "2023-06-01"
```

The following zones can be updated with a parser are listed on our wiki page [Capacity update process](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Capacity-update-process)

### The zone capacity is updated manually <a name="manual_update"></a>

[(back to top)](#top)

For more information on manual capacity updates, please check our wiki page [Manual capacity updates](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Manual-capacity-updates).

## Technical requirements for adding a new data source <a name="technical_requirements"></a>

[(back to top)](#top)

If a new data source becomes available for a zone that does **not** have a capacity parser:

- **Verify the data source.** Please refer to our wiki page [Verify data sources](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Verify-data-sources). The data should come from an authoritative data source, the criteria are listed on the wiki page.
- **Update this document with the new data source**. For maintainability and transparency reasons, the data should be easily accessible. This will enable another contributor to update the capacity breakdown in the future. You can create a new subsection in [The zone capacity is updated manually](#manual_update)
- **Add the guidelines to collect the data**. This should also be done for maintainability and transparency reasons.

If the capacity for the zone in question is collected using a capacity parser:

- **Verify the data source.**
- **Compare the new data with the existing data.** As explained above, we want to limit the number of data sources used and wish to use sources for which a certain level of quality is implied.
- **Discuss with the Electricity Maps team.** If the new data source is indeed of higher quality and meets all the requirements, feel free to ask the Electricity Maps team. We will find the best way forward otgether :)

You can create an issue on [contrib](https://github.com/electricitymaps/electricitymaps-contrib/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc) if you find a new data source or if an existing link is broken.

## Building a new capacity parser <a name="building_a_parser"></a>

[(back to top)](#top)

If data can be parsed from an online source, you can build a parser to automatically get this data.

Here are the following steps to build a capacity parser:

- **Building the parser.** The parser should include a `fetch_production_capacity` function.

```{python}
def fetch_production_capacity(zone_key: ZoneKey, target_datetime: datetime, session:Session)-> Dict[str:Any]:
  capacity_dict = ....
  return capacity_dict
```

- **Update the zone configuration.** Add the productionCapacity parser to the parsers items.

```
parsers:
  consumption: FR.fetch_consumption
  production: FR.fetch_production
  productionCapacity: ENTSOE.fetch_production_capacity
```
