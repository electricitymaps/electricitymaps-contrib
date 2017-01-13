var d3 = require('d3');
var topojson = require('topojson');

var topos = require('json-loader!./world_50m.json');

var exports = module.exports = {};

exports.addCountryTopos = function(countries) {
    function getSubUnits(ids) {
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return ids.indexOf(d.subid) != -1;
        }));
    }
    function getCountry(id) {
        return topojson.merge(topos, topos.objects.countries.geometries.filter(function(d) {
            return d.id == id;
        }));
    }

    // Map between "countries" iso_a2 and adm0_a3 in order to support XK, GB etc..
    // Note that the definition of "countries" is very vague here..
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
    countries['RS'] = getCountry('SRB');
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
    countries['XK'] = getCountry('KOS');

    // Clear memory
    topos = [];

    return countries;
}
