var exports = module.exports = {};

var defaultCo2eqFootprint = {
    'biomass': 230,
    'coal': 820,
    'gas': 490,
    'hydro': 24,
    'nuclear': 12,
    'oil': 650,
    'solar': 45,
    'wind': 12,
    'geothermal': 24,
    'unknown': 700, // assume conventional
    'other': 700 // same as 'unknown'. Here for backward compatibility
}; // in gCo2eq/kWh
var defaultCo2eqSource = 'IPCC 2014';

var countryCo2eqFootprint = {
    'DE': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? {value: 700, source: null} : null;
    },
    'DK': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? {value: 700, source: null} : null;
    },
    'EE': function (productionMode) {
        if (productionMode == 'oil') {
            // Estonian Shale Oil LCA emissions. Source: Issue #278; EASAC (2007) "A study on the EU oil shale industry – viewed in the light of the Estonian experience",
            return {value: 1515, source: 'EASAC 2007'};
        } else if (productionMode == 'unknown' || productionMode == 'other') {
            return {value: 700, source: null};
        };
    },
    'FI': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? {value: 700, source: null} : null;
    },
    'GB': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? {value: 300, source: null} : null;
    },
    'NO': function (productionMode) {
        if (productionMode == 'hydro') {
            // Source: Ostford Research (2015) "The inventory and life cycle data for Norwegian hydroelectricity"
            return {value: 1.9, source: 'Ostford Research 2015'};
        } else if (productionMode == 'unknown' || productionMode == 'other') {
            return {value: 700, source: null};
        };
    },
    'SE': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? {value: 700, source: null} : null;
    }
};

exports.footprintOf = function(productionMode, countryKey) {
    var defaultFootprint = {value: defaultCo2eqFootprint[productionMode], source: defaultCo2eqSource};
    var countryFootprint = countryCo2eqFootprint[countryKey] || function () { };
    var item = countryFootprint(productionMode) || defaultFootprint;
    return (item || {}).value;
};
exports.sourceOf = function(productionMode, countryKey) {
    var defaultFootprint = {value: defaultCo2eqFootprint[productionMode], source: defaultCo2eqSource};
    var countryFootprint = countryCo2eqFootprint[countryKey] || function () { };
    var item = countryFootprint(productionMode) || defaultFootprint;
    return (item || {}).source;
}
