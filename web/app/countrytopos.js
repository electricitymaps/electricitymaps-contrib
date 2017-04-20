var d3 = require('d3');
var topojson = require('topojson');

var topos = require('json-loader!./world_50m.json');

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
    countries['AL'] = getCountry('ALB');
    countries['AM'] = getCountry('ARM');
    countries['AT'] = getCountry('AUT');
    countries['AZ'] = getCountry('AZE');
    countries['BE'] = getCountry('BEL');
    countries['BG'] = getCountry('BGR');
    countries['BA'] = getCountry('BIH');
    countries['BY'] = getCountry('BLR');
    countries['CH'] = getCountry('CHE');
    countries['CY'] = getCountry('CYP');
    countries['CZ'] = getCountry('CZE');
    countries['DE'] = getCountry('DEU');
    countries['DK'] = getCountry('DNK');
    countries['DZ'] = getCountry('DZA');
    countries['ES'] = getCountry('ESP');
    countries['EE'] = getCountry('EST');
    countries['EG'] = getCountry('EGY');
    countries['FI'] = getCountry('FIN');
    countries['FO'] = getCountry('FRO');
    countries['FR'] = getCountry('FRA');
    countries['GB'] = getSubUnits(['ENG', 'SCT', 'WLS']);
    countries['GE'] = getCountry('GEO');
    countries['GR'] = getCountry('GRC');
    countries['HR'] = getCountry('HRV');
    countries['HU'] = getCountry('HUN');
    countries['IE'] = getCountry('IRL');
    countries['IL'] = getCountry('ISR');
    countries['IQ'] = getCountry('IRQ');
    countries['IR'] = getCountry('IRN');
    countries['IS'] = getCountry('ISL');
    countries['IT'] = getCountry('ITA');
    countries['JO'] = getCountry('JOR');
    countries['KZ'] = getCountry('KAZ');
    countries['LB'] = getCountry('LBN');
    countries['LT'] = getCountry('LTU');
    countries['LU'] = getCountry('LUX');
    countries['LV'] = getCountry('LVA');
    countries['LY'] = getCountry('LBY');
    countries['MA'] = getCountry('MAR');
    countries['MD'] = getCountry('MDA');
    countries['MK'] = getCountry('MKD');
    countries['ME'] = getCountry('MNE');
    countries['MT'] = getCountry('MLT');
    countries['GB-NIR'] = getSubUnits(['NIR']);
    countries['NL'] = getCountry('NLD');
    countries['NO'] = getCountry('NOR');
    countries['PL'] = getCountry('POL');
    countries['PS'] = getCountry('PSX');
    countries['PT'] = getCountry('PRT');
    countries['RO'] = getCountry('ROU');
    countries['RU'] = getCountry('RUS');
    countries['RS'] = getMergedCountries(['SRB','KOS']);
    countries['SA'] = getCountry('SAU');
    countries['SK'] = getCountry('SVK');
    countries['SI'] = getCountry('SVN');
    countries['SE'] = getCountry('SWE');
    countries['SY'] = getCountry('SYR');
    countries['TM'] = getCountry('TKM');
    countries['TN'] = getCountry('TUN');
    countries['TR'] = getCountry('TUR');
    countries['UA'] = getCountry('UKR');
    countries['UZ'] = getCountry('UZB');

    countries['XX'] = getCountry('CYN');

    // Australia
    countries['AUS-TAS'] = getState('AUS', 'AU.TS');
    countries['AUS-NSW'] = getState('AUS', 'AU.NS');
    countries['AUS-QLD'] = getState('AUS', 'AU.QL');
    countries['AUS-SA'] = getState('AUS', 'AU.SA');
    countries['AUS-VIC'] = getState('AUS', 'AU.VI');
    countries['AUS-WA'] = getState('AUS', 'AU.WA');
    countries['AUS-NT'] = getState('AUS', 'AU.NT');
    countries['AUS-ACT'] = getState('AUS', 'AU.AC');

    // North America
    countries['US'] = getCountry('USA');
    countries['MX'] = getCountry('MEX');
    countries['CU'] = getCountry('CUB');
    countries['DO'] = getCountry('DOM');
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
    

    // Clear memory
    topos = [];

    return countries;
}
