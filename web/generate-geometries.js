const fs = require('fs');

// https://stackoverflow.com/a/15030117/3218806
function flatten(arr) {
  return arr.reduce(function (flat, toFlatten) {
    return flat.concat(Array.isArray(toFlatten) ? flatten(toFlatten) : toFlatten);
  }, []);
}

function readNDJSON(path) {
  return fs.readFileSync(path, 'utf8').split('\n')
    .filter(d => d !== '')
    .map(JSON.parse);
}

const countryGeos = readNDJSON('./build/tmp_countries.json');
const stateGeos = readNDJSON('./build/tmp_states.json');
const thirpartyGeos = readNDJSON('./build/tmp_thirdparty.json')
  .concat([
    require('./third_party_maps/DK-DK2-without-BHM.json'),
    require('./third_party_maps/NO-NO1.json'),
    require('./third_party_maps/NO-NO2.json'),
    require('./third_party_maps/NO-NO3.json'),
    require('./third_party_maps/NO-NO4.json'),
    require('./third_party_maps/NO-NO5.json'),
    require('./third_party_maps/SE-SE1.json'),
    require('./third_party_maps/SE-SE2.json'),
    require('./third_party_maps/SE-SE3.json'),
    require('./third_party_maps/SE-SE4.json'),
  ]);

const allGeos = countryGeos.concat(stateGeos, thirpartyGeos);

function geomerge() {
  // Convert both into multipolygon
  const geos = Array.prototype.slice.call(arguments).filter(d => d != null);
  geos.forEach((geo) => {
    if (geo.geometry.type === 'Polygon') {
      geo.geometry = {
        type: 'MultiPolygon',
        coordinates: [geo.geometry.coordinates],
      };
    } else if (geo.geometry.type !== 'MultiPolygon') {
      throw new Error(`Unexpected geometry type '${geo.geometry.type}'`);
    }
  });
  // Merge both
  return {
    type: 'Feature',
    geometry: {
      type: 'MultiPolygon',
      coordinates: Array.prototype.concat(...geos.map(d => d.geometry.coordinates)),
    },
    properties: {},
  };
}

function hascMatch(properties, hasc) {
  return (
    properties.code_hasc === hasc ||
    (properties.hasc_maybe && properties.hasc_maybe.split('|').indexOf(hasc) !== -1)
  );
}

function getCountry(countryId) {
  return geomerge(...allGeos.filter(d => d.id === countryId));
}
function getByPropertiesId(zoneId) {
  return geomerge(...allGeos.filter(d => d.properties.id === zoneId));
}
function getSubUnit(subid) {
  return geomerge(...allGeos.filter(d => d.properties.subid === subid));
}
function getState(countryId, code_hasc, use_maybe=false) {
  return geomerge(...allGeos.filter(d =>
    d.id === countryId && (use_maybe && hascMatch(d.properties, code_hasc) || d.properties.code_hasc === code_hasc)));
}
function getStateByFips(countryId, fips) {
  return geomerge(...allGeos.filter(d =>
    d.id === countryId && d.properties.fips === fips));
}
function getStateByAdm1(adm1_code) {
  return geomerge(...allGeos.filter(d => d.properties.adm1_code === adm1_code));
}

function getStates(countryId, code_hascs, use_maybe) {
  return geomerge(...code_hascs.map(d => getState(countryId, d, use_maybe)));
}
function getStatesByAdm1(adm1_codes) {
  return geomerge(...adm1_codes.map(getStateByAdm1));
}
function getCountries(countryIds) {
  return geomerge(...countryIds.map(getCountry));
}
function getSubUnits(ids) {
  return geomerge(...ids.map(getSubUnit));
}

const zoneDefinitions = [
  // Map between "zones" iso_a2 and adm0_a3 in order to support XX, GB etc..
  // Note that the definition of "zones" is very vague here..
  // Specific case of Kosovo and Serbia: considered as a whole as long as they will be reported together in ENTSO-E.
  // Add moreDetails:true to use a smaller threshold for simplifying a zone thus the zone will have more details. More details also means bigger world.json so use with small zones.
  {zoneName:'XX', type:'country', id:'CYN'},

  // List of all zones
  {zoneName: 'AE', type: 'country', id: 'ARE'},
  {zoneName: 'AF', type: 'country', id: 'AFG'},
  {zoneName: 'AL', type: 'country', id: 'ALB'},
  {zoneName: 'AS', type: 'country', id: 'ASM'},
  {zoneName: 'AD', type: 'country', id: 'AND'},
  {zoneName: 'AO', type: 'country', id: 'AGO'},
  {zoneName: 'AG', type: 'country', id: 'ATG'},
  {zoneName: 'AI', type: 'country', id: 'AIA'},
  {zoneName: 'AN', type: 'country', id: 'ANT'},
  {zoneName: 'AR', type: 'country', id: 'ARG'},
  // {zoneName: 'AQ', type: 'country', id: 'AT},
  {zoneName: 'AM', type: 'country', id: 'ARM'},
  {zoneName: 'AT', type: 'country', id: 'AUT'},
  {zoneName: 'AUS-NSW', type: 'states', countryId: 'AUS', states: ['AU.NS', 'AU.AC']},
  {zoneName: 'AUS-NT', countryId: 'AUS', stateId: 'AU.NT', type: 'state'},
  // {zoneName: 'AU', type: 'country', id: 'AUS'},
  // {zoneName: 'AUS-ACT', countryId: 'AUS', stateId: 'AU.AC', type: 'state'},
  {zoneName: 'AUS-QLD', countryId: 'AUS', stateId: 'AU.QL', type: 'state'},
  {zoneName: 'AUS-SA', countryId: 'AUS', stateId: 'AU.SA', type: 'state'},
  {zoneName: 'AUS-TAS', countryId: 'AUS', stateId: 'AU.TS', type: 'state'},
  {zoneName: 'AUS-VIC', countryId: 'AUS', stateId: 'AU.VI', type: 'state'},
  {zoneName: 'AUS-WA', countryId: 'AUS', stateId: 'AU.WA', type: 'state'},
  {zoneName: 'AW', type: 'country', id: 'ABW', moreDetails: true},
  {zoneName: 'AX', type: 'country', id: 'ALA'},
  {zoneName: 'AZ', type: 'country', id: 'AZE'},
  //{zoneName: 'BA', type: 'country', id: 'BIH'},
  {zoneName: 'BA', type: 'administrations', administrations: [
      'BIH-4801', 'BIH-4802', 'BIH-2225', 'BIH-2224', 'BIH-2226', 'BIH-2227', 'BIH-2228', 'BIH-4807',
      'BIH-4808', 'BIH-4805', 'BIH-4806', 'BIH-2890', 'BIH-2891', 'BIH-2889', 'BIH-2887',
      'BIH-4804', 'BIH-3153', 'BIH-4803']},
  {zoneName: 'BB', type: 'country', id: 'BRB'},
  {zoneName: 'BD', type: 'country', id: 'BGD'},
  {zoneName: 'BE', type: 'country', id: 'BEL'},
  {zoneName: 'BH', type: 'country', id: 'BHR'},
  {zoneName: 'BJ', type: 'country', id: 'BEN'},
  {zoneName: 'BL', type: 'country', id: 'BLM'},
  {zoneName: 'BO', type: 'country', id: 'BOL'},
  {zoneName: 'BM', type: 'country', id: 'BMU'},
  //{zoneName: 'BR', type: 'country', id: 'BRA'},
  {zoneName: 'BR-CS', type: 'states', countryId: 'BRA', states: ['BR.', 'BR.AC', 'BR.GO', 'BR.SP', 'BR.DF', 'BR.MS', 'BR.MG', 'BR.MT', 'BR.ES', 'BR.RJ', 'BR.RO']},
  {zoneName: 'BR-N', type: 'states', countryId: 'BRA', states: ['BR.AM', 'BR.PA', 'BR.TO', 'BR.RR', 'BR.AP']},
  {zoneName: 'BR-NE', type: 'states', countryId: 'BRA', states: ['BR.PE', 'BR.MA', 'BR.CE', 'BR.PI', 'BR.AL', 'BR.BA', 'BR.PB', 'BR.RN', 'BR.SE']},
  {zoneName: 'BR-S', type: 'states', countryId: 'BRA', states: ['BR.RS', 'BR.SC', 'BR.PR']},
  {zoneName: 'BS', type: 'country', id: 'BHS'},
  {zoneName: 'BT', type: 'country', id: 'BTN'},
  {zoneName: 'BV', type: 'country', id: 'BVT'},
  {zoneName: 'BW', type: 'country', id: 'BWA'},
  {zoneName: 'BY', type: 'country', id: 'BLR'},
  {zoneName: 'BZ', type: 'country', id: 'BLZ'},
  {zoneName: 'BN', type: 'country', id: 'BRN'},
  {zoneName: 'BG', type: 'country', id: 'BGR'},
  {zoneName: 'BF', type: 'country', id: 'BFA'},
  {zoneName: 'BI', type: 'country', id: 'BDI'},
  {zoneName: 'CA-AB', countryId: 'CAN', stateId: 'CA.AB', type: 'state'},
  // {zoneName: 'CA', type: 'country', id: 'CAN'},
  {zoneName: 'CA-BC', countryId: 'CAN', stateId: 'CA.BC', type: 'state'},
  {zoneName: 'CA-MB', countryId: 'CAN', stateId: 'CA.MB', type: 'state'},
  {zoneName: 'CA-NB', countryId: 'CAN', stateId: 'CA.NB', type: 'state'},
  // since 2002, ISO 3166-2 is "CA-NL", code_hasc in naturalearth is "CA.NF"
  {zoneName: 'CA-NL', countryId: 'CAN', stateId: 'CA.NF', type: 'state'},
  {zoneName: 'CA-NS', countryId: 'CAN', stateId: 'CA.NS', type: 'state'},
  {zoneName: 'CA-ON', countryId: 'CAN', stateId: 'CA.ON', type: 'state'},
  {zoneName: 'CA-PE', countryId: 'CAN', stateId: 'CA.PE', type: 'state'},
  {zoneName: 'CA-QC', countryId: 'CAN', stateId: 'CA.QC', type: 'state'},
  {zoneName: 'CA-SK', countryId: 'CAN', stateId: 'CA.SK', type: 'state'},
  {zoneName: 'CA-NT', countryId: 'CAN', stateId: 'CA.NT', type: 'state'},
  {zoneName: 'CA-NU', countryId: 'CAN', stateId: 'CA.NU', type: 'state'},
  {zoneName: 'CA-YT', countryId: 'CAN', stateId: 'CA.YT', type: 'state'},
  {zoneName: 'CC', type: 'country', id: 'CCK'},
  {zoneName: 'CF', type: 'country', id: 'CAF'},
  {zoneName: 'CG', type: 'country', id: 'COG'},
  {zoneName: 'CH', type: 'country', id: 'CHE'},
  {zoneName: 'CI', type: 'country', id: 'CIV'},
  {zoneName: 'CL-SING', type: 'states', countryId: 'CHL', states: ['CL.AP', 'CL.TA', 'CL.AN']},
  //{zoneName: 'CL', type: 'country', id: 'CHL'},
  {zoneName: 'CL-SIC', type: 'administrations', administrations: ['CHL-2696', 'CHL-2697', 'CHL-2699', 'CHL-2698', 'CHL-2703', 'CHL-2705', 'CHL-2702', 'CHL-2700', 'CHL-2701', 'CHL-2704']},
  {zoneName: 'CL-SEM', countryId: 'CHL', stateId: 'CL.MA', type: 'state'},
  {zoneName: 'CL-SEA', countryId: 'CHL', stateId: 'CL.AI', type: 'state'},
  {zoneName: 'CM', type: 'country', id: 'CMR'},
  {zoneName: 'CN', type: 'country', id: 'CHN'},
  {zoneName: 'CO', type: 'country', id: 'COL'},
  {zoneName: 'CV', type: 'country', id: 'CPV'},
  {zoneName: 'CX', type: 'country', id: 'CXR'},
  {zoneName: 'CD', type: 'country', id: 'COD'},
  {zoneName: 'CK', type: 'country', id: 'COK'},
  {zoneName: 'CR', type: 'country', id: 'CRI'},
  {zoneName: 'CU', type: 'country', id: 'CUB'},
  {zoneName: 'CY', type: 'country', id: 'CYP'},
  {zoneName: 'CZ', type: 'country', id: 'CZE'},
  {zoneName: 'DE', type: 'country', id: 'DEU'},
  {zoneName: 'DJ', type: 'country', id: 'DJI'},
  // {zoneName: 'DK', type: 'subunits', subunits: ['DNK']},
  { zoneName: 'DK-DK1', type: 'states', countryId: 'DNK', states: ['DK.MJ', 'DK.ND', 'DK.SD'] },
  { zoneName: 'DK-DK2', type: 'subZone', id: 'DK-DK2' },
  {zoneName: 'DK-BHM', type: 'subunits', subunits: ['DNB']},
  {zoneName: 'DM', type: 'country', id: 'DMA'},
  {zoneName: 'DO', type: 'country', id: 'DOM'},
  {zoneName: 'DZ', type: 'country', id: 'DZA'},
  {zoneName: 'EC', type: 'country', id: 'ECU'},
  {zoneName: 'EE', type: 'country', id: 'EST'},
  {zoneName: 'EG', type: 'country', id: 'EGY'},
  {zoneName: 'EH', type: 'country', id: 'ESH'},
  {zoneName: 'ER', type: 'country', id: 'ERI'},
  {zoneName: 'ES', type: 'subunits', subunits: ['ESX', 'SEC', 'SEM']}, //Spain Peninsula
  // spain canaries islands
  {zoneName: 'ES-CN-LP', type: 'country', id: 'La Palma'},
  {zoneName: 'ES-CN-HI', type: 'country', id: 'Hierro'},
  {zoneName: 'ES-CN-IG', type: 'country', id: 'Isla de la Gomera'},
  {zoneName: 'ES-CN-TE', type: 'country', id: 'Tenerife'},
  {zoneName: 'ES-CN-GC', type: 'country', id: 'Gran Canaria'},
  {zoneName: 'ES-CN-FVLZ', type: 'countries', countries: ['Fuerteventura', 'Lanzarote']},
  {zoneName: 'ES-IB', type: 'subunits', subunits: ['ESI']}, //Spain Balearic islands
  {zoneName: 'ET', type: 'country', id: 'ETH'},
  {zoneName: 'FI', type: 'country', id: 'FIN'},
  {zoneName: 'FJ', type: 'country', id: 'FJI'},
  {zoneName: 'FK', type: 'country', id: 'FLK'},
  {zoneName: 'FM', type: 'country', id: 'FSM'},
  // {zoneName: 'FR', type: 'country', id: 'FRA'},
  {zoneName: 'FO', type: 'country', id: 'FRO'},
  {zoneName: 'FR', type: 'subunits', subunits: ['FXX']},
  {zoneName: 'FR-COR', type: 'subunits', subunits: ['FXC']},
  {zoneName: 'GA', type: 'country', id: 'GAB'},
  {zoneName: 'GB', type: 'subunits', subunits: ['ENG', 'SCT', 'WLS']},
  {zoneName: 'GB-NIR', type: 'subunits', subunits: ['NIR']},
  {zoneName: 'GD', type: 'country', id: 'GRD'},
  {zoneName: 'GE', type: 'country', id: 'GEO'},
  {zoneName: 'GF', type: 'country', id: 'GUF'},
  {zoneName: 'GG', type: 'country', id: 'GGY'},
  {zoneName: 'GH', type: 'country', id: 'GHA'},
  {zoneName: 'GI', type: 'country', id: 'GIB'},
  {zoneName: 'GL', type: 'country', id: 'GRL'},
  {zoneName: 'GM', type: 'country', id: 'GMB'},
  {zoneName: 'GN', type: 'country', id: 'GIN'},
  {zoneName: 'GP', type: 'country', id: 'GLP'},
  {zoneName: 'GQ', type: 'country', id: 'GNQ'},
  // {zoneName: 'GR', type: 'country', id: 'GRC'},
  {zoneName: 'GR', type: 'states', countryId: 'GRC', states: ['GR.AT', 'GR.EP', 'GR.GC','GR.GW',
      'GR.II', 'GR.MA', 'GR.MC', 'GR.MT', 'GR.MW', 'GR.PP', 'GR.TS']},
  {zoneName: 'GR-IS', type: 'states', countryId: 'GRC', states: ['GR.AN', 'GR.AS', 'GR.CR']},
  {zoneName: 'GS', type: 'country', id: 'SGS'},
  {zoneName: 'GT', type: 'country', id: 'GTM'},
  {zoneName: 'GU', type: 'country', id: 'GUM'},
  {zoneName: 'GW', type: 'country', id: 'GNB'},
  {zoneName: 'GY', type: 'country', id: 'GUY'},
  {zoneName: 'HK', type: 'country', id: 'HKG'},
  {zoneName: 'HM', type: 'country', id: 'HMD'},
  {zoneName: 'HN', type: 'country', id: 'HND'},
  {zoneName: 'HT', type: 'country', id: 'HTI'},
  {zoneName: 'HU', type: 'country', id: 'HUN'},
  {zoneName: 'HR', type: 'country', id: 'HRV'},
  {zoneName: 'ID', type: 'country', id: 'IDN'},
  {zoneName: 'IE', type: 'country', id: 'IRL'},
  {zoneName: 'IL', type: 'country', id: 'ISR'},
  {zoneName: 'IM', type: 'country', id: 'IMN'},
  // TODO: Use iso_3166_2 field instead
  {zoneName: 'IN-AN', countryId: 'IND', stateId: 'IN.AN', useMaybe: true, type: 'state'},
  {zoneName: 'IN-AP', countryId: 'IND', stateId: 'IN.AD', useMaybe: true, type: 'state'},
  {zoneName: 'IN-AR', countryId: 'IND', stateId: 'IN.AR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-AS', countryId: 'IND', stateId: 'IN.AS', useMaybe: true, type: 'state'},
  {zoneName: 'IN-BR', countryId: 'IND', stateId: 'IN.BR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-CT', countryId: 'IND', stateId: 'IN.CT', useMaybe: true, type: 'state'},
  {zoneName: 'IN-CH', countryId: 'IND', stateId: 'IN.CH', useMaybe: true, type: 'state'},
  {zoneName: 'IN-DD', countryId: 'IND', stateId: 'IN.DD', useMaybe: true, type: 'state'},
  {zoneName: 'IN-DN', countryId: 'IND', stateId: 'IN.DN', useMaybe: true, type: 'state'},
  {zoneName: 'IN-DL', countryId: 'IND', stateId: 'IN.DL', useMaybe: true, type: 'state'},
  {zoneName: 'IN-GA', countryId: 'IND', stateId: 'IN.GA', useMaybe: true, type: 'state'},
  // For some reason IN.GJ is not a code_hasc in database, use FIPS code instead.
  // {zoneName: 'IN-GJ', countryId: 'IND', stateId: 'IN.GJ', useMaybe: true, type: 'state'},
  {zoneName: 'IN-GJ', type: 'fips', fips:['IND', 'IN32']},
  {zoneName: 'IN-HR', countryId: 'IND', stateId: 'IN.HR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-HP', countryId: 'IND', stateId: 'IN.HP', useMaybe: true, type: 'state'},
  {zoneName: 'IN-JK', countryId: 'IND', stateId: 'IN.JK', useMaybe: true, type: 'state'},
  {zoneName: 'IN-JH', countryId: 'IND', stateId: 'IN.JH', useMaybe: true, type: 'state'},
  {zoneName: 'IN-KA', countryId: 'IND', stateId: 'IN.KA', useMaybe: true, type: 'state'},
  {zoneName: 'IN-KL', countryId: 'IND', stateId: 'IN.KL', useMaybe: true, type: 'state'},
  {zoneName: 'IN-LD', countryId: 'IND', stateId: 'IN.LD', useMaybe: true, type: 'state'},
  {zoneName: 'IN-MP', countryId: 'IND', stateId: 'IN.MP', useMaybe: false, type: 'state'},
  {zoneName: 'IN-MH', countryId: 'IND', stateId: 'IN.MH', useMaybe: true, type: 'state'},
  {zoneName: 'IN-MN', countryId: 'IND', stateId: 'IN.MN', useMaybe: true, type: 'state'},
  {zoneName: 'IN-ML', countryId: 'IND', stateId: 'IN.ML', useMaybe: true, type: 'state'},
  {zoneName: 'IN-MZ', countryId: 'IND', stateId: 'IN.MZ', useMaybe: true, type: 'state'},
  {zoneName: 'IN-NL', countryId: 'IND', stateId: 'IN.NL', useMaybe: true, type: 'state'},
  {zoneName: 'IN-OR', countryId: 'IND', stateId: 'IN.OR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-PB', countryId: 'IND', stateId: 'IN.PB', useMaybe: true, type: 'state'},
  {zoneName: 'IN-PY', countryId: 'IND', stateId: 'IN.PY', useMaybe: true, type: 'state'},
  {zoneName: 'IN-RJ', countryId: 'IND', stateId: 'IN.RJ', useMaybe: true, type: 'state'},
  {zoneName: 'IN-SK', countryId: 'IND', stateId: 'IN.SK', useMaybe: true, type: 'state'},
  {zoneName: 'IN-TN', countryId: 'IND', stateId: 'IN.TN', useMaybe: true, type: 'state'},
  {zoneName: 'IN-TG', countryId: 'IND', stateId: 'IN.TG', useMaybe: true, type: 'state'},
  {zoneName: 'IN-TR', countryId: 'IND', stateId: 'IN.TR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-UT', countryId: 'IND', stateId: 'IN.UT', useMaybe: true, type: 'state'},
  {zoneName: 'IN-UP', countryId: 'IND', stateId: 'IN.UP', useMaybe: true, type: 'state'},
  {zoneName: 'IN-WB', countryId: 'IND', stateId: 'IN.WB', useMaybe: true, type: 'state'},
  {zoneName: 'IO', type: 'country', id: 'IOT'},
  {zoneName: 'IQ', type: 'subunits', subunits: ['IRR']},
  {zoneName: 'IQ-KUR', type: 'subunits', subunits: ['IRK']},
  {zoneName: 'IR', type: 'country', id: 'IRN'},
  {zoneName: 'IS', type: 'country', id: 'ISL'},
  {zoneName: 'IT', type: 'country', id: 'ITA'},
  {zoneName: 'JE', type: 'country', id: 'JEY'},
  {zoneName: 'JM', type: 'country', id: 'JAM'},
  {zoneName: 'JP', type: 'country', id: 'JPN'},
  {zoneName: 'JO', type: 'country', id: 'JOR'},
  {zoneName: 'KE', type: 'country', id: 'KEN'},
  {zoneName: 'KG', type: 'country', id: 'KGZ'},
  {zoneName: 'KH', type: 'country', id: 'KHM'},
  {zoneName: 'KI', type: 'country', id: 'KIR'},
  {zoneName: 'KM', type: 'country', id: 'COM'},
  {zoneName: 'KN', type: 'country', id: 'KNA'},
  {zoneName: 'KP', type: 'country', id: 'PRK'},
  {zoneName: 'KR', type: 'country', id: 'KOR'},
  {zoneName: 'KW', type: 'country', id: 'KWT'},
  {zoneName: 'KY', type: 'country', id: 'CYM'},
  {zoneName: 'KZ', type: 'countries', countries: ['KAZ', 'KAB']},
  {zoneName: 'LA', type: 'country', id: 'LAO'},
  {zoneName: 'LB', type: 'country', id: 'LBN'},
  {zoneName: 'LC', type: 'country', id: 'LCA'},
  {zoneName: 'LK', type: 'country', id: 'LKA'},
  {zoneName: 'LI', type: 'country', id: 'LIE'},
  {zoneName: 'LR', type: 'country', id: 'LBR'},
  {zoneName: 'LS', type: 'country', id: 'LSO'},
  {zoneName: 'LT', type: 'country', id: 'LTU'},
  {zoneName: 'LU', type: 'country', id: 'LUX'},
  {zoneName: 'LV', type: 'country', id: 'LVA'},
  {zoneName: 'LY', type: 'country', id: 'LBY'},
  {zoneName: 'MA', type: 'country', id: 'MAR'},
  {zoneName: 'ME', type: 'country', id: 'MNE'},
  {zoneName: 'MF', type: 'country', id: 'MAF'},
  {zoneName: 'MC', type: 'country', id: 'MCO'},
  {zoneName: 'MD', type: 'country', id: 'MDA'},
  {zoneName: 'MG', type: 'country', id: 'MDG'},
  {zoneName: 'MH', type: 'country', id: 'MHL'},
  {zoneName: 'MK', type: 'country', id: 'MKD'},
  {zoneName: 'ML', type: 'country', id: 'MLI'},
  {zoneName: 'MM', type: 'country', id: 'MMR'},
  {zoneName: 'MN', type: 'country', id: 'MNG'},
  {zoneName: 'MO', type: 'country', id: 'MAC'},
  {zoneName: 'MP', type: 'country', id: 'MNP'},
  {zoneName: 'MV', type: 'country', id: 'MDV'},
  {zoneName: 'MT', type: 'country', id: 'MLT'},
  {zoneName: 'MQ', type: 'country', id: 'MTQ'},
  {zoneName: 'MR', type: 'country', id: 'MRT'},
  {zoneName: 'MS', type: 'country', id: 'MSR'},
  {zoneName: 'MU', type: 'country', id: 'MUS'},
  {zoneName: 'MX', type: 'country', id: 'MEX'},
  // {zoneName: 'MY', type: 'country', id: 'MYS'},
  {zoneName: 'MW', type: 'country', id: 'MWI'},
  {zoneName: 'MY-EM', type: 'administrations', administrations: ['MYS-1186', 'MYS-1187']},
  {zoneName: 'MY-WM', type: 'administrations', administrations: [
      'MYS-1141', 'MYS-1140', 'MYS-1139', 'MYS-1137', 'MYS-1144', 'MYS-1149', 'MYS-1147', 'MYS-1148',
      'MYS-4831', 'MYS-4832', 'MYS-1146', 'MYS-1145', 'MYS-1143']},
  {zoneName: 'MZ', type: 'country', id: 'MOZ'},
  {zoneName: 'NA', type: 'country', id: 'NAM'},
  {zoneName: 'NC', type: 'country', id: 'NCL'},
  {zoneName: 'NE', type: 'country', id: 'NER'},
  {zoneName: 'NF', type: 'country', id: 'NFK'},
  {zoneName: 'NG', type: 'country', id: 'NGA'},
  {zoneName: 'NI', type: 'country', id: 'NIC'},
  {zoneName: 'NL', type: 'country', id: 'NLD'},
  // {zoneName: 'NO', type: 'country', id: 'NOR'},
  { zoneName: 'NO-NO1', type: 'subZone', id: 'NO-NO1' },
  { zoneName: 'NO-NO2', type: 'subZone', id: 'NO-NO2' },
  { zoneName: 'NO-NO3', type: 'subZone', id: 'NO-NO3' },
  { zoneName: 'NO-NO4', type: 'subZone', id: 'NO-NO4' },
  { zoneName: 'NO-NO5', type: 'subZone', id: 'NO-NO5' },
  {zoneName: 'NP', type: 'country', id: 'NPL'},
  // {zoneName: 'NZ', type: 'country', id: 'NZL'},
  {zoneName: 'NU', type: 'country', id: 'NIU'},
  {zoneName: 'NR', type: 'country', id: 'NRU'},
  {zoneName: 'NZ-NZA', type: 'subunits', subunits: ['NZA']},
  {zoneName: 'NZ-NZC', type: 'subunits', subunits: ['NZC']},
  {zoneName: 'NZ-NZN', type: 'subunits', subunits: ['NZN']},
  {zoneName: 'NZ-NZS', type: 'subunits', subunits: ['NZS']},
  {zoneName: 'OM', type: 'country', id: 'OMN'},
  {zoneName: 'PA', type: 'country', id: 'PAN'},
  {zoneName: 'PE', type: 'country', id: 'PER'},
  {zoneName: 'PF', type: 'country', id: 'PYF'},
  {zoneName: 'PG', type: 'country', id: 'PNG'},
  {zoneName: 'PM', type: 'country', id: 'SPM'},
  {zoneName: 'PK', type: 'country', id: 'PAK'},
  {zoneName: 'PH', type: 'country', id: 'PHL'},
  {zoneName: 'PL', type: 'country', id: 'POL'},
  {zoneName: 'PN', type: 'country', id: 'PCN'},
  {zoneName: 'PR', type: 'country', id: 'PRI'},
  {zoneName: 'PS', type: 'country', id: 'PSX'},
  {zoneName: 'PT', type: 'subunits', subunits: ['PRX']}, // Portugal Mainland,
  {zoneName: 'PT-MA', type: 'subunits', subunits: ['PMD']}, // Madeira Island,
  {zoneName: 'PT-AC', type: 'subunits', subunits: ['PAZ']}, // Azores Islands,
  {zoneName: 'PW', type: 'country', id: 'PLW'},
  {zoneName: 'PY', type: 'country', id: 'PRY'},
  {zoneName: 'QA', type: 'country', id: 'QAT'},
  {zoneName: 'RE', type: 'country', id: 'REU'},
  {zoneName: 'RO', type: 'country', id: 'ROU'},
  {zoneName: 'RS', type: 'countries', countries: ['SRB', 'KOS']},
  //{zoneName: 'RU', type: 'administrations', administrations: [
  //  'RUS-2280', 'RUS-2416', 'RUS-3200', 'RUS-2356', 'RUS-2359', 'RUS-2343', 'RUS-2377', 'RUS-2397',
  //  'RUS-2366', 'RUS-2391', 'RUS-2167', 'RUS-2603', 'RUS-2401', 'RUS-2360', 'RUS-2602', 'RUS-2385',
  //  'RUS-2365', 'RUS-2375', 'RUS-2358', 'RUS-2334', 'RUS-2403', 'RUS-2305', 'RUS-2368', 'RUS-2388',
  //  'RUS-2605', 'RUS-2357', 'RUS-2361', 'RUS-2342', 'RUS-2373', 'RUS-2371', 'RUS-2610', 'RUS-2379',
  //  'RUS-2400', 'RUS-2303', 'RUS-2390', 'RUS-2382', 'RUS-2304', 'RUS-2389', 'RUS-2336', 'RUS-2386',
  //  'RUS-2376', 'RUS-2394', 'RUS-2395', 'RUS-2363', 'RUS-2398', 'RUS-2380', 'RUS-2370', 'RUS-2417',
  //  'RUS-2372', 'RUS-2392', 'RUS-2378', 'RUS-2402', 'RUS-2333', 'RUS-2362', 'RUS-2399',
  //  'RUS-2387', 'RUS-2396', 'RUS-2337', 'RUS-2367', 'RUS-2606', 'RUS-2364', 'RUS-2306',
  //  'RUS-2374', 'RUS-2353', 'RUS-2355', 'RUS-2384', 'RUS-2393', 'RUS-2335', 'RUS-2369', 'RUS-2279']},
  {zoneName: 'RU-1', type: 'administrations', administrations: [
    'RUS-2280', 'RUS-2416', 'RUS-3200', 'RUS-2356', 'RUS-2359', 'RUS-2343', 'RUS-2377', 'RUS-2366',
    'RUS-2391', 'RUS-2360', 'RUS-2385', 'RUS-2365', 'RUS-2375', 'RUS-2358', 'RUS-2334', 'RUS-2305',
    'RUS-2368', 'RUS-2388', 'RUS-2357', 'RUS-2361', 'RUS-2342', 'RUS-2373', 'RUS-2371', 'RUS-2379',
    'RUS-2303', 'RUS-2390', 'RUS-2382', 'RUS-2304', 'RUS-2389', 'RUS-2336', 'RUS-2386', 'RUS-2376',
    'RUS-2394', 'RUS-2395', 'RUS-2363', 'RUS-2398', 'RUS-2380', 'RUS-2370', 'RUS-2417', 'RUS-2372',
    'RUS-2392', 'RUS-2378', 'RUS-2333', 'RUS-2362', 'RUS-2387', 'RUS-2396', 'RUS-2337', 'RUS-2367',
    'RUS-2364', 'RUS-2306', 'RUS-2374', 'RUS-2353', 'RUS-2355', 'RUS-2384', 'RUS-2393', 'RUS-2335',
    'RUS-2369', 'RUS-2279']},
  {zoneName: 'RU-2', type: 'administrations', administrations: [
    'RUS-2400', 'RUS-2606', 'RUS-2605', 'RUS-2610', 'RUS-2397', 'RUS-2403',
    'RUS-2399', 'RUS-2603', 'RUS-2167', 'RUS-2401', 'RUS-2602', 'RUS-2402']},
  {zoneName: 'RU-EU', type: 'administrations', administrations: ['RUS-2354', 'RUS-2383', 'RUS-2381']},
  {zoneName: 'RU-AS', type: 'administrations', administrations: ['RUS-2321', 'RUS-2609', 'RUS-2611', 'RUS-2612', 'RUS-2613', 'RUS-2614', 'RUS-2615', 'RUS-2616', 'RUS-3468']},
  {zoneName: 'RU-KGD', type: 'administrations', administrations: ['RUS-2324']},
  {zoneName: 'RW', type: 'country', id: 'RWA'},
  {zoneName: 'SA', type: 'country', id: 'SAU'},
  {zoneName: 'SB', type: 'country', id: 'SLB'},
  {zoneName: 'SC', type: 'country', id: 'SYC'},
  {zoneName: 'SD', type: 'country', id: 'SDN'},
  {zoneName: 'SE', type: 'country', id: 'SWE'},
  // { zoneName: 'SE-SE1', type: 'subZone', id: 'SE-SE1' },
  // { zoneName: 'SE-SE2', type: 'subZone', id: 'SE-SE2' },
  // { zoneName: 'SE-SE3', type: 'subZone', id: 'SE-SE3' },
  // { zoneName: 'SE-SE4', type: 'subZone', id: 'SE-SE4' },
  {zoneName: 'SG', type: 'country', id: 'SGP'},
  {zoneName: 'SH', type: 'country', id: 'SHN'},
  {zoneName: 'SI', type: 'country', id: 'SVN'},
  {zoneName: 'SJ', type: 'country', id: 'SJM'},
  {zoneName: 'SK', type: 'country', id: 'SVK'},
  {zoneName: 'SL', type: 'country', id: 'SLE'},
  {zoneName: 'SM', type: 'country', id: 'SMR'},
  {zoneName: 'SN', type: 'country', id: 'SEN'},
  {zoneName: 'SO', type: 'countries', countries: ['SOL', 'SOM']},
  {zoneName: 'SR', type: 'country', id: 'SUR'},
  {zoneName: 'SS', type: 'country', id: 'SSD'},
  {zoneName: 'ST', type: 'country', id: 'STP'},
  {zoneName: 'SV', type: 'country', id: 'SLV'},
  {zoneName: 'SY', type: 'country', id: 'SYR'},
  {zoneName: 'SZ', type: 'country', id: 'SWZ'},
  {zoneName: 'TC', type: 'country', id: 'TCA'},
  {zoneName: 'TD', type: 'country', id: 'TCD'},
  {zoneName: 'TF', type: 'country', id: 'ATF'},
  {zoneName: 'TG', type: 'country', id: 'TGO'},
  {zoneName: 'TH', type: 'country', id: 'THA'},
  {zoneName: 'TJ', type: 'country', id: 'TJK'},
  {zoneName: 'TK', type: 'country', id: 'TKL'},
  {zoneName: 'TL', type: 'country', id: 'TLS'},
  {zoneName: 'TO', type: 'country', id: 'TON'},
  {zoneName: 'TM', type: 'country', id: 'TKM'},
  {zoneName: 'TN', type: 'country', id: 'TUN'},
  {zoneName: 'TR', type: 'country', id: 'TUR'},
  {zoneName: 'TT', type: 'country', id: 'TTO'},
  {zoneName: 'TV', type: 'country', id: 'TUV'},
  {zoneName: 'TW', type: 'country', id: 'TWN'},
  {zoneName: 'TZ', type: 'country', id: 'TZA'},
  {zoneName: 'UA', type: 'country', id: 'UKR'},
  // Crimea
  {zoneName: 'UA-CR', type: 'administrations', administrations: ['RUS-283', 'RUS-5482']},
  {zoneName: 'UG', type: 'country', id: 'UGA'},
  {zoneName: 'UM', type: 'country', id: 'UMI'},
  {zoneName: 'US-AK', countryId: 'USA', stateId: 'US.AK', type: 'state'},
  // {zoneName: 'US', type: 'subunits', subunits: ['USB']}, // Continental,
  // {zoneName: 'US-AK', type: 'subunits', subunits: ['USK']}, // Alaska,
  // {zoneName: 'US-HI', type: 'subunits', subunits: ['USH']}, // Hawaii,
  {zoneName: 'US-AL', countryId: 'USA', stateId: 'US.AL', type: 'state'},
  // {zoneName: 'US-AZ', countryId: 'USA', stateId: 'US.AZ', type: 'state'},
  // {zoneName: 'US-AR', countryId: 'USA', stateId: 'US.AR', type: 'state'},
  {zoneName: 'US-CA', countryId: 'USA', stateId: 'US.CA', type: 'state'},
  {zoneName: 'US-CO', countryId: 'USA', stateId: 'US.CO', type: 'state'},
  // {zoneName: 'US-CT', countryId: 'USA', stateId: 'US.CT', type: 'state'},
  {zoneName: 'US-DC', countryId: 'USA', stateId: 'US.DC', type: 'state'},
  // {zoneName: 'US-DE', countryId: 'USA', stateId: 'US.DE', type: 'state'},
  {zoneName: 'US-FL', countryId: 'USA', stateId: 'US.FL', type: 'state'},
  {zoneName: 'US-GA', countryId: 'USA', stateId: 'US.GA', type: 'state'},
  {zoneName: 'US-HI', countryId: 'USA', stateId: 'US.HI', type: 'state'},
  // {zoneName: 'US-IA', countryId: 'USA', stateId: 'US.IA', type: 'state'},
  // {zoneName: 'US-ID', countryId: 'USA', stateId: 'US.ID', type: 'state'},
  {zoneName: 'US-IPC', type: 'states', countryId: 'USA', states: ['US.ID']},
  // {zoneName: 'US-IL', countryId: 'USA', stateId: 'US.IL', type: 'state'},
  // {zoneName: 'US-IN', countryId: 'USA', stateId: 'US.IN', type: 'state'},
  // {zoneName: 'US-KS', countryId: 'USA', stateId: 'US.KS', type: 'state'},
  // {zoneName: 'US-KY', countryId: 'USA', stateId: 'US.KY', type: 'state'},
  // {zoneName: 'US-LA', countryId: 'USA', stateId: 'US.LA', type: 'state'},
  // {zoneName: 'US-MA', countryId: 'USA', stateId: 'US.MA', type: 'state'},
  // {zoneName: 'US-MD', countryId: 'USA', stateId: 'US.MD', type: 'state'},
  // {zoneName: 'US-ME', countryId: 'USA', stateId: 'US.ME', type: 'state'},
  // {zoneName: 'US-MI', countryId: 'USA', stateId: 'US.MI', type: 'state'},
  {zoneName: 'US-MISO', type: 'states', countryId: 'USA', states: [
    'US.AR', 'US.IA', 'US.IL', 'US.IN', 'US.LA', 'US.MI', 'US.MN', 'US.MO', 'US.WI']},
  // {zoneName: 'US-MN', countryId: 'USA', stateId: 'US.MN', type: 'state'},
  // {zoneName: 'US-MO', countryId: 'USA', stateId: 'US.MO', type: 'state'},
  {zoneName: 'US-MS', countryId: 'USA', stateId: 'US.MS', type: 'state'},
  {zoneName: 'US-MT', countryId: 'USA', stateId: 'US.MT', type: 'state'},
  {zoneName: 'US-NC', countryId: 'USA', stateId: 'US.NC', type: 'state'},
  // {zoneName: 'US-ND', countryId: 'USA', stateId: 'US.ND', type: 'state'},
  // {zoneName: 'US-NE', countryId: 'USA', stateId: 'US.NE', type: 'state'},
  {zoneName: 'US-NEISO', type: 'states', countryId: 'USA', states: [
    'US.CT', 'US.MA', 'US.ME', 'US.NH', 'US.RI', 'US.VT']},
  // {zoneName: 'US-NH', countryId: 'USA', stateId: 'US.NH', type: 'state'},
  // {zoneName: 'US-NJ', countryId: 'USA', stateId: 'US.NJ', type: 'state'},
  // {zoneName: 'US-NM', countryId: 'USA', stateId: 'US.NM', type: 'state'},
  {zoneName: 'US-NV', countryId: 'USA', stateId: 'US.NV', type: 'state'},
  {zoneName: 'US-NY', countryId: 'USA', stateId: 'US.NY', type: 'state'},
  // {zoneName: 'US-OH', countryId: 'USA', stateId: 'US.OH', type: 'state'},
  // {zoneName: 'US-OK', countryId: 'USA', stateId: 'US.OK', type: 'state'},
  {zoneName: 'US-OR', countryId: 'USA', stateId: 'US.OR', type: 'state'},
  // {zoneName: 'US-PA', countryId: 'USA', stateId: 'US.PA', type: 'state'},
  {zoneName: 'US-PJM', type: 'states', countryId: 'USA', states: [
    'US.PA', 'US.NJ', 'US.MD', 'US.DE', 'US.VA', 'US.WV', 'US.OH', 'US.KY']},
  // {zoneName: 'US-RI', countryId: 'USA', stateId: 'US.RI', type: 'state'},
  {zoneName: 'US-SC', countryId: 'USA', stateId: 'US.SC', type: 'state'},
  // {zoneName: 'US-SD', countryId: 'USA', stateId: 'US.SD', type: 'state'},
  {zoneName: 'US-SPP', type: 'states', countryId: 'USA', states: [
    'US.KS', 'US.NE','US.OK', 'US.ND', 'US.SD']},
  {zoneName: 'US-SVERI', type: 'states', countryId: 'USA', states: ['US.AZ', 'US.NM']},
  {zoneName: 'US-TN', countryId: 'USA', stateId: 'US.TN', type: 'state'},
  {zoneName: 'US-TX', countryId: 'USA', stateId: 'US.TX', type: 'state'},
  {zoneName: 'US-UT', countryId: 'USA', stateId: 'US.UT', type: 'state'},
  // {zoneName: 'US-VA', countryId: 'USA', stateId: 'US.VA', type: 'state'},
  // {zoneName: 'US-VT', countryId: 'USA', stateId: 'US.VT', type: 'state'},
  // {zoneName: 'US-WA', countryId: 'USA', stateId: 'US.WA', type: 'state'},
  {zoneName: 'US-BPA', countryId: 'USA', stateId: 'US.WA', type: 'state'},
  // {zoneName: 'US-WI', countryId: 'USA', stateId: 'US.WI', type: 'state'},
  // {zoneName: 'US-WV', countryId: 'USA', stateId: 'US.WV', type: 'state'},
  {zoneName: 'US-WY', countryId: 'USA', stateId: 'US.WY', type: 'state'},
  {zoneName: 'VC', type: 'country', id: 'VCT'},
  {zoneName: 'UY', type: 'country', id: 'URY'},
  {zoneName: 'UZ', type: 'country', id: 'UZB'},
  {zoneName: 'VA', type: 'country', id: 'VAT'},
  {zoneName: 'VE', type: 'country', id: 'VEN'},
  {zoneName: 'VG', type: 'country', id: 'VGB'},
  {zoneName: 'VI', type: 'country', id: 'VIR'},
  {zoneName: 'VN', type: 'country', id: 'VNM'},
  {zoneName: 'VU', type: 'country', id: 'VUT'},
  {zoneName: 'WF', type: 'country', id: 'WLF'},
  {zoneName: 'WS', type: 'country', id: 'WSM'},
  {zoneName: 'YE', type: 'country', id: 'YEM'},
  {zoneName: 'YT', type: 'country', id: 'MYT'},
  {zoneName: 'ZA', type: 'country', id: 'ZAF'},
  {zoneName: 'ZM', type: 'country', id: 'ZMB'},
  {zoneName: 'ZW', type: 'country', id: 'ZWE'},
];

const getDataForZone = (zone, mergeStates) => {
  /* for a specifi zone, defined by an Object having at least `zoneName` and
   * `type` as properties, call the corresponding function to get the data */
  if (zone.type === 'country'){
    return getCountry(zone.id)
  }
  else if (zone.type === 'states'){
    if (mergeStates){
      return getStates(zone.countryId, zone.states);
    }
    else{
      return ['multipleStates', zone.states.map(state => getState(zone.countryId, state))];
    }
  }
  else if (zone.type === 'state'){
    return getState(zone.countryId, zone.stateId, zone.useMaybe);
  }
  else if (zone.type === 'administrations'){
    return getStatesByAdm1(zone.administrations);
  }
  else if (zone.type === 'subunits'){
    return getSubUnits(zone.subunits);
  }
  else if (zone.type === 'countries'){
    return getCountries(zone.countries);
  }
  else if (zone.type === 'fips'){
    return getStateByFips(zone.fips[0], zone.fips[1]);
  }
  else if (zone.type === 'subZone') {
    return getByPropertiesId(zone.id);
  }
  else{
    console.warn('unknown type for zone ', zone);
  }
};

const toListOfFeatures = (zones) => {
  /* transform a list of (zoneName, properties) to the right geoJSON format */
  return zones.filter(d => d[1] != null).map((d) => {
    const [k, v] = d;
    let zoneName = k;
    v.id = zoneName;
    v.properties = {
      zoneName: zoneName,
    };
    return v;
  });
};

//Adds the zones from topo2 to topo1
function mergeTopoJsonSingleZone(topo1, topo2) {
  let srcArcsLength = topo1.arcs.length;
  // Copy Zones from topo2 to topo1
  Object.keys(topo2.objects).forEach(zoneName=>{
    topo1.objects[zoneName]=topo2.objects[zoneName];
    // Relocate arc into zone by adding srcArcsLength
    topo1.objects[zoneName].arcs.forEach(arcList1=>{
      arcList1.forEach(arcList2=>{
        for(i=0; i<arcList2.length; i++) {
          arcList2[i]+=srcArcsLength;
        }
      });
    });
  });

  // Add arcs from topo2
  topo2.arcs.forEach(arc=> {
    topo1.arcs.push(arc);
  });
}

// create zones from definitions, avoid zones having moreDetails==true
let zones = {};
zoneDefinitions.forEach(zone => {
  if (zone.zoneName in zones)
    throw ('Warning: ' + zone.zoneName + ' has duplicated entries. Each zoneName must be present ' +
      'only once in zoneDefinitions');
  // Avoid zone with moreDetails
  if ( !('moreDetails' in zone) || !zone.moreDetails) {
  	zones[zone.zoneName] = getDataForZone(zone, true);
  }
});

// create zonesMoreDetails by getting zone having moreDetails===true
let zonesMoreDetails = {};
zoneDefinitions.forEach(zone => {
  // Take only zones having modeDetails
  if (('moreDetails' in zone) && zone.moreDetails) {
	if (zone.zoneName in zonesMoreDetails || zone.zoneName in zones)
      throw ('Warning: ' + zone.zoneName + ' has duplicated entries. Each zoneName must be present ' +
        'only once in zoneDefinitions');
  zonesMoreDetails[zone.zoneName] = getDataForZone(zone, true);
  }
});

// We do not want to merge states
// related to PR #455 in the backend
let zoneFeatures = zoneDefinitions.map(
  zone => [zone.zoneName, getDataForZone(zone, false)]);
// where there are multiple states, we need to inline the values
let zoneFeaturesInline = [];
zoneFeatures.forEach((data) => {
  let [name, zoneFeature] = data;
  if (Array.isArray(zoneFeature) && zoneFeature[0] === 'multipleStates'){
    zoneFeature[1].forEach(z => {zoneFeaturesInline.push([name, z])});
  }
  else{
    zoneFeaturesInline.push(data);
  }
});
zoneFeatures = toListOfFeatures(zoneFeaturesInline);

// Write unsimplified list of geojson, without state merges
fs.writeFileSync('build/zonegeometries.json', zoneFeatures.map(JSON.stringify).join('\n'));

// Simplify all countries
const topojson = require('topojson');
let topo = topojson.topology(zones);
topo = topojson.presimplify(topo);
topo = topojson.simplify(topo, 0.01);

// Simplify to 0.001 zonesMoreDetails zones
topoMoreDetails = topojson.topology(zonesMoreDetails);
topoMoreDetails = topojson.presimplify(topoMoreDetails);
topoMoreDetails = topojson.simplify(topoMoreDetails, 0.001);
// Merge topoMoreDetails into topo
mergeTopoJsonSingleZone(topo, topoMoreDetails);

topo = topojson.filter(topo, topojson.filterWeight(topo, 0.01));
topo = topojson.quantize(topo, 1e5);
fs.writeFileSync('src/world.json', JSON.stringify(topo));
