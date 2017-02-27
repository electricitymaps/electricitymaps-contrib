var exports = module.exports = {};

if (__base) module.paths.push(__base + '/node_modules');
var d3 = require('d3');
var mathjs = require('mathjs');

exports.compute = function(countries) {
    var validCountries = d3.values(countries)
        .filter(function (d) { return d.countryCode && d.production; })
        .filter(function (d) {
            // Double check that total production + import >= export
            return (d.totalProduction + d.totalImport) >= d.totalExport &&
                d.totalProduction > 0;
        });
    var validCountryKeys = validCountries.map(function (d) { return d.countryCode });
    
    // We wish to solve Ax = b
    // See co2eq.js
    var n = validCountries.length;
    var A = mathjs.sparse().resize([n, n]);
    var b = mathjs.zeros(n);

    validCountries.forEach(function (country, i) {
        // Note that `totalProduction` is the sum of all *positive* production
        // which excludes all storage units
        A.set([i, i], country.totalProduction + country.totalImport);
        // Production
        d3.entries(country.production).forEach(function (production) {
            var footprint = 
                (production.key == 'coal' || 
                production.key == 'gas' || 
                production.key == 'oil') ? 1 : 0;
            // Accumulate
            b.set([i], b.get([i]) + footprint * production.value);
        });
        // Exchanges
        if (country.exchange) {
            d3.entries(country.exchange).forEach(function (exchange) {
                // Only look at imports (exports cancel out)
                if (exchange.value > 0) {
                    var j = validCountryKeys.indexOf(exchange.key);
                    if (j < 0) {
                        // The country we're importing from is not one
                        // we're solving for.
                        // Let's therefore give it the footprint of this country.
                        A.set([i, i], A.get([i, i]) - exchange.value);
                    } else {
                        A.set([i, j], -exchange.value);
                    }
                }
            });
        }
    });

    // Solve
    var x = mathjs.lusolve(A, b);
    var assignments = {};
    x.toArray().forEach(function (x, i) {
        assignments[validCountries[i].countryCode] = x[0];
    });

    return assignments;
}
