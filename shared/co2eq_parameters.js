var exports = module.exports = {};

defaultCo2eqFootprint = {
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

countryCo2eqFootprint = {
    'DE': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? 700 : null;
    },
    'DK': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? 700 : null;
    },
    'EE': function (productionMode) {
        return (productionMode == 'oil') ? 1515 : null; // Estonian Shale Oil LCA emissions. Source: Issue #278; EASAC (2007) "A study on the EU oil shale industry – viewed in the light of the Estonian experience",
    },
    'FI': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? 700 : null;
    },
    'GB': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? 300 : null;
    },
    'NO': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? 700 : null;
    },
    'SE': function (productionMode) {
        return (productionMode == 'unknown' || productionMode == 'other') ? 700 : null;
    }
};

exports.footprintOf = function(productionMode, countryKey) {
    var defaultFootprint = defaultCo2eqFootprint[productionMode];
    var countryFootprint = countryCo2eqFootprint[countryKey] || function () { };
    return countryFootprint(productionMode) || defaultFootprint;
};
