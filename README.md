# electricitymap
A real-time visualisation of electricity generation. Try it out at [http://corradio.github.io/electricitymap/](http://corradio.github.io/electricitymap/).


The CO2 footprint of each country is measured from the perspective of a consumer. It represents the CO2 footprint of 1 kWh consumed inside a given country. Therefore, the footprint takes into account the footprint of electricity imported in the country.
The numbers unfortunately do not take into account the construction of production units, nor the transportation or extraction of raw materials. Any help would be appreciated to get closer to the truth!


### Data sources

## Real-time electricity data sources
- Denmark: [energinet.dk](http://energinet.dk/EN/El/Sider/Elsystemet-lige-nu.aspx)
- Finland: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)
- France: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix)
- Germany: [Agora Energiewende](https://www.agora-energiewende.de/en/topics/-agothem-/Produkt/produkt/76/Agorameter/)
- Great Britain: [ELEXON](http://www.bmreports.com/bsp/additional/soapfunctions.php?element=generationbyfueltypetable)
- Norway: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)
- Spain: [REE](https://demanda.ree.es/generacion_acumulada.html)
- Sweden: [energinet.dk](http://www.energinet.dk/EN/El/Sider/Det-nordiske-elsystem.aspx)

## Real-time weather data sources
- Solar: [GFS 0.5 Degree](http://nomads.ncep.noaa.gov/)
- Wind: [CFS Flux](http://nomads.ncep.noaa.gov/)

## CO2 data sources
- Denmark: [energinet.dk](http://www.energinet.dk/DA/El/Engrosmarked/Udtraek-af-markedsdata/Sider/Om-Elsystemet-lige-nu.aspx)
- France: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix-co2-en)
- Great Britain [GridCarbon](http://www.gridcarbon.uk/)

## Production capacity sources
- Denmark
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_in_Denmark)
  - Wind: [wikipedia.org](https://en.wikipedia.org/wiki/Wind_power_in_Denmark#Capacities_and_production)
- Finland
  - Hydro: [worldenergy.org](https://www.worldenergy.org/data/resources/country/finland/hydropower/)
  - Nuclear: [iaea.org](http://www-pub.iaea.org/MTCD/Publications/PDF/CNPP2013_CD/countryprofiles/Finland/Finland.htm)
  - Wind: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)
- France
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_by_country)
  - Wind: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)
  - Other: [RTE](http://clients.rte-france.com/lang/an/visiteurs/vie/prod/parc_reference.jsp)
- Germany: [Fraunhofer ISE](https://www.energy-charts.de/power_inst.htm)
- Great Britain
  - Gas: [energy-uk.org.uk](http://www.energy-uk.org.uk/energy-industry/gas-generation.html)
  - Hydro: [wikipedia.org](https://en.wikipedia.org/wiki/Hydroelectricity_in_the_United_Kingdom)
  - Nuclear: [wikipedia.org](https://en.wikipedia.org/wiki/Nuclear_power_in_the_United_Kingdom)
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_by_country)
  - Wind: [wikipedia.org](https://en.wikipedia.org/wiki/Wind_power_in_the_United_Kingdom)
- Norway
  - Hydro: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Norway)
  - Wind: [ieawind.org](http://www.ieawind.org/countries/norway.html)  
- Spain: [ree.es](http://www.ree.es/sites/default/files/downloadable/preliminary_report_2014.pdf)
- Sweden
  - Hydro: [worldenergy.org](https://www.worldenergy.org/data/resources/country/sweden/hydropower/)
  - Nuclear: [world-nuclear.org](http://www.world-nuclear.org/information-library/country-profiles/countries-o-s/sweden.aspx)
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Energy_in_Sweden)
  - Wind: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)
