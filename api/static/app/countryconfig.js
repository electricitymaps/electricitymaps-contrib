function addCountryConfiguration(countries) {
    countries['DE'].data.capacity = {
        biomass: 8970,
        coal: 28310 + 21140,
        gas: 28490,
        hydro: 5590,
        nuclear: 10790,
        oil: 4240,
        solar: 39630,
        wind: 3740 + 42460,
    };
    countries['DK'].data.capacity = {
        hydro: 0,
        nuclear: 0,
        solar: 790,
        wind: 5070,
    };
    countries['ES'].data.capacity = {
        coal: 11482,
        gas: 3498 + 27206,
        hydro: 17787 + 2106,
        nuclear: 7866,
        solar: 4672 + 2300,
        wind: 23002,
    };
    countries['FI'].data.capacity = {
        hydro: 3080,
        nuclear: 2860,
        wind: 1000
    };
    countries['FR'].data.capacity = {
        nuclear: 63130,
        oil: 6670,
        coal: 2930,
        hydro: 10326 + 8204 + 4965,
        gas: 6121,
        wind: 10358,
        solar: 6580
    };
    countries['GB'].data.capacity = {
        wind: 13500,
        nuclear: 9000,
        hydro: 1550,
        gas: 38000,
        solar: 8780
    };
    countries['NO'].data.capacity = {
        hydro: 31000,
        nuclear: 0,
        solar: 0,
        wind: 856,
    };
    countries['SE'].data.capacity = {
        hydro: 16200,
        nuclear: 8849,
        solar: 79,
        wind: 6025
    };
}
