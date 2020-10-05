# electricityMap [![Slack Status](https://slack.tmrow.com/badge.svg)](https://slack.tmrow.com) [![CircleCI](https://circleci.com/gh/tmrowco/electricitymap-contrib.svg?style=shield)](https://circleci.com/gh/tmrowco/electricitymap-contrib) [![Twitter Follow](https://img.shields.io/twitter/follow/electricitymap.svg?style=social&label=Follow)](https://twitter.com/electricitymap)
A real-time visualisation of the Greenhouse Gas (in terms of CO<sub>2</sub> equivalent) footprint of electricity consumption built with [d3.js](https://d3js.org/) and [mapbox GL](https://github.com/mapbox/mapbox-gl-js/), maintained by [Tomorrow](https://www.tmrow.com). Try it out at [http://www.electricitymap.org](http://www.electricitymap.org), or download the app:

[![Get it on Google Play](https://cloud.githubusercontent.com/assets/1655848/25219122/99b446e6-25ad-11e7-934f-9491d2eb6c9b.png)](https://play.google.com/store/apps/details?id=com.tmrow.electricitymap&utm_source=github) [![Get it on the Apple Store](https://cloud.githubusercontent.com/assets/1655848/25218927/e0ec8bdc-25ac-11e7-8df8-7ab62787303e.png)](https://itunes.apple.com/us/app/electricity-map/id1224594248&utm_source=github)


![image](https://www.electricitymap.org/images/electricitymap_social_image.jpg)

You can [contribute](#contribute) in the following ways:
- **[Add a new region](#add-a-new-region) to the map**, including contact information for energy agencies, governments, and transmission system operators.
- Correct [data sources](#data-sources) and [capacities](#update-region-capacities).
- [Translate](https://github.com/tmrowco/electricitymap-contrib/tree/master/web/locales) the map.
- Fix existing [issues](https://github.com/tmrowco/electricitymap-contrib/issues).
- Submit ideas, feature requests, or bugs as a new [issue](https://github.com/tmrowco/electricitymap-contrib/issues).

You can also find a list of missing data displayed as warnings in the developer console, or question marks in the country panel:

![image](https://cloud.githubusercontent.com/assets/1655848/16256617/9c5872fc-3853-11e6-8c84-f562679086f3.png)

Check the [contributing](#contribute) section for more details.
Join us on [Slack](https://slack.tmrow.com) if you wish to discuss development or need help to get started.

## Frequently asked questions

**How do you define real-time data?**
Real-time data is defined as a data source with an hourly (or better) frequency, delayed by less than 2hrs. It should provide a breakdown by generation type. Often fossil fuel generation (coal/gas/oil) is combined under a single heading like 'thermal' or 'conventional', this is not a problem.

**Why do you calculate the carbon intensity of *consumption*?**
In short, citizens should not be responsible for the emissions associated with all the products they export, but only for what they consume.
Consumption-based accounting (CBA) is a very important aspect of climate policy, and allows assigning responsibility to consumers instead of producers.
Furthermore, this method is robust to governments relocating dirty production to neighbouring countries in order to green their image while still importing from it.
We published our methodology [here](https://arxiv.org/abs/1812.06679).

**Why don't you show emissions per capita?**
A country that has few inhabitants but a lot of factories will appear high on CO<sub>2</sub>/capita.
This means you can "trick" the numbers by moving your factory abroad and import the produced *good* instead of the electricity itself.
That country now has a low CO<sub>2</sub>/capita number because we only count CO<sub>2</sub> for electricity (not for imported/exported goods).
The CO<sub>2</sub>/capita metric, by involving the size of the population, and by not integrating all CO<sub>2</sub> emission sources, is thus an incomplete metric.
CO<sub>2</sub> intensity on the other hand only describes where is the best place to put that factory (and when it is best to use electricity), enabling proper decisions.

**CO<sub>2</sub> emission factors look high — what do they cover exactly?**
The carbon intensity of each type of power plant takes into account emissions arising from the whole life cycle of the plant (construction, fuel production, operational emissions, and decommissioning).

**Is delayed data useful?**
While the map relies on having real-time data to work it's still useful to collect data from days/months past. This older data can be used to show past emissions and build up a better dataset. So if there's an hourly data source that lags several days behind you can still build a parser for it.

**Can scheduled/assumed generation data be used?**
The electricityMap doesn't use scheduled generation data or make assumptions about unknown fuel mixes. This is to avoid introducing extra uncertainty into emissions calculations.

**Can areas other than countries be shown?**
Yes providing there is a valid GeoJSON geometry (or another format that can be converted) for the area. As an example we already split several countries into states and grid regions.

**How can I get access to historical data or the live API?**
All this and more can be found **[here](https://api.electricitymap.org/)**.

## Data sources

### Carbon intensity calculation and data source
The carbon intensity of each country is measured from the perspective of a consumer. It represents the greenhouse gas footprint of 1 kWh consumed inside a given country. The footprint is measured in gCO<sub>2</sub>eq (grams CO<sub>2</sub> equivalent), meaning each greenhouse gas is converted to its CO<sub>2</sub> equivalent in terms of [global warming potential](https://en.wikipedia.org/wiki/Global_warming_potential) over 100 year (for instance, 1 gram of methane emitted has the same global warming impact during 100 years as ~34 grams of CO<sub>2</sub> over the same period).

The carbon intensity of each type of power plant takes into account emissions arising from the whole life cycle of the plant (construction, fuel production, operational emissions, and decommissioning). Carbon-intensity factors used in the map are detailed in [co2eq_parameters.json](https://github.com/tmrowco/electricitymap-contrib/blob/master/config/co2eq_parameters.json). These numbers come mostly from the following scientific peer reviewed literature: IPCC (2014) Fifth Assessment Report is used as reference in most instances (see a summary in the [wikipedia entry](https://en.wikipedia.org/wiki/Life-cycle_greenhouse-gas_emissions_of_energy_sources#2014_IPCC.2C_Global_warming_potential_of_selected_electricity_sources))

Each country has a CO<sub>2</sub> mass flow that depends on neighbouring countries. In order to determine the carbon footprint of each country, the set of coupled CO<sub>2</sub> mass flow balance equations of each countries must be solved simultaneously. This is done by solving the linear system of equations defining the network of greenhouse gas exchanges. Take a look at this [notebook](https://github.com/tmrowco/electricitymap-contrib/blob/master/CO2eq%20Model%20Explanation.ipynb) for a deeper explanation. We also published our methodology [here](https://arxiv.org/abs/1812.06679).


### Real-time electricity data sources
Real-time electricity data is obtained using [parsers](https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers).
&nbsp;<details><summary>Click to see the full list of sources</summary>
- Åland: [Kraftnät Åland](http://www.kraftnat.ax/text2.con?iPage=28&iLan=1)
- Argentina: [Cammesa](http://portalweb.cammesa.com/Memnet1/default.aspx)
- Armenia: [Armenian Energy Power System Operator](http://epso.am/poweren.htm)
- Aruba: [WEB Aruba](https://www.webaruba.com/renewable-energy-dashboard/aruba) ([JSON](https://www.webaruba.com/renewable-energy-dashboard/app/rest/results.json))
- Australia: [AREMI National Map](http://nationalmap.gov.au/renewables/)
  ([CSV](http://services.aremi.nationalmap.gov.au/aemo/v3/csv/all))
- Australia (Western): [AEMO](http://wa.aemo.com.au/Electricity/Wholesale-Electricity-Market-WEM/Data-dashboard)
  ([CSV](http://wa.aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv))
- Australia (distributed solar generation): [Australian PV Institute](http://pv-map.apvi.org.au/live)
- Australia (South Battery): [Nemwatch](https://ausrealtimefueltype.global-roam.com/expanded)
- Austria: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Bahrain: [GCCIA](https://www.gccia.com.sa/)
- Bangladesh: [PGCB](https://pgcb.org.bd/PGCB/?a=pages/operational_daily.php)
- Bosnia and Herzegovina: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Bolivia: [CNDC](http://www.cndc.bo/media/archivos/graf/gene_hora/gweb_despdia_genera.php)
- Belgium: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Brazil: [ONS](http://www.ons.org.br/paginas/energia-agora/carga-e-geracao)
- Bulgaria: [TSO](http://tso.bg/default.aspx/page-707/bg)
- Canada (Alberta): [AESO](http://ets.aeso.ca/ets_web/ip/Market/Reports/CSDReportServlet)
- Canada (New Brunswick): [NB Power](https://tso.nbpower.com/Public/en/op/market/data.aspx)
- Canada (Nova Scotia): [Nova Scotia Power](https://www.nspower.ca/clean-energy/todays-energy-stats)
- Canada (Ontario): [IESO](http://www.ieso.ca/power-data)
- Canada (Prince Edward Island): [Government of PEI](https://www.princeedwardisland.ca/en/feature/pei-wind-energy/)
- Canada (Yukon): [Yukon Energy](http://www.yukonenergy.ca/energy-in-yukon/electricity-101/current-energy-consumption)
- Chile (SING/SIC): [Coordinador](https://sipub.coordinador.cl/api/v1/recursos/generacion_centrales_tecnologia_horario?)
- Czech Republic: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Costa Rica: [ICE](https://appcenter.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf)
- Croatia (Exchanges): [HOPS](https://www.hops.hr/wps/portal/hr/web)
- Cyprus: [TSO](https://tsoc.org.cy/total-daily-system-generation-on-the-transmission-system/)
- Denmark: [TSO](https://www.energidataservice.dk/en/group/production-and-consumption)
- Denmark (Bornholm): [PowerlabDK](http://bornholm.powerlab.dk/)
- Dominican Republic: [OC](http://www.oc.org.do/Reportes/postdespacho.aspx)
- El Salvador: [Unidad de Transacciones](http://estadistico.ut.com.sv/OperacionDiaria.aspx)
- Estonia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Faroe Islands: [SEV](https://w3.sev.fo/framleidsla/)
- Finland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- France: [RTE](https://opendata.reseaux-energies.fr)
- Germany: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Georgia: [GSE](http://www.gse.com.ge/home)
- Great Britain: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Great Britain (Orkney Islands): [SSEN](https://www.ssen.co.uk/ANM/)
- Greece: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Guatemala: [AMM](http://www.amm.org.gt)
- Honduras: [ENTE](https://www.enteoperador.org/flujos-regionales-en-tiempo-real/)
- Hungary: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Iceland: [LANDSNET](https://amper.landsnet.is/generation/api/Values)
- Ireland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Israel: [IEC](https://www.iec.co.il/en/pages/default.aspx)
- Italy: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- India: [meritindia](http://meritindia.in/)
- India (Andhra Pradesh): [CORE Dashboard](https://core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx)
- India (Chhattisgarh): [cspc.co.in](http://117.239.199.203/csptcl/GEN.aspx)
- India (Delhi): [delhisldc](http://www.delhisldc.org/Redirect.aspx?Loc=0804)
- India (Gujarat): [sldcguj](https://www.sldcguj.com/RealTimeData/RealTimeDemand.php)
- India (Himachal Pradesh): [HPSLDC](https://hpsldc.com/intra-state-power-transaction/)
- India (Maharashtra) [mahasldc](https://mahasldc.in/wp-content/reports/sldc/mvrreport3.jpg)
- India (Karnataka): [kptclsldc.com](http://kptclsldc.com/StateGen.aspx)
- India (Punjab): [punjabsldc](http://www.punjabsldc.org/pungenrealw.asp?pg=pbGenReal)
- India (Uttar Pradesh): [upsldc](http://www.upsldc.org/real-time-data)
- India (Uttarakhand): [uksldc](http://uksldc.in/real-time-data.php)
- Iraq: [Iraqi Power System](http://109.224.53.139:8080/IPS.php)
- Japan (Exchanges): [OCCTO](http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login)
- Japan (Chūbu): [Chūden](http://denki-yoho.chuden.jp/)
- Japan (Chūgoku): [Energia](http://www.energia.co.jp/jukyuu/)
- Japan (Hokkaidō): [Hokuden](http://denkiyoho.hepco.co.jp/area_forecast.html)
- Japan (Hokuriku): [Rikuden](http://www.rikuden.co.jp/denki-yoho/)
- Japan (Kansai): [Kepco](http://www.kepco.co.jp/energy_supply/supply/denkiyoho/)
- Japan (Kyūshū): [Kyūden](http://www.kyuden.co.jp/power_usages/pc.html)
- Japan (Kyūshū/Genkai NPP): [Kyūden](http://www.kyuden.co.jp/php/nuclear/genkai/rename.php?A=g_power.fdat&B=ncp_state.fdat&_=1520532904073)
- Japan (Kyūshū/Sendai NPP): [Kyūden](http://www.kyuden.co.jp/php/nuclear/sendai/rename.php?A=s_power.fdat&B=ncp_state.fdat&_=1520532401043)
- Japan (Shikoku): [Yonden](http://www.yonden.co.jp/denkiyoho/)
- Japan (Tōhoku-Niigata): [TH-EPCO](http://setsuden.tohoku-epco.co.jp/graph.html)
- Japan (Tōkyō area): [TEPCO](http://www.tepco.co.jp/forecast/html/images/juyo-j.csv)
- Kuwait (TSO): [Ministry of Electricity & Water](https://www.mew.gov.kw/en/)
- Kuwait (Power Market): [GCCIA](https://www.gccia.com.sa/)
- Latvia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Lithuania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Malaysia: [GSO](https://www.gso.org.my/LandingPage.aspx)
- Moldova: [MoldElectrica](http://www.moldelectrica.md/ro/activity/system_state)
- Montenegro: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Namibia: [NamPower](http://www.nampower.com.na/Scada.aspx)
- Netherlands:
  - [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
  - [Energieopwek.nl](https://energieopwek.nl/)
- New Zealand: [Transpower](https://www.transpower.co.nz/power-system-live-data)
- Nicaragua: [CNDC](http://www.cndc.org.ni/)
- Northern Ireland: [SONI](http://www.soni.ltd.uk/InformationCentre/)
- Norway: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Oman: [GCCIA](https://www.gccia.com.sa/)
- Panama: [CND](http://sitr.cnd.com.pa/m/pub/gen.html)
- Peru: [COES](http://www.coes.org.pe/Portal/portalinformacion/Generacion)
- Poland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Portugal: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Qatar: [GCCIA](https://www.gccia.com.sa/)
- Romania: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Russia: [SO-UPS](http://br.so-ups.ru/Public/MainPageData/BR/PowerGeneration.aspx)
- Serbia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Singapore: [EMC](https://www.emcsg.com)
- Singapore (Solar): [EMA](https://www.ema.gov.sg/solarmap.aspx)
- Slovakia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Slovenia: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- South Korea (Nuclear): [KHNP](http://cms.khnp.co.kr/eng/kori/realTimeMgr/list.do?mnCd=EN03020201&brnchCd=BR0302)
- South Korea (Hydro): [KHNP](http://cms.khnp.co.kr/eng/realTimeMgr/water.do?mnCd=EN040203)
- South Korea (Load): [KPX](http://power.kpx.or.kr/powerinfo_en.php)
- Spain: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Spain (Canary Islands): [REE](https://demanda.ree.es/movil)
- Spain (Balearic Islands): [REE](https://demanda.ree.es/movil)
- Sweden: [SVK](https://www.svk.se/en/national-grid/the-control-room/)
- Saudi Arabia: [GCCIA](https://www.gccia.com.sa/)
- Switzerland: [ENTSOE](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html)
- Taiwan: [TAIPOWER](http://www.taipower.com.tw/d006/loadGraph/loadGraph/genshx_.html)
- Turkey: [ytbs](https://ytbs.teias.gov.tr/ytbs/frm_login.jsf)
- Ukraine: [UKRENERGO](https://ua.energy/activity/dispatch-information/ues-operation/)
- United Arab Emirates: [GCCIA](https://www.gccia.com.sa/)
- United States of America
  - Bonneville Power Authority: [BPA](https://transmission.bpa.gov/business/operations/Wind/baltwg.txt)
  - California: [CAISO](http://www.caiso.com/Pages/default.aspx)
  - Hawaii (Oahu Island): [Islandpulse](https://www.islandpulse.org/)
  - Idaho Power Company: [IPC](https://www.idahopower.com/energy/delivering-power/generation-and-demand/)
  - MISO: [MISO](https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=json)
  - New England: [NEISO](https://www.iso-ne.com/isoexpress/)
  - New York: [NYISO](http://www.nyiso.com/public/markets_operations/market_data/graphs/index.jsp)
  - PJM: [PJM](http://www.pjm.com/markets-and-operations.aspx)
  - Southwest Power Pool: [SPP](https://marketplace.spp.org/pages/generation-mix)
  - Southwest Variable Energy Resource Initiative: [SVERI](https://sveri.energy.arizona.edu/#generation-by-fuel-type)
  - Texas: [ERCOT](http://www.ercot.com/content/cdr/html/real_time_system_conditions.html)
  - Seminole Electric Cooperative (Florida): [EIA](https://www.eia.gov/opendata/qb.php?category=2122629&sdid=EBA.SEC-ALL.NG.H), [SEC](https://www.seminole-electric.com/facilities/generation/)
- Uruguay: [UTE](https://apps.ute.com.uy/SgePublico/ConsPotenciaGeneracionArbolXFuente.aspx)
&nbsp;</details>

### Production capacity data sources
Production capacities are centralized in the [zones.json](https://github.com/tmrowco/electricitymap-contrib/blob/master/config/zones.json) file. Values in the `capacity` maps are in MW.

#### International sources
When determining the installed capacity for a country, these sources might help you get started. Note that if you end up using one of these sources, it *also* needs to be listed with the country/region.

- Renewables: [IRENA](https://www.irena.org/Search?keywords=%22Renewable+Capacity+Statistics%22&sort=date&content_type=2803e86c173c440f840aa721825b3656)
- Nuclear: [IAEA PRIS](https://pris.iaea.org/PRIS/WorldStatistics/OperationalReactorsByCountry.aspx)
- Coal: [Global Coal Plant Tracker](https://endcoal.org/global-coal-plant-tracker/)
- Various:
  - [Climatescope](https://global-climatescope.org/capacity-generation)
  - [Global Power Plant Database](https://datasets.wri.org/dataset/globalpowerplantdatabase)

For many European countries, data is available from [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)

#### Sources by region
<details><summary>Click to see the full list of sources</summary>

- Albania: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Argentina: [Cammesa](https://www.cammesa.com/linfomen.nsf/MINFOMEN?OpenFrameSet)
- Armenia
   - Biomass, Hydro, Solar, Wind: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
   - Nuclear, Gas: [wikipedia.org](https://en.wikipedia.org/wiki/List_of_power_stations_in_Armenia)
- Aruba: [WEB Aruba](https://www.webaruba.com/energy-production/power-production-figures)
- Australia [OpenNEM](https://opennem.org.au/facilities/all/)
- Austria
  - Wind: [IGWindKraft](https://www.igwindkraft.at)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Bahrain: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Belarus: [belstat.gov.by](http://www.belstat.gov.by/upload/iblock/7f7/7f70938f51eb9e49abc4a6e62f831a2c.rar), [RenEn](http://director.by/zhurnal/arkhiv-zhurnala/arkhiv-nomerov-2017/375-7-2017-iyul-2017/5456-zelenaya-energetika-nabiraet-oboroty)
- Belgium
  - Solar: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Hydro & Wind: [ELIA](https://www.elia.be/-/media/project/elia/shared/documents/elia-group/publications-pdfs/20200414_elia_annual-report-sustainability_en.pdf)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Bolivia: [CNDC](http://www.cndc.bo/agentes/generacion.php)
- Bosnia and Herzegovina: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Brazil: [ONS](http://www.ons.org.br/Paginas/resultados-da-operacao/historico-da-operacao/capacidade_instalada.aspx)
- Bulgaria: [wikipedia.org](https://en.wikipedia.org/wiki/Energy_in_Bulgaria)
- Canada (British Columbia, Manitoba, New Brunswick, Newfoundland and Labrador, Nova Scotia, Prince Edward Island):
    [wikipedia.org](https://en.wikipedia.org/wiki/List_of_generating_stations_in_Canada)
- Canada (Ontario): [IESO](http://www.ieso.ca/en/Power-Data/Supply-Overview/Transmission-Connected-Generation)
- Canada (Québec): [Hydro-Québec](http://www.hydroquebec.com/generation/)
- Canada (Saskatchewan): [SaskPower](http://www.saskpower.com/our-power-future/our-electricity/)
- Canada (Yukon)
  - Hydro: [YukonEnergy](https://yukonenergy.ca/energy-in-yukon/projects-facilities)
- Chile (SIC)
  - Geothermal, Hydro, Solar, Wind: [SIC](https://sic.coordinador.cl/capacidad-instalada/)
  - Other: [energiaabierta.cl](http://energiaabierta.cl/visualizaciones/capacidad-instalada/)
- Chile (SING)
  - Solar/Wind: [SGER](https://sger.coordinadorelectrico.cl/Plants/InstalledCapacity)
  - Other: [energiaabierta.cl](http://energiaabierta.cl/visualizaciones/capacidad-instalada/)
- Croatia: [HOPS](https://www.hrote.hr/planning-electricity-production-for-the-eco-balance-group)
- Costa Rica: [ICE](https://www.grupoice.com/wps/wcm/connect/579dfc1f-5156-41e0-807d-d6808f65d718/Fasciculo_Electricidad_2020_ingl%C3%A9s_compressed.pdf?MOD=AJPERES&CVID=m.pGzcp)
- Cyprus: [TSO](https://tsoc.org.cy/total-daily-system-generation-on-the-transmission-system/)
- Czech Republic: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Denmark (DK1 and DK2): [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Denmark (Bornholm)
  - Wind: [stateofgreen.com](https://stateofgreen.com/en/profiles/regional-municipality-of-bornholm/solutions/kalby-wind-turbines)
- Dominican Republic:
  - 2020 Data: [OC](https://www.dropbox.com/sh/8dec0z1ftf2nqr0/AAAbDG-6lSttxBprxhPRNkjaa/2020?dl=0&preview=OC-2020-000190-GG-SIE-INFORME+ANUAL+2019+V1.pdf&subfolder_nav_tracking=1)
  - Other: [Climatescope](http://global-climatescope.org/en/country/dominican-republic/#/details)
- El Salvador:
  - Thermal: [CNE](http://estadisticas.cne.gob.sv/wp-content/uploads/2016/09/Plan_indicativo_2016_2026-1.pdf)
  - Biomass, Geothermal, Hydro & Solar: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Estonia:
  - Biomass & Solar: [IRENA](http://resourceirena.irena.org/gatewable:ay/countrySearch/?countryCode=EST)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Faroe Islands: [Johan Pauli Magnussen's Thesis, p44](https://setur.fo/uploads/tx_userpubrep/BScThesis_JohanPauliMagnussen.pdf)
- Finland
  - Renewable: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- France:
  - Geothermal, Hydro, Solar: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show?)
- Germany: [Frauenhofer ISE](https://www.energy-charts.de/power_inst_de.htm?year=2020&period=annual&type=power_inst)
- Georgia: [GSE](http://www.gse.com.ge/for-customers/data-from-the-power-system)
- Great Britain: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Greece: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Guatemala: [AMM](http://www.amm.org.gt/pdfs2/2017/Capacidad_Instalada_2017.xls)
- Honduras: [ENEE](http://www.enee.hn/planificacion/2018/boletines/Boletin%20Estadistico%20Mes%20de%20Septiembre%202018%20PDF.pdf)
- Hungary
  - Solar: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=HUN)
  - Other[ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Iceland
  - Oil: [Statistics Iceland](http://px.hagstofa.is/pxen/pxweb/en/Atvinnuvegir/Atvinnuvegir__orkumal/IDN02101.px)
  - Geothermal, Wind and Hydro: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Ireland
  - Non-Renewable: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
  - Renewable: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Israel: [Global Power Plant Database](http://datasets.wri.org/dataset/globalpowerplantdatabase)
- Italy
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedCapacityPerProductionUnit/show)
  - Per Region Renewable: [Terna](https://www.terna.it/en/electric-system/statistical-data-forecast/evolution-electricity-market)
  - Wind & Solar: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=ITA)
- India: [mercomindia](https://mercomindia.com/solar-indias-installed-power-capacity/)
- India (Andhra Pradesh): [wikipedia.org](https://en.wikipedia.org/wiki/Power_sector_of_Andhra_Pradesh)
- India (Punjab): [PUNJABSLDC](http://www.punjabsldc.org/realtimepbGen.aspx)
- India (Chhattisgarh, Delhi, Gujarat, Karnataka, Punjab, Uttar Pradesh): [National Power Portal](https://npp.gov.in/dashBoard/cp-map-dashboard)
- Kuwait
  - Gas & oil: [KAPSARC](https://datasource.kapsarc.org/api/datasets/1.0/kuwait-power-plants-database/attachments/power_plants_xlsx/)
  - Solar & wind: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Latvia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Lithuania: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Malaysia: [GSO](https://www.gso.org.my/SystemData/PowerStation.aspx)
- Moldova
  - Renewable: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Other: [FAS](http://en.fas.gov.ru/upload/other/National%20Agency%20for%20Energy%20Regulation%20(G.%20Pyrzy).pdf)
- Montenegro
  - Solar, Hydro & Wind: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Other: [EPCG](http://www.epcg.com/en/about-us/production-facilities)
- Nagorno-Karabakh: [Artsakh HEK](http://artsakhhek.am/?lang=en)
- Namibia
  - Coal & Oil: [NamPower](http://www.nampower.com.na/Page.aspx?p=182)
  - Hydro, solar & wind: [African Energy](https://www.africa-energy.com/database)
- Nepal
  -List of PowerStations:[PowerStations](https://en.wikipedia.org/wiki/List_of_power_stations_in_Nepal)
  - GIS Map of Reservoir Projects: [GIS_Reservoir](https://www.doed.gov.np/download/GIS-map-of-reservoir-projects.pdf)
- Netherlands
  - Renewables: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Nicaragua: [Climatescope](http://global-climatescope.org/en/country/nicaragua/)
- Norway
  - Hydro: [NVE](https://www.nve.no/energiforsyning/kraftproduksjon/vannkraft/vannkraftdatabase/)
  - Wind: [NVE](https://www.nve.no/energiforsyning/kraftproduksjon/vindkraft/vindkraftdata/)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Northern Ireland: [ENTSO-E](https://m-transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Oman: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Panama: [Secretaría de Energía de Panamá](http://www.energia.gob.pa/mercado-energetico/?tag=84#documents-list)
- Peru: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Poland
  - Solar: [PSE Twitter](https://twitter.com/pse_pl/status/1291264471806218242)
  - Biomass: [URE](https://www.ure.gov.pl/download/9/11276/mocIIkw2020.pdf)
  - Wind: [URE](https://www.ure.gov.pl/download/9/11276/mocIIkw2020.pdf)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Portugal
  - Biomass, Solar, Wind and Geothermal: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Qatar: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- Romania:
  - Nuclear: [Nuclearelectrica](http://www.nuclearelectrica.ro/cne/)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Russia: [Minenergo](https://minenergo.gov.ru/node/532)
- Serbia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show?)
- Singapore
  - Solar: [Energy Market Authority Statistics](https://www.ema.gov.sg/statistic.aspx?sta_sid=20170711hc85chOLVvWp)
  - Other: [Energy Market Authority](https://www.ema.gov.sg/cmsmedia/Publications_and_Statistics/Publications/SES/2016/Singapore%20Energy%20Statistics%202016.pdf)
- Slovakia: [SEPS](https://www.sepsas.sk/Dokumenty/RocenkySed/ROCENKA_SED_2015.pdf)
- Slovenia: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- South Korea: [KHNP](http://cms.khnp.co.kr/content/163/main.do?mnCd=FN05040101)
- Spain:
  - Biomass: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Gas, Oil: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show?)
  - Other: [REE](https://www.ree.es/es/datos/publicaciones/series-estadisticas-nacionales)
- Spain (Canary Islands)
  - Hydro storage: [goronadelviento.es](http://www.goronadelviento.es/)
  - Wind, Solar: [REE](http://www.ree.es/sites/default/files/11_PUBLICACIONES/Documentos/Renovables-2016-v3.pdf)
- Spain (Balearic Islands)
  - Coal: [wikipedia.org](https://es.wikipedia.org/wiki/Central_t%C3%A9rmica_de_Es_Murterar)
  - Wind, Solar: [REE](http://www.ree.es/sites/default/files/11_PUBLICACIONES/Documentos/Renovables-2016-v3.pdf)
- Sweden
  - Renewables: [IRENA](http://resourceirena.irena.org/gateway/countrySearch/?countryCode=SWE)
  - Wind: [Svensk Vindenergi](https://svenskvindenergi.org/wp-content/uploads/2020/02/Statistics-and-forecast-Svensk-Vindenergi-feb-2020-FINAL.pdf)
  - Solar: [Energimyndigheten](http://pxexternal.energimyndigheten.se/sq/00626276-14d1-417a-89ac-f850e48e7f74)
  - Nuclear: [Vattenfall](https://group.vattenfall.com/se/var-verksamhet/forsmark/produktion)
  - Nuclear 2: [OKG](https://www.okg.se/sv/Om-OKG/)
  - Coal: [Stockholm Exergi](https://www.stockholmexergi.se/nyheter/kvv6/)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Switzerland
  - Solar: [IREAN](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2019/Mar/IRENA_RE_Capacity_Statistics_2019.pdf)
  - Nuclear: [BKW](https://www.bkw.ch/fr/le-groupe-bkw/notre-infrastructure/centrale-nucleaire-de-muehleberg/desaffectation/lapercu/#Home)
  - Other: [ENTSO-E](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)
- Taiwan: [TAIPOWER](http://www.taipower.com.tw/d006/loadGraph/loadGraph/genshx_.html)
- Turkey:
  - Renewable: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
  - Other: [TEİAŞ](https://www.teias.gov.tr/)
- Ukraine: [UKRENERGO](https://ua.energy/vstanovlena-potuzhnist-energosystemy-ukrayiny/)
- United Arab Emirates: [IRENA](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Mar/IRENA_RE_Capacity_Statistics_2020.pdf)
- United States of America
  - Federal: [EIA](https://www.eia.gov/electricity/data.cfm#gencapacity)
  - States: [EIA](https://www.eia.gov/electricity/data/state/)
  - BPA: [BPA](https://transmission.bpa.gov/business/operations/Wind/baltwg.aspx)
  - CAISO
    - CEC: [CEC](https://ww2.energy.ca.gov/almanac/electricity_data/electric_generation_capacity.html)
    - Renewables: [CAISO](http://www.caiso.com/informed/Pages/CleanGrid/default.aspx)
    - Nuclear: [wikipedia.org](https://en.wikipedia.org/wiki/Diablo_Canyon_Power_Plant)
  - MISO: [MISO](https://www.misoenergy.org/about/media-center/corporate-fact-sheet/)
  - NYISO: [NYISO Gold Book](https://home.nyiso.com/wp-content/uploads/2017/12/2017_Gold-Book.pdf)
  - PJM: [PJM](http://www.pjm.com/-/media/markets-ops/ops-analysis/capacity-by-fuel-type-2019.ashx?la=en)
  - SPP: [SPP](https://www.spp.org/about-us/fast-facts/)
- Uruguay: [UTE](https://portal.ute.com.uy/institucional/infraestructura/fuentes-de-generacion)
&nbsp;</details>

### Cross-border transmission capacity data sources
Cross-border transmission capacities between the zones are centralized in the [exchanges.json](https://github.com/tmrowco/electricitymap-contrib/blob/master/config/exchanges.json) file. Values in the `capacity` maps are in MW.
&nbsp;<details><summary>Click to see the full list of sources</summary>
- Åland ⇄ Sweden: ["Sverigekabeln": 80 MW](http://www.kraftnat.ax/files/rapportdel_2.pdf)
- Åland ⇄ Finland: ["Brändö-Gustafs": 9 MW](http://www.kraftnat.ax/files/rapportdel_2.pdf)
- Albania ⇄ Greece: [533 MW](https://ec.europa.eu/energy/sites/ener/files/documents/2nd_report_ic_with_neighbouring_countries_b5.pdf)
- Australia (Victoria) ⇄ Australia (Tasmania): ["Basslink": 500 MW (regular) or 630 MW (temporarily)](https://en.wikipedia.org/wiki/Basslink)
- Bulgaria ⇄ Noth Macedonia [950 MW](https://ec.europa.eu/energy/sites/ener/files/documents/2nd_report_ic_with_neighbouring_countries_b5.pdf)
- Bulgaria ⇄ Turkey [2485 MW](https://ec.europa.eu/energy/sites/ener/files/documents/2nd_report_ic_with_neighbouring_countries_b5.pdf)
- Denmark (West) ⇄ Norway: ["Skaggerak": 1700 MW](https://en.wikipedia.org/wiki/Skagerrak_(power_transmission_system))
- Denmark (East) ⇄ Denmark (West): ["Storebælt HVDC": 600 MW](https://en.wikipedia.org/wiki/Great_Belt_Power_Link)
- Denmark (East) ⇄ Germany: ["Kontek": 600 MW](https://en.wikipedia.org/wiki/Kontek)
- Denmark (West) ⇄ Sweden: ["Konti-Skan": 650 MW](https://en.wikipedia.org/wiki/Konti%E2%80%93Skan)
- Denmark (West) ⇄ Netherlands: ["COBRAcable": 700 MW](https://en.wikipedia.org/wiki/COBRAcable)
- Estonia ⇄ European Russia And Ural [2464 MW](https://ec.europa.eu/energy/sites/ener/files/documents/2nd_report_ic_with_neighbouring_countries_b5.pdf)
- Estonia ⇄ Finnland: ["Estlink 1&2": 1000 MW](https://en.wikipedia.org/wiki/Estlink)
- Germany ⇄ Sweden: ["Baltic Cable": 600 MW](https://en.wikipedia.org/wiki/Baltic_Cable)
- Germany ⇄ Norway: ["NordLink": 1400MW](https://en.wikipedia.org/wiki/NORD.LINK)
- Great Britain ⇄ Belgium: ["Nemo Link": 1000 MW](https://en.wikipedia.org/wiki/Nemo_Link)
- Great Britain ⇄ North Ireland: ["Moyle": 500 MW](http://www.wikiwand.com/en/HVDC_Moyle)
- Great Britain ⇄ Ireland: ["East-West Interconnector": 500 MW](https://en.wikipedia.org/wiki/East%E2%80%93West_Interconnector)
- Great Britain ⇄ France: ["Cross-Channel": 2000 MW](https://en.wikipedia.org/wiki/NorNed)
- Great Britain ⇄ Netherlands: ["BritNed": 1000 MW](https://en.wikipedia.org/wiki/BritNed)
- Greece ⇄ Italy: ["GRITA": 500 MW](https://en.wikipedia.org/wiki/HVDC_Italy%E2%80%93Greece)
- Greece ⇄ Turkey: [1900 MW](https://ec.europa.eu/energy/sites/ener/files/documents/2nd_report_ic_with_neighbouring_countries_b5.pdf)
- Italy Central South ⇄ Italy Sardinia: ["SAPEI": 1000 MW](https://en.wikipedia.org/wiki/SAPEI)
- Japan-Chūbu ⇄ Japan-Tōkyō: [3x HVDC interconnectors between 60Hz/50Hz areas: 1200 MW](https://www.jepic.or.jp/pub/pdf/epijJepic2019.pdf)
- Japan-Hokkaidō ⇄ Japan-Tōhoku: ["HVDC Hokkaidō–Honshū": 900 MW](https://ja.wikipedia.org/wiki/%E5%8C%97%E6%B5%B7%E9%81%93%E3%83%BB%E6%9C%AC%E5%B7%9E%E9%96%93%E9%80%A3%E7%B3%BB%E8%A8%AD%E5%82%99)
- Latvia ⇄ European Russia And Ural [696 MW](https://ec.europa.eu/energy/sites/ener/files/documents/2nd_report_ic_with_neighbouring_countries_b5.pdf)
- Lithuania ⇄ Sweden: ["NordBalt": 700 MW](https://en.wikipedia.org/wiki/NordBalt)
- Lithuania ⇄ Poland: ["LitPol Link": 500 MW](https://en.wikipedia.org/wiki/LitPol_Link)
- Malta ⇄ Italy Sicily: ["Malta–Sicily-Interconnector": 200 MW](https://en.wikipedia.org/wiki/Malta%E2%80%93Sicily_interconnector)
- Montenegro ⇄ Italy Central South: ["MONITA": 600MW](https://tyndp.entsoe.eu/tyndp2018/projects/projects/28)
- Norway ⇄ Netherlands: ["NorNed": 700 MW](https://en.wikipedia.org/wiki/NorNed)
- New Zealand (North Island) ⇄ New Zealand (South Island): ["HVDC Inter-Island": 1200 MW](https://en.wikipedia.org/wiki/HVDC_Inter-Island)
- Russia ⇉ Finland: ["Vyborg HVDC scheme": 1400 MW + 2 AC-connections: 160 MW](https://www.entsoe.eu/Documents/Publications/SOC/Nordic/System_Operation_Agreement_appendices(English_2016_update).pdf)
- Spain ⇄ France: [According to "The Spanish electricity system 2019" page 65: 2800 MW](https://www.ree.es/sites/default/files/11_PUBLICACIONES/Documentos/InformesSistemaElectrico/2019/ISE_2019_eng.pdf)
- Spain ⇄ Spain (Balearic Islands): ["Cometa": 400 MW](https://en.wikipedia.org/wiki/Cometa_(HVDC))
- Sweden ⇄ Poland: ["SwePol": 600 MW](https://en.wikipedia.org/wiki/SwePol)
- Ukraine ⇄ Belarus, ⇄ Hungary, ⇉ Poland, ⇄ Moldova, ⇄ Slovakia, ⇄ Romania, ⇄ Russia: [Ukrenergo](https://ua.energy/activity/dispatch-information/transborder-flows/)

A ⇄ B: bidirectional operation, with power flow either "from A to B" or "from B to A"

A ⇉ B: unidirectional operation, only with power flow "from A to B"
&nbsp;</details>

### Electricity prices (day-ahead) data sources
- France: [RTE](https://www.rte-france.com/en/eco2mix/market-data)
- Japan: [JEPX](http://www.jepx.org)
- Nicaragua: [CNDC](http://www.cndc.org.ni/)
- Singapore: [EMC](https://www.emcsg.com)
- Turkey: [EPIAS](https://seffaflik.epias.com.tr/transparency/piyasalar/gop/ptf.xhtml)
- Other: [ENTSO-E](https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show)

### Real-time weather data sources
We use the [US National Weather Service's Global Forecast System (GFS)](http://nomads.ncep.noaa.gov/)'s GFS 0.25 Degree Hourly data.
Forecasts are made every 6 hours, with a 1 hour time step.
The values extracted are wind speed and direction at 10m altitude, and ground solar irradiance (DSWRF - Downward Short-Wave Radiation Flux), which takes into account cloud coverage.
In order to obtain an estimate of those values at current time, an interpolation is made between two forecasts (the one at the beginning of the hour, and the one at the end of the hour).


### Topology data
We use the [Natural Earth Data Cultural Vectors](http://www.naturalearthdata.com/downloads/10m-cultural-vectors/) country subdivisions (map admin subunits).


## Contribute
Want to help? First of all, thank you for your interest!

Join us on Slack at [http://slack.tmrow.co](http://slack.tmrow.co) to see what we are working on and to get in touch with other contributors. Also, if you get stuck, you can write a message in our channel #electricitymap.

For different ways to help improve electricityMap, have a look at the [overview above](#electricitymap---). Here is how to get started:

### Steps to making a code contribution
Follow these steps to make your contribution:
1. [Fork](https://help.github.com/articles/fork-a-repo/) the repository.
2. [Clone](https://help.github.com/articles/cloning-a-repository/) *your fork* of the repository.
3. Download [Docker](https://docs.docker.com/engine/installation/).
4. Set up and start your local environment ([see steps below](#set-up-and-start-your-local-environment)).
5. Make your code changes and test them in your local environment.
6. Push your changes to your fork.
7. Submit a [pull request](https://help.github.com/articles/using-pull-requests/) to bring your contribution into the production version.

#### Set up and start your local environment

Note: to test parsers, go to [test-parsers-locally](#test-parsers-locally)

1. First, you need to compile the frontend. Open a terminal in the root directory and run:

   ```
   docker-compose build
   ```

2. Start the application by running:

   ```
   docker-compose up
   ```

   This will watch over source file changes, run nonstop and watch changes you make in the code to recompile the frontend if needed.

3. Go to [http://localhost:8000/](http://localhost:8000/) and you should now see the map!

Notes:
   - These steps only build with the English language (which will be faster as not all languages need to be built). To build all languages, change the `command` of the `web-watch-en` section of docker-compose.yml from `command: npm run watch-en` to `command: npm run watch`.
   - The backend handles the calculation of carbon emissions. The map data displayed comes from a mock server providing dummy data from the [state file](https://github.com/tmrowco/electricitymap-contrib/blob/master/mockserver/public/v3/state).

See [Troubleshooting](#troubleshooting) below for common issues and fixes when building the map locally.

### Logger
If you want to add new or change existing parsers you can use our public [logger](https://kibana.electricitymap.org/app/kibana#/discover/10af54f0-0c4a-11e9-85c1-1d63df8c862c?_g=()&_a=(columns:!(message,extra.key,level),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!f,index:'96f67170-0c49-11e9-85c1-1d63df8c862c',key:level,negate:!f,params:(query:ERROR,type:phrase),type:phrase,value:ERROR),query:(match:(level:(query:ERROR,type:phrase))))),index:'96f67170-0c49-11e9-85c1-1d63df8c862c',interval:auto,query:(language:lucene,query:''),sort:!('@timestamp',asc))) to see if your parser(s) can fetch data successfully.
The logs show warnings and errors for all parsers.

### Update region capacities
If you want to update or add production capacities for a region, go to the [zones file](https://github.com/tmrowco/electricitymap-contrib/blob/master/config/zones.json) and make changes to the `capacity` map. Values are in MW. The zones use [ISO 3166-1 codes](https://en.wikipedia.org/wiki/ISO_3166-1#Current_codes) as identifiers.

### Add a new region
As a first step, do a search for the region on our GitHub, as contributors may have explored things before.
It is very simple to add a new country. The electricityMap backend runs a list of so-called *parsers* every 5 minutes. Those parsers are responsible for fetching the generation mix of a given country. See the existing list in the [parsers](https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers) directory, or review [work in progress parsers](https://github.com/tmrowco/electricitymap-contrib/issues?q=is%3Aissue+is%3Aopen+label%3Aparser)).

#### I have not found a new data source
Open a new issue for the relevant region and add the relevant individual or organization to contact. Please include email, Twitter and phone number for the contact where available.

This helps us and the community to contact them and make them aware of the electricityMap. Usually, energy agencies, governments, and transmission system operators are good potential sources. If you can't code, this is an amazing way to help us!

#### I have found a data source and I could help build a parser
A parser is a python3 script that defines the method `fetch_production` and returns the production mix at current time, in this format:

```python
def fetch_production(zone_key='FR', session=None, target_datetime=None, logger=None):
    return {
      'zoneKey': 'FR',
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

It contains the following objects:

  - `session`: a [python request](http://docs.python-requests.org/en/master/) session that you can re-use to make HTTP requests.
  - `target_datetime`: used to fetch historical data when available.
  - `logger`: a `logging.Logger` whose output is publicly available for anyone to monitor correct functioning of the parsers.

The production values should never be negative. Use `None`, or omit the key if a specific production mode is not known.
Storage values can be both positive (when storing energy) or negative (when the storage is emptied).

The parser can also return an array of objects if multiple time values can be fetched. The backend will automatically update past values properly.

Once you're done, add your parser to the [zones.json](https://github.com/tmrowco/electricitymap-contrib/tree/master/config/zones.json) and [exchanges.json](https://github.com/tmrowco/electricitymap-contrib/tree/master/config/exchanges.json) configuration files. Finally update the [real-time sources](#real-time-electricity-data-sources).

Run all the parser tests with the following command from the root directory:
```
python -m unittest discover parsers/test/
```

For more info, check out the [example parser](https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers/example.py) or browse existing [parsers](https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers).

### Generate a new map
If your changes involve altering the way countries are displayed on the map, a new world.json will need to be generated. Make sure you're in the root directory then run the following command:

```
docker-compose run --rm web ./topogen.sh
```

[Learn more about how the map is generated](https://github.com/tmrowco/electricitymap-contrib/blob/master/web/README.md).

### Test parsers locally

1. Make sure you have installed the required modules as described in [parsers/requirements.txt](https://github.com/tmrowco/electricitymap-contrib/blob/master/parsers/requirements.txt), and are using python 3.6 (consider using a [virtual environment](https://docs.python.org/3/library/venv.html) for python). To confirm this, run:

   ```
   pip install -r parsers/requirements.txt
   ```
2. From the root folder, use the `test_parser.py` command line utility:

   ```python
   python test_parser.py FR price  # get latest price parser for France
   python test_parser.py FR  # defaults to production if no data type is given
   # test a specific datetime (parser needs to be able to fetch past datetimes)
   python test_parser.py DE --target_datetime 2018-01-01T08:00
   python test_parser.py "CH->FR" exchange # get the exchange data between Switzerland & France
   ```

Many of the tests require API keys of the data or web service providers, and therefore fail with an error message like

```
Exception: No ENTSOE_TOKEN found! Please add it into secrets.env!
```

In such cases, please browse the website related to the provider and ask for an API key. Once you get hold of the API key, make it an environment variable. This fixes the error.

### Update the map
We've added a testing server locally.

To add a new country to the map, run:
```
PYTHONPATH=. python mockserver/update_state.py <zone_name>
```

from the root directory, replacing `<zone_name>` by the zone identifier of the parser you want to test. This fetches production, and assigns it a random carbon intensity value. It should appear on the map as you refresh your local browser.

### Troubleshooting

- `ERROR: for X Cannot create container for service X: Invalid bind mount spec "<path>": Invalid volume specification: '<volume spec>'`. If you get this error after running `docker-compose up` on Windows, you should tell `docker-compose` to properly understand Windows paths by setting the environment variable `COMPOSE_CONVERT_WINDOWS_PATHS` to `0` by running `setx COMPOSE_CONVERT_WINDOWS_PATHS 0`. You will also need a recent version of `docker-compose`. We have successfully seen this fix work with [v1.13.0-rc4](https://github.com/docker/toolbox/releases/tag/v1.13.0-rc4). More info here: https://github.com/docker/compose/issues/4274.

- No website found at `http://localhost:8000`: This can happen if you're running Docker in a virtual machine. Find out docker's IP using `docker-machine ip default`, and replace `localhost` by your Docker IP when connecting.

#### Windows Specific

- `FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory`. You can configure the memory allocation using `NODE_OPTIONS=--max-old-space-size=4096` in the "build-release" script in package.json, example: `export NODE_OPTIONS=--max-old-space-size=4096 NODE_ENV=production && webpack --bail --mode production`. Also update the node version (last working version was `v12.16.3`).

- Expected linebreaks to be 'LF' but found 'CRLF': Configure your IDE to use LF instead of CRLF. If that doesn't fix it, add `"linebreak-style": 0` in "rules" in .estlintrc

- `ERROR: for electricitymap-contrib_mockserver_1  Cannot start service mockserver: OCI runtime create failed: container_linux.go:345: starting container process caused "process_linux.go:424: container init caused \"rootfs_linux.go:58: mounting \\\".../server.py\\\" to rootfs \\\"/mnt/sda1/var/lib/docker/overlay2/.../merged\\\" at \\\".../server.py\\\" caused \\\"not a directory\\\"\"": unknown: Are you trying to mount a directory onto a file (or vice-versa)? Check if the specified host path exists and is the expected type`.
   - Check that the project is cloned under C:/Users/

- nodemon not restarting on file changes: try adding the `-L` parameter to use the legacy watch: `"server-dev": "nodemon server.js -L"`. See https://www.npmjs.com/package/nodemon#application-isnt-restarting
