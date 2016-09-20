function addCountryConfiguration(countries) {
    countries['AT'].data.capacity = {
        biomass: 393,
        coal: 819,
        gas: 4187,
        hydro: 3622 + 2271 + 5161,
        oil: 288,
        solar: 814,
        wind: 2306,
    };
    countries['DE'].data.capacity = {
        biomass: 6609 + 1581,
        coal: 28670 + 22015,
        gas: 26694 + 73,
        hydro: 8644 + 3749 + 539,
        nuclear: 10952,
        oil: 3745,
        solar: 38994,
        wind: 3256 + 39937,
    };
    countries['DK'].data.capacity = {
        biomass: 197,
        coal: 4847,
        gas: 2941,
        hydro: 0,
        nuclear: 0,
        solar: 601,
        wind: 3574 + 1271,
    };
    countries['EE'].data.capacity = {
        biomass: 77 + 20,
        coal: 0,
        gas: 86 + 119,
        hydro: 0,
        oil: 1975,
        nuclear: 0,
        solar: 1,
        wind: 375 ,
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
    countries['HU'].data.capacity = {
        biomass: 246 + 28,
        coal: 1007,
        gas: 4124,
        hydro: 28 + 29,
        nuclear: 1887,
        oil: 410,
        solar: 29,
        wind: 328,
    };  
    countries['LT'].data.capacity = {
        biomass: 65 + 21,
        gas: 1719,
        hydro: 900 + 128, 
        oil: 160,
        solar: 69,
        wind: 366,
    };
    countries['LV'].data.capacity = {
        biomass: 102,
        gas: 1103,
        hydro: 1537,
        wind: 55,
    };
    countries['NO'].data.capacity = {
        hydro: 31000,
        nuclear: 0,
        solar: 0,
        wind: 856,
    };
    countries['RO'].data.capacity = {
        biomass: 95,
        coal: 1348 + 4546,
        gas: 4879,
        hydro: 2697 + 4006,
        nuclear: 1298,
        solar: 1152,
        wind: 2938,
    };
    countries['SE'].data.capacity = {
        hydro: 16200,
        nuclear: 8849,
        solar: 79,
        wind: 6025
    };
    countries['PT'].data.capacity = {
        hydro: 5815,
        solar: 57,
        wind: 4730
    };    
}
