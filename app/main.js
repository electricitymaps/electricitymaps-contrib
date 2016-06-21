var co2color = d3.scale.linear()
    .domain([0, 250, 500])
    .range(['green', 'orange', 'black']);
var maxWind = 15;
var windColor = d3.scale.linear()
    .domain(d3.range(0, 11).map( function (i) { return d3.interpolate(0, maxWind)(i / 10.0); } ))
    .range([
        "rgba(0, 255, 255, 0.5)",
        "rgba(100, 240, 255, 0.5)",
        "rgba(135, 225, 255, 0.5)",
        "rgba(160, 208, 255, 0.5)",
        "rgba(181, 192, 255, 0.5)",
        "rgba(198, 173, 255, 0.5)",
        "rgba(212, 155, 255, 0.5)",
        "rgba(225, 133, 255, 0.5)",
        "rgba(236, 109, 255, 0.5)",
        "rgba(255, 30, 219, 0.5)"
    ])
    .clamp(true);
var solarColor = d3.scale.linear()
    .range(['black', 'orange'])
    .domain([300, 440]);

// Set up objects
var countryMap = new CountryMap('.map', co2color);
var exchangeLayer = new ExchangeLayer('.map');
var countryTable = new CountryTable('.country-table', co2color);
var windLayer = new Windy({ canvas: d3.select('.wind').node() });

var co2Colorbar = new HorizontalColorbar('.co2-colorbar', co2color)
    .markerColor('black');
var windColorbar = new HorizontalColorbar('.wind-colorbar', windColor)
    .markerColor('black');

var co2eqCalculator = new Co2eqCalculator();

// TODO: Name properly
var canvas = d3.select('.wind');
var width = window.innerWidth;
var height = window.innerHeight;
canvas.attr('height', height);
canvas.attr('width', width);

var solarCanvas = d3.select('.solar');
solarCanvas.attr('height', height);
solarCanvas.attr('width', width);

if (solarCanvas.node()) {
    var ctx = solarCanvas.node().getContext('2d');
}

// Prepare data
var countries = {};

// Events
function windMouseOver(coordinates) {
    if (windLayer.field && coordinates) {
        var wind = windLayer.field(coordinates[0], coordinates[1]);
        windColorbar.currentMarker(wind[2]);
    } else {
        windColorbar.currentMarker(undefined);
    }
}

// Attach events
d3.select('.map')
    .on('mousemove', function() {
        windMouseOver(d3.mouse(this));
    })
    .on('mouseout', function() {
        windMouseOver(undefined);
    });
countryTable
    .onExchangeMouseOver(function (d, countryCode) {
        var co2 = countries[d.value < 0 ? countryCode : d.key].data.co2;
        co2Colorbar.currentMarker(co2);
    })
    .onExchangeMouseOut(function (d) {
        co2Colorbar.currentMarker(undefined);
    })
    .onProductionMouseOver(function (d, countryCode) {
        var co2 = co2eqCalculator.footprintOf(d.mode, countryCode);
        co2Colorbar.currentMarker(co2);
    })
    .onProductionMouseOut(function (d) {
        co2Colorbar.currentMarker(undefined);
    });

function dataLoaded(err, countryTopos, production, solar, wind) {
    if (err) {
        console.error(err);
        return;
    }

    console.log('wind', wind);
    var sw = countryMap.projection().invert([0, height]);
    var ne = countryMap.projection().invert([width, 0]);
    windLayer.params.data = wind;
    windLayer.start(
        [[0, 0], [width, height]], 
        width,
        height,
        [sw, ne]
    );

    console.log('solar', solar);
    if (ctx) {
        // Interpolates between two solar forecasts
        var Nx = solar.forecasts[0].DLWRF.length;
        var Ny = solar.forecasts[0].DLWRF[0].length;
        var t_before = d3.time.format.iso.parse(solar.forecasts[0].horizon).getTime();
        var t_after = d3.time.format.iso.parse(solar.forecasts[1].horizon).getTime();
        var now = (new Date()).getTime();
        console.log('solar updated', moment(now).fromNow());
        if (moment(now) > moment(solar.forecasts[1].horizon)) {
            console.error('Error while interpolating solar because current time is out of bounds');
        }
        var k = (now - t_before)/(t_after - t_before);
        for (var i of d3.range(Nx)) {
            for (var j of d3.range(Ny)) {
                var n = i * Ny + j;
                var lon = solar.forecasts[0].lonlats[0][n];
                var lat = solar.forecasts[0].lonlats[1][n];
                var val = d3.interpolate(solar.forecasts[0].DLWRF[i][j], solar.forecasts[1].DLWRF[i][j])(k);
                var p = countryMap.projection()([lon, lat]);
                if (isNaN(p[0]) || isNaN(p[1]))
                    continue;
                ctx.beginPath();
                ctx.arc(p[0], p[1], 2, 0, 2 * Math.PI);
                ctx.fillStyle = solarColor(val);
                ctx.fill();
            }
        }
    }

    var topo = topojson.object(countryTopos, countryTopos.objects.europe).geometries;

    countries['AT'] = topo[3];
    countries['BE'] = topo[4];
    countries['BG'] = topo[5];
    countries['BA'] = topo[6];
    countries['BY'] = topo[7];
    countries['CH'] = topo[8];
    countries['CZ'] = topo[9];
    countries['DE'] = topo[10];
    countries['DK'] = topo[11];
    countries['ES'] = topo[12];
    countries['EE'] = topo[13];
    countries['FI'] = topo[14];
    countries['FR'] = topo[15];
    countries['GB'] = topo[17];
    countries['GR'] = topo[20];
    countries['HR'] = topo[21];
    countries['HU'] = topo[22];
    countries['IE'] = topo[24];
    countries['IS'] = topo[25];
    countries['IT'] = topo[26];
    countries['LT'] = topo[30];
    countries['LU'] = topo[31];
    countries['LV'] = topo[32];
    countries['MD'] = topo[34];
    countries['NL'] = topo[38];
    countries['NO'] = topo[39];
    countries['PL'] = topo[40];
    countries['PT'] = topo[41];
    countries['RO'] = topo[42];
    countries['RU'] = topo[43];
    countries['RS'] = topo[45];
    countries['SK'] = topo[46];
    countries['SI'] = topo[47];
    countries['SE'] = topo[48];
    countries['UA'] = topo[49];

    // Add empty fields
    d3.keys(countries).forEach(function (countryCode) {
        countries[countryCode].data = {};
        countries[countryCode].data.capacity = {};
        countries[countryCode].data.exchange = {};
        countries[countryCode].data.neighborCo2 = {};
    });

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

    // Prepare exchanges
    var exchanges = [
        {
            countries: ['DE', 'DK'],
            lonlat: [9.3, 54.9],
            rotation: 0
        },
        {
            countries: ['SE', 'DK'],
            lonlat: [13, 55.7],
            rotation: -100
        },
        {
            countries: ['GB', 'FR'],
            lonlat: [0, 50.4],
            rotation: 160
        },
        {
            countries: ['DK', 'NO'],
            lonlat: [8.8, 58],
            rotation: -25
        },
        {
            countries: ['IE', 'GB'],
            lonlat: [-5.7, 53],
            rotation: 100
        },
        {
            countries: ['NL', 'GB'],
            lonlat: [3.3, 52.4],
            rotation: -90
        },
        {
            countries: ['FR', 'ES'],
            lonlat: [0.3, 42.9],
            rotation: -160
        },
        {
            countries: ['FR', 'DE'],
            lonlat: [5.7, 49.8],
            rotation: 50
        },
        {
            countries: ['FR', 'CH'],
            lonlat: [6.5, 46.7],
            rotation: 90
        },
        {
            countries: ['FR', 'IT'],
            lonlat: [6.5, 44.5],
            rotation: 70
        }
    ];

    // Populate with realtime production data
    for (var countryCode of d3.keys(production.data)) {
        var obj = production.data[countryCode];
        var country = countries[countryCode];
        if (!country) {
            console.warn(countryCode + ' has no country definition.');
            continue;
        }
        for (var k of d3.keys(obj))
            country.data[k] = obj[k];
        // Add own country code so each country is identifiable
        country.data.countryCode = countryCode;
        countryTable.PRODUCTION_MODES.forEach(function (mode) {
            if (mode == 'other') return;
            if (country.data.production[mode] === undefined)
                console.warn(countryCode + ' is missing production of ' + mode);
            else if (country.data.capacity[mode] === undefined)
                console.warn(countryCode + ' is missing capacity of ' + mode);
        });
        if (!country.data.exchange || !d3.keys(country.data.exchange).length)
            console.warn(countryCode + ' is missing exchanges');
    }

    // Populate exchange pairs for arrows
    exchanges.forEach(function (pair) {
        var o = pair.countries[0];
        var d = pair.countries[1];
        var netFlows = [
            countries[d].data.exchange[o],
            -countries[o].data.exchange[d]
        ];
        pair.netFlow = d3.mean(netFlows);
        pair.co2 = function () {
            return pair.countries.map(function (k) { return countries[k].data.co2; });
        };
        countries[o].data.exchange[d] = -pair.netFlow;
        countries[d].data.exchange[o] = pair.netFlow;
        countries[o].data.neighborCo2[d] = countries[d].data.co2;
        countries[d].data.neighborCo2[o] = countries[o].data.co2;
    });

    // Compute aggregates
    d3.entries(countries).forEach(function (entry) {
        country = entry.value;
        // Add extra data
        country.data.maxCapacity = 
            d3.max(d3.values(country.data.capacity));
        country.data.maxProduction = 
            d3.max(d3.values(country.data.production));
        country.data.totalProduction = 
            d3.sum(d3.values(country.data.production));
        country.data.totalNetExchange = 
            d3.sum(d3.values(country.data.exchange));
        country.data.maxExport = 
            -Math.min(d3.min(d3.values(country.data.exchange)), 0) || 0;
    });


    // Compute CO2
    d3.entries(co2eqCalculator.compute(countries).assignments).forEach(function (entry) {
        var country = countries[entry.key];
        // Assign co2
        country.data.co2 = entry.value;
        // Add co2 to each neighboring country
        country.data.neighborCo2 = {};
        d3.keys(country.data.exchange).forEach(function (k) {
            if (!countries[k])
                console.error(entry.key + ' neighbor ' + k + ' could not be found');
            country.data.neighborCo2[k] = function() {
                return countries[k].data.co2;
            };
        });
        // Display warnings for missing data
        if (country.data.co2 === undefined)
            console.warn(entry.key + ' is missing co2 footprint');
    });

    // Issue warnings for missing exchange configurations
    for (var countryCode of d3.keys(production.data)) {
        var country = countries[countryCode]
        if (!country) continue;
        d3.keys(country.data.exchange).forEach(function (sourceCountryCode) {
            // Find the exchange object
            var matches = exchanges.filter(function (e) { 
                return (e.countries[0] == countryCode && e.countries[1] == sourceCountryCode) || (e.countries[1] == countryCode && e.countries[0] == sourceCountryCode)
            });
            if (!matches.length)
                console.warn('Missing exchange configuration between ' + sourceCountryCode + ' and ' + countryCode);
        });
    }

    console.log('countries', countries);
    console.log('exchanges', exchanges);
    console.log('wind updated', moment(wind[0].header.refTime).fromNow());

    countryMap
        .data(d3.values(countries))
        .onCountryClick(function (d, i) {
            if (!d.data.production) return;
            countryTable
                .powerDomain([-d.data.maxExport, Math.max(d.data.maxCapacity, d.data.maxProduction)])
                .data(d.data);
        })
        .onCountryMouseOver(function (d) { 
            if (d.data.production)
                d3.select(this)
                    .style('opacity', 0.8)
                    .style('cursor', 'hand')
            if (d.data.co2)
                co2Colorbar.currentMarker(d.data.co2);
        })
        .onCountryMouseOut(function (d) { 
            if (d.data.production) 
                d3.select(this)
                    .style('opacity', 1)
                    .style('cursor', 'normal')
            if (d.data.co2)
                co2Colorbar.currentMarker(undefined);
        })
        .render();

    exchangeLayer
        .data(exchanges)
        .projection(countryMap.projection())
        .render();

    d3.select('.loading')
        .transition()
        .style('opacity', 0);
};

// Periodically load data
var REFRESH_TIME_MINUTES = 5;
function fetchAndReschedule() {
    queue()
        .defer(d3.json, 'http://localhost:8000/data/europe.topo.json')
        .defer(d3.json, 'http://localhost:8000/production')
        .defer(d3.json, 'http://localhost:8000/solar')
        .defer(d3.json, 'http://localhost:8000/wind')
        .await(dataLoaded);
    setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
}

function redraw() {
    countryMap.render();
    countryTable.render();
    exchangeLayer
        .projection(countryMap.projection())
        .render();
};

window.onresize = function () {
    redraw();
};

redraw();
fetchAndReschedule();
