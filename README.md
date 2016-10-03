# electricitymap
A real-time visualisation of the GHG and CO2 footprint of electricity generation built with [d3.js](https://d3js.org/), optimized for Google Chrome. Try it out at [http://electricitymap.tmrow.co](http://electricitymap.tmrow.co).

![image](https://cloud.githubusercontent.com/assets/1655848/16257011/15711692-3856-11e6-98ca-95cce4d02b02.png)

Consider [contributing](#contribute) or submit ideas, feature requests or bugs on the [issues](https://github.com/corradio/electricitymap/issues) page.


## Data sources

### GreenHouse Gas footprint calcuation and data source
The GreenHouse Gas (GHG) footprint of each country is measured from the perspective of a consumer. It represents the GHG footprint of 1 kWh consumed inside a given country, in the gCO2eq unit (meaning each GHG is converted to its CO2 equivalent in terms of global warming potential). 

The GHG footprint of each production mode takes into account the construction of production units and their usual lifetimes as calculated by the 2014 IPCC report (see [wikipedia entry](https://en.wikipedia.org/wiki/Life-cycle_greenhouse-gas_emissions_of_energy_sources#2014_IPCC.2C_Global_warming_potential_of_selected_electricity_sources) and [co2eq.js#L1](https://github.com/corradio/electricitymap/blob/master/api/static/app/co2eq.js#L1)).

Each country has a GHG mass flow that depends on neighboring countries. In order to determine the GHG footprint of each country, the set of coupled GHG mass flow balance equations of each countries must be solved simultaneously. This is done by solving the linear system of equations defining the network of GHG exchanges (see [co2eq.js#L49](https://github.com/corradio/electricitymap/blob/master/api/static/app/co2eq.js#L49)).


### Real-time electricity data sources
- Austria: [APG](https://www.apg.at/en/market/Markttransparenz/generation/Erzeugung%20pro%20Typ)
- Czech Republic: [CEPS](http://www.ceps.cz/ENG/Data/Vsechna-data/Pages/Vyroba.aspx)
- Denmark: [energinet.dk](http://energinet.dk/EN/El/Sider/Elsystemet-lige-nu.aspx)
- Estonia: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)
- Finland: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)
- France: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix)
- Germany: [Agora Energiewende](https://www.agora-energiewende.de/en/topics/-agothem-/Produkt/produkt/76/Agorameter/)
- Great Britain: [ELEXON](http://www.bmreports.com/bsp/additional/soapfunctions.php?element=generationbyfueltypetable)
- Hungary: [Mavir](http://www.mavir.hu/web/mavir-en/actual-generation-per-production-type-net-operation-control-measurement)
- Latvia: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)
- Lithuania: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)
- Norway: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)
- Portugal: [REN](http://www.centrodeinformacao.ren.pt/EN/InformacaoExploracao/Pages/EstatisticaDiaria.aspx)
- Romania: [Transelectrica](http://www.transelectrica.ro/en/web/tel/home)
- Spain: [REE](https://demanda.ree.es/generacion_acumulada.html)
- Sweden: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)

### Production capacity data sources
- Austria: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Czech Republic: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Denmark
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_in_Denmark)
  - Wind: [wikipedia.org](https://en.wikipedia.org/wiki/Wind_power_in_Denmark#Capacities_and_production)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Estonia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Finland
  - Hydro: [worldenergy.org](https://www.worldenergy.org/data/resources/country/finland/hydropower/)
  - Nuclear: [iaea.org](http://www-pub.iaea.org/MTCD/Publications/PDF/CNPP2013_CD/countryprofiles/Finland/Finland.htm)
  - Wind: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)
- France
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_by_country)
  - Wind: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)
  - Other: [RTE](http://clients.rte-france.com/lang/an/visiteurs/vie/prod/parc_reference.jsp)
- Germany: 
  - [Fraunhofer ISE](https://www.energy-charts.de/power_inst.htm)
  - [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Great Britain
  - Gas: [energy-uk.org.uk](http://www.energy-uk.org.uk/energy-industry/gas-generation.html)
  - Hydro: [wikipedia.org](https://en.wikipedia.org/wiki/Hydroelectricity_in_the_United_Kingdom)
  - Nuclear: [wikipedia.org](https://en.wikipedia.org/wiki/Nuclear_power_in_the_United_Kingdom)
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_by_country)
  - Wind: [wikipedia.org](https://en.wikipedia.org/wiki/Wind_power_in_the_United_Kingdom)
- Hungary: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Latvia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Lithuania: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Norway
  - Hydro: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Norway)
  - Wind: [ieawind.org](http://www.ieawind.org/countries/norway.html)  
- Portugal
  - Hydro: [wikipedia.org](https://pt.wikipedia.org/wiki/Hidroel%C3%A9tricas_em_Portugal)
  - Wind: [wikipedia.org](https://pt.wikipedia.org/wiki/Energia_eólica_em_Portugal)
  - Solar: [wikipedia.org](https://pt.wikipedia.org/wiki/Energia_solar_em_Portugal)
- Romania: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Spain: [ree.es](http://www.ree.es/sites/default/files/downloadable/preliminary_report_2014.pdf)
- Sweden
  - Hydro: [worldenergy.org](https://www.worldenergy.org/data/resources/country/sweden/hydropower/)
  - Nuclear: [world-nuclear.org](http://www.world-nuclear.org/information-library/country-profiles/countries-o-s/sweden.aspx)
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Energy_in_Sweden)
  - Wind: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)

### Real-time weather data sources
- Solar: [US National Weather Service's Prediction Climate Forecast System (CFS)](http://nomads.ncep.noaa.gov/)
- Wind: [US National Weather Service's Global Forecast System (GFS)](http://nomads.ncep.noaa.gov/)


## Contribute
You can contribute by
- adding your country by writing a [parser](https://github.com/corradio/electricitymap/tree/master/feeder/parsers)
- update an existing [parser](https://github.com/corradio/electricitymap/tree/master/feeder/parsers) with a different API if you know one with more data or closer to real-time
- optimising the code, correct inaccuracies...

You can also see a list of missing informations displayed as warnings in the developer console, or question marks in the country panel:

![image](https://cloud.githubusercontent.com/assets/1655848/16256617/9c5872fc-3853-11e6-8c84-f562679086f3.png)

To get started, clone or [fork](https://help.github.com/articles/fork-a-repo/) the repository, and install [Docker](https://docs.docker.com/engine/installation/). then you just run `docker-compose up`. Head over to [http://localhost:8000/](http://localhost:8000/) and you should see the map!

Once you're done doing your changes, submit a [pull request](https://help.github.com/articles/using-pull-requests/) to get them integrated.
