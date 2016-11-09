function addCountryConfiguration(countries) {
    countries['AT'].capacity = {
        biomass: 393,
        coal: 819,
        gas: 4187,
        hydro: 3622 + 2271 + 5161,
        oil: 288,
        solar: 814,
        wind: 2306,
    };
    countries['BE'].capacity = {
        biomass: 710 + 368,
        nuclear: 5919,
        oil: 145,
        coal: 470,
        hydro: 1308 + 117,
        gas: 5303,
        wind: 1249 + 712,
        solar: 2953,
    };
    countries['CZ'].capacity = {
        biomass: 350,
        coal: 380 + 1200 + 8334,
        gas: 1226,
        hydro: 1172 + 650 + 431,
        nuclear: 4040,
        oil: 0,
        solar: 2067,
        wind: 277,
    };
    countries['DE'].capacity = {
        biomass: 6609 + 1581,
        coal: 28670 + 22015,
        gas: 26694 + 73,
        hydro: 8644 + 3749 + 539,
        nuclear: 10952,
        oil: 3745,
        solar: 38994,
        wind: 3256 + 39937,
    };
    countries['DK'].capacity = {
        biomass: 197,
        coal: 4847,
        gas: 2941,
        hydro: 0,
        nuclear: 0,
        solar: 601,
        wind: 3574 + 1271,
    };
    countries['EE'].capacity = {
        biomass: 77 + 20,
        coal: 0,
        gas: 86 + 119,
        hydro: 0,
        oil: 1975,
        nuclear: 0,
        solar: 1,
        wind: 375 ,
    };
    countries['ES'].capacity = {
        coal: 11482,
        gas: 3498 + 27206,
        hydro: 17787 + 2106,
        nuclear: 7866,
        solar: 4672 + 2300,
        wind: 23002,
    };
    countries['FI'].capacity = {
        hydro: 3080,
        nuclear: 2860,
        wind: 1000
    };
    countries['FR'].capacity = {
        nuclear: 63130,
        oil: 6670,
        coal: 2930,
        hydro: 10326 + 8204 + 4965,
        gas: 6121,
        wind: 10358,
        solar: 6580
    };
    countries['GB'].capacity = {
        wind: 13500,
        nuclear: 9000,
        hydro: 1550,
        gas: 38000,
        solar: 8780
    };
    countries['GR'].capacity = {
        biomass: 51,
        coal: 3912,
        hydro: 699 + 2403 + 299,
        oil: 0,
        nuclear: 0,
        unknown: 69,
        gas: 5396,
        wind: 1875,
        solar: 2441,
    };
    countries['HU'].capacity = {
        biomass: 246 + 28,
        coal: 1007,
        gas: 4124,
        hydro: 28 + 29,
        nuclear: 1887,
        oil: 410,
        solar: 29,
        wind: 328,
    };  
    countries['IE'].capacity = {
        biomass: 344,
        oil: 811,
        coal: 855,
        hydro: 292 + 216,
        nuclear: 0,
        gas: 3801,
        unknown: 647,
        solar: 0,
        wind: 1920,
    };
     countries['IT'].capacity = {
        hydro: 22382,
        nuclear: 0,
        solar: 18420,
        wind: 8561,
    };
    countries['LT'].capacity = {
        biomass: 65 + 21,
        gas: 1719,
        hydro: 900 + 128, 
        oil: 160,
        solar: 69,
        wind: 366,
    };
    countries['LV'].capacity = {
        biomass: 102,
        gas: 1103,
        hydro: 1537,
        wind: 55,
    };
    countries['NO'].capacity = {
        hydro: 31000,
        nuclear: 0,
        solar: 0,
        wind: 856,
    };
    countries['PL'].capacity = {
        biomass: 435,
        oil: 345,
        coal: 18479 + 8483,
        hydro: 1770 + 156 + 395,
        nuclear: 0,
        gas: 158 + 1302,
        wind: 5494,
        solar: 77,
    };
     countries['PT'].capacity = {
        biomass: 582,
        oil: 0,
        coal: 1756,
        gas: 4695,
        hydro: 1623 + 1511 + 2987,
        nuclear: 0,
        solar: 251,
        wind: 4617,
    };    
    countries['RO'].capacity = {
        biomass: 95,
        coal: 1348 + 4546,
        gas: 4879,
        hydro: 2697 + 4006,
        nuclear: 1298,
        solar: 1152,
        wind: 2938,
    };
    countries['SE'].capacity = {
        hydro: 16200,
        nuclear: 8849,
        solar: 79,
        wind: 6025
    };
    countries['SI'].capacity = {
        biomass: 17 + 40,
        nuclear: 696,
        coal: 921,
        oil: 0,
        hydro: 180 + 1053,
        gas: 491,
        wind: 3,
        solar: 263,
    };
}
