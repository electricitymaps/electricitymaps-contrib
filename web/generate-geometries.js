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
const thirpartyGeos = readNDJSON('./build/tmp_thirdparty.json');

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
  {zoneName:'XX', type:'country', id:'CYN'},

  // List of all zones
  {zoneName:'AF', type:'country', id:'AFG'},
  {zoneName:'AX', type:'country', id:'ALA'},
  {zoneName:'AL', type:'country', id:'ALB'},
  {zoneName:'DZ', type:'country', id:'DZA'},
  {zoneName:'AS', type:'country', id:'ASM'},
  {zoneName:'AD', type:'country', id:'AND'},
  {zoneName:'AO', type:'country', id:'AGO'},
  {zoneName:'AI', type:'country', id:'AIA'},
  // {zoneName:'AQ', type:'country', id:'AT},
  {zoneName:'AG', type:'country', id:'ATG'},
  {zoneName:'AR', type:'country', id:'ARG'},
  {zoneName:'AM', type:'country', id:'ARM'},
  {zoneName:'AW', type:'country', id:'ABW'},
  // {zoneName:'AU', type:'country', id:'AUS'},
  // {zoneName: 'AUS-ACT', countryId:'AUS', stateId: 'AU.AC', type: 'state'},
  {zoneName: 'AUS-NSW', type: 'states', countryId:'AUS', states: ['AU.NS', 'AU.AC']},
  {zoneName: 'AUS-NT', countryId:'AUS', stateId: 'AU.NT', type: 'state'},
  {zoneName: 'AUS-QLD', countryId:'AUS', stateId: 'AU.QL', type: 'state'},
  {zoneName: 'AUS-SA', countryId:'AUS', stateId: 'AU.SA', type: 'state'},
  {zoneName: 'AUS-TAS', countryId:'AUS', stateId: 'AU.TS', type: 'state'},
  {zoneName: 'AUS-VIC', countryId:'AUS', stateId: 'AU.VI', type: 'state'},
  {zoneName: 'AUS-WA', countryId:'AUS', stateId: 'AU.WA', type: 'state'},
  {zoneName:'AT', type:'country', id:'AUT'},
  {zoneName:'AZ', type:'country', id:'AZE'},
  {zoneName:'BS', type:'country', id:'BHS'},
  {zoneName:'BH', type:'country', id:'BHR'},
  {zoneName:'BD', type:'country', id:'BGD'},
  {zoneName:'BB', type:'country', id:'BRB'},
  {zoneName:'BY', type:'country', id:'BLR'},
  {zoneName:'BE', type:'country', id:'BEL'},
  {zoneName:'BZ', type:'country', id:'BLZ'},
  {zoneName:'BJ', type:'country', id:'BEN'},
  {zoneName:'BM', type:'country', id:'BMU'},
  {zoneName:'BT', type:'country', id:'BTN'},
  {zoneName:'BO', type:'country', id:'BOL'},
  //{zoneName:'BA', type:'country', id:'BIH'},
  {zoneName: 'BA', type: 'administrations', administrations: [
    'BIH-4801', 'BIH-4802', 'BIH-2225', 'BIH-2224', 'BIH-2226', 'BIH-2227', 'BIH-2228', 'BIH-4807',
      'BIH-4808', 'BIH-4805', 'BIH-4806', 'BIH-2890', 'BIH-2891', 'BIH-2889', 'BIH-2887',
      'BIH-4804', 'BIH-3153', 'BIH-4803']},
  {zoneName:'BW', type:'country', id:'BWA'},
  {zoneName:'BV', type:'country', id:'BVT'},
  //{zoneName:'BR', type:'country', id:'BRA'},
  {zoneName: 'BR-N', type: 'states', countryId:'BRA', states: ['BR.AM', 'BR.PA', 'BR.TO', 'BR.RR', 'BR.AP']},
  {zoneName: 'BR-NE', type: 'states', countryId:'BRA', states: ['BR.PE', 'BR.MA', 'BR.CE', 'BR.PI', 'BR.AL', 'BR.BA', 'BR.PB', 'BR.RN', 'BR.SE']},
  {zoneName: 'BR-CS', type: 'states', countryId:'BRA', states: ['BR.', 'BR.AC', 'BR.GO', 'BR.SP', 'BR.DF', 'BR.MS', 'BR.MG', 'BR.MT', 'BR.ES', 'BR.RJ', 'BR.RO']},
  {zoneName: 'BR-S', type: 'states', countryId:'BRA', states: ['BR.RS', 'BR.SC', 'BR.PR']},
  {zoneName:'VG', type:'country', id:'VGB'},
  {zoneName:'IO', type:'country', id:'IOT'},
  {zoneName:'BN', type:'country', id:'BRN'},
  {zoneName:'BG', type:'country', id:'BGR'},
  {zoneName:'BF', type:'country', id:'BFA'},
  {zoneName:'BI', type:'country', id:'BDI'},
  {zoneName:'KH', type:'country', id:'KHM'},
  {zoneName:'CM', type:'country', id:'CMR'},
  // {zoneName:'CA', type:'country', id:'CAN'},
  {zoneName: 'CA-AB', countryId:'CAN', stateId: 'CA.AB', type: 'state'},
  {zoneName: 'CA-BC', countryId:'CAN', stateId: 'CA.BC', type: 'state'},
  {zoneName: 'CA-MB', countryId:'CAN', stateId: 'CA.MB', type: 'state'},
  {zoneName: 'CA-NB', countryId:'CAN', stateId: 'CA.NB', type: 'state'},
  {zoneName: 'CA-NL', countryId:'CAN', stateId: 'CA.NF', type: 'state'}, // since 2002, ISO 3166-2 is "CA-NL", code_hasc in naturalearth is "CA.NF"
  {zoneName: 'CA-NS', countryId:'CAN', stateId: 'CA.NS', type: 'state'},
  {zoneName: 'CA-ON', countryId:'CAN', stateId: 'CA.ON', type: 'state'},
  {zoneName: 'CA-PE', countryId:'CAN', stateId: 'CA.PE', type: 'state'},
  {zoneName: 'CA-QC', countryId:'CAN', stateId: 'CA.QC', type: 'state'},
  {zoneName: 'CA-SK', countryId:'CAN', stateId: 'CA.SK', type: 'state'},
  {zoneName: 'CA-NT', countryId:'CAN', stateId: 'CA.NT', type: 'state'},
  {zoneName: 'CA-NU', countryId:'CAN', stateId: 'CA.NU', type: 'state'},
  {zoneName: 'CA-YT', countryId:'CAN', stateId: 'CA.YT', type: 'state'},
  {zoneName:'CV', type:'country', id:'CPV'},
  {zoneName:'KY', type:'country', id:'CYM'},
  {zoneName:'CF', type:'country', id:'CAF'},
  {zoneName:'TD', type:'country', id:'TCD'},
  //{zoneName:'CL', type:'country', id:'CHL'},
  {zoneName: 'CL-SING', type: 'states', countryId:'CHL', states: ['CL.AP', 'CL.TA', 'CL.AN']},
  {zoneName: 'CL-SIC', type: 'administrations', administrations: ['CHL-2696', 'CHL-2697', 'CHL-2699', 'CHL-2698', 'CHL-2703', 'CHL-2705', 'CHL-2702', 'CHL-2700', 'CHL-2701', 'CHL-2704']},
  {zoneName: 'CL-SEM', countryId:'CHL', stateId: 'CL.MA', type: 'state'},
  {zoneName: 'CL-SEA', countryId:'CHL', stateId: 'CL.AI', type: 'state'},
  {zoneName:'CN', type:'country', id:'CHN'},
  {zoneName:'HK', type:'country', id:'HKG'},
  {zoneName:'MO', type:'country', id:'MAC'},
  {zoneName:'CX', type:'country', id:'CXR'},
  {zoneName:'CC', type:'country', id:'CCK'},
  {zoneName:'CO', type:'country', id:'COL'},
  {zoneName:'KM', type:'country', id:'COM'},
  {zoneName:'CG', type:'country', id:'COG'},
  {zoneName:'CD', type:'country', id:'COD'},
  {zoneName:'CK', type:'country', id:'COK'},
  {zoneName:'CR', type:'country', id:'CRI'},
  {zoneName:'CI', type:'country', id:'CIV'},
  {zoneName:'HR', type:'country', id:'HRV'},
  {zoneName:'CU', type:'country', id:'CUB'},
  {zoneName:'CY', type:'country', id:'CYP'},
  {zoneName:'CZ', type:'country', id:'CZE'},
  {zoneName: 'DK', type: 'subunits', subunits: ['DNK']},
  {zoneName: 'DK-BHM', type: 'subunits', subunits: ['DNB']},
  {zoneName:'DJ', type:'country', id:'DJI'},
  {zoneName:'DM', type:'country', id:'DMA'},
  {zoneName:'DO', type:'country', id:'DOM'},
  {zoneName:'EC', type:'country', id:'ECU'},
  {zoneName:'EG', type:'country', id:'EGY'},
  {zoneName:'SV', type:'country', id:'SLV'},
  {zoneName:'GQ', type:'country', id:'GNQ'},
  {zoneName:'ER', type:'country', id:'ERI'},
  {zoneName:'EE', type:'country', id:'EST'},
  {zoneName:'ET', type:'country', id:'ETH'},
  {zoneName:'FK', type:'country', id:'FLK'},
  {zoneName:'FO', type:'country', id:'FRO'},
  {zoneName:'FJ', type:'country', id:'FJI'},
  {zoneName:'FI', type:'country', id:'FIN'},
  // {zoneName:'FR', type:'country', id:'FRA'},
  {zoneName: 'FR', type: 'subunits', subunits: ['FXX']},
  {zoneName: 'FR-COR', type: 'subunits', subunits: ['FXC']},
  {zoneName:'GF', type:'country', id:'GUF'},
  {zoneName:'PF', type:'country', id:'PYF'},
  {zoneName:'TF', type:'country', id:'ATF'},
  {zoneName:'GA', type:'country', id:'GAB'},
  {zoneName:'GM', type:'country', id:'GMB'},
  {zoneName:'GE', type:'country', id:'GEO'},
  {zoneName:'DE', type:'country', id:'DEU'},
  {zoneName:'GH', type:'country', id:'GHA'},
  {zoneName:'GI', type:'country', id:'GIB'},
  {zoneName:'GR', type:'country', id:'GRC'},
  {zoneName:'GL', type:'country', id:'GRL'},
  {zoneName:'GD', type:'country', id:'GRD'},
  {zoneName:'GP', type:'country', id:'GLP'},
  {zoneName:'GU', type:'country', id:'GUM'},
  {zoneName:'GT', type:'country', id:'GTM'},
  {zoneName:'GG', type:'country', id:'GGY'},
  {zoneName:'GN', type:'country', id:'GIN'},
  {zoneName:'GW', type:'country', id:'GNB'},
  {zoneName:'GY', type:'country', id:'GUY'},
  {zoneName:'HT', type:'country', id:'HTI'},
  {zoneName:'HM', type:'country', id:'HMD'},
  {zoneName:'VA', type:'country', id:'VAT'},
  {zoneName:'HN', type:'country', id:'HND'},
  {zoneName:'HU', type:'country', id:'HUN'},
  {zoneName:'IS', type:'country', id:'ISL'},
  // TODO: Use iso_3166_2 field instead
  {zoneName: 'IN-AN', countryId:'IND', stateId: 'IN.AN', useMaybe: true, type: 'state'},
  {zoneName: 'IN-AP', countryId:'IND', stateId: 'IN.AD', useMaybe: true, type: 'state'},
  {zoneName: 'IN-AR', countryId:'IND', stateId: 'IN.AR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-AS', countryId:'IND', stateId: 'IN.AS', useMaybe: true, type: 'state'},
  {zoneName: 'IN-BR', countryId:'IND', stateId: 'IN.BR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-CT', countryId:'IND', stateId: 'IN.CT', useMaybe: true, type: 'state'},
  {zoneName: 'IN-CH', countryId:'IND', stateId: 'IN.CH', useMaybe: true, type: 'state'},
  {zoneName: 'IN-DD', countryId:'IND', stateId: 'IN.DD', useMaybe: true, type: 'state'},
  {zoneName: 'IN-DN', countryId:'IND', stateId: 'IN.DN', useMaybe: true, type: 'state'},
  {zoneName: 'IN-DL', countryId:'IND', stateId: 'IN.DL', useMaybe: true, type: 'state'},
  {zoneName: 'IN-GA', countryId:'IND', stateId: 'IN.GA', useMaybe: true, type: 'state'},
  // For some reason IN.GJ is not a code_hasc in database, use FIPS code instead.
  // {zoneName: 'IN-GJ', countryId:'IND', stateId: 'IN.GJ', useMaybe: true, type: 'state'},
  {zoneName: 'IN-GJ', type: 'fips', fips:['IND', 'IN32']},
  {zoneName: 'IN-HR', countryId:'IND', stateId: 'IN.HR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-HP', countryId:'IND', stateId: 'IN.HP', useMaybe: true, type: 'state'},
  {zoneName: 'IN-JK', countryId:'IND', stateId: 'IN.JK', useMaybe: true, type: 'state'},
  {zoneName: 'IN-JH', countryId:'IND', stateId: 'IN.JH', useMaybe: true, type: 'state'},
  {zoneName: 'IN-KA', countryId:'IND', stateId: 'IN.KA', useMaybe: true, type: 'state'},
  {zoneName: 'IN-KL', countryId:'IND', stateId: 'IN.KL', useMaybe: true, type: 'state'},
  {zoneName: 'IN-LD', countryId:'IND', stateId: 'IN.LD', useMaybe: true, type: 'state'},
  {zoneName: 'IN-MP', countryId:'IND', stateId: 'IN.MP', useMaybe: true, type: 'state'},
  {zoneName: 'IN-MH', countryId:'IND', stateId: 'IN.MH', useMaybe: true, type: 'state'},
  {zoneName: 'IN-MN', countryId:'IND', stateId: 'IN.MN', useMaybe: true, type: 'state'},
  {zoneName: 'IN-ML', countryId:'IND', stateId: 'IN.ML', useMaybe: true, type: 'state'},
  {zoneName: 'IN-MZ', countryId:'IND', stateId: 'IN.MZ', useMaybe: true, type: 'state'},
  {zoneName: 'IN-NL', countryId:'IND', stateId: 'IN.NL', useMaybe: true, type: 'state'},
  {zoneName: 'IN-OR', countryId:'IND', stateId: 'IN.OR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-PB', countryId:'IND', stateId: 'IN.PB', useMaybe: true, type: 'state'},
  {zoneName: 'IN-PY', countryId:'IND', stateId: 'IN.PY', useMaybe: true, type: 'state'},
  {zoneName: 'IN-RJ', countryId:'IND', stateId: 'IN.RJ', useMaybe: true, type: 'state'},
  {zoneName: 'IN-SK', countryId:'IND', stateId: 'IN.SK', useMaybe: true, type: 'state'},
  {zoneName: 'IN-TN', countryId:'IND', stateId: 'IN.TN', useMaybe: true, type: 'state'},
  {zoneName: 'IN-TG', countryId:'IND', stateId: 'IN.TG', useMaybe: true, type: 'state'},
  {zoneName: 'IN-TR', countryId:'IND', stateId: 'IN.TR', useMaybe: true, type: 'state'},
  {zoneName: 'IN-UT', countryId:'IND', stateId: 'IN.UT', useMaybe: true, type: 'state'},
  {zoneName: 'IN-UP', countryId:'IND', stateId: 'IN.UP', useMaybe: true, type: 'state'},
  {zoneName: 'IN-WB', countryId:'IND', stateId: 'IN.WB', useMaybe: true, type: 'state'},
  {zoneName:'ID', type:'country', id:'IDN'},
  {zoneName:'IR', type:'country', id:'IRN'},
  {zoneName:'IQ', type:'country', id:'IRQ'},
  {zoneName:'IE', type:'country', id:'IRL'},
  {zoneName:'IM', type:'country', id:'IMN'},
  {zoneName:'IL', type:'country', id:'ISR'},
  {zoneName:'IT', type:'country', id:'ITA'},
  {zoneName:'JM', type:'country', id:'JAM'},
  {zoneName:'JP', type:'country', id:'JPN'},
  {zoneName:'JE', type:'country', id:'JEY'},
  {zoneName:'JO', type:'country', id:'JOR'},
  {zoneName: 'KZ', type: 'countries', countries: ['KAZ', 'KAB']},
  {zoneName:'KE', type:'country', id:'KEN'},
  {zoneName:'KI', type:'country', id:'KIR'},
  {zoneName:'KP', type:'country', id:'PRK'},
  {zoneName:'KR', type:'country', id:'KOR'},
  {zoneName:'KW', type:'country', id:'KWT'},
  {zoneName:'KG', type:'country', id:'KGZ'},
  {zoneName:'LA', type:'country', id:'LAO'},
  {zoneName:'LV', type:'country', id:'LVA'},
  {zoneName:'LB', type:'country', id:'LBN'},
  {zoneName:'LS', type:'country', id:'LSO'},
  {zoneName:'LR', type:'country', id:'LBR'},
  {zoneName:'LY', type:'country', id:'LBY'},
  {zoneName:'LI', type:'country', id:'LIE'},
  {zoneName:'LT', type:'country', id:'LTU'},
  {zoneName:'LU', type:'country', id:'LUX'},
  {zoneName:'MK', type:'country', id:'MKD'},
  {zoneName:'MG', type:'country', id:'MDG'},
  {zoneName:'MW', type:'country', id:'MWI'},
  // {zoneName:'MY', type:'country', id:'MYS'},
  {zoneName: 'MY-EM', type: 'administrations', administrations: ['MYS-1186', 'MYS-1187']},
  {zoneName: 'MY-WM', type: 'administrations', administrations: [
    'MYS-1141', 'MYS-1140', 'MYS-1139', 'MYS-1137', 'MYS-1144', 'MYS-1149', 'MYS-1147', 'MYS-1148',
      'MYS-4831', 'MYS-4832', 'MYS-1146', 'MYS-1145', 'MYS-1143']},
  {zoneName:'MV', type:'country', id:'MDV'},
  {zoneName:'ML', type:'country', id:'MLI'},
  {zoneName:'MT', type:'country', id:'MLT'},
  {zoneName:'MH', type:'country', id:'MHL'},
  {zoneName:'MQ', type:'country', id:'MTQ'},
  {zoneName:'MR', type:'country', id:'MRT'},
  {zoneName:'MU', type:'country', id:'MUS'},
  {zoneName:'YT', type:'country', id:'MYT'},
  {zoneName:'MX', type:'country', id:'MEX'},
  {zoneName:'FM', type:'country', id:'FSM'},
  {zoneName:'MD', type:'country', id:'MDA'},
  {zoneName:'MC', type:'country', id:'MCO'},
  {zoneName:'MN', type:'country', id:'MNG'},
  {zoneName:'ME', type:'country', id:'MNE'},
  {zoneName:'MS', type:'country', id:'MSR'},
  {zoneName:'MA', type:'country', id:'MAR'},
  {zoneName:'MZ', type:'country', id:'MOZ'},
  {zoneName:'MM', type:'country', id:'MMR'},
  {zoneName:'NA', type:'country', id:'NAM'},
  {zoneName:'NR', type:'country', id:'NRU'},
  {zoneName:'NP', type:'country', id:'NPL'},
  {zoneName:'NL', type:'country', id:'NLD'},
  {zoneName:'AN', type:'country', id:'ANT'},
  {zoneName:'NC', type:'country', id:'NCL'},
  // {zoneName:'NZ', type:'country', id:'NZL'},
  {zoneName: 'NZ-NZA', type: 'subunits', subunits: ['NZA']},
  {zoneName: 'NZ-NZC', type: 'subunits', subunits: ['NZC']},
  {zoneName: 'NZ-NZN', type: 'subunits', subunits: ['NZN']},
  {zoneName: 'NZ-NZS', type: 'subunits', subunits: ['NZS']},
  {zoneName:'NI', type:'country', id:'NIC'},
  {zoneName:'NE', type:'country', id:'NER'},
  {zoneName:'NG', type:'country', id:'NGA'},
  {zoneName:'NU', type:'country', id:'NIU'},
  {zoneName:'NF', type:'country', id:'NFK'},
  {zoneName:'MP', type:'country', id:'MNP'},
  {zoneName:'NO', type:'country', id:'NOR'},
  {zoneName:'OM', type:'country', id:'OMN'},
  {zoneName:'PK', type:'country', id:'PAK'},
  {zoneName:'PW', type:'country', id:'PLW'},
  {zoneName:'PS', type:'country', id:'PSX'},
  {zoneName:'PA', type:'country', id:'PAN'},
  {zoneName:'PG', type:'country', id:'PNG'},
  {zoneName:'PY', type:'country', id:'PRY'},
  {zoneName:'PE', type:'country', id:'PER'},
  {zoneName:'PH', type:'country', id:'PHL'},
  {zoneName:'PN', type:'country', id:'PCN'},
  {zoneName:'PL', type:'country', id:'POL'},
  {zoneName: 'PT', type: 'subunits', subunits: ['PRX']}, // Portugal Mainland,
  {zoneName: 'PT-MA', type: 'subunits', subunits: ['PMD']}, // Madeira Island,
  {zoneName: 'PT-AC', type: 'subunits', subunits: ['PAZ']}, // Azores Islands,
  {zoneName:'PR', type:'country', id:'PRI'},
  {zoneName:'QA', type:'country', id:'QAT'},
  {zoneName:'RE', type:'country', id:'REU'},
  {zoneName:'RO', type:'country', id:'ROU'},
  {zoneName:'RU', type:'country', id:'RUS'},
  {zoneName:'RW', type:'country', id:'RWA'},
  {zoneName:'BL', type:'country', id:'BLM'},
  {zoneName:'SH', type:'country', id:'SHN'},
  {zoneName:'KN', type:'country', id:'KNA'},
  {zoneName:'LC', type:'country', id:'LCA'},
  {zoneName:'MF', type:'country', id:'MAF'},
  {zoneName:'PM', type:'country', id:'SPM'},
  {zoneName:'VC', type:'country', id:'VCT'},
  {zoneName:'WS', type:'country', id:'WSM'},
  {zoneName:'SM', type:'country', id:'SMR'},
  {zoneName:'ST', type:'country', id:'STP'},
  {zoneName:'SA', type:'country', id:'SAU'},
  {zoneName:'SN', type:'country', id:'SEN'},
  {zoneName: 'RS', type: 'countries', countries: ['SRB', 'KOS']},
  {zoneName:'SC', type:'country', id:'SYC'},
  {zoneName:'SL', type:'country', id:'SLE'},
  {zoneName:'SG', type:'country', id:'SGP'},
  {zoneName:'SK', type:'country', id:'SVK'},
  {zoneName:'SI', type:'country', id:'SVN'},
  {zoneName:'SB', type:'country', id:'SLB'},
  {zoneName: 'SO', type: 'countries', countries: ['SOL', 'SOM']},
  {zoneName:'ZA', type:'country', id:'ZAF'},
  {zoneName:'GS', type:'country', id:'SGS'},
  {zoneName:'SS', type:'country', id:'SSD'},
  {zoneName: 'ES', type: 'subunits', subunits: ['ESX', 'SEC', 'SEM']}, //Spain Peninsula
  {zoneName: 'ES-CN', type:'country', id: 'La palma' }, // spain canary islands
  {zoneName: 'ES-CN', type:'country', id: 'Hierro' },
  {zoneName: 'ES-CN', type:'country', id: 'Isla de la Gomera' },
  {zoneName: 'ES-CN', type:'country', id: 'Tenerife' },
  {zoneName: 'ES-CN', type:'country', id: 'Gran Canria' },
  {zoneName: 'ES-CN-FVLZ', type: 'countries', countries: ['Fuerteventura', 'Lanzarote']},
  {zoneName: 'ES-IB', type: 'subunits', subunits: ['ESI']}, //Spain Balearic islands
  {zoneName:'LK', type:'country', id:'LKA'},
  {zoneName:'SD', type:'country', id:'SDN'},
  {zoneName:'SR', type:'country', id:'SUR'},
  {zoneName:'SJ', type:'country', id:'SJM'},
  {zoneName:'SZ', type:'country', id:'SWZ'},
  {zoneName:'SE', type:'country', id:'SWE'},
  {zoneName:'CH', type:'country', id:'CHE'},
  {zoneName:'SY', type:'country', id:'SYR'},
  {zoneName:'TW', type:'country', id:'TWN'},
  {zoneName:'TJ', type:'country', id:'TJK'},
  {zoneName:'TZ', type:'country', id:'TZA'},
  {zoneName:'TH', type:'country', id:'THA'},
  {zoneName:'TL', type:'country', id:'TLS'},
  {zoneName:'TG', type:'country', id:'TGO'},
  {zoneName:'TK', type:'country', id:'TKL'},
  {zoneName:'TO', type:'country', id:'TON'},
  {zoneName:'TT', type:'country', id:'TTO'},
  {zoneName:'TN', type:'country', id:'TUN'},
  {zoneName:'TR', type:'country', id:'TUR'},
  {zoneName:'TM', type:'country', id:'TKM'},
  {zoneName:'TC', type:'country', id:'TCA'},
  {zoneName:'TV', type:'country', id:'TUV'},
  {zoneName:'UG', type:'country', id:'UGA'},
  {zoneName:'UA', type:'country', id:'UKR'},
  {zoneName:'AE', type:'country', id:'ARE'},
  {zoneName: 'GB', type: 'subunits', subunits: ['ENG', 'SCT', 'WLS']},
  {zoneName: 'GB-NIR', type: 'subunits', subunits: ['NIR']},
  // {zoneName: 'US', type: 'subunits', subunits: ['USB']}, // Continental,
  // {zoneName: 'US-AK', type: 'subunits', subunits: ['USK']}, // Alaska,
  // {zoneName: 'US-HI', type: 'subunits', subunits: ['USH']}, // Hawaii,
  {zoneName: 'US-AK', countryId:'USA', stateId: 'US.AK', type: 'state'},
  {zoneName: 'US-AL', countryId:'USA', stateId: 'US.AL', type: 'state'},
  // {zoneName: 'US-AR', countryId:'USA', stateId: 'US.AR', type: 'state'},
  {zoneName: 'US-AZ', countryId:'USA', stateId: 'US.AZ', type: 'state'},
  {zoneName: 'US-CA', countryId:'USA', stateId: 'US.CA', type: 'state'},
  {zoneName: 'US-CO', countryId:'USA', stateId: 'US.CO', type: 'state'},
  // {zoneName: 'US-CT', countryId:'USA', stateId: 'US.CT', type: 'state'},
  {zoneName: 'US-DC', countryId:'USA', stateId: 'US.DC', type: 'state'},
  // {zoneName: 'US-DE', countryId:'USA', stateId: 'US.DE', type: 'state'},
  {zoneName: 'US-FL', countryId:'USA', stateId: 'US.FL', type: 'state'},
  {zoneName: 'US-GA', countryId:'USA', stateId: 'US.GA', type: 'state'},
  {zoneName: 'US-HI', countryId:'USA', stateId: 'US.HI', type: 'state'},
  // {zoneName: 'US-IA', countryId:'USA', stateId: 'US.IA', type: 'state'},
  {zoneName: 'US-ID', countryId:'USA', stateId: 'US.ID', type: 'state'},
  // {zoneName: 'US-IL', countryId:'USA', stateId: 'US.IL', type: 'state'},
  // {zoneName: 'US-IN', countryId:'USA', stateId: 'US.IN', type: 'state'},
  {zoneName: 'US-KS', countryId:'USA', stateId: 'US.KS', type: 'state'},
  // {zoneName: 'US-KY', countryId:'USA', stateId: 'US.KY', type: 'state'},
  // {zoneName: 'US-LA', countryId:'USA', stateId: 'US.LA', type: 'state'},
  // {zoneName: 'US-MA', countryId:'USA', stateId: 'US.MA', type: 'state'},
  // {zoneName: 'US-MD', countryId:'USA', stateId: 'US.MD', type: 'state'},
  // {zoneName: 'US-ME', countryId:'USA', stateId: 'US.ME', type: 'state'},
  // {zoneName: 'US-MI', countryId:'USA', stateId: 'US.MI', type: 'state'},
  {zoneName: 'US-MISO', type: 'states', countryId:'USA', states: ['US.AR', 'US.IA', 'US.IL', 'US.IN', 'US.LA', 'US.MI', 'US.MN', 'US.MO', 'US.ND', 'US.SD', 'US.WI']},
  // {zoneName: 'US-MN', countryId:'USA', stateId: 'US.MN', type: 'state'},
  // {zoneName: 'US-MO', countryId:'USA', stateId: 'US.MO', type: 'state'},
  {zoneName: 'US-MS', countryId:'USA', stateId: 'US.MS', type: 'state'},
  {zoneName: 'US-MT', countryId:'USA', stateId: 'US.MT', type: 'state'},
  {zoneName: 'US-NC', countryId:'USA', stateId: 'US.NC', type: 'state'},
  // {zoneName: 'US-ND', countryId:'USA', stateId: 'US.ND', type: 'state'},
  {zoneName: 'US-NE', countryId:'USA', stateId: 'US.NE', type: 'state'},
  {zoneName: 'US-NEISO', type: 'states', countryId:'USA', states: ['US.CT', 'US.MA', 'US.ME', 'US.NH', 'US.RI', 'US.VT']},
  // {zoneName: 'US-NH', countryId:'USA', stateId: 'US.NH', type: 'state'},
  // {zoneName: 'US-NJ', countryId:'USA', stateId: 'US.NJ', type: 'state'},
  {zoneName: 'US-NM', countryId:'USA', stateId: 'US.NM', type: 'state'},
  {zoneName: 'US-NV', countryId:'USA', stateId: 'US.NV', type: 'state'},
  {zoneName: 'US-NY', countryId:'USA', stateId: 'US.NY', type: 'state'},
  // {zoneName: 'US-OH', countryId:'USA', stateId: 'US.OH', type: 'state'},
  {zoneName: 'US-OK', countryId:'USA', stateId: 'US.OK', type: 'state'},
  {zoneName: 'US-OR', countryId:'USA', stateId: 'US.OR', type: 'state'},
  // {zoneName: 'US-PA', countryId:'USA', stateId: 'US.PA', type: 'state'},
  {zoneName: 'US-PJM', type: 'states', countryId:'USA', states: ['US.PA', 'US.NJ', 'US.MD', 'US.DE', 'US.VA', 'US.WV', 'US.OH', 'US.KY']},
  // {zoneName: 'US-RI', countryId:'USA', stateId: 'US.RI', type: 'state'},
  {zoneName: 'US-SC', countryId:'USA', stateId: 'US.SC', type: 'state'},
  // {zoneName: 'US-SD', countryId:'USA', stateId: 'US.SD', type: 'state'},
  {zoneName: 'US-TN', countryId:'USA', stateId: 'US.TN', type: 'state'},
  {zoneName: 'US-TX', countryId:'USA', stateId: 'US.TX', type: 'state'},
  {zoneName: 'US-UT', countryId:'USA', stateId: 'US.UT', type: 'state'},
  // {zoneName: 'US-VA', countryId:'USA', stateId: 'US.VA', type: 'state'},
  // {zoneName: 'US-VT', countryId:'USA', stateId: 'US.VT', type: 'state'},
  {zoneName: 'US-WA', countryId:'USA', stateId: 'US.WA', type: 'state'},
  // {zoneName: 'US-WI', countryId:'USA', stateId: 'US.WI', type: 'state'},
  // {zoneName: 'US-WV', countryId:'USA', stateId: 'US.WV', type: 'state'},
  {zoneName: 'US-WY', countryId:'USA', stateId: 'US.WY', type: 'state'},
  {zoneName:'UM', type:'country', id:'UMI'},
  {zoneName:'UY', type:'country', id:'URY'},
  {zoneName:'UZ', type:'country', id:'UZB'},
  {zoneName:'VU', type:'country', id:'VUT'},
  {zoneName:'VE', type:'country', id:'VEN'},
  {zoneName:'VN', type:'country', id:'VNM'},
  {zoneName:'VI', type:'country', id:'VIR'},
  {zoneName:'WF', type:'country', id:'WLF'},
  {zoneName:'EH', type:'country', id:'ESH'},
  {zoneName:'YE', type:'country', id:'YEM'},
  {zoneName:'ZM', type:'country', id:'ZMB'},
  {zoneName:'ZW', type:'country', id:'ZWE'},
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

// create zones from definitions
let zones = {};
zoneDefinitions.forEach(zone => {
  zones[zone.zoneName] = getDataForZone(zone, true);
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
fs.writeFileSync('zonegeometries.json', zoneFeatures.map(JSON.stringify).join('\n'));

// Simplify
const topojson = require('topojson');
let topo = topojson.topology(zones);
topo = topojson.presimplify(topo);
topo = topojson.simplify(topo, 0.01);
topo = topojson.filter(topo, topojson.filterWeight(topo, 0.01));
topo = topojson.quantize(topo, 1e4);
fs.writeFileSync('src/world.json', JSON.stringify(topo));
