var exports = module.exports = {};

var defaultCo2eqSource = 'IPCC 2014';

var defaultCo2eqSourceUnknown = 'assumes thermal (coal, gas, oil or biomass)';

var defaultCo2eqFootprint = { // in gCo2eq/kWh
    'biomass': {
      'value': 230,
      'source': defaultCo2eqSource
    },
    'coal': {
      'value': 820,
      'source': defaultCo2eqSource
    },
    'gas': {
      'value': 490,
      'source': defaultCo2eqSource
    },
    'hydro': {
      'value': 24,
      'source': defaultCo2eqSource
    },
    'hydro discharge': { // This applies to discharge only
      'value': 24,
      'source': defaultCo2eqSource
    },
    'battery discharge': { // This applies to discharge only
      'value': 0,
      'source': 'TODO'
    },
    'nuclear': {
      'value': 12,
      'source': defaultCo2eqSource
    },
    'oil': {
      'value': 650,
      'source': 'UK POST 2014' // UK Parliamentary Office of Science and Technology (2006) "Carbon footprint of electricity generation"
    },
    'solar': {
      'value': 45,
      'source': defaultCo2eqSource
    },
    'wind': {
      'value': 11,
      'source': defaultCo2eqSource
    },
    'geothermal': {
      'value': 38,
      'source': defaultCo2eqSource
    },
    'unknown': {
      'value': 700, // assume conventional
      'source': defaultCo2eqSourceUnknown
    },
    'other': {
      'value': 700, // // same as 'unknown'. Here for backward compatibility
      'source': defaultCo2eqSourceUnknown
    }
};

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
    'NO': function (productionMode) {
        if (productionMode == 'hydro') {
            // Source: Ostford Research (2015) "The inventory and life cycle data for Norwegian hydroelectricity"
            return {value: 1.9, source: 'Ostford Research 2015'};
        } else if (productionMode == 'unknown' || productionMode == 'other') {
            return {value: 700, source: null};
        };
    },
    'SE': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? {value: 362, source: 'assumes 72% biomass, 28% conventional thermal'} : null;
    }
};

exports.footprintOf = function(productionMode, countryKey) {
    var defaultFootprint = defaultCo2eqFootprint[productionMode];
    var countryFootprint = countryCo2eqFootprint[countryKey] || function () { };
    var item = countryFootprint(productionMode) || defaultFootprint;
    return (item || {}).value;
};
exports.sourceOf = function(productionMode, countryKey) {
    var defaultFootprint = defaultCo2eqFootprint[productionMode];
    var countryFootprint = countryCo2eqFootprint[countryKey] || function () { };
    var item = countryFootprint(productionMode) || defaultFootprint;
    return (item || {}).source;
}
