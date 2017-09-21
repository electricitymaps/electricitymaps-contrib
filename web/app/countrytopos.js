var d3 = require('d3');
var topojson = require('topojson');

var topos = require('./world.json');

var exports = module.exports = {};

exports.addCountryTopos = function(countries) {

    // OPTIMIZATION:
    // A hash map would probably be much faster than doing a `filter`
    // for all countries O(n) instead of O(n^2)
    function hascMatch(properties, hasc) {
        return (
            properties.code_hasc == hasc ||
            (properties.hasc_maybe && properties.hasc_maybe.split('|').indexOf(hasc) != -1)
        );
    }
    function any(arr) {
        return arr.reduce(function(x, y) { return x || y});
    }
    function getSubUnits(ids) {
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return ids.indexOf(d.properties.subid) != -1;
        }));
    }
    function getState(countryId, code_hasc, use_maybe) {
        if (use_maybe == undefined) { use_maybe = false; }
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return d.id == countryId && (use_maybe && hascMatch(d.properties, code_hasc) || d.properties.code_hasc == code_hasc);
        }));
    }
    function getStates(countryId, code_hascs, use_maybe) {
        if (use_maybe == undefined) { use_maybe = false; }
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return d.id == countryId && (use_maybe && any(code_hascs.map(function(h) {
                return hascMatch(d.properties, h)
            }))) || code_hascs.indexOf(d.properties.code_hasc) != -1;
        }));
    }
    function getStateByFips(countryId, fips) {
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return d.id == countryId && d.properties.fips == fips;
        }));
    }
    function getCountry(id) {
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return d.id == id;
        }));
    }
    function getMergedCountries(ids) {
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return ids.indexOf(d.id) != -1;
        }));
    }

    // Map between "countries" iso_a2 and adm0_a3 in order to support XX, GB etc..
    // Note that the definition of "countries" is very vague here..
    // Specific case of Kosovo and Serbia: considered as a whole as long as they will be reported together in ENTSO-E. 
    countries['XX'] = getCountry('CYN');

    // List of all countries
    countries['AF'] = getCountry('AFG')
    countries['AX'] = getCountry('ALA')
    countries['AL'] = getCountry('ALB')
    countries['DZ'] = getCountry('DZA')
    countries['AS'] = getCountry('ASM')
    countries['AD'] = getCountry('AND')
    countries['AO'] = getCountry('AGO')
    countries['AI'] = getCountry('AIA')
    countries['AQ'] = getCountry('ATA')
    countries['AG'] = getCountry('ATG')
    countries['AR'] = getCountry('ARG')
    countries['AM'] = getCountry('ARM')
    countries['AW'] = getCountry('ABW')
    // countries['AU'] = getCountry('AUS');
    countries['AUS-ACT'] = getState('AUS', 'AU.AC');
    countries['AUS-NSW'] = getState('AUS', 'AU.NS');
    countries['AUS-NT'] = getState('AUS', 'AU.NT');
    countries['AUS-QLD'] = getState('AUS', 'AU.QL');
    countries['AUS-SA'] = getState('AUS', 'AU.SA');
    countries['AUS-TAS'] = getState('AUS', 'AU.TS');
    countries['AUS-VIC'] = getState('AUS', 'AU.VI');
    countries['AUS-WA'] = getState('AUS', 'AU.WA');
    countries['AT'] = getCountry('AUT')
    countries['AZ'] = getCountry('AZE')
    countries['BS'] = getCountry('BHS')
    countries['BH'] = getCountry('BHR')
    countries['BD'] = getCountry('BGD')
    countries['BB'] = getCountry('BRB')
    countries['BY'] = getCountry('BLR')
    countries['BE'] = getCountry('BEL')
    countries['BZ'] = getCountry('BLZ')
    countries['BJ'] = getCountry('BEN')
    countries['BM'] = getCountry('BMU')
    countries['BT'] = getCountry('BTN')
    countries['BO'] = getCountry('BOL')
    countries['BA'] = getCountry('BIH')
    countries['BW'] = getCountry('BWA')
    countries['BV'] = getCountry('BVT')
    //countries['BR'] = getCountry('BRA')
    countries['BR-N'] = getStates('BRA', ['BR.AM', 'BR.PA', 'BR.TO', 'BR.RR', 'BR.AP'])
    countries['BR-NE'] = getStates('BRA', ['BR.PE', 'BR.MA', 'BR.CE', 'BR.PI', 'BR.AL', 'BR.BA', 'BR.PB', 'BR.RN', 'BR.SE'])
    countries['BR-CS'] = getStates('BRA', ['BR.', 'BR.GO', 'BR.SP', 'BR.DF', 'BR.MS', 'BR.MG', 'BR.MT', 'BR.ES', 'BR.RJ'])
    countries['BR-S'] = getStates('BRA', ['BR.RS', 'BR.SC', 'BR.PR'])
    countries['VG'] = getCountry('VGB')
    countries['IO'] = getCountry('IOT')
    countries['BN'] = getCountry('BRN')
    countries['BG'] = getCountry('BGR')
    countries['BF'] = getCountry('BFA')
    countries['BI'] = getCountry('BDI')
    countries['KH'] = getCountry('KHM')
    countries['CM'] = getCountry('CMR')
    // countries['CA'] = getCountry('CAN');
    countries['CA-AB'] = getState('CAN', 'CA.AB');
    countries['CA-BC'] = getState('CAN', 'CA.BC');
    countries['CA-MB'] = getState('CAN', 'CA.MB');
    countries['CA-NB'] = getState('CAN', 'CA.NB');
    countries['CA-NL'] = getState('CAN', 'CA.NF'); // since 2002, ISO 3166-2 is "CA-NL", code_hasc in naturalearth is "CA.NF"
    countries['CA-NS'] = getState('CAN', 'CA.NS');
    countries['CA-ON'] = getState('CAN', 'CA.ON');
    countries['CA-PE'] = getState('CAN', 'CA.PE');
    countries['CA-QC'] = getState('CAN', 'CA.QC');
    countries['CA-SK'] = getState('CAN', 'CA.SK');
    countries['CA-NT'] = getState('CAN', 'CA.NT');
    countries['CA-NU'] = getState('CAN', 'CA.NU');
    countries['CA-YT'] = getState('CAN', 'CA.YT');
    countries['CV'] = getCountry('CPV')
    countries['KY'] = getCountry('CYM')
    countries['CF'] = getCountry('CAF')
    countries['TD'] = getCountry('TCD')
    countries['CL'] = getCountry('CHL')
    countries['CN'] = getCountry('CHN')
    countries['HK'] = getCountry('HKG')
    countries['MO'] = getCountry('MAC')
    countries['CX'] = getCountry('CXR')
    countries['CC'] = getCountry('CCK')
    countries['CO'] = getCountry('COL')
    countries['KM'] = getCountry('COM')
    countries['CG'] = getCountry('COG')
    countries['CD'] = getCountry('COD')
    countries['CK'] = getCountry('COK')
    countries['CR'] = getCountry('CRI')
    countries['CI'] = getCountry('CIV')
    countries['HR'] = getCountry('HRV')
    countries['CU'] = getCountry('CUB')
    countries['CY'] = getCountry('CYP')
    countries['CZ'] = getCountry('CZE')
    countries['DK'] = getCountry('DNK')
    countries['DJ'] = getCountry('DJI')
    countries['DM'] = getCountry('DMA')
    countries['DO'] = getCountry('DOM')
    countries['EC'] = getCountry('ECU')
    countries['EG'] = getCountry('EGY')
    countries['SV'] = getCountry('SLV')
    countries['GQ'] = getCountry('GNQ')
    countries['ER'] = getCountry('ERI')
    countries['EE'] = getCountry('EST')
    countries['ET'] = getCountry('ETH')
    countries['FK'] = getCountry('FLK')
    countries['FO'] = getCountry('FRO')
    countries['FJ'] = getCountry('FJI')
    countries['FI'] = getCountry('FIN')
    // countries['FR'] = getCountry('FRA')
    countries['FR'] = getSubUnits(['FXX'])
    countries['FR-COR'] = getSubUnits(['FXC'])
    countries['GF'] = getCountry('GUF')
    countries['PF'] = getCountry('PYF')
    countries['TF'] = getCountry('ATF')
    countries['GA'] = getCountry('GAB')
    countries['GM'] = getCountry('GMB')
    countries['GE'] = getCountry('GEO')
    countries['DE'] = getCountry('DEU')
    countries['GH'] = getCountry('GHA')
    countries['GI'] = getCountry('GIB')
    countries['GR'] = getCountry('GRC')
    countries['GL'] = getCountry('GRL')
    countries['GD'] = getCountry('GRD')
    countries['GP'] = getCountry('GLP')
    countries['GU'] = getCountry('GUM')
    countries['GT'] = getCountry('GTM')
    countries['GG'] = getCountry('GGY')
    countries['GN'] = getCountry('GIN')
    countries['GW'] = getCountry('GNB')
    countries['GY'] = getCountry('GUY')
    countries['HT'] = getCountry('HTI')
    countries['HM'] = getCountry('HMD')
    countries['VA'] = getCountry('VAT')
    countries['HN'] = getCountry('HND')
    countries['HU'] = getCountry('HUN')
    countries['IS'] = getCountry('ISL')
    countries['IN-AN'] = getState('IND', 'IN.AN', true);
    countries['IN-AP'] = getState('IND', 'IN.AP', true);
    countries['IN-AR'] = getState('IND', 'IN.AR', true);
    countries['IN-AS'] = getState('IND', 'IN.AS', true);
    countries['IN-BR'] = getState('IND', 'IN.BR', true);
    countries['IN-CT'] = getState('IND', 'IN.CT', true);
    countries['IN-CH'] = getState('IND', 'IN.CH', true);
    countries['IN-DD'] = getState('IND', 'IN.DD', true);
    countries['IN-DN'] = getState('IND', 'IN.DN', true);
    countries['IN-DL'] = getState('IND', 'IN.DL', true);
    countries['IN-GA'] = getState('IND', 'IN.GA', true);
    // For some reason IN.GJ is not a code_hasc in database, use FIPS code instead.
    // countries['IN-GJ'] = getState('IND', 'IN.GJ', true);
    countries['IN-GJ'] = getStateByFips('IND', 'IN32');
    countries['IN-HR'] = getState('IND', 'IN.HR', true);
    countries['IN-HP'] = getState('IND', 'IN.HP', true);
    countries['IN-JK'] = getState('IND', 'IN.JK', true);
    countries['IN-JH'] = getState('IND', 'IN.JH', true);
    countries['IN-KA'] = getState('IND', 'IN.KA', true);
    countries['IN-KL'] = getState('IND', 'IN.KL', true);
    countries['IN-LD'] = getState('IND', 'IN.LD', true);
    countries['IN-MP'] = getState('IND', 'IN.MP', true);
    countries['IN-MH'] = getState('IND', 'IN.MH', true);
    countries['IN-MN'] = getState('IND', 'IN.MN', true);
    countries['IN-ML'] = getState('IND', 'IN.ML', true);
    countries['IN-MZ'] = getState('IND', 'IN.MZ', true);
    countries['IN-NL'] = getState('IND', 'IN.NL', true);
    countries['IN-OR'] = getState('IND', 'IN.OR', true);
    countries['IN-PB'] = getState('IND', 'IN.PB', true); // Punjab State
    countries['IN-PY'] = getState('IND', 'IN.PY', true);
    countries['IN-RJ'] = getState('IND', 'IN.RJ', true);
    countries['IN-SK'] = getState('IND', 'IN.SK', true);
    countries['IN-TN'] = getState('IND', 'IN.TN', true);
    countries['IN-TG'] = getState('IND', 'IN.TG', true);
    countries['IN-TR'] = getState('IND', 'IN.TR', true);
    countries['IN-UT'] = getState('IND', 'IN.UT', true);
    countries['IN-UP'] = getState('IND', 'IN.UP', true);
    countries['IN-WB'] = getState('IND', 'IN.WB', true);
    countries['ID'] = getCountry('IDN')
    countries['IR'] = getCountry('IRN')
    countries['IQ'] = getCountry('IRQ')
    countries['IE'] = getCountry('IRL')
    countries['IM'] = getCountry('IMN')
    countries['IL'] = getCountry('ISR')
    countries['IT'] = getCountry('ITA')
    countries['JM'] = getCountry('JAM')
    countries['JP'] = getCountry('JPN')
    countries['JE'] = getCountry('JEY')
    countries['JO'] = getCountry('JOR')
    countries['KZ'] = getMergedCountries(['KAZ', 'KAB'])
    countries['KE'] = getCountry('KEN')
    countries['KI'] = getCountry('KIR')
    countries['KP'] = getCountry('PRK')
    countries['KR'] = getCountry('KOR')
    countries['KW'] = getCountry('KWT')
    countries['KG'] = getCountry('KGZ')
    countries['LA'] = getCountry('LAO')
    countries['LV'] = getCountry('LVA')
    countries['LB'] = getCountry('LBN')
    countries['LS'] = getCountry('LSO')
    countries['LR'] = getCountry('LBR')
    countries['LY'] = getCountry('LBY')
    countries['LI'] = getCountry('LIE')
    countries['LT'] = getCountry('LTU')
    countries['LU'] = getCountry('LUX')
    countries['MK'] = getCountry('MKD')
    countries['MG'] = getCountry('MDG')
    countries['MW'] = getCountry('MWI')
    countries['MY'] = getCountry('MYS')
    countries['MV'] = getCountry('MDV')
    countries['ML'] = getCountry('MLI')
    countries['MT'] = getCountry('MLT')
    countries['MH'] = getCountry('MHL')
    countries['MQ'] = getCountry('MTQ')
    countries['MR'] = getCountry('MRT')
    countries['MU'] = getCountry('MUS')
    countries['YT'] = getCountry('MYT')
    countries['MX'] = getCountry('MEX')
    countries['FM'] = getCountry('FSM')
    countries['MD'] = getCountry('MDA')
    countries['MC'] = getCountry('MCO')
    countries['MN'] = getCountry('MNG')
    countries['ME'] = getCountry('MNE')
    countries['MS'] = getCountry('MSR')
    countries['MA'] = getCountry('MAR')
    countries['MZ'] = getCountry('MOZ')
    countries['MM'] = getCountry('MMR')
    countries['NA'] = getCountry('NAM')
    countries['NR'] = getCountry('NRU')
    countries['NP'] = getCountry('NPL')
    countries['NL'] = getCountry('NLD')
    countries['AN'] = getCountry('ANT')
    countries['NC'] = getCountry('NCL')
    // countries['NZ'] = getCountry('NZL');
    countries['NZ-NZA'] = getSubUnits(['NZA'])
    countries['NZ-NZC'] = getSubUnits(['NZC'])
    countries['NZ-NZN'] = getSubUnits(['NZN'])
    countries['NZ-NZS'] = getSubUnits(['NZS'])
    countries['NI'] = getCountry('NIC')
    countries['NE'] = getCountry('NER')
    countries['NG'] = getCountry('NGA')
    countries['NU'] = getCountry('NIU')
    countries['NF'] = getCountry('NFK')
    countries['MP'] = getCountry('MNP')
    countries['NO'] = getCountry('NOR')
    countries['OM'] = getCountry('OMN')
    countries['PK'] = getCountry('PAK')
    countries['PW'] = getCountry('PLW')
    countries['PS'] = getCountry('PSX')
    countries['PA'] = getCountry('PAN')
    countries['PG'] = getCountry('PNG')
    countries['PY'] = getCountry('PRY')
    countries['PE'] = getCountry('PER')
    countries['PH'] = getCountry('PHL')
    countries['PN'] = getCountry('PCN')
    countries['PL'] = getCountry('POL')
    countries['PT'] = getSubUnits(['PRX']) // Portugal Mainland
    countries['PT-MA'] = getSubUnits(['PMD']) // Madeira Island
    countries['PT-AC'] = getSubUnits(['PAZ']) // Azores Islands
    countries['PR'] = getCountry('PRI')
    countries['QA'] = getCountry('QAT')
    countries['RE'] = getCountry('REU')
    countries['RO'] = getCountry('ROU')
    countries['RU'] = getCountry('RUS')
    countries['RW'] = getCountry('RWA')
    countries['BL'] = getCountry('BLM')
    countries['SH'] = getCountry('SHN')
    countries['KN'] = getCountry('KNA')
    countries['LC'] = getCountry('LCA')
    countries['MF'] = getCountry('MAF')
    countries['PM'] = getCountry('SPM')
    countries['VC'] = getCountry('VCT')
    countries['WS'] = getCountry('WSM')
    countries['SM'] = getCountry('SMR')
    countries['ST'] = getCountry('STP')
    countries['SA'] = getCountry('SAU')
    countries['SN'] = getCountry('SEN')
    countries['RS'] = getMergedCountries(['SRB','KOS']);
    countries['SC'] = getCountry('SYC')
    countries['SL'] = getCountry('SLE')
    countries['SG'] = getCountry('SGP')
    countries['SK'] = getCountry('SVK')
    countries['SI'] = getCountry('SVN')
    countries['SB'] = getCountry('SLB')
    countries['SO'] = getMergedCountries(['SOL', 'SOM'])
    countries['ZA'] = getCountry('ZAF')
    countries['GS'] = getCountry('SGS')
    countries['SS'] = getCountry('SSD')
    countries['ES'] = getSubUnits(['ESX', 'SEC', 'SEM']); //Spain Peninsula
    countries['ES-CN'] = getSubUnits(['ESC']); //Spain Canary Islands
    countries['ES-IB'] = getSubUnits(['ESI']); //Spain Balearic islands
    countries['LK'] = getCountry('LKA')
    countries['SD'] = getCountry('SDN')
    countries['SR'] = getCountry('SUR')
    countries['SJ'] = getCountry('SJM')
    countries['SZ'] = getCountry('SWZ')
    countries['SE'] = getCountry('SWE')
    countries['CH'] = getCountry('CHE')
    countries['SY'] = getCountry('SYR')
    countries['TW'] = getCountry('TWN')
    countries['TJ'] = getCountry('TJK')
    countries['TZ'] = getCountry('TZA')
    countries['TH'] = getCountry('THA')
    countries['TL'] = getCountry('TLS')
    countries['TG'] = getCountry('TGO')
    countries['TK'] = getCountry('TKL')
    countries['TO'] = getCountry('TON')
    countries['TT'] = getCountry('TTO')
    countries['TN'] = getCountry('TUN')
    countries['TR'] = getCountry('TUR')
    countries['TM'] = getCountry('TKM')
    countries['TC'] = getCountry('TCA')
    countries['TV'] = getCountry('TUV')
    countries['UG'] = getCountry('UGA')
    countries['UA'] = getCountry('UKR')
    countries['AE'] = getCountry('ARE')
    countries['GB'] = getSubUnits(['ENG', 'SCT', 'WLS'])
    countries['GB-NIR'] = getSubUnits(['NIR'])
    countries['US'] = getSubUnits(['USB']) // Continental
    countries['US-AK'] = getSubUnits(['USK']) // Alaska
    countries['US-HI'] = getSubUnits(['USH']) // Hawaii
    countries['UM'] = getCountry('UMI')
    countries['UY'] = getCountry('URY')
    countries['UZ'] = getCountry('UZB')
    countries['VU'] = getCountry('VUT')
    countries['VE'] = getCountry('VEN')
    countries['VN'] = getCountry('VNM')
    countries['VI'] = getCountry('VIR')
    countries['WF'] = getCountry('WLF')
    countries['EH'] = getCountry('ESH')
    countries['YE'] = getCountry('YEM')
    countries['ZM'] = getCountry('ZMB')
    countries['ZW'] = getCountry('ZWE')
    

    // Clear memory
    topos = [];

    return countries;
}
