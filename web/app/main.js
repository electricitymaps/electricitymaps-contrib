'use strict'
// Libraries
var Cookies = require('js-cookie');
var d3 = require('d3');
var moment = require('moment');
var redux = require('redux');
var reduxLogger = require('redux-logger').logger;

var thirdPartyServices = require('./services/thirdparty');
var store = require('./store');
var observeStore = require('./helpers/redux').observeStore;

var AreaGraph = require('./components/areagraph');
var LineGraph = require('./components/linegraph');
var CountryTable = require('./components/countrytable');
var HorizontalColorbar = require('./components/horizontalcolorbar');
var Tooltip = require('./components/tooltip');

var CountryTopos = require('./countrytopos');
var DataService = require('./dataservice');

var CountryMap = require('./components/layers/countrymap');
var ExchangeLayer = require('./components/layers/exchangelayer');
var Solar = require('./components/layers/solar');
var Wind = require('./components/layers/wind');

var flags = require('./flags');
var LoadingService = require('./loadingservice');

var grib = require('./helpers/grib');
var translation = require('./translation');
var tooltipHelper = require('./helpers/tooltip');

// Configs
var exchanges_config = require('../../config/exchanges.json');
var zones_config = require('../../config/zones.json');

// Constants
var REFRESH_TIME_MINUTES = 5;

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
    // '.' is not supported when serving from file://
    return (url == '?' ? '?' : url);
}
function replaceHistoryState(key, value) {
    if (value == null) {
        delete historyState[key];
    } else {
        historyState[key] = value;
    }
    history.replaceState(historyState, '', getHistoryStateURL());
}

// Global State
var isLocalhost = window.location.href.indexOf('electricitymap') == -1;
window.useRemoteEndpoint = isLocalhost ? false : true;

var selectedCountryCode;
var customDate;
var currentMoment;
var colorBlindModeEnabled = false;
var showPageState = 'map';
var previousShowPageState = undefined;
var showWindOption = true;
var showSolarOption = true;
var windEnabled = showWindOption ? (Cookies.get('windEnabled') == 'true' || false) : false;
var solarEnabled = showSolarOption ? (Cookies.get('solarEnabled') == 'true' || false) : false;
var mapDraggedSinceStart = false;

function isMobile() {
    return (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent);
}

// Read query string
function parseQueryString(querystring) {
    var args = querystring.replace('\?','').split('&');
    args.forEach(function(arg) {
        var kv = arg.split('=');
        // Store in history state to be able to reconstruct
        replaceHistoryState(kv[0], kv[1]);
        if (kv[0] == 'remote') {
            useRemoteEndpoint = kv[1] == 'true';
            replaceHistoryState('remote', useRemoteEndpoint);
        } else if (kv[0] == 'datetime') {
            customDate = kv[1];
            replaceHistoryState('datetime', customDate);
        } else if (kv[0] == 'countryCode') {
            selectedCountryCode = kv[1];
            replaceHistoryState('countryCode', selectedCountryCode);
        } else if (kv[0] == 'page') {
            showPageState = kv[1].replace('%20', '');
            replaceHistoryState('page', showPageState);
            if (showPage) showPage(showPageState);
        } else if (kv[0] == 'solar') {
            solarEnabled = kv[1] == 'true';
            replaceHistoryState('solar', solarEnabled);
        } else if (kv[0] == 'wind') {
            windEnabled = kv[1] == 'true';
            replaceHistoryState('wind', windEnabled);
        }
    });
}
parseQueryString(location.search);

// Computed State
var colorBlindModeEnabled = Cookies.get('colorBlindModeEnabled') == 'true' || false;
var isEmbedded = window.top !== window.self;
var REMOTE_ENDPOINT = 'https://api.electricitymap.org';
var LOCAL_ENDPOINT = 'http://localhost:9000';
var ENDPOINT = (document.domain != '' && document.domain.indexOf('electricitymap') == -1 && !useRemoteEndpoint) ?
    LOCAL_ENDPOINT : REMOTE_ENDPOINT;


var clientType = 'web';
if (isCordova) { clientType = 'mobileapp'; }

// Set history state of remaining variables
replaceHistoryState('wind', windEnabled);
replaceHistoryState('solar', solarEnabled);

// Add polyfill required by redux
if (typeof Object.assign != 'function') {
  Object.assign = function (target, varArgs) { // .length of function is 2
    'use strict';
    if (target == null) { // TypeError if undefined or null
      throw new TypeError('Cannot convert undefined or null to object');
    }

    var to = Object(target);

    for (var index = 1; index < arguments.length; index++) {
      var nextSource = arguments[index];

      if (nextSource != null) { // Skip over if undefined or null
        for (var nextKey in nextSource) {
          // Avoid bugs when hasOwnProperty is shadowed
          if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
            to[nextKey] = nextSource[nextKey];
          }
        }
      }
    }
    return to;
  };
}

// Initialise mobile app (cordova)
var app = {
    // Application Constructor
    initialize: function() {
        this.bindEvents();
    },

    bindEvents: function () {
        document.addEventListener('deviceready', this.onDeviceReady, false);
        document.addEventListener('resume', this.onResume, false);
        document.addEventListener('backbutton', this.onBack, false);
    },

    onBack: function (e) {
        if (showPageState != 'map') {
            selectedCountryCode = undefined;
            showPage(previousShowPageState || 'map');
            e.preventDefault();
        } else {
            navigator.app.exitApp();
        }
    },

    onDeviceReady: function() {
        // Resize if we're on iOS
        if (cordova.platformId == 'ios') {
            d3.select('#header')
                .style('padding-top', '20px');
        }
        // Geolocation support
        if (selectedCountryCode) {
            var lon = d3.mean(countries[selectedCountryCode].coordinates[0][0], function(d) { return d[0]; });
            var lat = d3.mean(countries[selectedCountryCode].coordinates[0][0], function(d) { return d[1]; });
            countryMap.center([lon, lat]);
        }
        else {
            LoadingService.startLoading();
            navigator.geolocation.getCurrentPosition(
                function(obj) {
                    if (!mapDraggedSinceStart) {
                        geo = [obj.coords.longitude, obj.coords.latitude];
                        console.log('Centering on', geo);
                        countryMap.center(geo);
                    }
                    LoadingService.stopLoading();
                },
                function(err) {
                    console.error(err);
                    countryMap.center([0, 50]);
                    LoadingService.stopLoading();
                },
                { enableHighAccuracy: false, timeout: 4000 });
        }
        // codePush.sync(null, {installMode: InstallMode.ON_NEXT_RESUME});
        universalLinks.subscribe(null, function (eventData) {
            // do some work
            parseQueryString(eventData.url.split('?')[1] || eventData.url);
        });
    },

    onResume: function() {
        // Count a pageview
        thirdPartyServices.track('Visit', {
            'bundleVersion': bundleHash,
            'clientType': clientType,
            'embeddedUri': isEmbedded ? document.referrer : null,
            'windEnabled': windEnabled,
            'solarEnabled': solarEnabled,
            'colorBlindModeEnabled': colorBlindModeEnabled
        });
        // codePush.sync(null, {installMode: InstallMode.ON_NEXT_RESUME});
    }
};
app.initialize();

function catchError(e) {
    console.error('Error Caught! ' + e);
    thirdPartyServices.opbeat('captureException', e);
    thirdPartyServices.track('error', {name: e.name, stack: e.stack, bundleHash: bundleHash});
}

// Analytics
thirdPartyServices.track('Visit', {
    'bundleVersion': bundleHash,
    'clientType': clientType,
    'embeddedUri': isEmbedded ? document.referrer : null,
    'windEnabled': windEnabled,
    'solarEnabled': solarEnabled,
    'colorBlindModeEnabled': colorBlindModeEnabled
});

// Set proper locale
moment.locale(locale.toLowerCase());

// Display embedded warning
// d3.select('#embedded-error').style('display', isEmbedded ? 'block' : 'none');

// Prepare co2 scale
var maxCo2 = 800;
var co2color;
var co2Colorbars;
function updateCo2Scale() {
    if (colorBlindModeEnabled) {
      co2color = d3.scaleSequential(d3.interpolateMagma)
        .domain([2000, 0]);
    } else {
      co2color = d3.scaleLinear()
        .domain([0, 375, 725, 800])
        .range(['green', 'orange', 'rgb(26,13,0)'])
    }

    co2color.clamp(true);
    co2Colorbars = co2Colorbars || [];
    co2Colorbars.push(new HorizontalColorbar('.layer-toggles .co2-colorbar', co2color)
      .markerColor('white')
      .domain([0, maxCo2])
      .render());
    co2Colorbars.push(new HorizontalColorbar('.co2-floating-legend .co2-colorbar', co2color, null, [0, 400, 800])
      .markerColor('white')
      .domain([0, maxCo2])
      .render());
    if (countryMap) countryMap.co2color(co2color).render();
    if (countryTable) countryTable.co2color(co2color).render();
    if (countryHistoryCarbonGraph) countryHistoryCarbonGraph.yColorScale(co2color);
    if (countryHistoryMixGraph) countryHistoryMixGraph.co2color(co2color);
    if (exchangeLayer) exchangeLayer.co2color(co2color).render();
    if (countryListSelector)
        countryListSelector.select('div.emission-rect')
            .style('background-color', function(d) {
                return d.co2intensity ? co2color(d.co2intensity) : 'gray';
            });
}
d3.select('#checkbox-colorblind').node().checked = colorBlindModeEnabled;
d3.select('#checkbox-colorblind').on('change', function() {
    colorBlindModeEnabled = !colorBlindModeEnabled;
    Cookies.set('colorBlindModeEnabled', colorBlindModeEnabled);
    updateCo2Scale();
});
updateCo2Scale();

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
var countryMap = new CountryMap('#map', Wind, '#wind', Solar, '#solar')
    .co2color(co2color)
    .onDragEnd(function() {
        if (!mapDraggedSinceStart) { mapDraggedSinceStart = true };
    });
var exchangeLayer = new ExchangeLayer('svg.map-layer', '.arrows-layer').co2color(co2color);
countryMap.exchangeLayer(exchangeLayer);


var countryTableExchangeTooltip = new Tooltip('#countrypanel-exchange-tooltip')
var countryTableProductionTooltip = new Tooltip('#countrypanel-production-tooltip')
var countryTooltip = new Tooltip('#country-tooltip')
var exchangeTooltip = new Tooltip('#exchange-tooltip')
var countryTable = new CountryTable('.country-table', modeColor, modeOrder)
    .co2color(co2color)
    .onExchangeMouseMove(function() {
        countryTableExchangeTooltip.update(d3.event.clientX, d3.event.clientY);
    })
    .onExchangeMouseOver(function (d, country, displayByEmissions) {
        tooltipHelper.showExchange(
            countryTableExchangeTooltip,
            d, country, displayByEmissions,
            co2color, co2Colorbars)
    })
    .onExchangeMouseOut(function (d) {
        if (co2Colorbars) co2Colorbars.forEach(function(d) { d.currentMarker(undefined) });
        countryTableExchangeTooltip.hide()
    })
    .onProductionMouseOver(function (mode, country, displayByEmissions) {
        tooltipHelper.showProduction(
            countryTableProductionTooltip,
            mode, country, displayByEmissions,
            co2color, co2Colorbars)
    })
    .onProductionMouseMove(function(d) {
        countryTableProductionTooltip.update(d3.event.clientX, d3.event.clientY)
    })
    .onProductionMouseOut(function (d) {
        if (co2Colorbars) co2Colorbars.forEach(function(d) { d.currentMarker(undefined) });
        countryTableProductionTooltip.hide()
    });

var countryHistoryCarbonGraph = new LineGraph('#country-history-carbon',
    function(d) { return moment(d.stateDatetime).toDate(); },
    function(d) { return d.co2intensity; },
    function(d) { return d.co2intensity != null; })
    .yColorScale(co2color)
    .gradient(true);
var countryHistoryPricesGraph = new LineGraph('#country-history-prices',
    function(d) { return moment(d.stateDatetime).toDate(); },
    function(d) { return (d.price || {}).value; },
    function(d) { return d.price && d.price.value != null; })
    .gradient(false);
var countryHistoryMixGraph = new AreaGraph('#country-history-mix', modeColor, modeOrder)
    .co2color(co2color)
    .onLayerMouseOver(function(mode, countryData, i) {
        var isExchange = modeOrder.indexOf(mode) == -1
        var fun = isExchange ?
            tooltipHelper.showExchange : tooltipHelper.showProduction
        var ttp = isExchange ?
            countryTableExchangeTooltip : countryTableProductionTooltip
        fun(ttp,
            mode, countryData, tableDisplayEmissions,
            co2color, co2Colorbars)
        store.dispatch({
            type: 'SELECT_DATA',
            payload: { countryData: countryData, index: i }
        })
    })
    .onLayerMouseMove(function(mode, countryData, i) {
        var isExchange = modeOrder.indexOf(mode) == -1
        var fun = isExchange ?
            tooltipHelper.showExchange : tooltipHelper.showProduction
        var ttp = isExchange ?
            countryTableExchangeTooltip : countryTableProductionTooltip
        ttp.update(
            d3.event.clientX - 7,
            countryHistoryMixGraph.rootElement.node().getBoundingClientRect().top + 7)
        fun(ttp,
            mode, countryData, tableDisplayEmissions,
            co2color, co2Colorbars)
        store.dispatch({
            type: 'SELECT_DATA',
            payload: { countryData: countryData, index: i }
        })
    })
    .onLayerMouseOut(function(mode, countryData, i) {
        if (co2Colorbars) co2Colorbars.forEach(function(d) { d.currentMarker(undefined) });
        var isExchange = modeOrder.indexOf(mode) == -1
        var ttp = isExchange ?
            countryTableExchangeTooltip : countryTableProductionTooltip
        ttp.hide()
    });

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
countryHistoryMixGraph
    .displayByEmissions(tableDisplayEmissions);
d3.select('.country-show-emissions-wrap a#emissions')
    .classed('selected', tableDisplayEmissions);
d3.select('.country-show-emissions-wrap a#production')
    .classed('selected', !tableDisplayEmissions);

// Set weather checkboxes
d3.select('#checkbox-wind').node().checked = windEnabled;
d3.selectAll('.wind-toggle').classed('active', windEnabled);
d3.select('#checkbox-solar').node().checked = solarEnabled;
d3.selectAll('.solar-toggle').classed('active', solarEnabled);
d3.select('.layer-toggles').style('display', !showWindOption && !showSolarOption ? 'none' : null);

window.toggleSource = function(state) {
    if(state === undefined)
        state = !tableDisplayEmissions;
    tableDisplayEmissions = state;
    thirdPartyServices.track(
        tableDisplayEmissions ? 'switchToCountryEmissions' : 'switchToCountryProduction',
        {countryCode: countryTable.data().countryCode});
    countryTable
        .displayByEmissions(tableDisplayEmissions);
    countryHistoryMixGraph
        .displayByEmissions(tableDisplayEmissions);
    d3.select('.country-show-emissions-wrap a#emissions')
        .classed('selected', tableDisplayEmissions);
    d3.select('.country-show-emissions-wrap a#production')
        .classed('selected', !tableDisplayEmissions);
}

// Prepare data
var countries = CountryTopos.addCountryTopos({});
// Validate selected country
if (d3.keys(countries).indexOf(selectedCountryCode) == -1) {
    selectedCountryCode = undefined;
    if (showPageState == 'country') {
        showPageState = 'map';
        replaceHistoryState('page', showPageState);
    }
}
// Assign data
countryMap
    .data(d3.values(countries))
// Add configurations
d3.entries(zones_config).forEach(function(d) {
    var zone = countries[d.key];
    if (!zone) {
        console.warn('Zone ' + d.key + ' from configuration is not found. Ignoring..')
        return;
    }
    d3.entries(d.value).forEach(function(o) { zone[o.key] = o.value; });
    zone.shortname = translation.translate('zoneShortName.' + d.key);
    zone.capacity = d.value.capacity;
    zone.maxCapacity = d3.max(d3.values(zone.capacity));
    zone.maxStorageCapacity = d3.max(d3.entries(zone.capacity), function(d) {
        return (d.key.indexOf('storage') != -1) ? d.value : 0;
    });
});
// Add id to each zone
d3.entries(countries).forEach(function(d) {
    var zone = countries[d.key];
    zone.countryCode = d.key; // TODO: Rename to zoneId
})
var exchanges = exchanges_config;
d3.entries(exchanges).forEach(function(entry) {
    entry.value.countryCodes = entry.key.split('->').sort();
    if (entry.key.split('->')[0] != entry.value.countryCodes[0])
        console.error('Exchange sorted key pair ' + entry.key + ' is not sorted alphabetically');
});

var wind, solar;

var histories = {};

function selectCountry(countryCode, notrack) {
    if (!countries) { return; }
    if (countryCode && countries[countryCode]) {
        // Selected
        if (!notrack) {
            thirdPartyServices.track('countryClick', {countryCode: countryCode});
        }
        countryTable
            .powerScaleDomain(null) // Always reset scale if click on a new country
            .co2ScaleDomain(null)
            .exchangeKeys(null) // Always reset exchange keys
        store.dispatch({
            type: 'ZONE_DATA',
            payload: countries[countryCode]
        })

        var maxStorageCapacity = countries[countryCode].maxStorageCapacity


        function updateGraph(countryHistory) {
            // No export capacities are not always defined, and they are thus
            // varying the scale.
            // Here's a hack to fix it.
            var lo = d3.min(countryHistory, function(d) {
                return Math.min(
                    -d.maxStorageCapacity || -maxStorageCapacity || 0,
                    -d.maxStorage || 0,
                    -d.maxExport || 0,
                    -d.maxExportCapacity || 0);
            });
            var hi = d3.max(countryHistory, function(d) {
                return Math.max(
                    d.maxCapacity || 0,
                    d.maxProduction || 0,
                    d.maxImport || 0,
                    d.maxImportCapacity || 0,
                    d.maxDischarge || 0,
                    d.maxStorageCapacity || maxStorageCapacity || 0);
            });
            // TODO(olc): do those aggregates server-side
            var lo_emission = d3.min(countryHistory, function(d) {
                return Math.min(
                    // Max export
                    d3.min(d3.entries(d.exchange), function(o) {
                        return Math.min(o.value, 0) * d.exchangeCo2Intensities[o.key] / 1e3 / 60.0
                    })
                    // Max storage
                    // ?
                );
            });
            var hi_emission = d3.max(countryHistory, function(d) {
                return Math.max(
                    // Max import
                    d3.max(d3.entries(d.exchange), function(o) {
                        return Math.max(o.value, 0) * d.exchangeCo2Intensities[o.key] / 1e3 / 60.0
                    }),
                    // Max production
                    d3.max(d3.entries(d.production), function(o) {
                        return Math.max(o.value, 0) * d.productionCo2Intensities[o.key] / 1e3 / 60.0
                    })
                );
            });
            
            // Figure out the highest CO2 emissions
            var hi_co2 = d3.max(countryHistory, function(d) {
                return d.co2intensity;
            });
            countryHistoryCarbonGraph.y.domain([0, 1.1 * hi_co2]);

            // Create price color scale
            var priceExtent = d3.extent(countryHistory, function(d) {
                return (d.price || {}).value;
            })
            countryHistoryPricesGraph.y.domain(
                [Math.min(0, priceExtent[0]), 1.1 * priceExtent[1]]);

            countryHistoryCarbonGraph
                .data(countryHistory);
            countryHistoryPricesGraph
                .yColorScale(d3.scaleLinear()
                    .domain(countryHistoryPricesGraph.y.domain())
                    .range(['yellow', 'red']))
                .data(countryHistory);
            countryHistoryMixGraph
                .data(countryHistory);

            // Update country table with all possible exchanges
            countryTable
                .exchangeKeys(
                    countryHistoryMixGraph.exchangeKeysSet.values())
                .render()

            var firstDatetime = countryHistory[0] &&
                moment(countryHistory[0].stateDatetime).toDate();
            [countryHistoryCarbonGraph, countryHistoryPricesGraph, countryHistoryMixGraph].forEach(function(g) {
                if (currentMoment && firstDatetime) {
                    g.xDomain([firstDatetime, currentMoment.toDate()])
                }
                g.onMouseMove(function(d, i) {
                    if (!d) return;
                    // In case of missing data
                    if (!d.countryCode)
                        d.countryCode = countryCode;
                    countryTable
                        .powerScaleDomain([lo, hi])
                        .co2ScaleDomain([lo_emission, hi_emission])

                    if (g == countryHistoryCarbonGraph) {
                        tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars)
                        countryTooltip.update(
                            d3.event.clientX - 7,
                            g.rootElement.node().getBoundingClientRect().top + 7)
                    }

                    store.dispatch({
                        type: 'SELECT_DATA',
                        payload: { countryData: d, index: i }
                    })
                })
                .onMouseOut(function(d, i) {
                    countryTable
                        .powerScaleDomain(null)
                        .co2ScaleDomain(null)

                    if (g == countryHistoryCarbonGraph) {
                        countryTooltip.hide();
                    } else if (g == countryHistoryMixGraph) {
                        countryTableProductionTooltip.hide();
                        countryTableExchangeTooltip.hide();
                    }

                    store.dispatch({
                        type: 'SELECT_DATA',
                        payload: { countryData: countries[countryCode], index: undefined }
                    })
                })
                .render();
            })
        }

        // Load graph
        if (customDate) {
            console.error('Can\'t fetch history when a custom date is provided!');
        }
        else if (!histories[countryCode]) {
            LoadingService.startLoading('.country-history .loading');
            DataService.fetchHistory(ENDPOINT, countryCode, function(err, obj) {
                LoadingService.stopLoading('.country-history .loading');
                if (err) console.error(err);
                if (!obj || !obj.data) console.warn('Empty history received for ' + countryCode);
                if (err || !obj || !obj.data) {
                    updateGraph([]);
                    return;
                }

                // Add capacities
                if ((zones_config[countryCode] || {}).capacity) {
                    var maxCapacity = d3.max(d3.values(
                        zones_config[countryCode].capacity));
                    obj.data.forEach(function(d) {
                        d.capacity = zones_config[countryCode].capacity;
                        d.maxCapacity = maxCapacity;
                    });
                }

                // Save to local cache
                histories[countryCode] = obj.data;

                // Show
                updateGraph(histories[countryCode]);
            });
        } else {
            updateGraph(histories[countryCode]);
        }

        // Update contributors
        var selector = d3.selectAll('.contributors').selectAll('a')
            .data((zones_config[countryCode] || {}).contributors || []);
        var enterA = selector.enter().append('a')
            .attr('target', '_blank')
        var enterImg = enterA.append('img')
        enterA.merge(selector)
            .attr('href', function(d) { return d; })
        enterImg.merge(selector.select('img'))
            .attr('src', function(d) { return d + '.png'; })
        selector.exit().remove()
    }
    replaceHistoryState('countryCode', selectedCountryCode);
}
// Bind
countryMap
    .onSeaClick(function () { selectedCountryCode = undefined; showPage('map'); })
    .onCountryClick(function (d) { selectedCountryCode = d.countryCode; showPage('country'); });
d3.selectAll('#left-panel-country-back')
    .on('click', function() { selectedCountryCode = undefined; showPage(previousShowPageState || 'map'); });
d3.selectAll('#left-panel-highscore-back')
    .on('click', function() { showPage('map'); }); // only triggered on large screens
d3.selectAll('.highscore-button').on('click', function() { showPage('highscore'); });
d3.selectAll('.map-button').on('click', function() { showPage('map'); });
d3.selectAll('.info-button').on('click', function() { showPage('info'); });
if(showPageState) {
    showPage(showPageState);
}

function showPage(pageName) {

    if(pageName === undefined)
        pageName = 'map';

    showPageState = pageName;

    if (showPageState != 'country')
        previousShowPageState = showPageState;

    replaceHistoryState('page', showPageState);

    // Hide all panels - we will show only the ones we need
    d3.selectAll('.left-panel > div').style('display', 'none');
    d3.selectAll('.left-panel .left-panel-social').style('display', undefined);

    // Hide info screen on large screen only
    d3.selectAll('.left-panel .left-panel-info')
        // Only show on info or map
        .style('display', (pageName == 'info' || pageName == 'map') ? undefined : 'none')
        // but hide for small screens on all but info
        .classed('large-screen-visible', pageName != 'info');

    // Hide map on small screens
    // It's important we show the map before rendering it to make sure 
    // sizes are set properly
    d3.selectAll('#map-container').classed('large-screen-visible', pageName != 'map');

    if(pageName == 'map') {
        d3.select('.left-panel').classed('large-screen-visible', true);
        selectCountry(undefined);
        renderMap();
        if (windEnabled) { Wind.show(); }
        if (solarEnabled) { Solar.show(); }
        if (co2Colorbars) co2Colorbars.forEach(function(d) { d.render() });
        if (windEnabled && windColorbar) windColorbar.render();
        if (solarEnabled && solarColorbar) solarColorbar.render();
    }
    else {
        d3.select('.left-panel').classed('large-screen-visible', false);
        d3.selectAll('.left-panel-'+pageName).style('display', undefined);
        if (pageName == 'country') {
            selectCountry(selectedCountryCode);
        } else if (pageName == 'info') {
            if (co2Colorbars) co2Colorbars.forEach(function(d) { d.render() });
            if (windEnabled) if (windColorbar) windColorbar.render();
            if (solarEnabled) if (solarColorbar) solarColorbar.render();
        }
    }
 
    d3.selectAll('#tab .list-item:not(.wind-toggle):not(.solar-toggle)').classed('active', false);   
    d3.selectAll('#tab .' + pageName + '-button').classed('active', true);
}

// Now that the width is set, we can render the legends
if (windEnabled && !selectedCountryCode) windColorbar.render();
if (solarEnabled && !selectedCountryCode) solarColorbar.render();

// Attach event handlers
function toggleWind() {
    windEnabled = !windEnabled;
    replaceHistoryState('wind', windEnabled);
    Cookies.set('windEnabled', windEnabled);
    d3.select('.wind-toggle').classed('active', windEnabled);
    d3.select('#checkbox-wind').node().checked = windEnabled;
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
}
d3.select('#checkbox-wind').on('change', toggleWind);
d3.select('.wind-toggle').on('click', toggleWind);

function toggleSolar() {
    solarEnabled = !solarEnabled;
    replaceHistoryState('solar', solarEnabled);
    Cookies.set('solarEnabled', solarEnabled);
    d3.select('.solar-toggle').classed('active', solarEnabled);
    d3.select('#checkbox-solar').node().checked = solarEnabled;
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
}
d3.select('#checkbox-solar').on('change', toggleSolar);
d3.select('.solar-toggle').on('click', toggleSolar);

function mapMouseOver(coordinates) {
    if (windEnabled && wind && coordinates) {
        var lonlat = countryMap._absProjection.invert(coordinates);
        var now = customDate ? moment(customDate) : (new Date()).getTime();
        if (!Wind.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
            var u = grib.getInterpolatedValueAtLonLat(lonlat,
                now, wind.forecasts[0][0], wind.forecasts[1][0]);
            var v = grib.getInterpolatedValueAtLonLat(lonlat,
                now, wind.forecasts[0][1], wind.forecasts[1][1]);
            if (!selectedCountryCode)
              windColorbar.currentMarker(Math.sqrt(u * u + v * v));
        }
    } else {
        windColorbar.currentMarker(undefined);
    }
    if (solarEnabled && solar && coordinates) {
        var lonlat = countryMap._absProjection.invert(coordinates);
        var now = customDate ? moment(customDate) : (new Date()).getTime();
        if (!Solar.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
            var val = grib.getInterpolatedValueAtLonLat(lonlat,
                now, solar.forecasts[0], solar.forecasts[1]);
            if (!selectedCountryCode)
              solarColorbar.currentMarker(val);
        }
    } else {
        solarColorbar.currentMarker(undefined);
    }
}
d3.select('.map-layer')
    .on('mousemove', function() {
        mapMouseOver(d3.mouse(this));
    })
    .on('mouseout', function() {
        mapMouseOver(undefined);
    });

function renderMap() {
    if (!countryMap) { return; }

    countryMap.render();
    
    if (!countryMap.projection()) {
        return;
    }
    if (!countryMap.center() && !isCordova) {
        // Cordova will handle this differently
        // This should be given by the server
        var geolocation = geo && [geo.ll[1], geo.ll[0]];
        if (selectedCountryCode) {
            var lon = d3.mean(countries[selectedCountryCode].coordinates[0][0], function(d) { return d[0]; });
            var lat = d3.mean(countries[selectedCountryCode].coordinates[0][0], function(d) { return d[1]; });
            countryMap.center([lon, lat]);
        }
        else if (geolocation) {
            console.log('Centering on', geolocation);
            countryMap.center(geolocation);
        }
        else {
            countryMap.center([0, 50]);
        }
    }
    exchangeLayer
        .projection(countryMap.projection())
        .render();

    if (!showWindOption)
        d3.select(d3.select('#checkbox-wind').node().parentNode).style('display', 'none');
    if (windEnabled && wind && wind['forecasts'][0] && wind['forecasts'][1]) {
        LoadingService.startLoading();
        // Make sure to disable wind if the drawing goes wrong
        Cookies.set('windEnabled', false);
        Wind.draw('#wind',
            customDate ? moment(customDate) : moment(new Date()),
            wind.forecasts[0],
            wind.forecasts[1],
            windColor,
            countryMap.absProjection());
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
        LoadingService.startLoading();
        // Make sure to disable solar if the drawing goes wrong
        Cookies.set('solarEnabled', false);
        Solar.draw('#solar',
            customDate ? moment(customDate) : moment(new Date()),
            solar.forecasts[0],
            solar.forecasts[1],
            solarColor,
            countryMap.absProjection(),
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
}

var countryListSelector;

function dataLoaded(err, clientVersion, state, argSolar, argWind) {
    if (err) {
        console.error(err);
        return;
    }

    thirdPartyServices.track('pageview', {
        'bundleVersion': bundleHash,
        'clientType': clientType,
        'embeddedUri': isEmbedded ? document.referrer : null,
        'windEnabled': windEnabled,
        'solarEnabled': solarEnabled,
        'colorBlindModeEnabled': colorBlindModeEnabled
    });

    // // Debug: randomly generate (consistent) data
    // Object.keys(countries).forEach(function(k) {
    //     if (state.countries[k])
    //         state.countries[k].co2intensity = Math.random() * 800;
    // });
    // Object.keys(exchanges).forEach(function(k) {
    //     if (state.exchanges[k]) {
    //         state.exchanges[k].netFlow = Math.random() * 1500 - 700;
    //         var countries = state.exchanges[k].countryCodes;
    //         var o = countries[(state.exchanges[k].netFlow >= 0) ? 0 : 1]
    //         state.exchanges[k].co2intensity = state.countries[o].co2intensity;
    //     }
    // });
    // // Debug: expose a fetch method
    // window.forceFetchNow = fetch;

    // Is there a new version?
    d3.select('#new-version')
        .classed('active', (clientVersion != bundleHash && !isLocalhost && !isCordova));

    // TODO: Code is duplicated
    currentMoment = (customDate && moment(customDate) || moment(state.datetime));
    d3.selectAll('.current-datetime').text(currentMoment.format('LL LT'));
    d3.selectAll('.current-datetime-from-now').text(currentMoment.fromNow());
    d3.selectAll('#current-datetime, #current-datetime-from-now')
        .style('color', 'darkred')
        .transition()
            .duration(800)
            .style('color', undefined);

    // Reset all data
    d3.entries(countries).forEach(function(entry) {
        entry.value.co2intensity = undefined;
        entry.value.exchange = {};
        entry.value.production = {};
        entry.value.productionCo2Intensities = {};
        entry.value.productionCo2IntensitySources = {};
        entry.value.dischargeCo2Intensities = {};
        entry.value.dischargeCo2IntensitySources = {};
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
        // Set date
        country.datetime = state.datetime;
        // Validate data
        if (!country.production) return;
        modeOrder.forEach(function (mode) {
            if (mode == 'other' || mode == 'unknown' || !country.datetime) return;
            // Check missing values
            // if (country.production[mode] === undefined && country.storage[mode] === undefined)
            //    console.warn(countryCode + ' is missing production or storage of ' + mode);
            // Check validity of production
            if (country.production[mode] !== undefined && country.production[mode] < 0)
                console.error(countryCode + ' has negative production of ' + mode);
            // Check validity of storage
            if (country.storage[mode] !== undefined && country.storage[mode] < 0)
                console.error(countryCode + ' has negative storage of ' + mode);
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

    // Render country list
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
        .append('span')
            .attr('class', 'name')
    enterA
        .append('img')
            .attr('class', 'flag')
    enterA
        .append('span')
            .attr('class', 'rank')
    var selector = enterA.merge(selector);
    countryListSelector = selector;
    selector.select('span.name')
        .text(function(d) { return ' ' + (translation.translate('zoneShortName.' + d.countryCode) || d.countryCode) + ' '; })
    selector.select('div.emission-rect')
        .style('background-color', function(d) {
            return d.co2intensity ? co2color(d.co2intensity) : 'gray';
        });
    selector.select('.flag')
        .attr('src', function(d) { return flags.flagUri(d.countryCode, 16); });
    // selector.select('span.rank')
    //     .html(function(d, i) { return ' (' + Math.round(d.co2intensity) + ' gCO<sub>2</sub>eq/kWh)' })
    selector.on('click', function(d) { selectedCountryCode = d.countryCode; showPage('country'); });

    // Assign country map data
    countryMap
        .data(d3.values(countries))

    // Add mouse over handlers
    countryMap.onCountryMouseOver(function (d) {
        d3.select(this)
            .style('opacity', 0.8)
            .style('cursor', 'pointer')
        tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars)
    })
    .onCountryMouseMove(function () {
        countryTooltip.update(d3.event.clientX, d3.event.clientY);
    })
    .onCountryMouseOut(function (d) {
        d3.select(this)
            .style('opacity', 1)
            .style('cursor', 'auto')
        if (d.co2intensity && co2Colorbars)
            co2Colorbars.forEach(function(c) { c.currentMarker(undefined) });
        countryTooltip.hide();
    });

    // Re-render country table if it already was visible
    if (selectedCountryCode)
        countryTable.data(countries[selectedCountryCode]).render()
    selectCountry(selectedCountryCode, true);

    // Populate exchange pairs for arrows
    d3.entries(state.exchanges).forEach(function(obj) {
        var exchange = exchanges[obj.key];
        if (!exchange || !exchange.lonlat) {
            console.error('Missing exchange configuration for ' + obj.key);
            return;
        }
        // Copy data
        d3.keys(obj.value).forEach(function(k) {
            exchange[k] = obj.value[k];
        });
    });

    // Render exchanges
    if (countryMap.projection()) {
        exchangeLayer.projection(countryMap.projection())
    }
    exchangeLayer
        .data(d3.values(exchanges).filter(function(d) {
            return d.netFlow != 0 && d.netFlow != null && d.lonlat;
        }))
        .onExchangeMouseOver(function (d) {
            d3.select(this)
                .style('opacity', 0.8)
                .style('cursor', 'pointer');
            tooltipHelper.showMapExchange(exchangeTooltip, d, co2color, co2Colorbars)
        })
        .onExchangeMouseMove(function () {
            exchangeTooltip.update(d3.event.clientX, d3.event.clientY);
        })
        .onExchangeMouseOut(function (d) {
            d3.select(this)
                .style('opacity', 1)
                .style('cursor', 'auto')
            if (d.co2intensity && co2Colorbars)
                co2Colorbars.forEach(function(c) { c.currentMarker(undefined) });
            exchangeTooltip.hide()
        })
        .render();

    // Render weather if provided
    // Do not overwrite with null/undefined
    if (argWind) wind = argWind;
    if (argSolar) solar = argSolar;

    // Update pages that need to be updated
    renderMap();

    // Debug
    console.log(countries)
};

function getCountryCode(lonlat, callback) {
    // Deactivated for now (UX was confusing)
    callback(null, null);
    return;

    d3.json('http://maps.googleapis.com/maps/api/geocode/json?latlng=' + lonlat[1] + ',' + lonlat[1], function (err, response) {
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
        d3.select('#connection-warning').classed('active', true);
    } else {
        d3.select('#connection-warning').classed('active', false);
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
        d3.select('#connection-warning').classed('active', true);
    }, 15 * 1000);
    var Q = d3.queue();
    // We ignore errors in case this is run from a file:// protocol (e.g. cordova)
    if (!isCordova) {
        Q.defer(d3.text, '/clientVersion');
    } else {
        Q.defer(DataService.fetchNothing);
    }
    Q.defer(DataService.fetchState, ENDPOINT, customDate);

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

    Q.await(function(err, clientVersion, state, solar, wind) {
        handleConnectionReturnCode(err);
        if (!err)
            dataLoaded(err, clientVersion, state.data, solar, wind);
        if (showLoading) LoadingService.stopLoading();
        if (callback) callback();
    });
};

function fetchAndReschedule() {
    // TODO(olc): Use `setInterval` instead of `setTimeout`
    if (!customDate)
        return fetch(false, function() {
            setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
        });
};

function redraw() {
    if (selectedCountryCode) {
        countryTable.render();
        countryHistoryCarbonGraph.render();
        countryHistoryPricesGraph.render();
        countryHistoryMixGraph.render();
    }
    countryMap.render();
    co2Colorbars.forEach(function(d) { d.render() });
    if (countryMap.projection()) {
        exchangeLayer
            .projection(countryMap.projection())
            .render();
    }
};

window.addEventListener('resize', function() {
    redraw();
});
window.retryFetch = function() {
    d3.select('#connection-warning').classed('active', false);
    clearInterval(connectionWarningTimeout);
    fetch(false);
}

// Observe for countryTable re-render
observeStore(store, function(state) { return state.countryData }, function(d) {
    countryTable
        .data(d)
        .render(true);
})
// Observe for history graph index change
observeStore(store, function(state) { return state.countryDataIndex }, function(i) {
    [countryHistoryCarbonGraph, countryHistoryMixGraph, countryHistoryPricesGraph].forEach(function(g) {
        g.selectedIndex(i)
    })
})

// Start a fetch showing loading.
// Later `fetchAndReschedule` won't show loading screen
fetch(true, function() {
    setTimeout(fetchAndReschedule, REFRESH_TIME_MINUTES * 60 * 1000);
});
