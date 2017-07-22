var exports = module.exports = {};

var defaultCo2eqSource = 'IPCC 2014';

var defaultCo2eqFootprint = { // in gCo2eq/kWh
    'biomass': {
      'co2eq': 230,
      'source': defaultCo2eqSource
    },
    'coal': {
      'co2eq': 820,
      'source': defaultCo2eqSource
    },
    'gas': {
      'co2eq': 490,
      'source': defaultCo2eqSource
    },
    'hydro': {
      'co2eq': 24,
      'source': defaultCo2eqSource
    },
    'nuclear': {
      'co2eq': 12,
      'source': defaultCo2eqSource
    },
    'oil': {
      'co2eq': 650,
      'source': 'UK POST 2014' // UK Parliamentary Office of Science and Technology (2006) "Carbon footprint of electricity generation"
    },
    'solar': {
      'co2eq': 45,
      'source': defaultCo2eqSource
    },
    'wind': {
      'co2eq': 12,
      'source': defaultCo2eqSource
    },
    'geothermal': {
      'co2eq': 38,
      'source': defaultCo2eqSource
    },
    'unknown': {
      'co2eq': 700, // assume conventional
      'source': defaultCo2eqSource
    },
    'other': {
      'co2eq': 700, // // same as 'unknown'. Here for backward compatibility
      'source': defaultCo2eqSource
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
    var defaultFootprint = {value: defaultCo2eqFootprint[productionMode]['co2eq'], source: defaultCo2eqFootprint[productionMode]['source']};
    var countryFootprint = countryCo2eqFootprint[countryKey] || function () { };
    var item = countryFootprint(productionMode) || defaultFootprint;
    return (item || {}).value;
};
exports.sourceOf = function(productionMode, countryKey) {
    var defaultFootprint = {value: defaultCo2eqFootprint[productionMode]['co2eq'], source: defaultCo2eqFootprint[productionMode]['source']};
    var countryFootprint = countryCo2eqFootprint[countryKey] || function () { };
    var item = countryFootprint(productionMode) || defaultFootprint;
    return (item || {}).source;
}
