// Constants
var REFRESH_TIME_MINUTES = 5;

// Global State
var selectedCountryCode;
var forceRemoteEndpoint = false;
var customDate;
var windEnabled = true;
var solarEnabled = false;

(function readQueryString() {
    args = location.search.replace('\?','').split('&');
    args.forEach(function(arg) {
        kv = arg.split('=');
        if (kv[0] == 'remote') {
            forceRemoteEndpoint = kv[1] == 'true';
        } else if (kv[0] == 'datetime') {
            customDate = kv[1];
        } else if (kv[0] == 'wind') {
            windEnabled = kv[1] == 'true';
        } else if (kv[0] == 'solar') {
            solarEnabled = kv[1] == 'true';
        }
    });
})();

function isMobile() {
    return (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent);
}
function isSmallScreen() {
    // Should be in sync with media queries in CSS
    return screen.width < 600;
}

function trackAnalyticsEvent(eventName, paramObj) {
    if (window.location.href.indexOf("electricitymap") !== -1) {
        try {
            FB.AppEvents.logEvent(eventName, undefined, paramObj);
            mixpanel.track(eventName, paramObj);
            ga('send', eventName);
        } catch(err) {
            console.error('Error in trackAnalyticsEvent' + err);
        }
    }
}

// Start chrome (or forced) version
var REMOTE_ENDPOINT = '//electricitymap.tmrow.co';
var ENDPOINT = (document.domain != '' && document.domain.indexOf('electricitymap') == -1 && !forceRemoteEndpoint) ?
    '' : REMOTE_ENDPOINT;

var co2color = d3.scale.linear()
    .domain([0, 350, 700])
    .range(['green', 'orange', 'darkred'])
    .clamp(true);
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
    ])
    .clamp(true);
// ** Solar Scale **
var maxSolar = 500;
var minDayDSWRF = 10;
var nightOpacity = 0.4;
var minSolarDayOpacity = 0.3;
var maxSolarDayOpacity = 0.0;
var solarDomain = d3.range(10).map(function (i) { return d3.interpolate(minDayDSWRF, maxSolar)(i / (10 - 1)); } );
var solarRange = d3.range(10).map(function (i) {
    var c = Math.round(d3.interpolate(0, 0)(i / (10 - 1)));
    var a = d3.interpolate(minSolarDayOpacity, maxSolarDayOpacity)(i / (10 - 1));
    return 'rgba(' + c + ', ' + c + ', ' + c + ', ' + a + ')';
});
// Insert the night (DWSWRF \in [0, 1]) domain
solarDomain.splice(0, 0, 1);
solarRange.splice(0, 0, rgba(0, 0, 0, ' + nightOpacity + ')
// Create scale
var solarColor = d3.scale.linear()
    .domain(solarDomain)
    .range(solarRange)
    .clamp(true);

// Set up objects
var countryMap = new CountryMap('.map', co2color);
var exchangeLayer = new ExchangeLayer('.map');
var countryTable = new CountryTable('.country-table', co2color);
var windLayer = new Windy({ canvas: d3.select('.wind').node() });

var co2Colorbar = new HorizontalColorbar('.co2-colorbar', co2color)
    .markerColor('black');
var windColorbar = new HorizontalColorbar('.wind-colorbar', windColor)
    .markerColor('black');
var solarColorbar = new HorizontalColorbar('.solar-colorbar', solarColor)
    .markerColor('black');

var co2eqCalculator = new Co2eqCalculator();

var tableDisplayEmissions = countryTable.displayByEmissions();

function toogleSource() {
    tableDisplayEmissions = !tableDisplayEmissions;
    trackAnalyticsEvent(
        tableDisplayEmissions ? 'switchToCountryEmissions' : 'switchToCountryProduction',
        {countryCode: countryTable.data().countryCode});
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
var countries = getCountryTopos(countries);
addCountriesConfiguration(countries);
d3.entries(countries).forEach(function (o) {
    var country = o.value;
    country.maxCapacity =
        d3.max(d3.values(country.capacity));
    country.countryCode = o.key;
});
var exchanges = {};
addExchangesConfiguration(exchanges);
d3.entries(exchanges).forEach(function(entry) {
    entry.value.countryCodes = entry.key.split('->').sort();
    if (entry.key.split('->')[0] != entry.value.countryCodes[0])
        console.error('Exchange sorted key pair ' + entry.key + ' is not sorted alphabetically');
});
var wind, solar;

function selectCountry(countryCode) {
    if (!countryCode || !countries[countryCode]) {
        // Unselected
        d3.select('.country-table-initial-text')
            .style('display', 'block');
        countryTable.hide();
        selectedCountryCode = undefined;
    } else {
        // Selected
        console.log(countries[countryCode]);
        trackAnalyticsEvent('countryClick', {countryCode: countryCode});
        d3.select('.country-table-initial-text')
            .style('display', 'none');
        countryTable
            .show()
            .data(countries[countryCode]);
        selectedCountryCode = countryCode;
    }
    if (isSmallScreen())
        d3.select('#country-table-back-button').style('display',
                selectedCountryCode ? 'block' : 'none');
}

// Mobile
if (isSmallScreen()) {
    d3.select('.map').selectAll('*').remove();
    d3.select('#country-table-back-button')
        .on('click', function() { selectCountry(undefined); });
} else {
    d3.select('.panel-container')
        .style('width', '330px');

    // Attach event handlers
    function mapMouseOver(coordinates) {
        if (windLayer.field && coordinates) {
            var wind = windLayer.field(coordinates[0], coordinates[1]);
            windColorbar.currentMarker(wind[2]);
        } else {
            windColorbar.currentMarker(undefined);
        }
        if (solar && coordinates) {
            var t_before = moment(solar.forecasts[0].header.refTime).unix() * 1000.0 + 
                solar.forecasts[0].header.forecastTime * 3600.0 * 1000.0;
            var t_after = moment(solar.forecasts[1].header.refTime).unix() * 1000.0 + 
                solar.forecasts[1].header.forecastTime * 3600.0 * 1000.0;
            var lonlat = countryMap.projection().invert(coordinates);
            // TODO: Optimise by grouping in a solar or grib class
            var now = (new Date()).getTime();
            if (moment(now) <= moment(t_after)) {
                var Nx = solar.forecasts[0].header.nx;
                var Ny = solar.forecasts[0].header.ny;
                var lo1 = solar.forecasts[0].header.lo1;
                var la1 = solar.forecasts[0].header.la1;
                var dx = solar.forecasts[0].header.dx;
                var dy = solar.forecasts[0].header.dy;
                var i = parseInt(lonlat[0] - lo1) / dx;
                var j = parseInt(la1 - lonlat[1]) / dy;
                var n = j * Nx + i;
                var k = (now - t_before)/(t_after - t_before);
                var val = d3.interpolate(
                    solar.forecasts[0].data[n],
                    solar.forecasts[1].data[n])(k);
                solarColorbar.currentMarker(val);
                console.log(val)
            }
        } else {
            solarColorbar.currentMarker(undefined);
        }
    }
    d3.select('.map')
        .on('mousemove', function() {
            mapMouseOver(d3.mouse(this));
        })
        .on('mouseout', function() {
            mapMouseOver(undefined);
        });
    countryTable
        .onExchangeMouseOver(function (d, countryCode) {
            var o = d.value < 0 ? countryCode : d.key;
            var co2 = countries[o].co2intensity;
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

function dataLoaded(err, state, argSolar, argWind) {
    if (err) {
        console.error(err);
        return;
    }
    wind = argWind;
    solar = argSolar;

    if (wind && windEnabled) {
        console.log('wind', wind);
        d3.select('.wind-legend').style('display', 'block');
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
    } else {
        d3.select('.wind-legend').style('display', 'none');
    }

    if (solar && solarEnabled) {
        console.log('solar', solar);
        d3.select('.solar-legend').style('display', 'block');
        if (ctx) {
            // Interpolates between two solar forecasts
            var Nx = solar.forecasts[0].header.nx;
            var Ny = solar.forecasts[0].header.ny;
            var lo1 = solar.forecasts[0].header.lo1;
            var la1 = solar.forecasts[0].header.la1;
            var dx = solar.forecasts[0].header.dx;
            var dy = solar.forecasts[0].header.dy;
            var t_before = moment(solar.forecasts[0].header.refTime).unix() * 1000.0 + 
                solar.forecasts[0].header.forecastTime * 3600.0 * 1000.0;
            var t_after = moment(solar.forecasts[1].header.refTime).unix() * 1000.0 + 
                solar.forecasts[1].header.forecastTime * 3600.0 * 1000.0;
            var now = (new Date()).getTime();
            console.log('#1 solar forecast target', 
                moment(t_before).fromNow(),
                'made', moment(solar.forecasts[0].header.refTime).fromNow());
            console.log('#2 solar forecast target',
                moment(t_after).fromNow(),
                'made', moment(solar.forecasts[1].header.refTime).fromNow());
            if (moment(now) > moment(t_after)) {
                console.error('Error while interpolating solar because current time is out of bounds');
            } else {
                var k = (now - t_before)/(t_after - t_before);
                var buckets = d3.range(solarColor.range().length)
                    .map(function(d) { return []; });
                var bucketIndex = d3.scale.linear()
                    .rangeRound(d3.range(buckets.length))
                    .domain(solarColor.domain())
                    .clamp(true);
                var k = (now - t_before)/(t_after - t_before);

                function bilinearInterpolate(x, y, x1, x2, y1, y2, Q11, Q12, Q21, Q22) {
                    var R1 = ((x2 - x)/(x2 - x1))*Q11 + ((x - x1)/(x2 - x1))*Q21;
                    var R2 = ((x2 - x)/(x2 - x1))*Q12 + ((x - x1)/(x2 - x1))*Q22;
                    return ((y2 - y)/(y2 - y1))*R1 + ((y - y1)/(y2 - y1))*R2;
                }

                d3.range(solarCanvas.attr('width')).forEach(function(x) {
                    d3.range(solarCanvas.attr('height')).forEach(function(y) {
                        var lonlat = countryMap.projection().invert([x, y]);
                        var positions = [
                            [Math.floor(lonlat[0] - lo1) / dx, Math.ceil(la1 - lonlat[1]) / dy],
                            [Math.floor(lonlat[0] - lo1) / dx, Math.floor(la1 - lonlat[1]) / dy],
                            [ Math.ceil(lonlat[0] - lo1) / dx, Math.ceil(la1 - lonlat[1]) / dy],
                            [ Math.ceil(lonlat[0] - lo1) / dx, Math.floor(la1 - lonlat[1]) / dy],
                        ];
                        var values = positions.map(function(d) {
                            var n = d[0] + Nx * d[1];
                            return d3.interpolate(
                                solar.forecasts[0].data[n],
                                solar.forecasts[1].data[n])(k);
                        });
                        var val = bilinearInterpolate(
                            (lonlat[0] - lo1) / dx,
                            (la1 - lonlat[1]) / dy,
                            positions[0][0],
                            positions[2][0],
                            positions[0][1],
                            positions[1][1],
                            values[0],
                            values[1],
                            values[2],
                            values[3]);
                        buckets[bucketIndex(val)].push([x, y]);
                    });
                });
                buckets.forEach(function(d, i) {
                    ctx.beginPath()
                    rgbaColor = solarColor.range()[i];
                    ctx.strokeStyle = d3.rgb(rgbaColor.replace('rgba', 'rgb'));
                    ctx.globalAlpha = parseFloat(rgbaColor
                        .replace('(', '')
                        .replace(')', '')
                        .replace('rgba', '')
                        .split(', ')[3]);
                    d.forEach(function(d) { ctx.rect(d[0], d[1], 1, 1); });
                    ctx.stroke();
                });
                buckets = []; // Release memory
            }
        }
    } else {
        d3.select('.solar-legend').style('display', 'none');
    }

    // Populate with realtime country data
    d3.entries(state.countries).forEach(function(entry) {
        var countryCode = entry.key;
        var country = countries[countryCode];
        if (!country) {
            console.warn(countryCode + ' has no country definition.');
            return;
        }
        // Copy data
        d3.keys(entry.value).forEach(function(k) {
            country[k] = entry.value[k];
        });
        // Validate data
        if (!country.production) return;
        countryTable.PRODUCTION_MODES.forEach(function (mode) {
            if (mode == 'other' || mode == 'unknown') return;
            if (country.production[mode] === undefined)
                console.warn(countryCode + ' is missing production of ' + mode);
            else if (!country.capacity || country.capacity[mode] === undefined)
                console.warn(countryCode + ' is missing capacity of ' + mode);
        });
        if (!country.exchange || !d3.keys(country.exchange).length)
            console.warn(countryCode + ' is missing exchanges');
    });
    console.log('countries', countries);

    // Render country picker if we're on mobile
    if (isSmallScreen()) {
        var validCountries = d3.values(countries).filter(function(d) {
            return d.production;
        }).sort(function(x, y) {
            return d3.ascending(x.co2intensity || x.fullname || x.countryCode,
                y.co2intensity || y.fullname || y.countryCode);
        });
        var selector = d3.select('.country-picker-container p')
            .selectAll('a')
            .data(validCountries);
        var enterA = selector.enter().append('a');
        enterA
            .append('div')
            .attr('class', 'country-emission-rect')
        enterA
            .append('text')
        enterA
            .attr('href', '#')
            .append('i').attr('id', 'country-flag')
        selector.select('text')
            .text(function(d) { return ' ' + (d.fullname || d.countryCode) + ' '; })
        selector.select('div.country-emission-rect')
            .style('background-color', function(d) {
                return d.co2intensity ? co2color(d.co2intensity) : 'gray';
            });
        selector.select('i#country-flag')
            .attr('class', function(d) { 
                return 'flag-icon flag-icon-' + d.countryCode.toLowerCase();
            })
        selector.on('click', function(d) { return selectCountry(d.countryCode); });
    }

    // Render country map
    countryMap
        .data(d3.values(countries))
        .onSeaClick(function () { selectCountry(undefined); })
        .onCountryClick(function (d) { selectCountry(d.countryCode); })
        .onCountryMouseOver(function (d) { 
            d3.select(this)
                .style('opacity', 0.8)
                .style('cursor', 'hand')
            if (d.co2intensity)
                co2Colorbar.currentMarker(d.co2intensity);
            d3.select('#country-tooltip')
                .style('display', 'inline');
        })
        .onCountryMouseMove(function (d) {
            var tooltip = d3.select('#country-tooltip');
            var w = tooltip.node().getBoundingClientRect().width;
            var h = tooltip.node().getBoundingClientRect().height;
            tooltip
                .style('left', (d3.event.pageX - w - 5) + 'px')
                .style('top', (d3.event.pageY - h - 5) + 'px');
            tooltip.select('i#country-flag')
                .attr('class', 'flag-icon flag-icon-' + d.countryCode.toLowerCase())
            tooltip.select('#country-code')
                .text(d.countryCode);
            tooltip.select('.country-emission-rect')
                .style('background-color', d.co2intensity ? co2color(d.co2intensity) : 'gray');
            tooltip.select('.country-emission-intensity')
                .text(Math.round(d.co2intensity) || '?');
        })
        .onCountryMouseOut(function (d) { 
            d3.select(this)
                .style('opacity', 1)
                .style('cursor', 'normal')
            if (d.co2intensity)
                co2Colorbar.currentMarker(undefined);
            d3.select('#country-tooltip')
                .style('display', 'none');
        })
        .render();

        // Render country table if it already was visible
        if (selectedCountryCode)
            countryTable.data(countries[selectedCountryCode]).render()

    if (!isSmallScreen()) {
        // Populate exchange pairs for arrows
        d3.entries(state.exchanges).forEach(function(obj) {
            var exchange = exchanges[obj.key];
            if (!exchange) {
                console.error('Missing exchange configuration for ' + obj.key);
                return;
            }
            // Copy data
            d3.keys(obj.value).forEach(function(k) {
                exchange[k] = obj.value[k];
            });
        });
        console.log('exchanges', exchanges);

        // Render exchanges
        exchangeLayer
            .data(d3.values(exchanges))
            .projection(countryMap.projection())
            .onExchangeMouseOver(function (d) { 
                d3.select(this)
                    .style('opacity', 0.8)
                    .style('cursor', 'hand')
                if (d.co2intensity)
                    co2Colorbar.currentMarker(d.co2intensity);
                d3.select('#exchange-tooltip')
                    .style('display', 'inline');
            })
            .onExchangeMouseMove(function (d) {
                var tooltip = d3.select('#exchange-tooltip');
                var w = tooltip.node().getBoundingClientRect().width;
                var h = tooltip.node().getBoundingClientRect().height;
                tooltip
                    .style('left', (d3.event.pageX - w - 5) + 'px')
                    .style('top', (d3.event.pageY - h - 5) + 'px');
                tooltip.select('.country-emission-rect')
                    .style('background-color', d.co2intensity ? co2color(d.co2intensity) : 'gray');
                var i = d.netFlow > 0 ? 0 : 1;
                tooltip.select('span#from')
                    .text(d.countryCodes[i]);
                tooltip.select('span#to')
                    .text(d.countryCodes[(i + 1) % 2]);
                tooltip.select('span#flow')
                    .text(Math.abs(Math.round(d.netFlow)));
                tooltip.select('i#from')
                    .attr('class', 'flag-icon flag-icon-' + d.countryCodes[i].toLowerCase());
                tooltip.select('i#to')
                    .attr('class', 'flag-icon flag-icon-' + d.countryCodes[(i + 1) % 2].toLowerCase());
            })
            .onExchangeMouseOut(function (d) {
                d3.select(this)
                    .style('opacity', 1)
                    .style('cursor', 'normal')
                if (d.co2intensity)
                    co2Colorbar.currentMarker(undefined);
                d3.select('#exchange-tooltip')
                    .style('display', 'none');
            })
            .render();
    }

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
        Q.defer(d3.json, ENDPOINT + '/v1/state');
        Q.defer(geolocaliseCountryCode);
        Q.await(function(err, state, geolocalisedCountryCode) {
            handleConnectionError(err);
            if (!err) {
                dataLoaded(err, state.data);
            }
            setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
        });
    } else {
        Q.defer(d3.json, ENDPOINT + '/v1/state' + (customDate ? '?datetime=' + customDate : ''));
        if (solarEnabled || windEnabled) {
            Q.defer(d3.json, ENDPOINT + '/v1/solar');
            Q.defer(d3.json, ENDPOINT + '/v1/wind');
        }
        Q.await(function(err, state, solar, wind) {
            handleConnectionError(err);
            if (!err)
                dataLoaded(err, state.data, solar, wind);
            setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
        });
    }
};

function redraw() {
    countryTable.render();
    if (!isSmallScreen()) {
        countryMap.render();
        co2Colorbar.render();
        windColorbar.render();
        solarColorbar.render();
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
