const fs = require('fs');

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

const zones = {};

// Map between "zones" iso_a2 and adm0_a3 in order to support XX, GB etc..
// Note that the definition of "zones" is very vague here..
// Specific case of Kosovo and Serbia: considered as a whole as long as they will be reported together in ENTSO-E.
zones['XX'] = getCountry('CYN');

// List of all zones
zones['AF'] = getCountry('AFG');
zones['AX'] = getCountry('ALA');
zones['AL'] = getCountry('ALB');
zones['DZ'] = getCountry('DZA');
zones['AS'] = getCountry('ASM');
zones['AD'] = getCountry('AND');
zones['AO'] = getCountry('AGO');
zones['AI'] = getCountry('AIA');
// zones['AQ'] = getCountry('AT;A')
zones['AG'] = getCountry('ATG');
zones['AR'] = getCountry('ARG');
zones['AM'] = getCountry('ARM');
zones['AW'] = getCountry('ABW');
// zones['AU'] = getCountry('AUS');
// zones['AUS-ACT'] = getState('AUS', 'AU.AC');
zones['AUS-NSW'] = getStates('AUS', ['AU.NS', 'AU.AC']);
zones['AUS-NT'] = getState('AUS', 'AU.NT');
zones['AUS-QLD'] = getState('AUS', 'AU.QL');
zones['AUS-SA'] = getState('AUS', 'AU.SA');
zones['AUS-TAS'] = getState('AUS', 'AU.TS');
zones['AUS-VIC'] = getState('AUS', 'AU.VI');
zones['AUS-WA'] = getState('AUS', 'AU.WA');
zones['AT'] = getCountry('AUT');
zones['AZ'] = getCountry('AZE');
zones['BS'] = getCountry('BHS');
zones['BH'] = getCountry('BHR');
zones['BD'] = getCountry('BGD');
zones['BB'] = getCountry('BRB');
zones['BY'] = getCountry('BLR');
zones['BE'] = getCountry('BEL');
zones['BZ'] = getCountry('BLZ');
zones['BJ'] = getCountry('BEN');
zones['BM'] = getCountry('BMU');
zones['BT'] = getCountry('BTN');
zones['BO'] = getCountry('BOL');
//zones['BA'] = getCountry('BIH');
zones['BA'] = getStatesByAdm1(['BIH-4801', 'BIH-4802', 'BIH-2225', 'BIH-2224', 'BIH-2226', 'BIH-2227', 'BIH-2228', 'BIH-4807', 'BIH-4808', 'BIH-4805', 'BIH-4806', 'BIH-2890', 'BIH-2891', 'BIH-2889', 'BIH-2887', 'BIH-4804', 'BIH-3153', 'BIH-4803']);
zones['BW'] = getCountry('BWA');
zones['BV'] = getCountry('BVT');
//zones['BR'] = getCountry('BRA');
zones['BR-N'] = getStates('BRA', ['BR.AM', 'BR.PA', 'BR.TO', 'BR.RR', 'BR.AP']);
zones['BR-NE'] = getStates('BRA', ['BR.PE', 'BR.MA', 'BR.CE', 'BR.PI', 'BR.AL', 'BR.BA', 'BR.PB', 'BR.RN', 'BR.SE']);
zones['BR-CS'] = getStates('BRA', ['BR.', 'BR.AC', 'BR.GO', 'BR.SP', 'BR.DF', 'BR.MS', 'BR.MG', 'BR.MT', 'BR.ES', 'BR.RJ', 'BR.RO']);
zones['BR-S'] = getStates('BRA', ['BR.RS', 'BR.SC', 'BR.PR']);
zones['VG'] = getCountry('VGB');
zones['IO'] = getCountry('IOT');
zones['BN'] = getCountry('BRN');
zones['BG'] = getCountry('BGR');
zones['BF'] = getCountry('BFA');
zones['BI'] = getCountry('BDI');
zones['KH'] = getCountry('KHM');
zones['CM'] = getCountry('CMR');
// zones['CA'] = getCountry('CAN');
zones['CA-AB'] = getState('CAN', 'CA.AB');
zones['CA-BC'] = getState('CAN', 'CA.BC');
zones['CA-MB'] = getState('CAN', 'CA.MB');
zones['CA-NB'] = getState('CAN', 'CA.NB');
zones['CA-NL'] = getState('CAN', 'CA.NF'); // since 2002, ISO 3166-2 is "CA-NL", code_hasc in naturalearth is "CA.NF"
zones['CA-NS'] = getState('CAN', 'CA.NS');
zones['CA-ON'] = getState('CAN', 'CA.ON');
zones['CA-PE'] = getState('CAN', 'CA.PE');
zones['CA-QC'] = getState('CAN', 'CA.QC');
zones['CA-SK'] = getState('CAN', 'CA.SK');
zones['CA-NT'] = getState('CAN', 'CA.NT');
zones['CA-NU'] = getState('CAN', 'CA.NU');
zones['CA-YT'] = getState('CAN', 'CA.YT');
zones['CV'] = getCountry('CPV');
zones['KY'] = getCountry('CYM');
zones['CF'] = getCountry('CAF');
zones['TD'] = getCountry('TCD');
//zones['CL'] = getCountry('CHL');
zones['CL-SING'] = getStates('CHL', ['CL.AP', 'CL.TA', 'CL.AN']);
zones['CL-SIC'] = getStatesByAdm1(['CHL-2696', 'CHL-2697', 'CHL-2699', 'CHL-2698', 'CHL-2703', 'CHL-2705', 'CHL-2702', 'CHL-2700', 'CHL-2701', 'CHL-2704']);
zones['CL-SEM'] = getState('CHL', 'CL.MA');
zones['CL-SEA'] = getState('CHL', 'CL.AI');
zones['CN'] = getCountry('CHN');
zones['HK'] = getCountry('HKG');
zones['MO'] = getCountry('MAC');
zones['CX'] = getCountry('CXR');
zones['CC'] = getCountry('CCK');
zones['CO'] = getCountry('COL');
zones['KM'] = getCountry('COM');
zones['CG'] = getCountry('COG');
zones['CD'] = getCountry('COD');
zones['CK'] = getCountry('COK');
zones['CR'] = getCountry('CRI');
zones['CI'] = getCountry('CIV');
zones['HR'] = getCountry('HRV');
zones['CU'] = getCountry('CUB');
zones['CY'] = getCountry('CYP');
zones['CZ'] = getCountry('CZE');
zones['DK'] = getSubUnits(['DNK']);
zones['DK-BHM'] = getSubUnits(['DNB']);
zones['DJ'] = getCountry('DJI');
zones['DM'] = getCountry('DMA');
zones['DO'] = getCountry('DOM');
zones['EC'] = getCountry('ECU');
zones['EG'] = getCountry('EGY');
zones['SV'] = getCountry('SLV');
zones['GQ'] = getCountry('GNQ');
zones['ER'] = getCountry('ERI');
zones['EE'] = getCountry('EST');
zones['ET'] = getCountry('ETH');
zones['FK'] = getCountry('FLK');
zones['FO'] = getCountry('FRO');
zones['FJ'] = getCountry('FJI');
zones['FI'] = getCountry('FIN');
// zones['FR'] = getCountry('FRA');
zones['FR'] = getSubUnits(['FXX']);
zones['FR-COR'] = getSubUnits(['FXC']);
zones['GF'] = getCountry('GUF');
zones['PF'] = getCountry('PYF');
zones['TF'] = getCountry('ATF');
zones['GA'] = getCountry('GAB');
zones['GM'] = getCountry('GMB');
zones['GE'] = getCountry('GEO');
zones['DE'] = getCountry('DEU');
zones['GH'] = getCountry('GHA');
zones['GI'] = getCountry('GIB');
zones['GR'] = getCountry('GRC');
zones['GL'] = getCountry('GRL');
zones['GD'] = getCountry('GRD');
zones['GP'] = getCountry('GLP');
zones['GU'] = getCountry('GUM');
zones['GT'] = getCountry('GTM');
zones['GG'] = getCountry('GGY');
zones['GN'] = getCountry('GIN');
zones['GW'] = getCountry('GNB');
zones['GY'] = getCountry('GUY');
zones['HT'] = getCountry('HTI');
zones['HM'] = getCountry('HMD');
zones['VA'] = getCountry('VAT');
zones['HN'] = getCountry('HND');
zones['HU'] = getCountry('HUN');
zones['IS'] = getCountry('ISL');
// TODO: Use iso_3166_2 field instead
zones['IN-AN'] = getState('IND', 'IN.AN', true);
zones['IN-AP'] = getState('IND', 'IN.AD', true);
zones['IN-AR'] = getState('IND', 'IN.AR', true);
zones['IN-AS'] = getState('IND', 'IN.AS', true);
zones['IN-BR'] = getState('IND', 'IN.BR', true);
zones['IN-CT'] = getState('IND', 'IN.CT', true);
zones['IN-CH'] = getState('IND', 'IN.CH', true);
zones['IN-DD'] = getState('IND', 'IN.DD', true);
zones['IN-DN'] = getState('IND', 'IN.DN', true);
zones['IN-DL'] = getState('IND', 'IN.DL', true);
zones['IN-GA'] = getState('IND', 'IN.GA', true);
// For some reason IN.GJ is not a code_hasc in database, use FIPS code instead.
// zones['IN-GJ'] = getState('IND', 'IN.GJ', true);
zones['IN-GJ'] = getStateByFips('IND', 'IN32');
zones['IN-HR'] = getState('IND', 'IN.HR', true);
zones['IN-HP'] = getState('IND', 'IN.HP', true);
zones['IN-JK'] = getState('IND', 'IN.JK', true);
zones['IN-JH'] = getState('IND', 'IN.JH', true);
zones['IN-KA'] = getState('IND', 'IN.KA', true);
zones['IN-KL'] = getState('IND', 'IN.KL', true);
zones['IN-LD'] = getState('IND', 'IN.LD', true);
zones['IN-MP'] = getState('IND', 'IN.MP', true);
zones['IN-MH'] = getState('IND', 'IN.MH', true);
zones['IN-MN'] = getState('IND', 'IN.MN', true);
zones['IN-ML'] = getState('IND', 'IN.ML', true);
zones['IN-MZ'] = getState('IND', 'IN.MZ', true);
zones['IN-NL'] = getState('IND', 'IN.NL', true);
zones['IN-OR'] = getState('IND', 'IN.OR', true);
zones['IN-PB'] = getState('IND', 'IN.PB', true); // Punjab State
zones['IN-PY'] = getState('IND', 'IN.PY', true);
zones['IN-RJ'] = getState('IND', 'IN.RJ', true);
zones['IN-SK'] = getState('IND', 'IN.SK', true);
zones['IN-TN'] = getState('IND', 'IN.TN', true);
zones['IN-TG'] = getState('IND', 'IN.TG', true);
zones['IN-TR'] = getState('IND', 'IN.TR', true);
zones['IN-UT'] = getState('IND', 'IN.UT', true);
zones['IN-UP'] = getState('IND', 'IN.UP', true);
zones['IN-WB'] = getState('IND', 'IN.WB', true);
zones['ID'] = getCountry('IDN');
zones['IR'] = getCountry('IRN');
zones['IQ'] = getCountry('IRQ');
zones['IE'] = getCountry('IRL');
zones['IM'] = getCountry('IMN');
zones['IL'] = getCountry('ISR');
zones['IT'] = getCountry('ITA');
zones['JM'] = getCountry('JAM');
zones['JP'] = getCountry('JPN');
zones['JE'] = getCountry('JEY');
zones['JO'] = getCountry('JOR');
zones['KZ'] = getCountries(['KAZ', 'KAB']);
zones['KE'] = getCountry('KEN');
zones['KI'] = getCountry('KIR');
zones['KP'] = getCountry('PRK');
zones['KR'] = getCountry('KOR');
zones['KW'] = getCountry('KWT');
zones['KG'] = getCountry('KGZ');
zones['LA'] = getCountry('LAO');
zones['LV'] = getCountry('LVA');
zones['LB'] = getCountry('LBN');
zones['LS'] = getCountry('LSO');
zones['LR'] = getCountry('LBR');
zones['LY'] = getCountry('LBY');
zones['LI'] = getCountry('LIE');
zones['LT'] = getCountry('LTU');
zones['LU'] = getCountry('LUX');
zones['MK'] = getCountry('MKD');
zones['MG'] = getCountry('MDG');
zones['MW'] = getCountry('MWI');
// zones['MY'] = getcountry('MYS');
zones['MY-EM'] = getStatesByAdm1(['MYS-1186', 'MYS-1187']);
zones['MY-WM'] = getStatesByAdm1(['MYS-1141', 'MYS-1140', 'MYS-1139', 'MYS-1137', 'MYS-1144', 'MYS-1149', 'MYS-1147', 'MYS-1148', 'MYS-4831', 'MYS-4832', 'MYS-1146', 'MYS-1145', 'MYS-1143']);
zones['MV'] = getCountry('MDV');
zones['ML'] = getCountry('MLI');
zones['MT'] = getCountry('MLT');
zones['MH'] = getCountry('MHL');
zones['MQ'] = getCountry('MTQ');
zones['MR'] = getCountry('MRT');
zones['MU'] = getCountry('MUS');
zones['YT'] = getCountry('MYT');
zones['MX'] = getCountry('MEX');
zones['FM'] = getCountry('FSM');
zones['MD'] = getCountry('MDA');
zones['MC'] = getCountry('MCO');
zones['MN'] = getCountry('MNG');
zones['ME'] = getCountry('MNE');
zones['MS'] = getCountry('MSR');
zones['MA'] = getCountry('MAR');
zones['MZ'] = getCountry('MOZ');
zones['MM'] = getCountry('MMR');
zones['NA'] = getCountry('NAM');
zones['NR'] = getCountry('NRU');
zones['NP'] = getCountry('NPL');
zones['NL'] = getCountry('NLD');
zones['AN'] = getCountry('ANT');
zones['NC'] = getCountry('NCL');
// zones['NZ'] = getCountry('NZL');;
zones['NZ-NZA'] = getSubUnits(['NZA']);
zones['NZ-NZC'] = getSubUnits(['NZC']);
zones['NZ-NZN'] = getSubUnits(['NZN']);
zones['NZ-NZS'] = getSubUnits(['NZS']);
zones['NI'] = getCountry('NIC');
zones['NE'] = getCountry('NER');
zones['NG'] = getCountry('NGA');
zones['NU'] = getCountry('NIU');
zones['NF'] = getCountry('NFK');
zones['MP'] = getCountry('MNP');
zones['NO'] = getCountry('NOR');
zones['OM'] = getCountry('OMN');
zones['PK'] = getCountry('PAK');
zones['PW'] = getCountry('PLW');
zones['PS'] = getCountry('PSX');
zones['PA'] = getCountry('PAN');
zones['PG'] = getCountry('PNG');
zones['PY'] = getCountry('PRY');
zones['PE'] = getCountry('PER');
zones['PH'] = getCountry('PHL');
zones['PN'] = getCountry('PCN');
zones['PL'] = getCountry('POL');
zones['PT'] = getSubUnits(['PRX']) // Portugal Mainland;
zones['PT-MA'] = getSubUnits(['PMD']) // Madeira Island;
zones['PT-AC'] = getSubUnits(['PAZ']) // Azores Islands;
zones['PR'] = getCountry('PRI');
zones['QA'] = getCountry('QAT');
zones['RE'] = getCountry('REU');
zones['RO'] = getCountry('ROU');
zones['RU'] = getCountry('RUS');
zones['RW'] = getCountry('RWA');
zones['BL'] = getCountry('BLM');
zones['SH'] = getCountry('SHN');
zones['KN'] = getCountry('KNA');
zones['LC'] = getCountry('LCA');
zones['MF'] = getCountry('MAF');
zones['PM'] = getCountry('SPM');
zones['VC'] = getCountry('VCT');
zones['WS'] = getCountry('WSM');
zones['SM'] = getCountry('SMR');
zones['ST'] = getCountry('STP');
zones['SA'] = getCountry('SAU');
zones['SN'] = getCountry('SEN');
zones['RS'] = getCountries(['SRB', 'KOS']);
zones['SC'] = getCountry('SYC');
zones['SL'] = getCountry('SLE');
zones['SG'] = getCountry('SGP');
zones['SK'] = getCountry('SVK');
zones['SI'] = getCountry('SVN');
zones['SB'] = getCountry('SLB');
zones['SO'] = getCountries(['SOL', 'SOM']);
zones['ZA'] = getCountry('ZAF');
zones['GS'] = getCountry('SGS');
zones['SS'] = getCountry('SSD');
zones['ES'] = getSubUnits(['ESX', 'SEC', 'SEM']); //Spain Peninsula
zones['ES-CN-LP'] = getCountry('La Palma'); //Spain Canary Islands
zones['ES-CN-HI'] = getCountry('Hierro');
zones['ES-CN-IG'] = getCountry('Isla de la Gomera');
zones['ES-CN-TE'] = getCountry('Tenerife');
zones['ES-CN-GC'] = getCountry('Gran Canaria');
zones['ES-CN-FVLZ'] = getCountries(['Fuerteventura', 'Lanzarote']);
zones['ES-IB'] = getSubUnits(['ESI']); //Spain Balearic islands
zones['LK'] = getCountry('LKA');
zones['SD'] = getCountry('SDN');
zones['SR'] = getCountry('SUR');
zones['SJ'] = getCountry('SJM');
zones['SZ'] = getCountry('SWZ');
zones['SE'] = getCountry('SWE');
zones['CH'] = getCountry('CHE');
zones['SY'] = getCountry('SYR');
zones['TW'] = getCountry('TWN');
zones['TJ'] = getCountry('TJK');
zones['TZ'] = getCountry('TZA');
zones['TH'] = getCountry('THA');
zones['TL'] = getCountry('TLS');
zones['TG'] = getCountry('TGO');
zones['TK'] = getCountry('TKL');
zones['TO'] = getCountry('TON');
zones['TT'] = getCountry('TTO');
zones['TN'] = getCountry('TUN');
zones['TR'] = getCountry('TUR');
zones['TM'] = getCountry('TKM');
zones['TC'] = getCountry('TCA');
zones['TV'] = getCountry('TUV');
zones['UG'] = getCountry('UGA');
zones['UA'] = getCountry('UKR');
zones['AE'] = getCountry('ARE');
zones['GB'] = getSubUnits(['ENG', 'SCT', 'WLS']);
zones['GB-NIR'] = getSubUnits(['NIR']);
// zones['US'] = getSubUnits(['USB']) // Continental;
// zones['US-AK'] = getSubUnits(['USK']) // Alaska;
// zones['US-HI'] = getSubUnits(['USH']) // Hawaii;
zones['US-AK'] = getState('USA', 'US.AK');
zones['US-AL'] = getState('USA', 'US.AL');
// zones['US-AR'] = getState('USA', 'US.AR');
zones['US-AZ'] = getState('USA', 'US.AZ');
zones['US-CA'] = getState('USA', 'US.CA');
zones['US-CO'] = getState('USA', 'US.CO');
// zones['US-CT'] = getState('USA', 'US.CT');
zones['US-DC'] = getState('USA', 'US.DC');
// zones['US-DE'] = getState('USA', 'US.DE');
zones['US-FL'] = getState('USA', 'US.FL');
zones['US-GA'] = getState('USA', 'US.GA');
zones['US-HI'] = getState('USA', 'US.HI');
// zones['US-IA'] = getState('USA', 'US.IA');
zones['US-ID'] = getState('USA', 'US.ID');
// zones['US-IL'] = getState('USA', 'US.IL');
// zones['US-IN'] = getState('USA', 'US.IN');
zones['US-KS'] = getState('USA', 'US.KS');
// zones['US-KY'] = getState('USA', 'US.KY');
// zones['US-LA'] = getState('USA', 'US.LA');
// zones['US-MA'] = getState('USA', 'US.MA');
// zones['US-MD'] = getState('USA', 'US.MD');
// zones['US-ME'] = getState('USA', 'US.ME');
// zones['US-MI'] = getState('USA', 'US.MI');
zones['US-MISO'] = getStates('USA', ['US.AR', 'US.IA', 'US.IL', 'US.IN', 'US.LA', 'US.MI', 'US.MN', 'US.MO', 'US.ND', 'US.SD', 'US.WI']);
// zones['US-MN'] = getState('USA', 'US.MN');
// zones['US-MO'] = getState('USA', 'US.MO');
zones['US-MS'] = getState('USA', 'US.MS');
zones['US-MT'] = getState('USA', 'US.MT');
zones['US-NC'] = getState('USA', 'US.NC');
// zones['US-ND'] = getState('USA', 'US.ND');
zones['US-NE'] = getState('USA', 'US.NE');
zones['US-NEISO'] = getStates('USA', ['US.CT', 'US.MA', 'US.ME', 'US.NH', 'US.RI', 'US.VT']);
// zones['US-NH'] = getState('USA', 'US.NH');
// zones['US-NJ'] = getState('USA', 'US.NJ');
zones['US-NM'] = getState('USA', 'US.NM');
zones['US-NV'] = getState('USA', 'US.NV');
zones['US-NY'] = getState('USA', 'US.NY');
// zones['US-OH'] = getState('USA', 'US.OH');
zones['US-OK'] = getState('USA', 'US.OK');
zones['US-OR'] = getState('USA', 'US.OR');
// zones['US-PA'] = getState('USA', 'US.PA');
zones['US-PJM'] = getStates('USA', ['US.PA', 'US.NJ', 'US.MD', 'US.DE', 'US.VA', 'US.WV', 'US.OH', 'US.KY']);
// zones['US-RI'] = getState('USA', 'US.RI');
zones['US-SC'] = getState('USA', 'US.SC');
// zones['US-SD'] = getState('USA', 'US.SD');
zones['US-TN'] = getState('USA', 'US.TN');
zones['US-TX'] = getState('USA', 'US.TX');
zones['US-UT'] = getState('USA', 'US.UT');
// zones['US-VA'] = getState('USA', 'US.VA');
// zones['US-VT'] = getState('USA', 'US.VT');
zones['US-WA'] = getState('USA', 'US.WA');
// zones['US-WI'] = getState('USA', 'US.WI');
// zones['US-WV'] = getState('USA', 'US.WV');
zones['US-WY'] = getState('USA', 'US.WY');
zones['UM'] = getCountry('UMI');
zones['UY'] = getCountry('URY');
zones['UZ'] = getCountry('UZB');
zones['VU'] = getCountry('VUT');
zones['VE'] = getCountry('VEN');
zones['VN'] = getCountry('VNM');
zones['VI'] = getCountry('VIR');
zones['WF'] = getCountry('WLF');
zones['EH'] = getCountry('ESH');
zones['YE'] = getCountry('YEM');
zones['ZM'] = getCountry('ZMB');
zones['ZW'] = getCountry('ZWE');

// Convert to list of feature
const zoneFeatures = Object.entries(zones).filter(d => d[1] != null).map((d) => {
  const [k, v] = d;
  v.id = k;
  v.properties = {
    zoneName: k,
  };
  return v;
});

// Write unsimplified list of geojson
fs.writeFileSync('zonegeometries.json', zoneFeatures.map(JSON.stringify).join('\n'));

// Simplify
const topojson = require('topojson');
let topo = topojson.topology(zones, 1e5);
topo = topojson.presimplify(topo);
topo = topojson.simplify(topo, 0.01);
topo = topojson.filter(topo);
// Convert
const simplifiedZones = {};
Object.keys(zones).forEach((k) => {
  if (!topo.objects[k].arcs) { return; }
  let geo
  // Do merge inner arcs for those
  if (['US'].indexOf(k.split('-')[0]) !== -1) {
    geo = topojson.feature(topo, topo.objects[k]);
  } else {
    geo = { geometry: topojson.merge(topo, [topo.objects[k]]) };
  }
  // Exclude countries with null geometries.
  if (geo.geometry) {
    simplifiedZones[k] = geo;
  }
})

fs.writeFileSync('src/world.json', JSON.stringify(simplifiedZones));
//TODO:Try to output topojson to see size reduction?
