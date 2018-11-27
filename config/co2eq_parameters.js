var exports = module.exports = {};

var defaultExportConfig = {
    'AZ': {
        carbonIntensity: 470,
        renewableRatio: 0.07,
        fossilFuelRatio: 0.92,
        source: 'IEA yearly data for 2015',
        url: 'https://www.iea.org/statistics/statisticssearch/report/?country=AZERBAIJAN&product=electricityandheat&year=2015'
    },
    'CA-BC': {
        carbonIntensity: 47,
        renewableRatio: 0.97,
        fossilFuelRatio: 0.03,
        source: 'List of Generating Stations in BC (Wikipedia) / IPCC 2014 Emissions Factors By Source',
        url: 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_British_Columbia',
        comment: 'Average carbon intensity using 2016 mean production per fuel source (88% hydro, 9% biomass, 1% wind, 1% gas) and IPCC 2014 default lifecycle emission factors'
    },
    'CA-NB': {
        carbonIntensity: 300,
        renewableRatio: 0.27,
        fossilFuelRatio: 0.40,
        source: 'Canada NEB yearly data for 2016',
        url: 'https://www.neb-one.gc.ca/nrg/ntgrtd/mrkt/nrgsstmprfls/nb-eng.html'
    },
    'CA-QC': {
        carbonIntensity: 30,
        renewableRatio: 0.98,
        fossilFuelRatio: 1 - 0.98,
        source: 'StatCan CANSIM Table 127-0002 for 2011-2015',
        comment: 'see http://piorkowski.ca/rev/2017/06/canadian-electricity-co2-intensities/ and https://gist.github.com/jarek/bb06a7e1c5d9005b29c63562ac812ad7',
        comment2: 'not using NEB data here since the NEB resolution is 1% which makes a difference at these scales'
    },
    'RU-KGD': {
        carbonIntensity: 480,
        renewableRatio: 0.02,
        fossilFuelRatio: 1 - 0.02,
        source: 'Energy security in Kaliningrad and geopolitics (2/2014)',
        comment: 'see http://www.centrumbalticum.org/files/1899/BSR_Policy_Briefing_2_2014.pdf and https://newsbase.com/topstories/russia-invest-us156bn-kaliningrad-power-plants',
        comment2: 'About 98% generation from gas in RU-KGD in the past. 5.1 MW wind (2002) and 1.7 MW total hydro installed. 3 gas units (1x440 + 2x156 MW) may come online in 2018, 3x65 MW coal units of Primorskaya TPP probably in 2019 due to future seperation of Baltics from BRELL synchronous area.'
    },
    'US': {
        carbonIntensity: 325,
        renewableRatio: 0.30,
        fossilFuelRatio: 0.70,
        source: 'https://github.com/tmrowco/electricitymap/issues/1497',
        comment: 'Only for imports to California! Renewable ratio assumed as average 25% hydro with some wind/solar; low-carbon assumed as with average 20% nuclear; from information in Github issue we assume it is either mostly from source with hydro or from source with nuclear but not both'
    },
    'ZA': {
        carbonIntensity: 750,
        renewableRatio: 0.03,
        fossilFuelRatio: 0.92,
        source: 'IEA yearly data for 2015',
        url: 'https://www.iea.org/statistics/statisticssearch/report/?country=SOUTHAFRIC&product=electricityandheat&year=2015'
    },
    'ZM': {
        carbonIntensity: 50,
        renewableRatio: 0.97,
        fossilFuelRatio: 0.03,
        source: 'IEA yearly data for 2015',
        url: 'https://www.iea.org/statistics/statisticssearch/report/?country=ZAMBIA&product=electricityandheat&year=2015'
    }
}

const co2eqParameters = require('./co2eq_parameters.json');

exports.footprintOf = function(mode, zoneKey) {
  const defaultFootprint = co2eqParameters.defaults[mode];
  const override = (co2eqParameters.zoneOverrides[zoneKey] || {})[mode];
  return (override || defaultFootprint || {}).value;
};
exports.sourceOf = function(mode, zoneKey) {
  const defaultFootprint = co2eqParameters.defaults[mode];
  const override = (co2eqParameters.zoneOverrides[zoneKey] || {})[mode];
  return (override || defaultFootprint || {}).source;
}
exports.defaultExportIntensityOf = zoneKey =>
  (defaultExportConfig[zoneKey] || {}).carbonIntensity;
exports.defaultRenewableRatioOf = zoneKey =>
  (defaultExportConfig[zoneKey] || {}).renewableRatio;
exports.defaultFossilFuelRatioOf = zoneKey =>
  (defaultExportConfig[zoneKey] || {}).fossilFuelRatio;
