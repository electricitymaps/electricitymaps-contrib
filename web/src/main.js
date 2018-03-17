'use strict';

import ZoneMap from './components/map';
// see https://stackoverflow.com/questions/36887428/d3-event-is-null-in-a-reactjs-d3js-component
import { event as currentEvent } from 'd3-selection';
import CircularGauge from './components/circulargauge';

// Libraries
const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-queue'),
  require('d3-request'),
  require('d3-scale'),
  require('d3-selection'),
);
const Cookies = require('js-cookie');
const moment = require('moment');

// State management
const { dispatch, getState, observe } = require('./store');

// Components
const AreaGraph = require('./components/areagraph');
const LineGraph = require('./components/linegraph');
const CountryTable = require('./components/countrytable');
const HorizontalColorbar = require('./components/horizontalcolorbar');
const Tooltip = require('./components/tooltip');

// Layer Components
const ExchangeLayer = require('./components/layers/exchange');
const SolarLayer = require('./components/layers/solar');
const WindLayer = require('./components/layers/wind');

// Services
const DataService = require('./services/dataservice');
const LoadingService = require('./services/loadingservice');
const thirdPartyServices = require('./services/thirdparty');

// Helpers
const { modeOrder, modeColor } = require('./helpers/constants');
const flags = require('./helpers/flags');
const grib = require('./helpers/grib');
const HistoryState = require('./helpers/historystate');
const scales = require('./helpers/scales');
const tooltipHelper = require('./helpers/tooltip');
const translation = require('./helpers/translation');

const getSymbolFromCurrency = require('currency-symbol-map');

// Configs
const zonesConfig = require('../../config/zones.json');

// Constants
// TODO(olc): should this be moved to constants.js?
const REMOTE_ENDPOINT = 'https://api.electricitymap.org';
const LOCAL_ENDPOINT = 'http://localhost:9000';

// Timing
if (thirdPartyServices._ga) {
  thirdPartyServices._ga.timingMark('start_executing_js');
}

// Constants
const REFRESH_TIME_MINUTES = 5;

function dispatchApplication(key, value) {
  // Do not dispatch unnecessary events
  if (getState().application[key] === value) {
    return;
  }
  dispatch({
    key,
    value,
    type: 'APPLICATION_STATE_UPDATE',
  });
}

// Set state depending on URL params
HistoryState.parseInitial(window.location.search);
const applicationState = HistoryState.getStateFromHistory();
Object.keys(applicationState).forEach((k) => {
  if (k === 'selectedZoneName' &&
    Object.keys(getState().data.grid.zones).indexOf(applicationState[k]) === -1) {
    // The selectedZoneName doesn't exist, so don't update it
    return;
  }
  dispatchApplication(k, applicationState[k]);
});

// TODO(olc): should be stored in redux?
const ENDPOINT = getState().application.useRemoteEndpoint ?
  REMOTE_ENDPOINT : LOCAL_ENDPOINT;

// TODO(olc) move those to redux state
// or to component state
let currentMoment;
let mapDraggedSinceStart = false;
let mapLoaded = false;
let wind;
let solar;
let tableDisplayEmissions = false;
let hasCenteredMap = false;

// Set up objects
let exchangeLayer = null;
LoadingService.startLoading('#loading');
LoadingService.startLoading('#small-loading');
let zoneMap;
let windLayer;
let solarLayer;

// ** Create components
const countryTable = new CountryTable('.country-table', modeColor, modeOrder);
const countryHistoryCarbonGraph = new LineGraph(
  '#country-history-carbon',
  d => moment(d.stateDatetime).toDate(),
  d => d.co2intensity,
  d => d.co2intensity != null,
);
const countryHistoryPricesGraph = new LineGraph(
  '#country-history-prices',
  d => moment(d.stateDatetime).toDate(),
  d => (d.price || {}).value,
  d => d.price && d.price.value != null,
).gradient(false);
const countryHistoryMixGraph = new AreaGraph('#country-history-mix', modeColor, modeOrder);

const countryTableExchangeTooltip = new Tooltip('#countrypanel-exchange-tooltip');
const countryTableProductionTooltip = new Tooltip('#countrypanel-production-tooltip');
const countryTooltip = new Tooltip('#country-tooltip');
const exchangeTooltip = new Tooltip('#exchange-tooltip');
const priceTooltip = new Tooltip('#price-tooltip');

const countryLowCarbonGauge = new CircularGauge('country-lowcarbon-gauge');
const countryRenewableGauge = new CircularGauge('country-renewable-gauge');

const windColorbar = new HorizontalColorbar('.wind-potential-bar', scales.windColor)
  .markerColor('black');
const solarColorbarColor = d3.scaleLinear()
  .domain([0, 0.5 * scales.maxSolarDSWRF, scales.maxSolarDSWRF])
  .range(['black', 'white', 'gold']);
const solarColorbar = new HorizontalColorbar('.solar-potential-bar', solarColorbarColor)
  .markerColor('red');

// TODO: Move to component
let countryListSelector;

// Initialise mobile app (cordova)
const app = {
  // Application Constructor
  initialize() {
    this.bindEvents();
  },

  bindEvents() {
    document.addEventListener('deviceready', this.onDeviceReady, false);
    document.addEventListener('resume', this.onResume, false);
    document.addEventListener('backbutton', this.onBack, false);
  },

  onBack(e) {
    if (getState().application.showPageState !== 'map') {
      dispatchApplication('selectedZoneName', undefined);
      dispatchApplication('showPageState', getState().application.pageToGoBackTo || 'map');
      e.preventDefault();
    } else {
      navigator.app.exitApp();
    }
  },

  onDeviceReady() {
    // Resize if we're on iOS
    if (cordova.platformId === 'ios') {
      d3.select('#header')
        .style('padding-top', '20px');
      if (typeof zoneMap !== 'undefined') {
        zoneMap.map.resize();
      }
    }
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
    universalLinks.subscribe(null, (eventData) => {
      HistoryState.parseInitial(eventData.url.split('?')[1] || eventData.url);
      // In principle we should only do the rest of the app loading
      // after this point, instead of dispating a new event
      const applicationState = HistoryState.getStateFromHistory();
      Object.keys(applicationState).forEach((k) => {
        dispatchApplication(k, applicationState[k]);
      });
    });
  },

  onResume() {
    // Count a pageview
    const params = getState().application;
    params.bundleVersion = params.bundleHash;
    params.embeddedUri = params.isEmbedded ? document.referrer : null;
    thirdPartyServices.track('Visit', params);
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },
};
app.initialize();

function catchError(e) {
  console.error(`Error Caught! ${e}`);
  thirdPartyServices.opbeat('captureException', e);
  thirdPartyServices.ga('event', 'exception', { description: e, fatal: false });
  const params = getState().application;
  params.name = e.name;
  params.stack = e.stack;
  thirdPartyServices.track('error', params);
}

// Set proper locale
moment.locale(getState().application.locale.toLowerCase());

// Analytics
(() => {
  const params = getState().application;
  params.bundleVersion = params.bundleHash;
  params.embeddedUri = params.isEmbedded ? document.referrer : null;
  thirdPartyServices.track('Visit', params);
})();

// Display embedded warning
// d3.select('#embedded-error').style('display', isEmbedded ? 'block' : 'none');

// Set up co2 scales
let co2color;
let co2Colorbars;
function updateCo2Scale() {
  if (getState().application.colorBlindModeEnabled) {
    co2color = scales.colorBlindCo2Color;
  } else {
    co2color = scales.classicalCo2Color;
  }

  co2color.clamp(true);
  co2Colorbars = co2Colorbars || [];
  co2Colorbars.push(new HorizontalColorbar('.floating-legend-container .co2-colorbar', co2color, null, [0, 400, 800])
    .markerColor('white')
    .domain([0, scales.maxCo2])
    .render());
  if (typeof zoneMap !== 'undefined') zoneMap.setCo2color(co2color);
  if (countryTable) countryTable.co2color(co2color).render();
  if (countryHistoryCarbonGraph) countryHistoryCarbonGraph.yColorScale(co2color);
  if (countryHistoryMixGraph) countryHistoryMixGraph.co2color(co2color);
  if (countryListSelector) {
    countryListSelector
      .select('div.emission-rect')
      .style('background-color', d =>
        (d.co2intensity ? co2color(d.co2intensity) : 'gray'));
  }
}
d3.select('#checkbox-colorblind').node().checked = getState().application.colorBlindModeEnabled;
d3.select('#checkbox-colorblind').on('change', () => {
  dispatchApplication('colorBlindModeEnabled', !getState().application.colorBlindModeEnabled);
});


// Start initialising map
try {
  zoneMap = new ZoneMap('zones')
    .setCo2color(co2color)
    .onDragEnd(() => {
      // Somehow there is a drag event sent before the map is loaded.
      // We want to ignore it.
      if (!mapDraggedSinceStart && mapLoaded) { mapDraggedSinceStart = true; }
    })
    .onMapLoaded((map) => {
      mapLoaded = true;
      // Nest the exchange layer inside
      const el = document.createElement('div');
      el.id = 'arrows-layer';
      map.map.getCanvas()
        .parentNode
        .appendChild(el);
      // Create exchange layer as a result
      exchangeLayer = new ExchangeLayer('arrows-layer', zoneMap)
        .onExchangeMouseOver((d) => {
          tooltipHelper.showMapExchange(exchangeTooltip, d, co2color, co2Colorbars);
        })
        .onExchangeMouseMove(() => {
          exchangeTooltip.update(currentEvent.clientX, currentEvent.clientY);
        })
        .onExchangeMouseOut((d) => {
          if (d.co2intensity && co2Colorbars) {
            co2Colorbars.forEach((c) => { c.currentMarker(undefined); });
          }
          exchangeTooltip.hide();
        })
        .onExchangeClick((d) => {
          console.log(d);
        })
        .setData(Object.values(getState().data.grid.exchanges))
        .render();
      LoadingService.stopLoading('#loading');
      LoadingService.stopLoading('#small-loading');
      if (thirdPartyServices._ga) {
        thirdPartyServices._ga.timingMark('map_loaded');
      }
    });
  windLayer = new WindLayer('wind', zoneMap);
  solarLayer = new SolarLayer('solar', zoneMap);
  dispatchApplication('webglsupported', true);
} catch (e) {
  if (e === 'WebGL not supported') {
    // Set mobile mode, and disable maps
    dispatchApplication('webglsupported', false);
    dispatchApplication('showPageState', 'highscore');
    document.getElementById('tab').className = 'nomap';

    // Loading is finished
    LoadingService.stopLoading('#loading');
    LoadingService.stopLoading('#small-loading');
  } else {
    throw e;
  }
}

countryTable
  .co2color(co2color)
  .displayByEmissions(tableDisplayEmissions)
  .onExchangeMouseMove(() => {
    countryTableExchangeTooltip.update(currentEvent.clientX, currentEvent.clientY);
  })
  .onExchangeMouseOver((d, country, displayByEmissions) => {
    tooltipHelper.showExchange(
      countryTableExchangeTooltip,
      d, country, displayByEmissions,
      co2color, co2Colorbars,
    );
  })
  .onExchangeMouseOut(() => {
    if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(undefined); });
    countryTableExchangeTooltip.hide();
  })
  .onProductionMouseOver((mode, country, displayByEmissions) => {
    tooltipHelper.showProduction(
      countryTableProductionTooltip,
      mode, country, displayByEmissions,
      co2color, co2Colorbars,
    );
  })
  .onProductionMouseMove(() =>
    countryTableProductionTooltip.update(currentEvent.clientX, currentEvent.clientY))
  .onProductionMouseOut(() => {
    if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(undefined); });
    countryTableProductionTooltip.hide();
  });

countryHistoryCarbonGraph
  .yColorScale(co2color)
  .gradient(true);
countryHistoryMixGraph
  .co2color(co2color)
  .onLayerMouseOver((mode, countryData, i) => {
    const isExchange = modeOrder.indexOf(mode) === -1;
    const fun = isExchange ?
      tooltipHelper.showExchange : tooltipHelper.showProduction;
    const ttp = isExchange ?
      countryTableExchangeTooltip : countryTableProductionTooltip;
    fun(ttp,
      mode, countryData, tableDisplayEmissions,
      co2color, co2Colorbars,
    );
    dispatchApplication('selectedZoneTimeIndex', i);
  })
  .onLayerMouseMove((mode, countryData, i) => {
    const isExchange = modeOrder.indexOf(mode) === -1;
    const fun = isExchange ?
      tooltipHelper.showExchange : tooltipHelper.showProduction;
    const ttp = isExchange ?
      countryTableExchangeTooltip : countryTableProductionTooltip;
    ttp.update(
      currentEvent.clientX - 7,
      countryHistoryMixGraph.rootElement.node().getBoundingClientRect().top - 7);
    fun(ttp,
      mode, countryData, tableDisplayEmissions,
      co2color, co2Colorbars,
    );
    dispatchApplication('selectedZoneTimeIndex', i);
  })
  .onLayerMouseOut((mode, countryData, i) => {
    if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(undefined); });
    const isExchange = modeOrder.indexOf(mode) === -1;
    const ttp = isExchange ?
      countryTableExchangeTooltip : countryTableProductionTooltip;
    ttp.hide();
  });

countryHistoryMixGraph
  .displayByEmissions(tableDisplayEmissions);
d3.select('.country-show-emissions-wrap a#emissions')
  .classed('selected', tableDisplayEmissions);
d3.select('.country-show-emissions-wrap a#production')
  .classed('selected', !tableDisplayEmissions);

// TODO(olc): Move to redux
window.toggleSource = (state) => {
  /* changing whether we display electricity production or carbon emission graphs */
  if (state === undefined) {
    state = !tableDisplayEmissions;
  }
  tableDisplayEmissions = state;
  thirdPartyServices.track(
    tableDisplayEmissions ? 'switchToCountryEmissions' : 'switchToCountryProduction',
    { countryCode: countryTable.data().countryCode },
  );
  countryTable
    .displayByEmissions(tableDisplayEmissions);
  countryHistoryMixGraph
    .displayByEmissions(tableDisplayEmissions);
  d3.select('.country-show-emissions-wrap a#emissions')
    .classed('selected', tableDisplayEmissions);
  d3.select('.country-show-emissions-wrap a#production')
    .classed('selected', !tableDisplayEmissions);
  // update wording, see #893
  document.getElementById('country-history-electricity-carbonintensity')
    .textContent = translation.translate(
      tableDisplayEmissions ?
        'country-history.carbonintensity24h' : 'country-history.electricityorigin24h');
};

function mapMouseOver(lonlat) {
  if (getState().application.windEnabled && wind && lonlat && typeof windLayer !== 'undefined') {
    const now = getState().application.customDate ?
      moment(getState().application.customDate) : (new Date()).getTime();
    if (!windLayer.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
      const u = grib.getInterpolatedValueAtLonLat(lonlat,
        now, wind.forecasts[0][0], wind.forecasts[1][0]);
      const v = grib.getInterpolatedValueAtLonLat(lonlat,
        now, wind.forecasts[0][1], wind.forecasts[1][1]);
        windColorbar.currentMarker(Math.sqrt(u * u + v * v));
    }
  } else {
    windColorbar.currentMarker(undefined);
  }
  if (getState().application.solarEnabled && solar && lonlat && typeof solarLayer !== 'undefined') {
    const now = getState().application.customDate ?
      moment(getState().application.customDate) : (new Date()).getTime();
    if (!solarLayer.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
      const val = grib.getInterpolatedValueAtLonLat(lonlat,
        now, solar.forecasts[0], solar.forecasts[1]);
        solarColorbar.currentMarker(val);
    }
  } else {
    solarColorbar.currentMarker(undefined);
  }
}

// Only center once
function renderMap(state) {
  if (typeof zoneMap === 'undefined') { return; }

  if (!mapDraggedSinceStart && !hasCenteredMap) {
    const { selectedZoneName, callerLocation } = state.application;
    if (selectedZoneName) {
      const selectedZone = state.data.grid.zones[selectedZoneName];
      const selectedZoneCoordinates = selectedZone.geometry.coordinates[0][0];
      const lon = d3.mean(selectedZoneCoordinates, d => d[0]);
      const lat = d3.mean(selectedZoneCoordinates, d => d[1]);
      console.log('Centering on selectedZoneName @', [lon, lat]);
      zoneMap.setCenter([lon, lat]);
      hasCenteredMap = true;
    } else if (callerLocation) {
      console.log('Centering on browser location @', callerLocation);
      zoneMap.setCenter(callerLocation);
      hasCenteredMap = true;
    } else {
      zoneMap.setCenter([0, 50]);
    }
  }
  if (exchangeLayer) {
    exchangeLayer.render();
  }

  if (getState().application.windEnabled && wind && wind['forecasts'][0] && wind['forecasts'][1] && typeof windLayer !== 'undefined') {
    LoadingService.startLoading('#loading');
    // Make sure to disable wind if the drawing goes wrong
    Cookies.set('windEnabled', false);
    windLayer.draw(
      getState().application.customDate ?
        moment(getState().application.customDate) : moment(new Date()),
      wind.forecasts[0],
      wind.forecasts[1],
      scales.windColor,
    );
    if (getState().application.windEnabled) {
      windLayer.show();
    } else {
      windLayer.hide();
    }
    // Restore setting
    Cookies.set('windEnabled', getState().application.windEnabled);
    LoadingService.stopLoading('#loading');
  } else if (typeof windLayer !== 'undefined') {
    windLayer.hide();
  }

  if (getState().application.solarEnabled && solar && solar['forecasts'][0] && solar['forecasts'][1] && typeof solarLayer !== 'undefined') {
    LoadingService.startLoading('#loading');
    // Make sure to disable solar if the drawing goes wrong
    Cookies.set('solarEnabled', false);
    solarLayer.draw(
      getState().application.customDate ?
        moment(getState().application.customDate) : moment(new Date()),
      solar.forecasts[0],
      solar.forecasts[1],
      scales.solarColor,
      () => {
        if (getState().application.solarEnabled) {
          solarLayer.show();
        } else {
          solarLayer.hide();
        }
        // Restore setting
        Cookies.set('solarEnabled', getState().application.solarEnabled);
        LoadingService.stopLoading('#loading');
      },
    );
  } else if (typeof solarLayer !== 'undefined') {
    solarLayer.hide();
  }

  // Resize map to make sure it takes all container space
  zoneMap.map.resize();
}

// Inform the user the last time the map was updated.
function setLastUpdated() {
  currentMoment = getState().application.customDate ?
    moment(getState().application.customDate) :
    moment((getState().data.grid || {}).datetime);
  d3.selectAll('.current-datetime').text(currentMoment.format('LL LT'));
  d3.selectAll('.current-datetime-from-now')
    .text(currentMoment.fromNow())
    .style('color', 'darkred')
    .transition()
    .duration(800)
    .style('color', undefined);
}
// Re-check every minute
setInterval(setLastUpdated, 60 * 1000);

// Add search bar with handler
// TODO(olc): move to component
d3.select('.country-search-bar input')
  .on('keyup', (obj, i, nodes) => {
    const query = nodes[i].value.toLowerCase();

    d3.select('.country-picker-container p')
      .selectAll('a').each((obj, i, nodes) => {
        const zoneName = (obj.shortname || obj.countryCode).toLowerCase();
        const listItem = d3.select(nodes[i]);

        if (zoneName.indexOf(query) !== -1) {
          listItem.style('display', '');
        } else {
          listItem.style('display', 'none');
        }
      });
  });

function dataLoaded(err, clientVersion, callerLocation, state, argSolar, argWind) {
  if (err) {
    console.error(err);
    return;
  }

  // Track pageview
  const params = getState().application;
  params.bundleVersion = params.bundleHash;
  params.embeddedUri = params.isEmbedded ? document.referrer : null;
  thirdPartyServices.track('pageview', params);

  // Is there a new version?
  d3.select('#new-version')
    .classed('active', (
      clientVersion !== getState().application.bundleHash &&
      !getState().application.isLocalhost && !getState().application.isCordova
    ));

  const node = document.getElementById('map-container');
  if (typeof zoneMap !== 'undefined') {
    // Assign country map data
    zoneMap
      .onCountryMouseOver((d) => {
        tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars);
      })
      .onZoneMouseMove((d, i, clientX, clientY) => {
        // TODO: Check that i changed before calling showMapCountry
        tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars);
        const rect = node.getBoundingClientRect();
        countryTooltip.update(clientX + rect.left, clientY + rect.top);
      })
      .onMouseMove((lonlat) => {
        mapMouseOver(lonlat);
      })
      .onZoneMouseOut(() => {
        if (co2Colorbars) {
          co2Colorbars.forEach((c) => { c.currentMarker(undefined); });
        }
        mapMouseOver(undefined);
        countryTooltip.hide();
      });
  }

  // Render weather if provided
  // Do not overwrite with null/undefined
  if (argWind) wind = argWind;
  if (argSolar) solar = argSolar;

  dispatchApplication('callerLocation', callerLocation);
  dispatch({
    payload: state,
    type: 'GRID_DATA',
  });
}

// Periodically load data
function handleConnectionReturnCode(err) {
  if (err) {
    if (err.target) {
      // Avoid catching HTTPError 0
      // The error will be empty, and we can't catch any more info
      // for security purposes
      // See http://stackoverflow.com/questions/4844643/is-it-possible-to-trap-cors-errors
      if (err.target.status) {
        catchError(new Error(
          'HTTPError ' +
          err.target.status + ' ' + err.target.statusText + ' at ' +
          err.target.responseURL + ': ' +
          err.target.responseText));
      }
    } else {
      catchError(err);
    }
    d3.select('#connection-warning').classed('active', true);
  } else {
    d3.select('#connection-warning').classed('active', false);
  }
}

const ignoreError = func =>
  (...args) => {
    const callback = args[args.length - 1];
    args[args.length - 1] = (err, obj) => {
      if (err) { return callback(null, null); }
      return callback(null, obj);
    };
    func.apply(this, args);
  };

function fetch(showLoading, callback) {
  if (showLoading) LoadingService.startLoading('#loading');
  LoadingService.startLoading('#small-loading');
  const Q = d3.queue();
  // We ignore errors in case this is run from a file:// protocol (e.g. cordova)
  if (getState().application.clientType === 'web' && !getState().application.isLocalhost) {
    Q.defer(d3.text, '/clientVersion');
  } else {
    Q.defer(DataService.fetchNothing);
  }
  Q.defer(DataService.fetchState, ENDPOINT, getState().application.customDate);

  const now = getState().application.customDate || new Date();

  if (!getState().application.solarEnabled) {
    Q.defer(DataService.fetchNothing);
  } else if (!solar || solarLayer.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
    Q.defer(ignoreError(DataService.fetchGfs), ENDPOINT, 'solar', now);
  } else {
    Q.defer(cb => cb(null, solar));
  }

  if (!getState().application.windEnabled || typeof windLayer === 'undefined') {
    Q.defer(DataService.fetchNothing);
  } else if (!wind || windLayer.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
    Q.defer(ignoreError(DataService.fetchGfs), ENDPOINT, 'wind', now);
  } else {
    Q.defer(cb => cb(null, wind));
  }
  Q.await((err, clientVersion, state, solar, wind) => {
    handleConnectionReturnCode(err);
    if (!err) {
      dataLoaded(err, clientVersion, state.data.callerLocation, state.data, solar, wind);
    }
    if (showLoading) {
      LoadingService.stopLoading('#loading');
    }
    LoadingService.stopLoading('#small-loading');
    if (callback) callback();
  });
}

window.addEventListener('resize', () => {
  if (getState().application.selectedZoneName) {
    countryTable.render();
    countryHistoryCarbonGraph.render();
    countryHistoryPricesGraph.render();
    countryHistoryMixGraph.render();
  }
  co2Colorbars.forEach((d) => { d.render(); });
});
// Only for debugging purposes
window.retryFetch = () => {
  d3.select('#connection-warning').classed('active', false);
  fetch(false);
};


// *** DISPATCHERS ***
// Declare and attach all event handlers that will
// cause events to be emitted

// Wind
function toggleWind() {
  if (typeof windLayer === 'undefined') { return; }
  dispatchApplication('windEnabled', !getState().application.windEnabled);
}
d3.select('.wind-button').on('click', toggleWind);

// Solar
function toggleSolar() {
  if (typeof solarLayer === 'undefined') { return; }
  dispatchApplication('solarEnabled', !getState().application.solarEnabled);
}
d3.select('.solar-button').on('click', toggleSolar);

// Legend 
function toggleLegend(){
  dispatchApplication('legendVisible', !getState().application.legendVisible);
}
 d3.selectAll('.toggle-legend-button').on('click', toggleLegend);


// Close button on left-panel
d3.selectAll('#left-panel-country-back')
  .on('click', () => {
    dispatchApplication('selectedZoneName', undefined);
    dispatchApplication('showPageState', getState().application.pageToGoBackTo || 'map'); // TODO(olc): infer in reducer
  });

// Close button on highscore (only triggered on large screens)
d3.selectAll('#left-panel-highscore-back')
  .on('click', () => dispatchApplication('showPageState', 'map'));

// Highscore button click
d3.selectAll('.highscore-button')
  .on('click', () => dispatchApplication('showPageState', 'highscore'));

// Mobile toolbar buttons
d3.selectAll('.map-button').on('click', () => dispatchApplication('showPageState', 'map'));
d3.selectAll('.info-button').on('click', () => dispatchApplication('showPageState', 'info'));

// Map click
// TODO(olc): make sure to assign even if map is not ready yet
if (typeof zoneMap !== 'undefined') {
  zoneMap
    .onSeaClick(() => {
      dispatchApplication('showPageState', 'map'); // TODO(olc): infer in reducer?
      dispatchApplication('selectedZoneName', undefined);
    })
    .onCountryClick((d) => {
      dispatchApplication('showPageState', 'country'); // TODO(olc): infer in reducer?
      dispatchApplication('selectedZoneName', d.countryCode);
    });
}


// *** OBSERVERS ***
// Declare and attach all listeners that will react
// to state changes and cause a side-effect

function getCurrentZoneData(state) {
  const { grid } = state.data;
  const zoneName = state.application.selectedZoneName;
  const i = state.application.selectedZoneTimeIndex;
  if (!grid || !zoneName) {
    return null;
  }
  if (i == null) {
    return grid.zones[zoneName];
  }
  return (state.data.histories[zoneName] || {})[i];
}

function renderGauges(state) {
  const d = getCurrentZoneData(state);
  if (!d) {
    countryLowCarbonGauge.setPercentage(null);
    countryRenewableGauge.setPercentage(null);
  } else {
    const countryLowCarbonPercentage = d.fossilFuelRatio != null ?
      100 - (d.fossilFuelRatio * 100) : null;
    countryLowCarbonGauge.setPercentage(countryLowCarbonPercentage);
    const countryRenewablePercentage = d.renewableRatio != null ? d.renewableRatio * 100 : null;
    countryRenewableGauge.setPercentage(countryRenewablePercentage);
  }
}
function renderContributors(state) {
  const { selectedZoneName } = state.application;
  // TODO(olc): move to component
  const selector = d3.selectAll('.contributors').selectAll('a')
    .data((zonesConfig[selectedZoneName] || {}).contributors || []);
  const enterA = selector.enter().append('a')
    .attr('target', '_blank');
  const enterImg = enterA.append('img');
  enterA.merge(selector)
    .attr('href', d => d);
  enterImg.merge(selector.select('img'))
    .attr('src', d => `${d}.png`);
  selector.exit().remove();
}
function renderCountryTable(state) {
  const d = getCurrentZoneData(state);
  if (!d) {
    // In this cases there's nothing to do,
    // as the countryTable doesn't support receiving null data
  } else {
    countryTable.data(d).render(true);
  }
}
function renderCountryList(state) {
  // TODO(olc): refactor into component
  const countries = state.data.grid.zones;
  const validCountries = d3.values(countries)
    .filter(d => d.co2intensity)
    .sort((x, y) => {
      if (!x.co2intensity && !x.countryCode) {
        return d3.ascending(
          x.shortname || x.countryCode,
          y.shortname || y.countryCode);
      } else {
        return d3.ascending(
          x.co2intensity || Infinity,
          y.co2intensity || Infinity);
      }
    });
  const selector = d3.select('.country-picker-container p')
    .selectAll('a')
    .data(validCountries);
  const enterA = selector.enter().append('a');
  enterA
    .append('div')
    .attr('class', 'emission-rect');
  enterA
    .append('span')
    .attr('class', 'name');
  enterA
    .append('img')
    .attr('class', 'flag');
  enterA
    .append('span')
    .attr('class', 'rank');
  countryListSelector = enterA.merge(selector);
  countryListSelector.select('span.name')
    .text(d => ' ' + (translation.translate('zoneShortName.' + d.countryCode) || d.countryCode) + ' ')
  countryListSelector.select('div.emission-rect')
    .style('background-color', (d) => {
      return d.co2intensity ? co2color(d.co2intensity) : 'gray';
    });
  countryListSelector.select('.flag')
    .attr('src', d => flags.flagUri(d.countryCode, 16));
  countryListSelector.on('click', (d) => {
    dispatchApplication('selectedZoneName', d.countryCode);
    dispatchApplication('showPageState', 'country');
  });
}
function renderHistory(state) {
  const { selectedZoneName } = state.application;
  const history = state.data.histories[selectedZoneName];

  if (!history) {
    countryHistoryCarbonGraph.data([]).render();
    countryHistoryPricesGraph.data([]).render();
    countryHistoryMixGraph.data([]).render();
    return;
  }

  const zone = state.data.grid.zones[selectedZoneName];

  countryTable
    .powerScaleDomain(null) // Always reset scale if click on a new country
    .co2ScaleDomain(null)
    .exchangeKeys(null); // Always reset exchange keys

  const { maxStorageCapacity } = zone;

  // No export capacities are not always defined, and they are thus
  // varying the scale.
  // Here's a hack to fix it.
  const lo = d3.min(history, d =>
    Math.min(
      -d.maxStorageCapacity || -maxStorageCapacity || 0,
      -d.maxStorage || 0,
      -d.maxExport || 0,
      -d.maxExportCapacity || 0),
  );
  const hi = d3.max(history, d =>
    Math.max(
      d.maxCapacity || 0,
      d.maxProduction || 0,
      d.maxImport || 0,
      d.maxImportCapacity || 0,
      d.maxDischarge || 0,
      d.maxStorageCapacity || maxStorageCapacity || 0),
  );
  // TODO(olc): do those aggregates server-side
  const lo_emission = d3.min(history, d =>
    Math.min(
      // Max export
      d3.min(d3.entries(d.exchange), o =>
        Math.min(o.value, 0) * d.exchangeCo2Intensities[o.key] / 1e3 / 60.0
      ) || 0
      // Max storage
      // ?
    )
  );
  const hi_emission = d3.max(history, d =>
    Math.max(
      // Max import
      d3.max(d3.entries(d.exchange), o =>
        Math.max(o.value, 0) * d.exchangeCo2Intensities[o.key] / 1e3 / 60.0
      ) || 0,
      // Max production
      d3.max(d3.entries(d.production), o =>
        Math.max(o.value, 0) * d.productionCo2Intensities[o.key] / 1e3 / 60.0
      ) || 0
    )
  );

  // Figure out the highest CO2 emissions
  const hi_co2 = d3.max(history, d => d.co2intensity);
  countryHistoryCarbonGraph.y.domain([0, 1.1 * hi_co2]);

  // Create price color scale
  const priceExtent = d3.extent(history, d => (d.price || {}).value);

  countryHistoryPricesGraph.y.domain([Math.min(0, priceExtent[0]), 1.1 * priceExtent[1]]);

  countryHistoryCarbonGraph
    .data(history);
  countryHistoryPricesGraph
    .yColorScale(d3.scaleLinear()
      .domain(countryHistoryPricesGraph.y.domain())
      .range(['yellow', 'red']))
    .data(history);
  countryHistoryMixGraph
    .data(history);

  // Update country table with all possible exchanges
  countryTable
    .exchangeKeys(countryHistoryMixGraph.exchangeKeysSet.values())
    .render();

  const firstDatetime = history[0] && moment(history[0].stateDatetime).toDate();
  [countryHistoryCarbonGraph, countryHistoryPricesGraph, countryHistoryMixGraph].forEach((g) => {
    if (currentMoment && firstDatetime) {
      g.xDomain([firstDatetime, currentMoment.toDate()]);
    }
    g
      .onMouseMove((d, i) => {
        if (!d) return;
        // In case of missing data
        if (!d.countryCode) {
          d.countryCode = selectedZoneName;
        }
        countryTable
          .powerScaleDomain([lo, hi])
          .co2ScaleDomain([lo_emission, hi_emission]);

        if (g === countryHistoryCarbonGraph) {
          tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars);
          countryTooltip.update(
            currentEvent.clientX - 7,
            g.rootElement.node().getBoundingClientRect().top - 7);
        } else if (g === countryHistoryPricesGraph) {
          const tooltip = d3.select(priceTooltip._selector);
          tooltip.select('.value').html((d.price || {}).value || '?');
          tooltip.select('.currency').html(getSymbolFromCurrency((d.price || {}).currency) || '?');
          priceTooltip.show();
          priceTooltip.update(
            currentEvent.clientX - 7,
            g.rootElement.node().getBoundingClientRect().top - 7,
          );
        }

        dispatchApplication('selectedZoneTimeIndex', i);
      })
      .onMouseOut((d, i) => {
        countryTable
          .powerScaleDomain(null)
          .co2ScaleDomain(null);

        if (g === countryHistoryCarbonGraph) {
          countryTooltip.hide();
        } else if (g === countryHistoryMixGraph) {
          countryTableProductionTooltip.hide();
          countryTableExchangeTooltip.hide();
        } else if (g === countryHistoryPricesGraph) {
          priceTooltip.hide();
        }

        dispatchApplication('selectedZoneTimeIndex', null);
      })
      .render();
  });
}
function routeToPage(pageName, state) {
  // Hide all panels - we will show only the ones we need
  d3.selectAll('.left-panel > div').style('display', 'none');
  d3.selectAll('.left-panel .left-panel-social').style('display', undefined);

  // Hide info screen on large screen only
  d3.selectAll('.left-panel .left-panel-info')
    // Only show on info or map
    .style('display', (pageName === 'info' || pageName === 'map') ? undefined : 'none')
    // but hide for small screens on all but info
    .classed('large-screen-visible', pageName !== 'info');

  // Hide map on small screens
  // It's important we show the map before rendering it to make sure
  // sizes are set properly
  d3.selectAll('#map-container').classed('large-screen-visible', pageName !== 'map');

  // Analytics
  // TODO(olc): where should we put all tracking code?
  // at the source events, or in observers?
  const params = getState().application;
  params.bundleVersion = params.bundleHash;
  params.embeddedUri = params.isEmbedded ? document.referrer : null;
  thirdPartyServices.track('pageview', params);
  if (pageName === 'country') {
    thirdPartyServices.track('countryClick', { countryCode: params.selectedZoneName });
  }

  if (pageName === 'map') {
    d3.select('.left-panel').classed('large-screen-visible', true);
    renderMap(state);
    if (state.application.windEnabled && typeof windLayer !== 'undefined') { windLayer.show(); }
    if (state.application.solarEnabled && typeof solarLayer !== 'undefined') { solarLayer.show(); }
    if (co2Colorbars) co2Colorbars.forEach((d) => { d.render(); });
    if (state.application.windEnabled && windColorbar) windColorbar.render();
    if (state.application.solarEnabled && solarColorbar) solarColorbar.render();
  } else {
    d3.select('.left-panel').classed('large-screen-visible', false);
    d3.selectAll(`.left-panel-${pageName}`).style('display', undefined);
    if (pageName === 'info') {
      if (co2Colorbars) co2Colorbars.forEach((d) => { d.render(); });
      if (state.application.windEnabled) if (windColorbar) windColorbar.render();
      if (state.application.solarEnabled) if (solarColorbar) solarColorbar.render();
    }
  }

  d3.selectAll('#tab .list-item:not(.wind-toggle):not(.solar-toggle)').classed('active', false);
  d3.selectAll(`#tab .${pageName}-button`).classed('active', true);
}
function tryFetchHistory(state) {
  const { selectedZoneName } = state.application;
  if (state.application.customDate) {
    console.error('Can\'t fetch history when a custom date is provided!');
  } else if (!state.data.histories[selectedZoneName]) {
    LoadingService.startLoading('.country-history .loading');
    DataService.fetchHistory(ENDPOINT, selectedZoneName, (err, obj) => {
      LoadingService.stopLoading('.country-history .loading');
      if (err) { return console.error(err); }
      if (!obj || !obj.data) {
        return console.warn(`Empty history received for ${selectedZoneName}`);
      }
      // Save to local cache
      return dispatch({
        payload: obj.data,
        zoneName: selectedZoneName,
        type: 'HISTORY_DATA',
      });
    });
  }
}

// Observe for grid zones change
observe(state => state.data.grid.zones, (zones, state) => {
  if (typeof zoneMap !== 'undefined') {
    zoneMap.setData(Object.values(zones));
  }
  renderCountryList(state);
});
// Observe for grid exchanges change
observe(state => state.data.grid.exchanges, (exchanges) => {
  if (exchangeLayer) {
    exchangeLayer
      .setData(Object.values(exchanges))
      .render();
  }
});
// Observe for grid change
observe(state => state.data.grid, (grid, state) => {
  renderCountryTable(state);
  renderGauges(state);
  renderMap(state);
});
// Observe for page change
observe(state => state.application.showPageState, (showPageState, state) => {
  routeToPage(showPageState, state);
});
// Observe for zone change (for example after map click)
observe(state => state.application.selectedZoneName, (k, state) => {
  if (!state.application.selectedZoneName) { return; }

  renderCountryTable(state);
  renderGauges(state);
  renderContributors(state);
  renderHistory(state);

  // Fetch history if needed
  tryFetchHistory(state);
});
// Observe for history change
observe(state => state.data.histories, (histories, state) => {
  if (state.application.showPageState === 'country') {
    renderHistory(state);
  }
  // If history was cleared by the grid data for the currently selected country,
  // try to refetch it.
  const { selectedZoneName } = state.application;
  if (selectedZoneName && !state.data.histories[selectedZoneName]) {
    tryFetchHistory(state);
  }
});
// Observe for index change (for example by history graph)
observe(state => state.application.selectedZoneTimeIndex, (i, state) => {
  renderGauges(state);
  renderCountryTable(state);
  [countryHistoryCarbonGraph, countryHistoryMixGraph, countryHistoryPricesGraph].forEach((g) => {
    g.selectedIndex(i);
  });
});
// Observe for color blind mode changes
observe(state => state.application.colorBlindModeEnabled, (colorBlindModeEnabled) => {
  Cookies.set('colorBlindModeEnabled', colorBlindModeEnabled);
  updateCo2Scale();
});
// Observe for solar settings change
observe(state => state.application.solarEnabled, (solarEnabled, state) => {
  d3.selectAll('.solar-button').classed('active', solarEnabled);
  d3.select('.solar-potential-legend').classed('visible', solarEnabled);
  Cookies.set('solarEnabled', solarEnabled);

  const now = state.customDate ?
    moment(state.customDate) : (new Date()).getTime();
  if (solarEnabled && typeof solarLayer !== 'undefined') {
    solarColorbar.render();
    if (!solar || solarLayer.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
      fetch(true);
    } else {
      solarLayer.show();
    }
  } else if (typeof solarLayer !== 'undefined') {
    solarLayer.hide();
  }
});
// Observe for wind settings change
observe(state => state.application.windEnabled, (windEnabled, state) => {

  d3.selectAll('.wind-button').classed('active', windEnabled);
  d3.select('.wind-potential-legend').classed('visible', windEnabled);

  Cookies.set('windEnabled', windEnabled);

  const now = state.customDate ?
    moment(state.customDate) : (new Date()).getTime();
  if (windEnabled && typeof windLayer !== 'undefined') {
    windColorbar.render();
    if (!wind || windLayer.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
      fetch(true);
    } else {
      windLayer.show();
    }
  } else if (typeof windLayer !== 'undefined') {
    windLayer.hide();
  }
});
// Observe for changes requiring an update of history
Object.values(HistoryState.querystringMappings).forEach((k) => {
  observe(state => state.application[k], (_, state) => {
    HistoryState.updateHistoryFromState(state.application);
  });
});
// Observe for datetimechanes
observe(state => state.data.grid, (grid) => {
  if (grid && grid.datetime) {
    setLastUpdated();
  }
});

// Observe for legend visibility change
observe(state => state.application.legendVisible, (legendVisible, state) => {
  d3.selectAll('.floating-legend').classed('mobile-collapsed', !legendVisible);
  d3.select('.floating-legend-container').classed('mobile-collapsed', !legendVisible);
  d3.select('.toggle-legend-button.up').classed('visible', !legendVisible);
  d3.select('.toggle-legend-button.down').classed('visible', legendVisible);
})

// ** START

// Start a fetch and show loading screen
fetch(true, () => {
  if (!getState().application.customDate) {
    // Further calls to `fetch` won't show loading screen
    setInterval(fetch, REFRESH_TIME_MINUTES * 60 * 1000);
  }
});
