// read querystring args
nobrowsercheck = false;
force_remote_endpoint = false;
args = location.search.replace('\?','').split('&');
args.forEach(function(arg) {
    kv = arg.split('=');
    if (kv[0] == 'nobrowsercheck' && kv[1] == '1') {
        nobrowsercheck = true;
    } else if (kv[0] == 'remote' && kv[1] == 'true') {
        force_remote_endpoint = true;
    }
});

var isMobile = function() {
    return (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent);
}

if (!nobrowsercheck && !isChrome()) {
    // show force-chrome overlay
    document.getElementById('force-chrome-overlay').style.display = "flex";
} else {
    // load all
    var REMOTE_ENDPOINT = 'http://electricitymap-api.tmrow.co';
    var ENDPOINT = (document.domain == 'localhost' && !force_remote_endpoint) ?
        'http://localhost:8000' : REMOTE_ENDPOINT;

    var co2color = d3.scale.linear()
        .domain([0, 350, 700])
        .range(['green', 'orange', 'black']);
    var maxWind = 15;
    var windColor = d3.scale.linear()
        .domain(d3.range(10).map( function (i) { return d3.interpolate(0, maxWind)(i / (10 - 1)); } ))
        .range([
            "rgba(0,   255, 255, 0.5)",
            "rgba(100, 240, 255, 0.5)",
            "rgba(135, 225, 255, 0.5)",
            "rgba(160, 208, 255, 0.5)",
            "rgba(181, 192, 255, 0.5)",
            "rgba(198, 173, 255, 0.5)",
            "rgba(212, 155, 255, 0.5)",
            "rgba(225, 133, 255, 0.5)",
            "rgba(236, 109, 255, 0.5)",
            "rgba(255,  30, 219, 0.5)"
        ]);
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

    // State
    var tableDisplayEmissions = countryTable.displayByEmissions();

    function toogleSource() {
        tableDisplayEmissions = !tableDisplayEmissions;
        countryTable
            .displayByEmissions(tableDisplayEmissions);
        d3.select('.country-show-emissions')
            .style('display', tableDisplayEmissions ? 'none' : 'block');
        d3.select('.country-show-electricity')
            .style('display', tableDisplayEmissions ? 'block' : 'none');
    }

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

    // Mobile
    if (isMobile()) {
        d3.select('.map').selectAll('*').remove();
        d3.select('.legend').style('display', 'none');

        function onSelectedCountryChange() {
            var countryCode = d3.select('select.country-picker').node().value;
            if (countries[countryCode]) {
                d3.select('.country-table-initial-text')
                    .style('display', 'none');
                countryTable
                    .show()
                    .data(countries[countryCode].data);
                d3.select('select.country-picker').node().selectedIndex = 0;
            }
        }
    } else {
        d3.select('.panel-container')
            .style('width', 360);
        d3.select('.country-picker')
            .style('display', 'none');

        // Attach event handlers
        function windMouseOver(coordinates) {
            if (windLayer.field && coordinates) {
                var wind = windLayer.field(coordinates[0], coordinates[1]);
                windColorbar.currentMarker(wind[2]);
            } else {
                windColorbar.currentMarker(undefined);
            }
        }
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
    }

    function dataLoaded(err, countryTopos, production, solar, wind) {
        if (err) {
            console.error(err);
            return;
        }

        if (!isMobile()) {
            console.log('wind', wind);
            var t_before = moment(wind.forecasts[0][0].header.refTime).add(wind.forecasts[0][0].header.forecastTime, 'hours');
            var t_after = moment(wind.forecasts[1][0].header.refTime).add(wind.forecasts[1][0].header.forecastTime, 'hours');
            console.log('#1 wind forecast target', 
                t_before.fromNow(),
                'made', moment(wind.forecasts[0][0].header.refTime).fromNow());
            console.log('#2 wind forecast target',
                t_after.fromNow(),
                'made', moment(wind.forecasts[1][0].header.refTime).fromNow());
            // Interpolate wind
            var now = (new Date()).getTime();
            var interpolatedWind = wind.forecasts[0];
            if (moment(now) > moment(t_after)) {
                console.error('Error while interpolating wind because current time is out of bounds');
            } else {
                var k = (now - t_before)/(t_after - t_before);
                interpolatedWind[0].data = interpolatedWind[0].data.map(function (d, i) {
                    return d3.interpolate(d, wind.forecasts[1][0].data[i])(k)
                });
                interpolatedWind[1].data = interpolatedWind[1].data.map(function (d, i) {
                    return d3.interpolate(d, wind.forecasts[1][1].data[i])(k)
                });
                var sw = countryMap.projection().invert([0, height]);
                var ne = countryMap.projection().invert([width, 0]);
                windLayer.params.data = interpolatedWind;
                windLayer.start(
                    [[0, 0], [width, height]], 
                    width,
                    height,
                    [sw, ne]
                );
            }

            console.log('solar', solar);
            if (ctx) {
                // Interpolates between two solar forecasts
                var Nx = solar.forecasts[0].DSWRF.length;
                var Ny = solar.forecasts[0].DSWRF[0].length;
                var t_before = d3.time.format.iso.parse(solar.forecasts[0].horizon).getTime();
                var t_after = d3.time.format.iso.parse(solar.forecasts[1].horizon).getTime();
                var now = (new Date()).getTime();
                console.log('#1 solar forecast target', 
                    moment(t_before).fromNow(),
                    'made', moment(solar.forecasts[0].date).fromNow());
                console.log('#2 solar forecast target',
                    moment(t_after).fromNow(),
                    'made', moment(solar.forecasts[1].date).fromNow());
                if (moment(now) > moment(solar.forecasts[1].horizon)) {
                    console.error('Error while interpolating solar because current time is out of bounds');
                } else {
                    var k = (now - t_before)/(t_after - t_before);
                    var dotSize = 1.0;
                    d3.range(Nx).forEach(function(i) {
                        d3.range(Ny).forEach(function(j) {
                            var n = i * Ny + j;
                            var lon = solar.forecasts[0].lonlats[0][n];
                            var lat = solar.forecasts[0].lonlats[1][n];
                            var val = d3.interpolate(solar.forecasts[0].DSWRF[i][j], solar.forecasts[1].DSWRF[i][j])(k);
                            var p = countryMap.projection()([lon, lat]);
                            if (isNaN(p[0]) || isNaN(p[1]))
                                return;
                            ctx.beginPath();
                            ctx.arc(p[0], p[1], dotSize, 0, 2 * Math.PI);
                            ctx.fillStyle = solarColor(val);
                            ctx.fill();
                        });
                    });
                }
            }
        }

        var topo = topojson.object(countryTopos, countryTopos.objects.europe).geometries;

        countries['AL'] = topo[0];
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
        countries['XK'] = topo[28];
        countries['LT'] = topo[30];
        countries['LU'] = topo[31];
        countries['LV'] = topo[32];
        countries['MD'] = topo[34];
        countries['MK'] = topo[35];
        countries['ME'] = topo[37];
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

        // Load country configs
        addCountryConfiguration(countries);

        // Populate with realtime production data
        d3.keys(production.data).forEach(function(countryCode) {
            var obj = production.data[countryCode];
            var country = countries[countryCode];
            if (!country) {
                console.warn(countryCode + ' has no country definition.');
                return;
            }
            d3.keys(obj).forEach(function(k) {
                country.data[k] = obj[k];
                // Cap to a minimum value of 0
                d3.keys(country.data[k]).forEach(function (mode) {
                    if (country.data[k][mode] < 0)
                        country.data[k][mode] = 0;
                });
            });
            // Add own country code so each country is identifiable
            country.data.countryCode = countryCode;
            // Validate data
            countryTable.PRODUCTION_MODES.forEach(function (mode) {
                if (mode == 'other' || mode == 'unknown') return;
                if (country.data.production[mode] === undefined)
                    console.warn(countryCode + ' is missing production of ' + mode);
                else if (country.data.capacity[mode] === undefined)
                    console.warn(countryCode + ' is missing capacity of ' + mode);
            });
            if (!country.data.exchange || !d3.keys(country.data.exchange).length)
                console.warn(countryCode + ' is missing exchanges');
        });

        // Populate exchange pairs for arrows
        var exchanges = []
        EXCHANGES_CONFIG.forEach(function (item) {
            // Shallow copy the configuration item
            var pair = {};
            d3.entries(item).forEach(function (d) {
                pair[d.key] = d.value;
            });
            var o = pair.countries[0];
            var d = pair.countries[1];
            var netFlows = [
                countries[d].data.exchange[o],
                -countries[o].data.exchange[d]
            ];
            pair.netFlow = d3.mean(netFlows);
            if (pair.netFlow === undefined)
                return;
            pair.co2 = function () {
                return pair.countries.map(function (k) { return countries[k].data.co2; });
            };
            exchanges.push(pair);

            countries[o].data.exchange[d] = -pair.netFlow;
            countries[d].data.exchange[o] = pair.netFlow;
        });

        console.log('exchanges', exchanges);

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
                if (k == 'datetime') return;
                if (!countries[k])
                    console.error(entry.key + ' neighbor ' + k + ' could not be found');
                else
                    country.data.neighborCo2[k] = function() {
                        return countries[k].data.co2;
                    };
            });
            // Display warnings for missing data
            if (country.data.co2 === undefined)
                console.warn(entry.key + ' is missing co2 footprint');
        });

        // Issue warnings for missing exchange configurations
        d3.keys(production.data).forEach(function(countryCode) {
            var country = countries[countryCode]
            if (!country) return;
            d3.keys(country.data.exchange).forEach(function (sourceCountryCode) {
                if (sourceCountryCode == 'datetime') return;
                // Find the exchange object
                var matches = exchanges.filter(function (e) {
                    return (e.countries[0] == countryCode && e.countries[1] == sourceCountryCode) || (e.countries[1] == countryCode && e.countries[0] == sourceCountryCode)
                });
                if (!matches.length)
                    console.warn('Missing exchange configuration between ' + sourceCountryCode + ' and ' + countryCode);
            });
        });

        console.log('countries', countries);

        countryMap
            .data(d3.values(countries))
            .onSeaClick(function () {
                d3.select('.country-table-initial-text')
                    .style('display', 'block');
                countryTable.hide();
            })
            .onCountryClick(function (d, i) {
                if (!d.data.production) {
                    countryMap.onSeaClick()();
                    return;
                };
                d3.select('.country-table-initial-text')
                    .style('display', 'none');
                countryTable
                    .show()
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
            .style('opacity', 0)
            .each('end', function () {
                d3.select(this).remove();
            });
    };

    // Get geolocation is on mobile (in order to select country)
    function geolocaliseCountryCode(callback) {
        // Deactivated for now (UX was confusing)
        callback(null, null);
        return;
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                d3.json('http://maps.googleapis.com/maps/api/geocode/json?latlng=' + position.coords.latitude + ',' + position.coords.longitude, function (err, response) {
                    if (err) {
                        console.warn(err);
                        callback(null, null);
                        return;
                    }
                    var obj = response.results[0].address_components
                        .filter(function(d) { return d.types.indexOf('country') != -1; });
                    if (obj.length)
                        callback(null, obj[0].short_name);
                    else {
                        console.warn(Error('Invalid geocoder response'), response);
                        callback(null, null);
                    }
                });
            }, function(err) { 
                console.warn(err);
                callback(null, null);
            });
        } else {
            console.warn(Error('Browser geolocation is not supported'));
            callback(null, null);
        }
    }

    // Periodically load data
    var REFRESH_TIME_MINUTES = 5;
    var connectionWarningTimeout = null;

    function handleConnectionError(err) {
        if (err) {
            console.error(err);
            document.getElementById('connection-warning').className = "show";
        } else {
            document.getElementById('connection-warning').className = "hide";
            clearInterval(connectionWarningTimeout);
        }
    }

    function fetchAndReschedule() {
        // If data doesn't load in 30 secs, show connection warning
        connectionWarningTimeout = setTimeout(function(){
            document.getElementById('connection-warning').className = "show";
        }, 15 * 1000);
        var Q = queue()
        if (isMobile()) {
            Q
                .defer(d3.json, 'europe.topo.json')
                .defer(d3.json, ENDPOINT + '/v1/production');
            if (d3.select('.country-table-initial-text').style() != 'none') {
                Q.defer(geolocaliseCountryCode);
            }
            Q.await(function(err, countryTopos, production, countryCode) {
                handleConnectionError(err);
                if (!err) {
                    dataLoaded(err, countryTopos, production);
                    if (d3.select('.country-table-initial-text').style() != 'none') {
                        if (countryCode && countries[countryCode] ) {
                            // Select one country
                            d3.select('.country-table-initial-text')
                                .style('display', 'none');
                            countryTable
                                .show()
                                .data(countries[countryCode].data);
                        } else {
                            // Show picker
                            var countryCodes = d3.entries(countries)
                                .filter(function (d) { return d.value.data.production; })
                                .map(function (d) { return d.key; });
                            countryCodes.unshift('< press to select >');
                            var countryOptions = d3.select('select.country-picker')
                                .selectAll('option')
                                .data(countryCodes);
                            countryOptions.enter()
                                .append('option');
                            countryOptions
                                .text(function(d) { return d });
                            countryOptions.exit().remove();
                        }
                    }
                }
                setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
            });
        } else {
            Q
                .defer(d3.json, 'europe.topo.json')
                .defer(d3.json, ENDPOINT + '/v1/production')
                .defer(d3.json, ENDPOINT + '/v1/solar')
                .defer(d3.json, ENDPOINT + '/v1/wind')
                .await(function(err, countryTopos, production, solar, wind) {
                    handleConnectionError(err);
                    if (!err)
                        dataLoaded(err, countryTopos, production, solar, wind);
                    setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
                });
        }
    };

    function redraw() {
        countryTable.render();
        if (!isMobile()) {
            countryMap.render();
            co2Colorbar.render();
            windColorbar.render();
            exchangeLayer
                .projection(countryMap.projection())
                .render();
        }
    };

    window.onresize = function () {
        redraw();
    };

    redraw();
    fetchAndReschedule();
}
