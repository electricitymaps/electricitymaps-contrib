# electricitymap [![Slack Status](http://slack.tmrow.co/badge.svg)](http://slack.tmrow.co)
 
A real-time visualisation of the Greenhouse Gas (in terms of CO2 equivalent) footprint of electricity generation built with [d3.js](https://d3js.org/), optimized for Google Chrome. Try it out at [http://www.electricitymap.org](http://www.electricitymap.org).


![image](https://cloud.githubusercontent.com/assets/1655848/20340757/5ada5cf6-abe3-11e6-97c4-e68929b8a135.png)

You can [contribute](#contribute) by correcting data sources, translating the map or by writing a parser to add a new country on the map. See the [contributing](#contribute) section.
You can also submit ideas, feature requests or bugs on the [issues](https://github.com/corradio/electricitymap/issues) page.


## Fonti dei dati

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


### Fonti dei dati sull'elettricità in tempo reale
I dati sull'elettricità in tempo reale sono ottenuti utilizzando dei [parser](https://github.com/corradio/electricitymap/tree/master/parsers)

- Austria: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Belgio: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Bulgaria: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Repubblica Ceca: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Danimarca: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Estonia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Finlandia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Francia: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix-mix-energetique-en)
- Germania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Gran Bretagna: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Grecia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Ungheria: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Islanda: [LANDSNET](http://amper.landsnet.is/MapData/api/measurements)
- Irlanda: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Italia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Latvia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Lituania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Montenegro: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Olanda: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Norvegia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Polonia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Portogallo: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Romania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Serbia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Slovacchia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Slovenia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Spagna: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Svezia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Svizzera: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)

### Fonti dei dati sulla capacità produttiva
Le capacità produttive sono centralizzate nel file [capacities.json](https://github.com/corradio/electricitymap/blob/master/web/app/configs/capacities.json).

- Austria: 
  - Eolico: [IGWindKraft](https://www.igwindkraft.at)
  - Altro: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Belgio: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Bulgaria: [wikipedia.org](https://en.wikipedia.org/wiki/Energy_in_Bulgaria)
- Repubblica Ceca: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Danimarca
  - Fotovoltaico: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_in_Denmark)
  - Eolico: [wikipedia.org](https://en.wikipedia.org/wiki/Wind_power_in_Denmark#Capacities_and_production)
  - Altro: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Estonia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Finlandia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Francia
  - Fotovoltaico: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_by_country)
  - Eolico: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)
  - Altro: [RTE](http://clients.rte-france.com/lang/an/visiteurs/vie/prod/parc_reference.jsp)
- Germania: [Fraunhoffer] (https://energy-charts.de/power_inst.htm)
- Gran Bretagna: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Grecia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Ungheria: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Islanda: [Statistics Iceland](http://px.hagstofa.is/pxen/pxweb/en/Atvinnuvegir/Atvinnuvegir__orkumal/IDN02101.px)
- Ireland
  - Tutti i tipi di produzione: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
  - Eolico: [IWEA](http://www.iwea.com/index.cfm/page/windenergyfaqs?#q21)
- Italia
  - Idroelettrico: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Italy)
  - Nucleare: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Italy)
  - Fotovoltaico: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Italy)
  - Eolico: [wikipedia.org](https://en.wikipedia.org/wiki/Electricity_sector_in_Italy)
- Latvia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Lituania: [ENMIN](https://enmin.lrv.lt/en/sectoral-policy/renewable-energy-sources)
- Montenegro: [EPCG](http://www.epcg.com/en/about-us/production-facilities)
- Olanda: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Norvegia
  - Gas: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
  - Idroelettrico: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
  - Eolico: [ieawind.org](http://www.ieawind.org/countries/norway.html)  
- Irlanda del Nord: [EIR Grid](http://www.eirgridgroup.com/site-files/library/EirGrid/Generation_Capacity_Statement_20162025_FINAL.pdf)
- Polonia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Portogallo: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Romania: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Serbia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Slovacchia: [SEPS](https://www.sepsas.sk/Dokumenty/RocenkySed/ROCENKA_SED_2015.pdf)
- Slovenia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Spagna: [ree.es](http://www.ree.es/sites/default/files/downloadable/preliminary_report_2014.pdf)
- Svezia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Svizzera: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)

### Fonti dei dati sul prezzo dell'elettricità (al giorno)
- Francia: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix-mix-energetique-en)
- Altri: [ENTSO-E](https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show)

### Real-time weather data sources
We use the [US National Weather Service's Global Forecast System (GFS)](http://nomads.ncep.noaa.gov/)'s GFS 0.25 Degree Hourly data.
Forecasts are made every 6 hours, with a 1 hour time step.
The values extracted are wind speed and direction at 10m altitude, and ground solar irradiance (DSWRF - Downward Short-Wave Radiation Flux), which takes into account cloud coverage.
In order to obtain an estimate of those values at current time, an interpolation is made between two forecasts (the one at the beginning of the hour, and the one at the end of the hour).


### Topologia dei dati
We use the [Natural Earth Data Cultural Vectors](http://www.naturalearthdata.com/downloads/10m-cultural-vectors/) country subdivisions (map admin subunits).


## Contribuisci
Vuoi aiutarci? Vieni da noi sul nostro Slack all'indirizzo [http://slack.tmrow.co](http://slack.tmrow.co).
Nel frattempo, ecco alcune cose che puoi fare:
- Controlla i [problemi](https://github.com/corradio/electricitymap/issues)
- Aggiungi una nuova nazione scrivendo un [parser](https://github.com/corradio/electricitymap/tree/master/parsers)
- Aggiungi una nuova [traduzione](https://github.com/corradio/electricitymap/tree/master/web/locales) della mappa
- Ottimizza il codice, correggi le inaccuratezze...

Puoi anche vedere una lista delle informazioni mancanti guardando nella console sviluppatore, o con i punti interrogativi nel pannello della nazione:

![image](https://cloud.githubusercontent.com/assets/1655848/16256617/9c5872fc-3853-11e6-8c84-f562679086f3.png)

### Come iniziare
Per iniziare, clona o fai un [fork](https://help.github.com/articles/fork-a-repo/) della repository, e installa [Docker](https://docs.docker.com/engine/installation/). 

Il progetto ha bisogno di essere compilato. Per farlo, apri un terminale ed avvia il comando
```
docker-compose run --rm web npm run watch
```
Questo vedrà se ci sono dei cambiamenti nei file sorgente, e li ricompilerà se necessario.

Adesso che il progetto è compilato, puoi avviare l'applicazione (che utilizzerà i dati già preesistenti), digitando questo comando in un nuovo terminale:
```
docker-compose up --build
```

Head over to [http://localhost:8000/](http://localhost:8000/) and you should see the map!

Once you're done doing your changes, submit a [pull request](https://help.github.com/articles/using-pull-requests/) to get them integrated into the production version.

### Risoluzione dei problemi

- `ERROR: for X  Cannot create container for service X: Invalid bind mount spec "<path>": Invalid volume specification: '<volume spec>'`. Se ottieni questo errore dopo aver utilizzato il comando `docker-compose up` su Windows, dovresti impostare il comando `docker-compose` in modo che capisca i percorsi di Windows impostando la variabile ambientale `COMPOSE_CONVERT_WINDOWS_PATHS` su `0` digitando il comando `setx COMPOSE_CONVERT_WINDOWS_PATHS 0`. Avrai bisogno di una versione recente del comando `docker-compose`. La versione con cui questo ha più successo è la [v1.13.0-rc4](https://github.com/docker/toolbox/releases/tag/v1.13.0-rc4). Per più informazioni: https://github.com/docker/compose/issues/4274.

- Nessun sito web all'indirizzo `http://localhost:8000`: Questo può accadere se hai Docker su una macchina virtuale. Trova l'indirizzo IP Docker usando il comando `docker-machine ip default`, e sostituisci `localhost` con il tuo IP Docker quando ti connetti.
