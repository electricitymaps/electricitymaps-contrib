// Libraries
var Cookies = require('js-cookie');
var d3 = require('d3');
var Flatpickr = require('flatpickr');
var moment = require('moment');

// Modules
//var AreaGraph = require('./areagraph');
var LineGraph = require('./linegraph');
var CountryMap = require('./countrymap');
var CountryTable = require('./countrytable');
var CountryTopos = require('./countrytopos');
var DataService = require('./dataservice');
var ExchangeConfig = require('./exchangeconfig');
var ExchangeLayer = require('./exchangelayer');
var grib = require('./grib');
var HorizontalColorbar = require('./horizontalcolorbar');
var lang = require('json-loader!./configs/lang.json')[locale];
var LoadingService = require('./loadingservice');
var Solar = require('./solar');
var Tooltip = require('./tooltip');
var Wind = require('./wind');

// Configs
var capacities = require('json-loader!./configs/capacities.json');
var zones = require('json-loader!./configs/zones.json');

// Constants
var REFRESH_TIME_MINUTES = 5;

// Global State
var selectedCountryCode;
var forceRemoteEndpoint = false;
var customDate;
var timelineEnabled = false;
var currentMoment;

function isMobile() {
    return (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent);
}
function isSmallScreen() {
    // Should be in sync with media queries in CSS
    return window.innerWidth < 768;
}

// History state
// TODO: put in a module

// History state init (state that is reflected in the url)
var historyState = {};
function appendQueryString(url, key, value) {
    return (url == '?' ? url : url + '&') + key + '=' + value;
}
function getHistoryStateURL() {
    var url = '?';
    d3.entries(historyState).forEach(function(d) {
        url = appendQueryString(url, d.key, d.value);
    });
    return (url == '?' ? '.' : url);
}
function replaceHistoryState(key, value) {
    if (value == null) {
        delete historyState[key];
    } else {
        historyState[key] = value;
    }
    history.replaceState(historyState, '', getHistoryStateURL());
}

// Read query string
args = location.search.replace('\?','').split('&');
args.forEach(function(arg) {
    kv = arg.split('=');
    // Store in history state to be able to reconstruct
    replaceHistoryState(kv[0], kv[1]);
    if (kv[0] == 'remote') {
        forceRemoteEndpoint = kv[1] == 'true';
        replaceHistoryState('remote', forceRemoteEndpoint);
    } else if (kv[0] == 'datetime') {
        customDate = kv[1];
        replaceHistoryState('datetime', customDate);
    } else if (kv[0] == 'timeline') {
        timelineEnabled = kv[1] == 'true';
        replaceHistoryState('timeline', timelineEnabled);
    } else if (kv[0] == 'countryCode') {
        selectedCountryCode = kv[1];
        replaceHistoryState('countryCode', selectedCountryCode);
    }
});

// Computed State
var showWindOption = !isSmallScreen();
var showSolarOption = !isSmallScreen();
var windEnabled = showWindOption ? (Cookies.get('windEnabled') == 'true' || false) : false;
var solarEnabled = showSolarOption ? (Cookies.get('solarEnabled') == 'true' || false) : false;
var isLocalhost = window.location.href.indexOf('//electricitymap') == -1;
var isEmbedded = window.top !== window.self;
var REMOTE_ENDPOINT = '//www.electricitymap.org';
var ENDPOINT = (document.domain != '' && document.domain.indexOf('electricitymap') == -1 && !forceRemoteEndpoint) ?
    '' : REMOTE_ENDPOINT;

if (typeof _opbeat !== 'undefined')
    _opbeat('config', {
        orgId: '093c53b0da9d43c4976cd0737fe0f2b1',
        appId: 'f40cef4b37'
    });
else
    console.warn('Opbeat could not be initialized!');

function catchError(e) {
    console.error('Error Caught! ' + e);
    if (!isLocalhost) {
        if(typeof _opbeat !== 'undefined')
            _opbeat('captureException', e);
        trackAnalyticsEvent('error', {name: e.name, stack: e.stack, bundleHash: bundleHash});
    }
}

// Analytics
function trackAnalyticsEvent(eventName, paramObj) {
    if (!isLocalhost) {
        try {
            if(typeof FB !== 'undefined')
                FB.AppEvents.logEvent(eventName, undefined, paramObj);
        } catch(err) { console.error('FB AppEvents error: ' + err); }
        try {
            if(typeof mixpanel !== 'undefined')
                mixpanel.track(eventName, paramObj);
        } catch(err) { console.error('Mixpanel error: ' + err); }
        try {
            if(typeof ga !== 'undefined')
                ga('send', eventName);
        } catch(err) { console.error('Google Analytics error: ' + err); }
    }
}

// Set proper locale
moment.locale(locale);

// Display embedded warning
// d3.select('#embedded-error').style('display', isEmbedded ? 'block' : 'none');

var co2color = d3.scaleLinear()
    .domain([0, 375, 725, 800])
    .range(['green', 'orange', 'rgb(26,13,0)'])
    .clamp(true);
var maxWind = 15;
var windColor = d3.scaleLinear()
    .domain(d3.range(10).map( function (i) { return d3.interpolate(0, maxWind)(i / (10 - 1)); } ))
    .range([
        "rgba(0,   255, 255, 1.0)",
        "rgba(100, 240, 255, 1.0)",
        "rgba(135, 225, 255, 1.0)",
        "rgba(160, 208, 255, 1.0)",
        "rgba(181, 192, 255, 1.0)",
        "rgba(198, 173, 255, 1.0)",
        "rgba(212, 155, 255, 1.0)",
        "rgba(225, 133, 255, 1.0)",
        "rgba(236, 109, 255, 1.0)",
        "rgba(255,  30, 219, 1.0)"
    ])
    .clamp(true);
// ** Solar Scale **
var maxSolarDSWRF = 1000;
var minDayDSWRF = 0;
// var nightOpacity = 0.8;
var minSolarDayOpacity = 0.6;
var maxSolarDayOpacity = 0.0;
var solarDomain = d3.range(10).map(function (i) { return d3.interpolate(minDayDSWRF, maxSolarDSWRF)(i / (10 - 1)); } );
var solarRange = d3.range(10).map(function (i) {
    var c = Math.round(d3.interpolate(0, 0)(i / (10 - 1)));
    var a = d3.interpolate(minSolarDayOpacity, maxSolarDayOpacity)(i / (10 - 1));
    return 'rgba(' + c + ', ' + c + ', ' + c + ', ' + a + ')';
});
// Insert the night (DWSWRF \in [0, minDayDSWRF]) domain
// solarDomain.splice(0, 0, 0);
// solarRange.splice(0, 0, 'rgba(0, 0, 0, ' + nightOpacity + ')');
// Create scale
var solarColor = d3.scaleLinear()
    .domain(solarDomain)
    .range(solarRange)
    .clamp(true);

// Production/imports-exports mode
var modeColor = {
    'wind': '#74cdb9',
    'solar': '#f27406',
    'hydro': '#2772b2',
    'hydro storage': '#2772b2',
    'biomass': '#166a57',
    'geothermal': 'yellow',
    'nuclear': '#AEB800',
    'gas': '#bb2f51',
    'coal': '#ac8c35',
    'oil': '#867d66',
    'unknown': 'lightgray'
};
var modeOrder = [
    'wind',
    'solar',
    'hydro',
    'hydro storage',
    'geothermal',
    'biomass',
    'nuclear',
    'gas',
    'coal',
    'oil',
    'unknown'
];

// Set up objects
var countryMap = new CountryMap('.map', co2color);
var exchangeLayer = new ExchangeLayer('.map', co2color);
var countryTable = new CountryTable('.country-table', co2color, modeColor, modeOrder);
//var countryHistoryGraph = new AreaGraph('.country-history', modeColor, modeOrder);
var countryHistoryGraph = new LineGraph('.country-history',
    function(d) { return moment(d.stateDatetime).toDate(); },
    function(d) { return d.co2intensity; },
    function(d) { return d.co2intensity != null; },
    co2color);

if (!isSmallScreen())
    var co2Colorbar = new HorizontalColorbar('.co2-colorbar', co2color)
        .markerColor('white')
        .render();
var windColorbar = new HorizontalColorbar('.wind-colorbar', windColor)
    .markerColor('black');
d3.select('.wind-colorbar').style('display', windEnabled ? 'block': 'none');
var solarColorbarColor = d3.scaleLinear()
    .domain([0, 0.5 * maxSolarDSWRF, maxSolarDSWRF])
    .range(['black', 'white', 'gold'])
var solarColorbar = new HorizontalColorbar('.solar-colorbar', solarColorbarColor)
    .markerColor('red');
d3.select('.solar-colorbar').style('display', solarEnabled ? 'block': 'none');

var tableDisplayEmissions = countryTable.displayByEmissions();

// Set weather checkboxes
d3.select('#checkbox-wind').node().checked = windEnabled;
d3.select('#checkbox-solar').node().checked = solarEnabled;
d3.select('.layer-toggles').style('display', !showWindOption && !showSolarOption ? 'none' : null);

window.toggleSource = function() {
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

// Timeline
d3.select('.time-travel').style('display', timelineEnabled ? 'block' : 'none');
function setCustomDatetime(datetime) {
    customDate = datetime;
    replaceHistoryState('datetime', datetime);
    fetch(false);
}
var flatpickr = new Flatpickr(d3.select('.flatpickr').node(), {
    enableTime: true,
    onClose: function(selectedDates, dateStr, instance) {
        setCustomDatetime(moment(dateStr).toISOString());
    }
});

// Tooltips
function placeTooltip(selector, d3Event) {
    var tooltip = d3.select(selector);
    var w = tooltip.node().getBoundingClientRect().width;
    var h = tooltip.node().getBoundingClientRect().height;
    var x = d3Event.pageX + 5; if (window.innerWidth - x <= w) x = d3Event.pageX - w - 5;
    var y = d3Event.pageY - h - 5; if (y <= 5) y = d3Event.pageY + 5;
    tooltip
        .style('transform',
            'translate(' + x + 'px' + ',' + y + 'px' + ')');
}
var width = window.innerWidth;
var height = window.innerHeight;

var windCanvas = d3.select('.wind');
windCanvas.attr('height', height);
windCanvas.attr('width', width);

var solarCanvas = d3.select('.solar');
solarCanvas.attr('height', height);
solarCanvas.attr('width', width);

// Prepare data
var countries = CountryTopos.addCountryTopos({});
// Add configurations
d3.entries(zones).forEach(function(d) {
    var zone = countries[d.key];
    d3.entries(d.value).forEach(function(o) { zone[o.key] = o.value; });
    zone.maxCapacity = d3.max(d3.values(zone.capacity));
    // Add translation
    zone.shortname = lang.zoneShortName[d.key];
});
// Add capacities
d3.entries(capacities).forEach(function(d) {
    var zone = countries[d.key];
    zone.capacity = d.value.capacity;
    zone.maxCapacity = d3.max(d3.values(zone.capacity));
});
// Add id to each zone
d3.entries(countries).forEach(function(d) {
    var zone = countries[d.key];
    zone.countryCode = d.key; // TODO: Rename to zoneId
})
var exchanges = {};
ExchangeConfig.addExchangesConfiguration(exchanges);
d3.entries(exchanges).forEach(function(entry) {
    entry.value.countryCodes = entry.key.split('->').sort();
    if (entry.key.split('->')[0] != entry.value.countryCodes[0])
        console.error('Exchange sorted key pair ' + entry.key + ' is not sorted alphabetically');
});
var wind, solar;

var histories = {};

function selectCountry(countryCode, notrack) {
    if (!countryCode || !countries[countryCode]) {
        // Unselected
        d3.select('.left-panel-initial-text')
            .style('display', 'block');
        d3.select('.country-panel')
            .style('display', 'none');
        selectedCountryCode = undefined;
    } else {
        // Selected
        console.log(countries[countryCode]);
        if (!notrack)
            trackAnalyticsEvent('countryClick', {countryCode: countryCode});
        d3.select('.left-panel-initial-text')
            .style('display', 'none');
        d3.select('.country-panel')
            .style('display', 'block');
        countryTable
            .data(countries[countryCode])
            .powerScaleDomain(null) // Always reset scale if click on a new country
            .render();
        selectedCountryCode = countryCode;

        function updateGraph(countryHistory) {
            // No export capacities are defined, and they are thus
            // varying the scale.
            // Here's a hack to fix it.
            var lo = d3.min(countryHistory, function(d) {
                return Math.min(
                    -d.maxExport || 0,
                    -d.maxStorage || 0);
            });
            var hi = d3.max(countryHistory, function(d) {
                return Math.max(
                    d.maxCapacity || 0,
                    d.maxProduction || 0,
                    d.maxImport || 0)
            });

            countryHistoryGraph
                .data(countryHistory)
                .onMouseMove(function(d) {
                    if (!d) return;
                    // In case of missing data
                    if (!d.countryCode)
                        d.countryCode = countryCode;
                    countryTable
                        .powerScaleDomain([lo, hi])
                        .data(d)
                        .render(true);
                })
                .onMouseOut(function() {
                    countryTable
                        .powerScaleDomain(null)
                        .data(countries[countryCode])
                        .render();
                })
                .render();
        }

        // Load graph
        if (customDate)
            console.error('Can\'t fetch history when a custom date is provided!');
        else if (!histories[countryCode])
            d3.json(ENDPOINT + '/v2/history?countryCode=' + countryCode, function(err, obj) {
                if (err) console.error(err);
                if (!obj || !obj.data) console.warn('Empty history received for ' + countryCode);
                if (err || !obj || !obj.data) {
                    updateGraph([]);
                    return;
                }

                // Add capacities
                if (capacities[countryCode]) {
                    var maxCapacity = d3.max(d3.values(capacities[countryCode].capacity));
                    obj.data.forEach(function(d) {
                        d.capacity = capacities[countryCode].capacity;
                        d.maxCapacity = maxCapacity;
                    });
                }

                // Push current state if present
                if (countries[countryCode].datetime)
                    obj.data.push(countries[countryCode]);

                // Save to local cache
                histories[countryCode] = obj.data;

                // Show
                updateGraph(histories[countryCode]);
            });
        else
            updateGraph(histories[countryCode]);
    }
    replaceHistoryState('countryCode', selectedCountryCode);
    d3.select('#country-table-back-button').style('display',
        selectedCountryCode ? 'block' : 'none');
}
// Set initial
selectCountry(selectedCountryCode, true);
d3.select('#country-table-back-button')
    .on('click', function() { selectCountry(undefined); });

if (isSmallScreen()) {
    // Mobile
    d3.select('.map').selectAll('*').remove();
} else {
    // Now that the width is set, we can render the legends
    if (windEnabled) windColorbar.render();
    if (solarEnabled) solarColorbar.render();

    // Set example arrow
    exchangeLayer.renderOne('svg#example-arrow');

    // Attach event handlers
    d3.select('#checkbox-wind').on('change', function() {
        windEnabled = !windEnabled;
        Cookies.set('windEnabled', windEnabled);
        var now = customDate ? moment(customDate) : (new Date()).getTime();
        if (windEnabled) {
            d3.select('.wind-colorbar').style('display', 'block');
            windColorbar.render()
            if (!wind || Wind.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
                fetch(true);
            } else {
                Wind.show();
            }
        } else {
            d3.select('.wind-colorbar').style('display', 'none');
            Wind.hide();
        }
    });
    d3.select('#checkbox-solar').on('change', function() {
        solarEnabled = !solarEnabled;
        Cookies.set('solarEnabled', solarEnabled);
        var now = customDate ? moment(customDate) : (new Date()).getTime();
        if (solarEnabled) {
            d3.select('.solar-colorbar').style('display', 'block');
            solarColorbar.render()
            if (!solar || Solar.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
                fetch(true);
            } else {
                Solar.show();
            }
        } else {
            d3.select('.solar-colorbar').style('display', 'none');
            Solar.hide();
        }
    });
    function mapMouseOver(coordinates) {
        if (windEnabled && wind && coordinates) {
            var lonlat = countryMap.projection().invert(coordinates);
            var now = customDate ? moment(customDate) : (new Date()).getTime();
            if (!Wind.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
                var u = grib.getInterpolatedValueAtLonLat(lonlat, 
                    now, wind.forecasts[0][0], wind.forecasts[1][0]);
                var v = grib.getInterpolatedValueAtLonLat(lonlat, 
                    now, wind.forecasts[0][1], wind.forecasts[1][1]);
                windColorbar.currentMarker(Math.sqrt(u * u + v * v));
            }
        } else {
            windColorbar.currentMarker(undefined);
        }
        if (solarEnabled && solar && coordinates) {
            var lonlat = countryMap.projection().invert(coordinates);
            var now = customDate ? moment(customDate) : (new Date()).getTime();
            if (!Solar.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
                var val = grib.getInterpolatedValueAtLonLat(lonlat, 
                    now, solar.forecasts[0], solar.forecasts[1]);
                solarColorbar.currentMarker(val);
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

    // Tooltip setup
    Tooltip.setupCountryTable(countryTable, countries, co2Colorbar, co2color);
}

function dataLoaded(err, clientVersion, state, argSolar, argWind) {
    if (err) {
        console.error(err);
        return;
    }

    // Is there a new version?
    d3.select('#new-version')
        .style('top', (clientVersion === bundleHash || forceRemoteEndpoint) ? undefined : 0);

    currentMoment = (customDate && moment(customDate) || moment());
    d3.select('#current-date').text(currentMoment.format('LL'));
    d3.select('#current-time').text(currentMoment.format('LT [UTC]Z'));
    d3.selectAll('#current-date, #current-time')
        .style('color', 'darkred')
        .transition()
            .duration(800)
            .style('color', 'lightgrey');
    flatpickr.setDate(moment(customDate).toDate());

    // Reset all data
    d3.entries(countries).forEach(function(entry) {
        entry.value.co2intensity = undefined;
        entry.value.exchange = {};
        entry.value.production = {};
        entry.value.productionCo2Intensities = {};
        entry.value.storage = {};
        entry.value.source = undefined;
    });
    d3.entries(exchanges).forEach(function(entry) {
        entry.value.netFlow = undefined;
    });
    histories = {};

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
        modeOrder.forEach(function (mode) {
            if (mode == 'other' || mode == 'unknown' || !country.datetime) return;
            // Check missing values
            if (country.production[mode] === undefined && country.storage[mode] === undefined)
                console.warn(countryCode + ' is missing production or storage of ' + mode);
            // Check validity of production
            if (country.production[mode] !== undefined && country.production[mode] < 0)
                console.error(countryCode + ' has negative production of ' + mode);
            // Check validity of storage
            if (country.storage[mode] !== undefined && country.storage[mode] < 0)
                console.error(countryCode + ' has negative storage of ' + mode);
            // Check missing capacities
            if (country.production[mode] !== undefined &&
                (country.capacity || {})[mode] === undefined)
            {
                console.warn(countryCode + ' is missing capacity of ' + mode);
            }
            // Check load factors > 1
            if (country.production[mode] !== undefined &&
                (country.capacity || {})[mode] !== undefined &&
                country.production[mode] > country.capacity[mode])
            {
                console.error(countryCode + ' produces more than its capacity of ' + mode);
            }
        });
        if (!country.exchange || !d3.keys(country.exchange).length)
            console.warn(countryCode + ' is missing exchanges');
    });
    console.log('countries', countries);

    // Render country picker if we're on mobile
    if (isSmallScreen()) {
        var validCountries = d3.values(countries).filter(function(d) {
            return d.co2intensity;
        }).sort(function(x, y) {
            if (!x.co2intensity && !x.countryCode)
                return d3.ascending(x.shortname || x.countryCode,
                    y.shortname || y.countryCode);
            else
                return d3.ascending(x.co2intensity || Infinity,
                    y.co2intensity || Infinity);
        });
        var selector = d3.select('.country-picker-container p')
            .selectAll('a')
            .data(validCountries);
        var enterA = selector.enter().append('a');
        enterA
            .append('div')
            .attr('class', 'emission-rect')
        enterA
            .append('text')
        enterA
            .append('i').attr('id', 'country-flag')
        var selector = enterA.merge(selector);
        selector.select('text')
            .text(function(d) { return ' ' + (d.shortname || d.countryCode) + ' '; })
        selector.select('div.emission-rect')
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
    if (!isSmallScreen())
        countryMap
            .data(d3.values(countries))
            .onSeaClick(function () { selectCountry(undefined); })
            .onCountryClick(function (d) { selectCountry(d.countryCode); })
            .render();

    // Only add mouse over handlers if not on mobile
    if (!isMobile()) {
        countryMap.onCountryMouseOver(function (d) { 
            d3.select(this)
                .style('opacity', 0.8)
                .style('cursor', 'pointer')
            if (d.co2intensity && co2Colorbar)
                co2Colorbar.currentMarker(d.co2intensity);
            var tooltip = d3.select('#country-tooltip');
            tooltip.style('display', 'inline');
            tooltip.select('i#country-flag')
                .attr('class', 'flag-icon flag-icon-' + d.countryCode.toLowerCase())
            tooltip.select('#country-code')
                .text(d.countryCode)
                .style('font-weight', 'bold');
            tooltip.select('.emission-rect')
                .style('background-color', d.co2intensity ? co2color(d.co2intensity) : 'gray');
            tooltip.select('.country-emission-intensity')
                .text(Math.round(d.co2intensity) || '?');
            tooltip.select('.country-spot-price')
                .text(Math.round((d.price || {}).value) || '?')
                .style('color', ((d.price || {}).value || 0) < 0 ? 'darkred' : undefined);
            var hasFossilFuelData = 
                ((d.production || {}).gas  != null) || 
                ((d.production || {}).coal != null) || 
                ((d.production || {}).oil  != null);
            var fossilFuelPercent = (
                ((d.production || {}).gas || 0) + 
                ((d.production || {}).coal || 0) + 
                ((d.production || {}).oil || 0)
            ) / (d.totalProduction + d.totalImport) * 100;
            tooltip.select('.fossil-fuel-percentage')
                .text(hasFossilFuelData ? Math.round(fossilFuelPercent) : '?');
        })
        .onCountryMouseMove(function () {
            placeTooltip("#country-tooltip", d3.event);
        })
        .onCountryMouseOut(function (d) { 
            d3.select(this)
                .style('opacity', 1)
                .style('cursor', 'auto')
            if (d.co2intensity && co2Colorbar)
                co2Colorbar.currentMarker(undefined);
            d3.select('#country-tooltip')
                .style('display', 'none');
        })
    }

    // Re-render country table if it already was visible
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
                    .style('cursor', 'pointer');
                if (d.co2intensity && co2Colorbar)
                    co2Colorbar.currentMarker(d.co2intensity);
                var tooltip = d3.select('#exchange-tooltip');
                tooltip.style('display', 'inline');
                tooltip.select('.emission-rect')
                    .style('background-color', d.co2intensity ? co2color(d.co2intensity) : 'gray');
                var i = d.netFlow > 0 ? 0 : 1;
                tooltip.selectAll('span#from')
                    .text(d.countryCodes[i]);
                tooltip.select('span#to')
                    .text(d.countryCodes[(i + 1) % 2]);
                tooltip.select('span#flow')
                    .text(Math.abs(Math.round(d.netFlow)));
                tooltip.selectAll('i#from')
                    .attr('class', 'flag-icon flag-icon-' + d.countryCodes[i].toLowerCase());
                tooltip.select('i#to')
                    .attr('class', 'flag-icon flag-icon-' + d.countryCodes[(i + 1) % 2].toLowerCase());
                tooltip.select('.country-emission-intensity')
                    .text(Math.round(d.co2intensity) || '?');
            })
            .onExchangeMouseMove(function () {
                placeTooltip("#exchange-tooltip", d3.event);
            })
            .onExchangeMouseOut(function (d) {
                d3.select(this)
                    .style('opacity', 1)
                    .style('cursor', 'auto')
                if (d.co2intensity && co2Colorbar)
                    co2Colorbar.currentMarker(undefined);
                d3.select('#exchange-tooltip')
                    .style('display', 'none');
            })
            .render();
    }

    // Render weather if provided
    // Do not overwrite with null/undefined
    if (argWind) wind = argWind;
    if (argSolar) solar = argSolar;

    if (!showWindOption)
        d3.select(d3.select('#checkbox-wind').node().parentNode).style('display', 'none');
    if (windEnabled && wind && wind['forecasts'][0] && wind['forecasts'][1]) {
        console.log('wind', wind);
        LoadingService.startLoading();
        // Make sure to disable wind if the drawing goes wrong
        Cookies.set('windEnabled', false);
        Wind.draw('.wind',
            customDate ? moment(customDate) : moment(new Date()),
            wind.forecasts[0],
            wind.forecasts[1],
            windColor,
            countryMap.projection());
        if (windEnabled)
            Wind.show();
        else
            Wind.hide();
        // Restore setting
        Cookies.set('windEnabled', windEnabled);
        LoadingService.stopLoading();
    } else {
        Wind.hide();
    }

    if (!showSolarOption)
        d3.select(d3.select('#checkbox-solar').node().parentNode).style('display', 'none');
    if (solarEnabled && solar && solar['forecasts'][0] && solar['forecasts'][1]) {
        console.log('solar', solar);
        LoadingService.startLoading();
        // Make sure to disable solar if the drawing goes wrong
        Cookies.set('solarEnabled', false);
        Solar.draw('.solar',
            customDate ? moment(customDate) : moment(new Date()),
            solar.forecasts[0],
            solar.forecasts[1],
            solarColor,
            countryMap.projection(),
            function() {
                if (solarEnabled)
                    Solar.show();
                else
                    Solar.hide();
                // Restore setting
                Cookies.set('solarEnabled', solarEnabled);
                LoadingService.stopLoading();
            });
    } else {
        Solar.hide();
    }
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

function handleConnectionReturnCode(err) {
    if (err) {
        if (err.target) {
            // Avoid catching HTTPError 0
            // The error will be empty, and we can't catch any more info
            // for security purposes
            // See http://stackoverflow.com/questions/4844643/is-it-possible-to-trap-cors-errors
            if (err.target.status)
                catchError(Error(
                    'HTTPError ' +
                    err.target.status + ' ' + err.target.statusText + ' at ' + 
                    err.target.responseURL + ': ' +
                    err.target.responseText));
        } else {
            catchError(err);
        }
        d3.select('#connection-warning').style('top', 0);
    } else {
        d3.select('#connection-warning').style('top', undefined);
        clearInterval(connectionWarningTimeout);
    }
}

function ignoreError(func) {
    return function() {
        var callback = arguments[arguments.length - 1];
        arguments[arguments.length - 1] = function(err, obj) {
            if (err) {
                return callback(null, null);
            } else {
                return callback(null, obj);
            }
        }
        func.apply(this, arguments);
    }
}

function fetch(showLoading, callback) {
    if (!showLoading) showLoading = false;
    if (showLoading) LoadingService.startLoading();
    // If data doesn't load in 15 secs, show connection warning
    connectionWarningTimeout = setTimeout(function(){
        d3.select('#connection-warning').style('top', 0);
    }, 15 * 1000);
    var Q = d3.queue();
    Q.defer(d3.text, ENDPOINT + '/clientVersion');
    Q.defer(d3.json, ENDPOINT + '/v1/state' + (customDate ? '?datetime=' + customDate : ''));

    var now = customDate || new Date();

    if (!solarEnabled)
        Q.defer(DataService.fetchNothing);
    else if (!solar || Solar.isExpired(now, solar.forecasts[0], solar.forecasts[1]))
        Q.defer(ignoreError(DataService.fetchGfs), ENDPOINT, 'solar', now);
    else
        Q.defer(function(cb) { return cb(null, solar); });

    if (!windEnabled)
        Q.defer(DataService.fetchNothing);
    else if (!wind || Wind.isExpired(now, wind.forecasts[0], wind.forecasts[1]))
        Q.defer(ignoreError(DataService.fetchGfs), ENDPOINT, 'wind', now);
    else
        Q.defer(function(cb) { return cb(null, wind); });

    if (isMobile()) {
        Q.defer(geolocaliseCountryCode);
        Q.await(function(err, clientVersion, state, solar, wind, geolocalisedCountryCode) {
            handleConnectionReturnCode(err);
            if (!err)
                dataLoaded(err, clientVersion, state.data, solar, wind);
            if (showLoading) LoadingService.stopLoading();
            if (callback) callback();
        });
    } else {
        Q.await(function(err, clientVersion, state, solar, wind) {
            handleConnectionReturnCode(err);
            if (!err)
                dataLoaded(err, clientVersion, state.data, solar, wind);
            if (showLoading) LoadingService.stopLoading();
            if (callback) callback();
        });
    }
};

function fetchAndReschedule() {
    if (!customDate)
        return fetch(false, function() { 
            setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
        });
    else
        setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
};

function redraw() {
    if (selectedCountryCode) {
        countryTable.render();
        countryHistoryGraph.render();
    }
    if (!isSmallScreen()) {
        countryMap.render();
        co2Colorbar.render();
        exchangeLayer
            .projection(countryMap.projection())
            .render();
    }
};

window.onresize = function () {
    redraw();
};

// Start a fetch showing loading.
// Later `fetchAndReschedule` won't show loading screen
fetch(true, function() { 
    setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
});
