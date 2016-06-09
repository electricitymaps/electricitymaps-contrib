var co2Footprint = {
    'biomass': 900,
    'coal': 930,
    'gas': 400,
    'hydro': 0,
    'nuclear': 0,
    'oil': 650,
    'solar': 0,
    'wind': 0,
};

function computeCO2(countries) {
    // Only consider countries which have a co2 rating
    var validCountries = d3.entries(countries)
        .map(function(d) { return d.value.data })
        .filter(function (d) {
            return d.countryCode !== undefined;
        });
    var validCountryKeys = validCountries.map(function (d) { return d.countryCode });

    // x_i: unknown co2 (consumption) footprint of i-th country
    // f_ij: known co2 footprint of j-th system of i-th country
    // v_ij: power volume of j-th system of i-th country
    // CO2 mass flow balance equation for each country i:
    // x_i * (sum_j_intern(v_ij) + sum_j_import(v_ij) - sum_j_export(v_ij)) = 
    //     sum_j_intern(f_ij * v_ij)
    //   + sum_j_import(x_j * v_ij)
    //   - x_i * sum_j_export(v_ij)
    
    // We wish to solve Ax = b
    var n = validCountries.length;
    var A = math.sparse().resize([n, n]);
    var b = math.zeros(n);

    validCountries.forEach(function (country, i) {
        A.set([i, i], -country.totalProduction - country.totalNetExchange);
        // Intern
        d3.entries(country.production).forEach(function (production) {
            if (co2Footprint[production.key] === undefined) {
                console.warn(country.countryCode + ' CO2 footprint of ' + production.key + ' is unknown.');
                return;
            }
            // Accumulate
            b.set([i], b.get([i]) - co2Footprint[production.key] * production.value);
        });
        // Exchanges
        d3.entries(country.exchange).forEach(function (exchange) {
            var j = validCountryKeys.indexOf(exchange.key);
            if (j < 0) {
                console.warn(country.countryCode + ' neighbor ' + exchange.key + ' was not found.');
                return;
            }
            // Accumulate
            if (exchange.value > 0) {
                // Import
                A.set([i, j], exchange.value);
            } else {
                // Export
                A.set([i, i], A.get([i, 0]) - Math.abs(exchange.value));
            }
        });
    });
    
    console.log('A', JSON.stringify(A.toArray()));
    console.log('b', JSON.stringify(b));

    // Solve
    var x = math.lusolve(A, b);
    console.log('x', JSON.stringify(x));
    x.toArray().forEach(function (x, i) {
        console.log(validCountries[i].countryCode, x, validCountries[i].co2);
    });
    return x;
}
