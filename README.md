# electricitymap [![Slack Status](http://slack.tmrow.co/badge.svg)](http://slack.tmrow.co)
 
A real-time visualisation of the Greenhouse Gas (in terms of CO2 equivalent) footprint of electricity generation built with [d3.js](https://d3js.org/), optimized for Google Chrome. Try it out at [http://www.electricitymap.org](http://www.electricitymap.org).


![image](https://cloud.githubusercontent.com/assets/1655848/20340757/5ada5cf6-abe3-11e6-97c4-e68929b8a135.png)

You can [contribute](#contribute) by correcting data sources, translating the map or by writing a parser to add a new country on the map. See the [contributing](#contribute) section.
You can also submit ideas, feature requests or bugs on the [issues](https://github.com/corradio/electricitymap/issues) page.


## Data sources

### Carbon intensity calcuation and data source
The carbon intensity of each country is measured from the perspective of a consumer. It represents the greenhouse gas footprint of 1 kWh consumed inside a given country. The footprint is measured in gCO2eq (grams CO2 equivalent), meaning each greenhouse gas is converted to its CO2 equivalent in terms of global warming potential over 100 year (for instance, 1 gram of methane emitted has the same global warming impact during 100 years as ~20 grams of CO2 over the same period).

The carbon intensity of each type of power plant takes into account emissions arising from the whole lifecyle of the plant (construction, fuel production, operational emissions, and decomissioning). Carbon-intensity factors used in the map are detailed in [co2eq-parameters.js](https://github.com/corradio/electricitymap/blob/master/shared/co2eq_parameters.js). These numbers come from the following scientific peer reviewed litterature: 
- IPCC 2014 Assessment Report is used as reference in most instances (see a summary in the [wikipedia entry](https://en.wikipedia.org/wiki/Life-cycle_greenhouse-gas_emissions_of_energy_sources#2014_IPCC.2C_Global_warming_potential_of_selected_electricity_sources))

Country-specific carbon-intensity factors:
- Estonia:
  - Oil Shale: [EASAC (2007) "A study on the EU oil shale industry – viewed in the light of the Estonian experience"](www.easac.eu/fileadmin/PDF_s/reports_statements/Study.pdf)
- Norway:
  - Hydro: [Ostford Research (2015) "The inventory and life cycle data for Norwegian hydroelectricity"](http://ostfoldforskning.no/en/publications/Publication/?id=1236)

Each country has a CO2 mass flow that depends on neighboring countries. In order to determine the carbon footprint of each country, the set of coupled CO2 mass flow balance equations of each countries must be solved simultaneously. This is done by solving the linear system of equations defining the network of GHG exchanges. Take a look at this [notebook](https://github.com/corradio/electricitymap/blob/master/CO2eq%20Model%20Explanation.ipynb) for a deeper explanation.


### Real-time electricity data sources
Real-time electricity data is obtained using [parsers](https://github.com/corradio/electricitymap/tree/master/parsers)

- Austria: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Belgium: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Bulgaria: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Czech Republic: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Denmark: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Estonia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Finland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- France: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix-mix-energetique-en)
- Germany: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Great Britain: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Greece: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Hungary: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Iceland [LANDSNET](http://amper.landsnet.is/MapData/api/measurements)
- Ireland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Italy: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Latvia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Lithuania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Montenegro: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Netherlands: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Norway: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Poland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Portugal: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Romania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Serbia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Slovakia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Slovenia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Spain: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Sweden: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Switzerland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)

### Production capacity data sources
Production capacities are centralized in the [capacities.json](https://github.com/corradio/electricitymap/blob/master/web/app/configs/capacities.json) file.

- Austria: 
  - Wind: [IGWindKraft](https://www.igwindkraft.at)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Belgium: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Bulgaria: [wikipedia.org](https://en.wikipedia.org/wiki/Energy_in_Bulgaria)
- Czech Republic: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Denmark
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_in_Denmark)
  - Wind: [wikipedia.org](https://en.wikipedia.org/wiki/Wind_power_in_Denmark#Capacities_and_production)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Estonia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Finland: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- France
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_by_country)
  - Wind: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)
  - Other: [RTE](http://clients.rte-france.com/lang/an/visiteurs/vie/prod/parc_reference.jsp)
- Germany: [Fraunhoffer] (https://energy-charts.de/power_inst.htm)
- Great Britain: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Greece: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Hungary: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Iceland: [Statistics Iceland](http://px.hagstofa.is/pxen/pxweb/en/Atvinnuvegir/Atvinnuvegir__orkumal/IDN02101.px)
- Ireland
  - All production types: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
  - Wind: [IWEA](http://www.iwea.com/index.cfm/page/windenergyfaqs?#q21)
- Italy
  - Hydro: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Italy)
  - Nuclear: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Italy)
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Italy)
  - Wind: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Italy)
- Latvia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Lithuania: [ENMIN](https://enmin.lrv.lt/en/sectoral-policy/renewable-energy-sources)
- Montenegro: [EPCG](http://www.epcg.com/en/about-us/production-facilities)
- Netherlands: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Norway
  - Gas: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
  - Hydro: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
  - Wind: [ieawind.org](http://www.ieawind.org/countries/norway.html)  
- Northern Ireland: [EIR Grid](http://www.eirgridgroup.com/site-files/library/EirGrid/Generation_Capacity_Statement_20162025_FINAL.pdf)
- Poland: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Portugal: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Romania: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Serbia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Slovakia: [SEPS](https://www.sepsas.sk/Dokumenty/RocenkySed/ROCENKA_SED_2015.pdf)
- Slovenia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Spain: [ree.es](http://www.ree.es/sites/default/files/downloadable/preliminary_report_2014.pdf)
- Sweden [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Switzerland: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)

### Electricity prices (day-ahead) data sources
- France: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix-mix-energetique-en)
- Other: [ENTSO-E](https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show)

### Real-time weather data sources
We use the [US National Weather Service's Global Forecast System (GFS)](http://nomads.ncep.noaa.gov/)'s GFS 0.25 Degree Hourly data.
Forecasts are made every 6 hours, with a 1 hour time step.
The values extracted are wind speed and direction at 10m altitude, and ground solar irradiance (DSWRF - Downward Short-Wave Radiation Flux), which takes into account cloud coverage.
In order to obtain an estimate of those values at current time, an interpolation is made between two forecasts (the one at the beginning of the hour, and the one at the end of the hour).


### Topology data
We use the [Natural Earth Data Cultural Vectors](http://www.naturalearthdata.com/downloads/10m-cultural-vectors/) country subdivisions (map admin subunits).


## Contribute
Want to help? Join us on slack at [http://slack.tmrow.co](http://slack.tmrow.co).
In the meantime, here's some things you can do:
- check out the [issues](https://github.com/corradio/electricitymap/issues)
- add a new country by writing a [parser](https://github.com/corradio/electricitymap/tree/master/parsers)
- add a new [translation](https://github.com/corradio/electricitymap/tree/master/web/locales) of the map
- optimise the code, correct inaccuracies...

You can also see a list of missing informations displayed as warnings in the developer console, or question marks in the country panel:

![image](https://cloud.githubusercontent.com/assets/1655848/16256617/9c5872fc-3853-11e6-8c84-f562679086f3.png)

### Getting started
To get started, clone or [fork](https://help.github.com/articles/fork-a-repo/) the repository, and install [Docker](https://docs.docker.com/engine/installation/). 

The frontend will need compiling. In order to do this, open a terminal and run
```
docker-compose run --rm web npm run watch
```
This will watch over source file changes, and recompile if needed.

Now that the frontend is compiled, you can run the application (which will use our existing backend to pull data), by running the following command in a new terminal:
```
docker-compose up --build
```

Head over to [http://localhost:8000/](http://localhost:8000/) and you should see the map!

Once you're done doing your changes, submit a [pull request](https://help.github.com/articles/using-pull-requests/) to get them integrated into the production version.

### Troubleshooting

- `ERROR: for X  Cannot create container for service X: Invalid bind mount spec "<path>": Invalid volume specification: '<volume spec>'`. If you get this error after running `docker-compose up` on Windows, you should tell `docker-compose` to properly understand Windows paths by setting the environment variable `COMPOSE_CONVERT_WINDOWS_PATHS` to `0` by running `setx COMPOSE_CONVERT_WINDOWS_PATHS 0`. You will also need a recent version of `docker-compose`. We have successfully seen this fix work with [v1.13.0-rc4](https://github.com/docker/toolbox/releases/tag/v1.13.0-rc4). More info here: https://github.com/docker/compose/issues/4274.

- No website found at `http://localhost:8000`: This can happen if you're running Docker in a virtual machine. Find out docker's IP using `docker-machine ip default`, and replace `localhost` by your Docker IP when connecting.
