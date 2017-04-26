var d3 = require('d3');
var topojson = require('topojson');

var topos = require('json-loader!./world.json');

var exports = module.exports = {};

exports.addCountryTopos = function(countries) {
    function getSubUnits(ids) {
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return ids.indexOf(d.properties.subid) != -1;
        }));
    }
    function getState(countryId, code_hasc) {
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return d.id == countryId && d.properties.code_hasc == code_hasc;
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
    countries['BR'] = getCountry('BRA')
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
    countries['CA-NL'] = getState('CAN', 'CA.NL');
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
    countries['FR'] = getCountry('FRA')
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
    countries['IN'] = getCountry('IND')
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
    countries['KZ'] = getCountry('KAZ')
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
    countries['NZ-NZA'] = getSubUnits(['NZA']);
    countries['NZ-NZC'] = getSubUnits(['NZC']);
    countries['NZ-NZN'] = getSubUnits(['NZN']);
    countries['NZ-NZS'] = getSubUnits(['NZS']);
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
    countries['PS'] = getCountry('PSE')
    countries['PA'] = getCountry('PAN')
    countries['PG'] = getCountry('PNG')
    countries['PY'] = getCountry('PRY')
    countries['PE'] = getCountry('PER')
    countries['PH'] = getCountry('PHL')
    countries['PN'] = getCountry('PCN')
    countries['PL'] = getCountry('POL')
    countries['PT'] = getCountry('PRT')
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
    countries['SO'] = getCountry('SOM')
    countries['ZA'] = getCountry('ZAF')
    countries['GS'] = getCountry('SGS')
    countries['SS'] = getCountry('SSD')
    countries['ES'] = getCountry('ESP')
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
    countries['GB'] = getSubUnits(['ENG', 'SCT', 'WLS']);
    countries['GB-NIR'] = getSubUnits(['NIR']);
    countries['US'] = getCountry('USA')
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
