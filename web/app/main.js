// Libraries
var Cookies = require('js-cookie');
var d3 = require('d3');
var moment = require('moment');
var getSymbolFromCurrency = require('currency-symbol-map').getSymbolFromCurrency;

// Modules
//var AreaGraph = require('./areagraph');
var LineGraph = require('./linegraph');
var CountryMap = require('./countrymap');
var CountryTable = require('./countrytable');
var CountryTopos = require('./countrytopos');
var DataService = require('./dataservice');
var ExchangeConfig = require('./exchangeconfig');
var ExchangeLayer = require('./exchangelayer');
var flags = require('./flags');
var grib = require('./grib');
var HorizontalColorbar = require('./horizontalcolorbar');
var lang = require('json-loader!./configs/lang.json')[locale];
var LoadingService = require('./loadingservice');
var Solar = require('./solar');
var Tooltip = require('./tooltip');
var Wind = require('./wind');

// Configs
var capacities = require('json-loader!../../config/capacities.json');
var zones = require('json-loader!../../config/zones.json');

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
var selectedCountryCode;
var useRemoteEndpoint = true;
var customDate;
var currentMoment;
var colorBlindModeEnabled = false;
var showPageState = 'map';
var previousShowPageState = undefined;
var showWindOption = true;
var showSolarOption = true;
var windEnabled = showWindOption ? (Cookies.get('windEnabled') == 'true' || false) : false;
var solarEnabled = showSolarOption ? (Cookies.get('solarEnabled') == 'true' || false) : false;

function isMobile() {
    return (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent);
}

// Read query string
function parseQueryString(querystring) {
    args = querystring.replace('\?','').split('&');
    args.forEach(function(arg) {
        kv = arg.split('=');
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
            showPageState = kv[1];
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

// Initialise mobile app (cordova)
var app = {
    // Application Constructor
    initialize: function() {
        this.bindEvents();
    },

    bindEvents: function () {
        document.addEventListener('deviceready', this.onDeviceReady, false);
        document.addEventListener('resume', this.onResume, false);
    },

    onDeviceReady: function() {
        // We will init / bootstrap our application here
        codePush.sync(null, {installMode: InstallMode.ON_NEXT_RESUME});
        universalLinks.subscribe(null, function (eventData) {
            // do some work
            parseQueryString(eventData.url.split('?')[1] || eventData.url);
        });
    },

    onResume: function() {
        codePush.sync(null, {installMode: InstallMode.ON_NEXT_RESUME});
    }
};
app.initialize();

// Computed State
var colorBlindModeEnabled = Cookies.get('colorBlindModeEnabled') == 'true' || false;
var isLocalhost = window.location.href.indexOf('electricitymap') == -1;
var isEmbedded = window.top !== window.self;
var REMOTE_ENDPOINT = 'https://api.electricitymap.org';
var LOCAL_ENDPOINT = 'http://localhost:9000';
var ENDPOINT = (document.domain != '' && document.domain.indexOf('electricitymap') == -1 && !useRemoteEndpoint) ?
    LOCAL_ENDPOINT : REMOTE_ENDPOINT;

// Set history state of remaining variables
replaceHistoryState('wind', windEnabled);
replaceHistoryState('solar', solarEnabled);

// Twitter
window.twttr = (function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0],
    t = window.twttr || {};
    if (d.getElementById(id)) return t;
    js = d.createElement(s);
    js.id = id;
    js.src = "https://platform.twitter.com/widgets.js";
    fjs.parentNode.insertBefore(js, fjs);

    t._e = [];
    t.ready = function(f) {
        t._e.push(f);
    };

    return t;
}(document, "script", "twitter-wjs"));

// Facebook
window.fbAsyncInit = function() {
    FB.init({
        appId      : '1267173759989113',
        xfbml      : true,
        version    : 'v2.8'
    });
    if (!isLocalhost) {
        FB.AppEvents.logPageView('pageview');
    }
};

(function(d, s, id){
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) {return;}
    js = d.createElement(s); js.id = id;
    //js.src = "https://connect.facebook.net/" + FBLocale + "/sdk.js";
    // Do not translate facebook because we fixed the size of buttons
    // because of a cordova bug serving from file://
    js.src = "https://connect.facebook.net/en_US/sdk.js";
    fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));

if (!isLocalhost) {
    var clientType = 'web';
    if (isCordova) { clientType = 'mobileapp'; }

    // Mixpanel
    (function(e,b){if(!b.__SV){var a,f,i,g;window.mixpanel=b;b._i=[];b.init=function(a,e,d){function f(b,h){var a=h.split(".");2==a.length&&(b=b[a[0]],h=a[1]);b[h]=function(){b.push([h].concat(Array.prototype.slice.call(arguments,0)))}}var c=b;"undefined"!==typeof d?c=b[d]=[]:d="mixpanel";c.people=c.people||[];c.toString=function(b){var a="mixpanel";"mixpanel"!==d&&(a+="."+d);b||(a+=" (stub)");return a};c.people.toString=function(){return c.toString(1)+".people (stub)"};i="disable time_event track track_pageview track_links track_forms register register_once alias unregister identify name_tag set_config reset people.set people.set_once people.increment people.append people.union people.track_charge people.clear_charges people.delete_user".split(" ");
    for(g=0;g<i.length;g++)f(c,i[g]);b._i.push([a,e,d])};b.__SV=1.2;a=e.createElement("script");a.type="text/javascript";a.async=!0;a.src="undefined"!==typeof MIXPANEL_CUSTOM_LIB_URL?MIXPANEL_CUSTOM_LIB_URL:"file:"===e.location.protocol&&"//cdn.mxpnl.com/libs/mixpanel-2-latest.min.js".match(/^\/\//)?"https://cdn.mxpnl.com/libs/mixpanel-2-latest.min.js":"//cdn.mxpnl.com/libs/mixpanel-2-latest.min.js";f=e.getElementsByTagName("script")[0];f.parentNode.insertBefore(a,f)}})(document,window.mixpanel||[]);
    mixpanel.init('f350f1ec866f4737a5f69497e58cf67d');
    mixpanel.track('Visit', {
        'bundleVersion': bundleHash,
        'clientType': clientType,
        'embeddedUri': isEmbedded ? document.referrer : null,
        'windEnabled': windEnabled,
        'solarEnabled': solarEnabled
    });

    // Google Analytics
    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
      (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
      m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
      })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');
      ga('create', 'UA-79729918-1', 'auto');
      ga('send', 'pageview');
}

if (!isLocalhost) {
  _opbeat = window._opbeat || function() {
      (window._opbeat.q = window._opbeat.q || []).push(arguments)
  };
  if (typeof _opbeat !== 'undefined') {
      _opbeat('config', {
          orgId: '093c53b0da9d43c4976cd0737fe0f2b1',
          appId: 'f40cef4b37'
      });
      _opbeat('setExtraContext', {
          bundleHash: bundleHash
      });
  } else {
      console.warn('Opbeat could not be initialized!');
  }
}

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
moment.locale(locale.toLowerCase());

// Display embedded warning
// d3.select('#embedded-error').style('display', isEmbedded ? 'block' : 'none');

// Prepare co2 scale
var maxCo2 = 800;
var co2color;
var co2Colorbar;
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
    co2Colorbar = new HorizontalColorbar('.co2-colorbar', co2color)
      .markerColor('white')
      .domain([0, maxCo2])
      .render();
    if (countryMap) countryMap.co2color(co2color).render();
    if (countryTable) countryTable.co2color(co2color).render();
    if (countryHistoryGraph) countryHistoryGraph.yColorScale(co2color);
    if (exchangeLayer) exchangeLayer.co2color(co2color).render();
    if (tooltip)
      tooltip
        .co2color(co2color)
        .co2Colorbar(co2Colorbar);
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
var countryMap = new CountryMap('#map', Wind, '.wind', Solar, '.solar')
    .co2color(co2color);
var exchangeLayer = new ExchangeLayer('svg.map-layer', '.arrows-layer').co2color(co2color);
countryMap.exchangeLayer(exchangeLayer);
var countryTable = new CountryTable('.country-table', modeColor, modeOrder).co2color(co2color);
var tooltip = new Tooltip(countryTable, countries)
    .co2color(co2color)
    .co2Colorbar(co2Colorbar);
//var countryHistoryGraph = new AreaGraph('.country-history', modeColor, modeOrder);
var countryHistoryGraph = new LineGraph('.country-history',
    function(d) { return moment(d.stateDatetime).toDate(); },
    function(d) { return d.co2intensity; },
    function(d) { return d.co2intensity != null; }).yColorScale(co2color);
countryHistoryGraph.y.domain([0, maxCo2]);

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
    trackAnalyticsEvent(
        tableDisplayEmissions ? 'switchToCountryEmissions' : 'switchToCountryProduction',
        {countryCode: countryTable.data().countryCode});
    countryTable
        .displayByEmissions(tableDisplayEmissions);
    d3.select('.country-show-emissions-wrap a#emissions')
        .classed('selected', tableDisplayEmissions);
    d3.select('.country-show-emissions-wrap a#production')
        .classed('selected', !tableDisplayEmissions);
}

// Tooltips
// TODO: Move to module together with countrymap tooltip
function placeTooltip(selector, d3Event) {
    var tooltip = d3.select(selector);
    var w = tooltip.node().getBoundingClientRect().width;
    var h = tooltip.node().getBoundingClientRect().height;
    var margin = 5;
    var mapWidth = d3.select('#map-container').node().getBoundingClientRect().width;

    // TODO: d3Event.layerY does not return the proper cursor coordinates.
    // or it needs to be remapped to container coordinates..

    // On very small screens
    if (w > mapWidth) {
        tooltip
            .style('width', '100%');
    }
    else {
        var x = 0;
        if (w > mapWidth / 2 - 5) {
            // Tooltip won't fit on any side, so don't translate x
            x = 0.5 * (mapWidth - w);
        } else {
            x = d3Event.layerX + margin;
            if (mapWidth - x <= w) {
                x = d3Event.layerX - w - margin;
            }
        }
        var y = d3Event.layerY - h - margin; if (y <= margin) y = d3Event.layerY + margin;
        tooltip
            .style('transform',
                'translate(' + x + 'px' + ',' + y + 'px' + ')');
    }
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
d3.entries(zones).forEach(function(d) {
    var zone = countries[d.key];
    d3.entries(d.value).forEach(function(o) { zone[o.key] = o.value; });
    // Add translation
    zone.shortname = lang && lang.zoneShortName[d.key];
});
// Add capacities
d3.entries(capacities).forEach(function(d) {
    var zone = countries[d.key];
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
var exchanges = {};
ExchangeConfig.addExchangesConfiguration(exchanges);
d3.entries(exchanges).forEach(function(entry) {
    entry.value.countryCodes = entry.key.split('->').sort();
    if (entry.key.split('->')[0] != entry.value.countryCodes[0])
        console.error('Exchange sorted key pair ' + entry.key + ' is not sorted alphabetically');
});
var wind, solar, geolocation;

var histories = {};

function selectCountry(countryCode, notrack) {
    if (!countries) { return; }
    if (countryCode && countries[countryCode]) {
        // Selected
        if (!notrack)
            trackAnalyticsEvent('countryClick', {countryCode: countryCode});
        countryTable
            .data(countries[countryCode])
            .powerScaleDomain(null) // Always reset scale if click on a new country
            .render();

        function updateGraph(countryHistory) {
            // No export capacities are not always defined, and they are thus
            // varying the scale.
            // Here's a hack to fix it.
            var lo = d3.min(countryHistory, function(d) {
                return Math.min(
                    -d.maxStorageCapacity || 0,
                    -d.maxStorage || 0,
                    -d.maxExport || 0,
                    -d.maxExportCapacity || 0);
            });
            var hi = d3.max(countryHistory, function(d) {
                return Math.max(
                    d.maxCapacity || 0,
                    d.maxProduction || 0,
                    d.maxImport || 0,
                    d.maxImportCapacity || 0);
            });

            // Figure out the highest CO2 emissions
            var hi_co2 = d3.max(countryHistory, function(d) {
                return d.co2intensity;
            });
            countryHistoryGraph.y.domain([0, Math.max(maxCo2, hi_co2)]);

            // Set x domain based on current time
            if (countryHistory.length && currentMoment)
                countryHistoryGraph.x.domain(
                    d3.extent([
                      countryHistoryGraph.xAccessor(countryHistory[0]),
                      currentMoment.toDate()]));

            countryHistoryGraph
                .data(countryHistory);
            if (countryHistoryGraph.frozen) {
                var data = countryHistoryGraph.data()[countryHistoryGraph.selectedIndex];
                if (!data) {
                    // This country has no history at this time
                    // Reset view
                    countryTable
                        .data({countryCode: countryCode})
                        .render()
                } else {
                    countryTable
                        .data(data)
                        .powerScaleDomain([lo, hi])
                        .render()
                }
            }
            countryHistoryGraph
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

                // Save to local cache
                histories[countryCode] = obj.data;

                // Show
                updateGraph(histories[countryCode]);
            });
        else
            updateGraph(histories[countryCode]);
    }
    replaceHistoryState('countryCode', selectedCountryCode);
}
// Bind
countryMap
    .onSeaClick(function () { selectedCountryCode = undefined; showPage('map'); })
    .onCountryClick(function (d) { selectedCountryCode = d.countryCode; console.log(d); showPage('country'); });
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
        if (co2Colorbar) co2Colorbar.render();
        if (windEnabled) if (windColorbar) windColorbar.render();
        if (solarEnabled) if (solarColorbar) solarColorbar.render();
    }
    else {
        d3.select('.left-panel').classed('large-screen-visible', false);
        d3.selectAll('.left-panel-'+pageName).style('display', undefined);
        if (pageName == 'country') {
            selectCountry(selectedCountryCode);
        } else if (pageName == 'info') {
            if (co2Colorbar) co2Colorbar.render();
            if (windEnabled) if (windColorbar) windColorbar.render();
            if (solarEnabled) if (solarColorbar) solarColorbar.render();
        }
    }
 
    d3.selectAll('#bottom-menu .list-item').classed('active', false);   
    d3.selectAll('#bottom-menu .' + pageName + '-button').classed('active', true);
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
    if (!countryMap) { return ; }

    countryMap.render();
    
    if (!countryMap.projection()) {
        return;
    }

    if (!countryMap.center()) {
        if (geolocation) {
            countryMap.center(geolocation);
        } else if (selectedCountryCode) {
            var lon = d3.mean(countries[selectedCountryCode].coordinates[0][0], function(d) { return d[0]; });
            var lat = d3.mean(countries[selectedCountryCode].coordinates[0][0], function(d) { return d[1]; });
            countryMap.center([lon, lat]);
        } else {
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
        Wind.draw('.wind',
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
        Solar.draw('.solar',
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

function dataLoaded(err, clientVersion, state, argSolar, argWind, argGeolocation) {
    if (err) {
        console.error(err);
        return;
    }

    // Debug: randomly generate data
    // Object.keys(exchanges).forEach(function(k) {
    //     if (state.exchanges[k]) {
    //         state.exchanges[k].netFlow = Math.random() * 1500 - 700;
    //         state.exchanges[k].co2intensity = Math.random() * 800;
    //     }
    // });
    // Object.keys(countries).forEach(function(k) {
    //     if (state.countries[k])
    //         state.countries[k].co2intensity = Math.random() * 800;
    // });

    // Is there a new version?
    d3.select('#new-version')
        .style('top', (clientVersion === bundleHash || useRemoteEndpoint) ? undefined : 0);

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
            // Check missing capacities
            // if (country.production[mode] !== undefined &&
            //     (country.capacity || {})[mode] === undefined)
            // {
            //     console.warn(countryCode + ' is missing capacity of ' + mode);
            // }
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
    enterA
        .append('img')
            .attr('class', 'flag')
    var selector = enterA.merge(selector);
    countryListSelector = selector;
    selector.select('span')
        .text(function(d) { return ' ' + (lang.zoneShortName[d.countryCode] || d.countryCode) + ' '; })
    selector.select('div.emission-rect')
        .style('background-color', function(d) {
            return d.co2intensity ? co2color(d.co2intensity) : 'gray';
        });
    selector.select('.flag')
        .attr('src', function(d) { return flags.flagUri(d.countryCode, 16); });
    selector.on('click', function(d) { selectedCountryCode = d.countryCode; showPage('country'); });

    // Assign country map data
    countryMap
        .data(d3.values(countries))

    // Add mouse over handlers
    countryMap.onCountryMouseOver(function (d) {
        d3.select(this)
            .style('opacity', 0.8)
            .style('cursor', 'pointer')
        if (d.co2intensity && co2Colorbar)
            co2Colorbar.currentMarker(d.co2intensity);
        var tooltip = d3.select('#country-tooltip');
        tooltip.classed('country-tooltip-visible', true);
        tooltip.select('#country-flag')
            .attr('src', flags.flagUri(d.countryCode, 16));
        tooltip.select('#country-name')
            .text(lang.zoneShortName[d.countryCode] || d.countryCode)
            .style('font-weight', 'bold');
        tooltip.select('.emission-rect')
            .style('background-color', d.co2intensity ? co2color(d.co2intensity) : 'gray');
        tooltip.select('.country-emission-intensity')
            .text(Math.round(d.co2intensity) || '?');

        var priceData = d.price || {};
        var hasPrice = priceData.value != null;
        tooltip.select('.country-spot-price')
            .text(hasPrice ? Math.round(priceData.value) : '?')
            .style('color', (priceData.value || 0) < 0 ? 'red' : undefined);
        tooltip.select('.country-spot-price-currency')
            .text(getSymbolFromCurrency(priceData.currency) || priceData.currency || '?')
        var hasFossilFuelData = d.fossilFuelRatio != null;
        var fossilFuelPercent = d.fossilFuelRatio * 100;
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
        d3.select('#country-tooltip').classed('country-tooltip-visible', false);
    });

    // Re-render country table if it already was visible
    if (selectedCountryCode && !countryHistoryGraph.frozen)
        countryTable.data(countries[selectedCountryCode]).render()
    selectCountry(selectedCountryCode, true);

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

    // Render exchanges
    if (countryMap.projection()) {
        exchangeLayer.projection(countryMap.projection())
    }
    exchangeLayer
        .data(d3.values(exchanges).filter(function(d) {
            return d.netFlow != 0 && d.netFlow != null;
        }))
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
            var ctrFrom = d.countryCodes[i];
            tooltip.selectAll('span#from')
                .text(lang.zoneShortName[ctrFrom] || ctrFrom);
            var ctrTo = d.countryCodes[(i + 1) % 2];
            tooltip.select('span#to')
                .text(lang.zoneShortName[ctrTo] || ctrTo);
            tooltip.select('span#flow')
                .text(Math.abs(Math.round(d.netFlow)));
            tooltip.select('img.flag.from')
                .attr('src', flags.flagUri(d.countryCodes[i], 16));
            tooltip.select('img.flag.to')
                .attr('src', flags.flagUri(d.countryCodes[(i + 1) % 2], 16));
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

    // Render weather if provided
    // Do not overwrite with null/undefined
    if (argWind) wind = argWind;
    if (argSolar) solar = argSolar;
    if (argGeolocation) geolocation = argGeolocation;

    // Update pages that need to be updated
    renderMap();

    // Debug
    console.log(countries)
};

// Get geolocation is on mobile (in order to select country)
function geolocalise(callback) {
    // Deactivated for now (too slow)
    callback(null, null);
    return;

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            var lonlat = [position.coords.longitude, position.coords.latitude];
            console.log('Current position is', lonlat);
            callback(null, lonlat);
        }, function(err) {
            console.warn(err);
            callback(null, null);
        });
    } else {
        console.warn(Error('Browser geolocation is not supported'));
        callback(null, null);
    }
}
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
    // We ignore errors in case this is run from a file:// protocol (e.g. cordova)
    Q.defer(ignoreError(d3.text), '/clientVersion');
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

    Q.defer(geolocalise);
    Q.await(function(err, clientVersion, state, solar, wind, geolocation) {
        handleConnectionReturnCode(err);
        if (!err)
            dataLoaded(err, clientVersion, state.data, solar, wind, geolocation);
        if (showLoading) LoadingService.stopLoading();
        if (callback) callback();
    });
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
    countryMap.render();
    co2Colorbar.render();
    if (countryMap.projection()) {
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
