# electricitymap [![Slack Status](http://slack.tmrow.co/badge.svg)](http://slack.tmrow.co) [![CircleCI](https://circleci.com/gh/tmrowco/electricitymap.svg?style=shield)](https://circleci.com/gh/blackleg/electricitymap) [![Twitter Follow](https://img.shields.io/twitter/follow/tmrowco.svg?style=social&label=Follow)](https://twitter.com/tmrowco)
A real-time visualisation of the Greenhouse Gas (in terms of CO<sub>2</sub> equivalent) footprint of electricity consumption built with [d3.js](https://d3js.org/), optimized for Google Chrome. Try it out at [http://www.electricitymap.org](http://www.electricitymap.org), or download the app:

[![Get it on Google Play](https://cloud.githubusercontent.com/assets/1655848/25219122/99b446e6-25ad-11e7-934f-9491d2eb6c9b.png)](https://play.google.com/store/apps/details?id=com.tmrow.electricitymap&utm_source=github) [![Get it on the Apple Store](https://cloud.githubusercontent.com/assets/1655848/25218927/e0ec8bdc-25ac-11e7-8df8-7ab62787303e.png)](https://itunes.apple.com/us/app/electricity-map/id1224594248&utm_source=github)


![image](https://cloud.githubusercontent.com/assets/1655848/20340757/5ada5cf6-abe3-11e6-97c4-e68929b8a135.png)

You can [contribute](#contribute) by
- **[adding a new country on the map](#adding-a-new-country)**
- correcting [data sources](#data-sources) and [capacities](#updating-country-capacities)
- [translating](https://github.com/tmrowco/electricitymap/tree/master/web/locales) the map
- fixing existing [issues](https://github.com/tmrowco/electricitymap/issues)
- submitting ideas, feature requests, or bugs in the [issues](https://github.com/tmrowco/electricitymap/issues) section.

You can also see a list of missing data displayed as warnings in the developer console, or question marks in the country panel:

![image](https://cloud.githubusercontent.com/assets/1655848/16256617/9c5872fc-3853-11e6-8c84-f562679086f3.png)

Check the [contributing](#contribute) section for more details.

## Frequently asked questions

**How do you define real-time data?**  
Real-time data is defined as a data source with an hourly (or better) frequency, delayed by less than 2hrs. It should provide a breakdown by generation type. Often fossil fuel generation (coal/gas/oil) is combined under a single heading like 'thermal' or 'conventional', this is not a problem.

**Why do you calculate the carbon intensity of *consumption*?**
In short, citizens should not responsible for the emissions associated with all the products they export, but only for what they consume.
Cconsumption-based accounting (CBA) is a very important aspect of climate policy, and allows to assign responsibility to consumers instead of producers.
Furthermore, this method is robust to governments relocating dirty production to neighbouring countries in order to green their image while still importing from it.

**Why don't you show emissions per capita?**
A country that has few inhabitants but a lot of factories will appear high on CO2/capita.
This means you can "trick" the numbers by moving your factory abroad and import the produced *good* instead of the electricity itself.
That country now has a low co2/cap number because we only count CO2 for electricity (not for imported/exported goods).
The CO2/capita metric, by involving the size of the population, and by not integrating all CO2 emission sources, is thus an incomplete metric.
CO2 intensity on the other hand only describes where is the best place to put that factory (and when it is best to use electricity), enabling proper decisions.

**CO2 emission factors look high - what do they cover exactly?**
The carbon intensity of each type of power plant takes into account emissions arising from the whole lifecycle of the plant (construction, fuel production, operational emissions, and decommissioning).

**Is delayed data useful?**  
While the map relies on having real-time data to work it's still useful to collect data from days/months past. This older data can used to show past emissions and build up a better dataset. So if there's an hourly data source that lags several days behind you can still build a parser for it.

**Can scheduled generation data be used?**  
The electricitymap doesn't use scheduled or planned generation data. This is to avoid introducing extra uncertainty into emissions calculations.

**Can areas other than countries be shown?**  
Yes providing there is a valid GeoJSON geometry (or another format that can be converted) for the area. As an example we already split several countries into states and grid regions.

**How can I get access to historical data or the live API?**  
All this and more can be found **[here](https://pro.electricitymap.org/)**.

## Data sources

### Carbon intensity calculation and data source
The carbon intensity of each country is measured from the perspective of a consumer. It represents the greenhouse gas footprint of 1 kWh consumed inside a given country. The footprint is measured in gCO<sub>2</sub>eq (grams CO<sub>2</sub> equivalent), meaning each greenhouse gas is converted to its CO<sub>2</sub> equivalent in terms of global warming potential over 100 year (for instance, 1 gram of methane emitted has the same global warming impact during 100 years as ~20 grams of CO<sub>2</sub> over the same period).

The carbon intensity of each type of power plant takes into account emissions arising from the whole lifecycle of the plant (construction, fuel production, operational emissions, and decommissioning). Carbon-intensity factors used in the map are detailed in [co2eq_parameters.js](https://github.com/tmrowco/electricitymap/blob/master/config/co2eq_parameters.js). These numbers come from the following scientific peer reviewed literature:
- IPCC (2014) Fifth Assessment Report is used as reference in most instances (see a summary in the [wikipedia entry](https://en.wikipedia.org/wiki/Life-cycle_greenhouse-gas_emissions_of_energy_sources#2014_IPCC.2C_Global_warming_potential_of_selected_electricity_sources))

Country-specific carbon-intensity factors:
- Estonia:
  - Oil Shale: [EASAC (2007) "A study on the EU oil shale industry – viewed in the light of the Estonian experience"](http://www.easac.eu/fileadmin/PDF_s/reports_statements/Study.pdf)
- Norway:
  - Hydro: [Ostford Research (2015) "The inventory and life cycle data for Norwegian hydroelectricity"](http://ostfoldforskning.no/en/publications/Publication/?id=1236)

Each country has a CO<sub>2</sub> mass flow that depends on neighbouring countries. In order to determine the carbon footprint of each country, the set of coupled CO<sub>2</sub> mass flow balance equations of each countries must be solved simultaneously. This is done by solving the linear system of equations defining the network of greenhouse gas exchanges. Take a look at this [notebook](https://github.com/tmrowco/electricitymap/blob/master/CO2eq%20Model%20Explanation.ipynb) for a deeper explanation.


### Real-time electricity data sources
Real-time electricity data is obtained using [parsers](https://github.com/tmrowco/electricitymap/tree/master/parsers)

- Argentina: [Cammesa](http://portalweb.cammesa.com/Memnet1/default.aspx)
- Australia: [AREMI National Map](http://nationalmap.gov.au/renewables/)
  ([CSV](http://services.aremi.nationalmap.gov.au/aemo/v3/csv/all))
- Australia (Western): [AEMO](http://wa.aemo.com.au/Electricity/Wholesale-Electricity-Market-WEM/Data-dashboard)
  ([CSV](http://wa.aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv))
- Australia (distributed solar generation): [Australian PV Institute](http://pv-map.apvi.org.au/live)
- Australia (South Battery): [Nemwatch](https://ausrealtimefueltype.global-roam.com/expanded)
- Austria: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Bosnia and Herzegovina: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Bolivia: [CNDC](http://www.cndc.bo/media/archivos/graf/gene_hora/gweb_despdia_genera.php)
- Belgium: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Brazil: [ONS](http://www.ons.org.br/pt/paginas/energia-agora/carga-e-geracao)
- Bulgaria: [TSO](http://tso.bg/default.aspx/page-707/bg)
- Canada (Alberta): [AESO](http://ets.aeso.ca/ets_web/ip/Market/Reports/CSDReportServlet)
- Canada (New Brunswick): [NB Power](https://tso.nbpower.com/Public/en/op/market/data.aspx)
- Canada (Nova Scotia): [Nova Scotia Power](http://www.nspower.ca/en/home/about-us/todayspower.aspx)
- Canada (Ontario): [IESO](http://www.ieso.ca/power-data)
- Canada (Prince Edward Island): [Government of PEI](http://www.gov.pe.ca/windenergy/chart.php)
- Canada (Yukon): [Yukon Energy](http://www.yukonenergy.ca/energy-in-yukon/electricity-101/current-energy-consumption)
- Chile (SING): [SGER](https://sger.coordinadorelectrico.cl/Charts/AmChartCurvaCompuesta?showinfo=True)
- Czech Republic: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Costa Rica: [ICE](https://appcenter.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf)
- Croatia (Exchanges): [HOPS](https://www.hops.hr/wps/portal/hr/web)
- Cyprus : [TSO](http://www.dsm.org.cy/en/daily-system-generation-on-the-transmission-system-mw)
- Denmark: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
  - Bornholm: [PowerlabDK](http://bornholm.powerlab.dk/)
- Dominican Republic: [OC](http://www.oc.org.do/Reportes/postdespacho.aspx)
- El Salvador: [Unidad de Transacciones](http://estadistico.ut.com.sv/OperacionDiaria.aspx)
- Estonia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Faroe Islands: [SEV](https://w3.sev.fo/framleidsla/)
- Finland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- France: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix-mix-energetique-en)
- Germany: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Great Britain: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Greece: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Guatemala : [AMM](http://www.amm.org.gt)
- Hungary: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Iceland: [LANDSNET](http://amper.landsnet.is/MapData/api/measurements)
- Ireland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Italy: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- India (Andhra Pradesh): [CORE Dashboard](http://www.core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx)
- India (Chhattisgarh): [cspc.co.in](http://117.239.199.203/csptcl/GEN.aspx)
- India (Delhi): [delhisldc](http://www.delhisldc.org/Redirect.aspx?Loc=0804)
- India (Karnataka): [kptclsldc.com](http://kptclsldc.com/StateGen.aspx)
- India (Punjab): [punjabsldc](http://www.punjabsldc.org/pungenrealw.asp?pg=pbGenReal)
- India (Gujarat): [sldcguj](https://www.sldcguj.com/RealTimeData/RealTimeDemand.php)
- Latvia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Lithuania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Malaysia: [GSO](https://www.gso.org.my/LandingPage.aspx)
- Moldova: [MoldElectrica](http://www.moldelectrica.md/ro/activity/system_state)
- Montenegro: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Netherlands: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- New Zealand: [Transpower](https://www.transpower.co.nz/power-system-live-data)
- Nicaragua: [CNDC](http://www.cndc.org.ni/)
- Northern Ireland: [SONI](http://www.soni.ltd.uk/InformationCentre/)
- Norway: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Panama: [CND](http://sitr.cnd.com.pa/m/pub/gen.html)
- Peru: [COES](http://www.coes.org.pe/Portal/portalinformacion/Generacion)
- Poland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Portugal: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Romania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Russia: [SO-UPS](http://br.so-ups.ru/Public/MainPageData/BR/PowerGeneration.aspx)
- Serbia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Singapore: [EMC](https://www.emcsg.com)
- Slovakia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Slovenia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Spain:
  - Hydro: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=ESP)
  - Other: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Spain (Canary Islands): [REE](https://demanda.ree.es/movil)
- Spain (Balearic Islands): [REE](https://demanda.ree.es/movil)
- Sri Lanka: [ceb.lk](http://www.ceb.lk/yesterday-electricity/)
- Sweden: [Statnett](http://www.statnett.no/en/Market-and-operations/Data-from-the-power-system/Nordic-power-balance/)
- Switzerland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Taiwan: [TAIPOWER](http://www.taipower.com.tw/content/new_info/new_info_in.aspx?LinkID=27)
- Turkey: [ytbs](https://ytbs.teias.gov.tr/ytbs/frm_login.jsf)
- Ukraine: [UKRENERGO](https://ua.energy/activity/dispatch-information/ues-operation/)
- United States of America:
  - California: [CAISO](http://www.caiso.com/Pages/default.aspx)
  - MISO: [MISO](https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=json)
  - New England: [NEISO](https://www.iso-ne.com/isoexpress/)
  - New York: [NYISO](http://www.nyiso.com/public/markets_operations/market_data/graphs/index.jsp)
  - PJM: [PJM](http://www.pjm.com/markets-and-operations.aspx)
- Uruguay: [UTE](http://www.ute.com.uy/SgePublico/ConsPotenciaGeneracionArbolXFuente.aspx)

### Production capacity data sources
Production capacities are centralized in the [zones.json](https://github.com/tmrowco/electricitymap/blob/master/config/zones.json) file.

- Argentina: [Cammesa](http://portalweb.cammesa.com/Documentos%20compartidos/Noticias/Informe%20Anual%202016.pdf)
- Austria:
  - Wind: [IGWindKraft](https://www.igwindkraft.at)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Belarus: [belstat.gov.by](http://www.belstat.gov.by/upload/iblock/7f7/7f70938f51eb9e49abc4a6e62f831a2c.rar), [RenEn](http://director.by/zhurnal/arkhiv-zhurnala/arkhiv-nomerov-2017/375-7-2017-iyul-2017/5456-zelenaya-energetika-nabiraet-oboroty)  
- Belgium: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Bolivia: [CNDC](http://www.cndc.bo/agentes/generacion.php)
- Brazil: [ONS](http://www.ons.org.br/Paginas/resultados-da-operacao/historico-da-operacao/capacidade_instalada.aspx)
- Bulgaria: [wikipedia.org](https://en.wikipedia.org/wiki/Energy_in_Bulgaria)
- Canada (British Columbia, Manitoba, New Brunswick, Newfoundland and Labrador, Nova Scotia, Prince Edward Island):
    [wikipedia.org](https://en.wikipedia.org/wiki/List_of_generating_stations_in_Canada)
- Canada (Ontario): [Gridwatch](http://live.gridwatch.ca/total-capacity.html)
- Canada (Québec): [Hydro-Québec](http://www.hydroquebec.com/generation/)
- Canada (Saskatchewan): [SaskPower](http://www.saskpower.com/our-power-future/our-electricity/)
- Chile (SING):
  - Solar/Wind: [SGER](https://sger.coordinadorelectrico.cl/Plants/InstalledCapacity)
  - Other: [CIGRE](http://www.cigre.org/var/cigre/storage/original/application/6a789c1375a22a39e14a284bee7ff988.pdf)
- Czech Republic: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Denmark
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_in_Denmark)
  - Wind: [wikipedia.org](https://en.wikipedia.org/wiki/Wind_power_in_Denmark#Capacities_and_production)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Denmark (Bornholm)
  - Wind: [stateofgreen.com](https://stateofgreen.com/en/profiles/regional-municipality-of-bornholm/solutions/kalby-wind-turbines)
- Dominican Republic: [Climatescope](http://global-climatescope.org/en/country/dominican-republic/#/details)
- Estonia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Faroe Islands: [Johan Pauli Magnussen's Thesis, p44](https://setur.fo/uploads/tx_userpubrep/BScThesis_JohanPauliMagnussen.pdf)
- Finland:
  - Wind: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=FIN)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- France
  - Solar: [wikipedia.org](https://en.wikipedia.org/wiki/Solar_power_by_country)
  - Wind: [EWEA](http://www.ewea.org/fileadmin/files/library/publications/statistics/EWEA-Annual-Statistics-2015.pdf)
  - Other: [RTE](http://clients.rte-france.com/lang/an/visiteurs/vie/prod/parc_reference.jsp)
- Germany: [BNetzA](https://www.bundesnetzagentur.de/DE/Sachgebiete/ElektrizitaetundGas/Unternehmen_Institutionen/Versorgungssicherheit/Erzeugungskapazitaeten/Kraftwerksliste/kraftwerksliste-node.html)
- Great Britain: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Greece: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Guatemala: [AMM](http://www.amm.org.gt/pdfs2/2017/Capacidad_Instalada_2017.xls)
- Hungary:
  - Solar: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=HUN)
  - Other[ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Iceland: [Statistics Iceland](http://px.hagstofa.is/pxen/pxweb/en/Atvinnuvegir/Atvinnuvegir__orkumal/IDN02101.px)
- Ireland
  - All production types: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
  - Wind: [IWEA](http://www.iwea.com/index.cfm/page/windenergyfaqs?#q21)
- Italy
  - Wind & Solar: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=ITA)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- India (Andhra Pradesh): [wikipedia.org](https://en.wikipedia.org/wiki/Power_sector_of_Andhra_Pradesh)
- India (Karnataka):
  - Coal: [kptclsldc.com](http://kptclsldc.com/StateGen.aspx)
  - Hydro: [kptclsldc.com](http://kptclsldc.com/StateGen.aspx)
  - Renewables [kptclsldc.com](http://kptclsldc.com/StateNCEP.aspx)
- Latvia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Lithuania: [ENMIN](https://enmin.lrv.lt/en/sectoral-policy/renewable-energy-sources)
- Malaysia: [GSO](https://www.gso.org.my/SystemData/PowerStation.aspx)
- Moldova: [FAS](http://en.fas.gov.ru/upload/other/National%20Agency%20for%20Energy%20Regulation%20(G.%20Pyrzy).pdf)
- Montenegro: [EPCG](http://www.epcg.com/en/about-us/production-facilities)
- Netherlands: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Nicaragua: [Climatescope](http://global-climatescope.org/en/country/nicaragua/)
- Norway
  - Wind: [ieawind.org](http://www.ieawind.org/countries/norway.html)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Northern Ireland: [EIR Grid](http://www.eirgridgroup.com/site-files/library/EirGrid/Generation_Capacity_Statement_20162025_FINAL.pdf)
- Poland: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Portugal:
  - Solar: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=PTA)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Romania: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Russia: [Minenergo](https://minenergo.gov.ru/node/532)
- Serbia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Singapore: [Energy Market Authority](https://www.ema.gov.sg/cmsmedia/Publications_and_Statistics/Publications/SES/2016/Singapore%20Energy%20Statistics%202016.pdf)
- Slovakia: [SEPS](https://www.sepsas.sk/Dokumenty/RocenkySed/ROCENKA_SED_2015.pdf)
- Slovenia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Spain: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=01.01.2017+00:00|UTC|YEAR&dateTime.endDateTime=01.01.2017+00:00|UTC|YEAR&area.values=CTY|10YES-REE------0!BZN|10YES-REE------0&productionType.values=B01&productionType.values=B02&productionType.values=B03&productionType.values=B04&productionType.values=B05&productionType.values=B06&productionType.values=B07&productionType.values=B08&productionType.values=B09&productionType.values=B10&productionType.values=B11&productionType.values=B12&productionType.values=B13&productionType.values=B14&productionType.values=B20&productionType.values=B15&productionType.values=B16&productionType.values=B17&productionType.values=B18&productionType.values=B19)
- Spain (Canary Islands):
  - Hydro storage [goronadelviento.es](http://www.goronadelviento.es/)
  - Wind, Solar [REE](http://www.ree.es/sites/default/files/11_PUBLICACIONES/Documentos/Renovables-2016-v3.pdf)
- Spain (Balearic Islands):
  - Coal: [wikipedia.org](https://es.wikipedia.org/wiki/Central_t%C3%A9rmica_de_Es_Murterar)
  - Wind, Solar [REE](http://www.ree.es/sites/default/files/11_PUBLICACIONES/Documentos/Renovables-2016-v3.pdf)
- Sweden:
  - Renewables: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=SWE)
  - Other:[ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Switzerland: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Turkey: [TEİAŞ](https://www.teias.gov.tr/)
- Ukraine [wikipedia.org](https://uk.wikipedia.org/wiki/%D0%95%D0%BB%D0%B5%D0%BA%D1%82%D1%80%D0%BE%D0%B5%D0%BD%D0%B5%D1%80%D0%B3%D0%B5%D1%82%D0%B8%D0%BA%D0%B0_%D0%A3%D0%BA%D1%80%D0%B0%D1%97%D0%BD%D0%B8)
- United States of America:
  - Federal [EIA](https://www.eia.gov/electricity/data.cfm#gencapacity)
  - States [EIA](https://www.eia.gov/electricity/data/state/)
  - MISO [MISO](https://www.misoenergy.org/about/media-center/corporate-fact-sheet/)
  - PJM [PJM](http://www.pjm.com/-/media/markets-ops/ops-analysis/capacity-by-fuel-type-2017.ashx?la=en)

### Electricity prices (day-ahead) data sources
- France: [RTE](http://www.rte-france.com/en/eco2mix/eco2mix-mix-energetique-en)
- Nicaragua: [CNDC](http://www.cndc.org.ni/)
- Singapore: [EMC](https://www.emcsg.com)
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

### Running locally

To get started, [clone](https://help.github.com/articles/cloning-a-repository/) or [fork](https://help.github.com/articles/fork-a-repo/) the repository, and install [Docker](https://docs.docker.com/engine/installation/).

The frontend will need compiling. In order to do this, open a terminal and run
```
docker-compose run --rm web npm run watch
```
This will watch over source file changes, and recompile if needed.

Now that the frontend is compiled, you can run the application by running the following command in a new terminal:
```
docker-compose up --build
```

Head over to [http://localhost:8000/](http://localhost:8000/) and you should see the map! Note that the backend is responsible for calculation carbon emissions, so the map will be empty.

Once you're done doing your changes, submit a [pull request](https://help.github.com/articles/using-pull-requests/) to get them integrated into the production version.

### Updating country capacities
If you want to update or add production capacities for a country then head over to the [zones file](https://github.com/tmrowco/electricitymap/blob/master/config/zones.json) and make any changes needed.
The zones use ISO 3166-1 codes as identifiers, a list of which can be found [here](https://en.wikipedia.org/wiki/ISO_3166-1#Current_codes).

### Adding a new country
It is very simple to add a new country. The Electricity Map backend runs a list of so-called *parsers* every 5min. Those parsers are responsible for fetching the generation mix of a given country (check out the existing list in the [parsers](https://github.com/tmrowco/electricitymap/tree/master/parsers) directory, or look at the [work in progress](https://github.com/tmrowco/electricitymap/issues?q=is%3Aissue+is%3Aopen+label%3Aparser)).

A parser is a python3 script that is expected to define the method `fetch_production` which returns the production mix at current time, in the format:

```python
def fetch_production(country_code='FR', session=None):
    return {
      'countryCode': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': None,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
```

The `session` object is a [python request](http://docs.python-requests.org/en/master/) session that you can re-use to make HTTP requests.

The production values should never be negative. Use `None`, or omit the key if a specific production mode is not known.
Storage values can be both positive (when storing energy) or negative (when the storage is emptied).

The parser can also return an array of objects if multiple time values can be fetched. The backend will automatically update past values properly.

Once you're done, add your parser to the [zones.json](https://github.com/tmrowco/electricitymap/tree/master/config/zones.json) and [exchanges.json](https://github.com/tmrowco/electricitymap/tree/master/config/exchanges.json) configuration files. Finally update the [real-time sources](#real-time-electricity-data-sources).

For more info, check out the [example parser](https://github.com/tmrowco/electricitymap/tree/master/parsers/example.py) or browse existing [parsers](https://github.com/tmrowco/electricitymap/tree/master/parsers).

### Testing parsers locally
We've added a testing server locally. In order to test your parser, make sure first that you have installed the required modules as described in parsers/requirements.txt: for that you can run
```
pip install -r parsers/requirements.txt
```

Then, you can run
```
PYTHONPATH=. python3 mockserver/update_state.py <zone_name>
```

from the root directory, replacing `<zone_name>` by the zone identifier of the parser you want to test. This will fetch production and exchanges and assign it a random carbon intensity value. It should appear on the map as you refresh your local browser.

### Troubleshooting

- `ERROR: for X  Cannot create container for service X: Invalid bind mount spec "<path>": Invalid volume specification: '<volume spec>'`. If you get this error after running `docker-compose up` on Windows, you should tell `docker-compose` to properly understand Windows paths by setting the environment variable `COMPOSE_CONVERT_WINDOWS_PATHS` to `0` by running `setx COMPOSE_CONVERT_WINDOWS_PATHS 0`. You will also need a recent version of `docker-compose`. We have successfully seen this fix work with [v1.13.0-rc4](https://github.com/docker/toolbox/releases/tag/v1.13.0-rc4). More info here: https://github.com/docker/compose/issues/4274.

- No website found at `http://localhost:8000`: This can happen if you're running Docker in a virtual machine. Find out docker's IP using `docker-machine ip default`, and replace `localhost` by your Docker IP when connecting.
