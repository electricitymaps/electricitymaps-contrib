'use strict';

// see https://stackoverflow.com/questions/36887428/d3-event-is-null-in-a-reactjs-d3js-component
import { event as currentEvent } from 'd3-selection';
import CircularGauge from './components/circulargauge';
import ContributorList from './components/contributorlist';
import OnboardingModal from './components/onboardingmodal';
import SearchBar from './components/searchbar';
import ZoneList from './components/zonelist';
import ZoneMap from './components/map';
import FAQ from './components/faq';
import TimeSlider from './components/timeslider.js'
import { formatPower } from './helpers/formatting';

// Libraries
const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-queue'),
  require('d3-request'),
  require('d3-scale'),
  require('d3-selection'),
  require('d3-scale-chromatic'),
  require('d3-interpolate'),
);
const Cookies = require('js-cookie');
const moment = require('moment');

// State management
const { dispatch, dispatchApplication, getState, observe } = require('./store');

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
const grib = require('./helpers/grib');
const HistoryState = require('./helpers/historystate');
const scales = require('./helpers/scales');
const tooltipHelper = require('./helpers/tooltip');
const translation = require('./helpers/translation');
const themes = require('./helpers/themes').themes;

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
let onboardingModal;

// Set standard theme
let theme = themes.bright;

// ** Create components
const countryTable = new CountryTable('.country-table-container', modeColor, modeOrder);
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
const tooltipLowCarbonGauge = new CircularGauge('tooltip-country-lowcarbon-gauge');
const tooltipRenewableGauge = new CircularGauge('tooltip-country-renewable-gauge');
const contributorList = new ContributorList('.contributors');

const windColorbar = new HorizontalColorbar('.wind-potential-bar', scales.windColor)
  .markerColor('black');
const solarColorbarColor = d3.scaleLinear()
  .domain([0, 0.5 * scales.maxSolarDSWRF, scales.maxSolarDSWRF])
  .range(['black', 'white', 'gold']);
const solarColorbar = new HorizontalColorbar('.solar-potential-bar', solarColorbarColor)
  .markerColor('red');

const zoneList = new ZoneList('.zone-list');
const zoneSearchBar = new SearchBar('.zone-search-bar input');

const faq = new FAQ('.faq');
const mobileFaq = new FAQ('.mobile-faq');
const zoneDetailsTimeSlider = new TimeSlider('.zone-time-slider', dataEntry => dataEntry.stateDatetime);

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
      d3.select('#mobile-header')
        .style('padding-top', '20px');
      if (typeof zoneMap !== 'undefined') {
        zoneMap.map.resize();
      }
      // iphone X nodge
      if (device.model === 'iPhone10,3' || device.model === 'iPhone10,6') {
        d3.select('#header')
          .style('padding-top', '30px');
        d3.select('#mobile-header')
          .style('padding-top', '30px');
        if (typeof zoneMap !== 'undefined') {
          zoneMap.map.resize();
        }
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
    thirdPartyServices.trackWithCurrentApplicationState('Visit'),
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },
};
app.initialize();

function catchError(e) {
  console.error(`Error Caught! ${e}`);
  thirdPartyServices.reportError(e);
  thirdPartyServices.ga('event', 'exception', { description: e, fatal: false });
  const params = getState().application;
  params.name = e.name;
  params.stack = e.stack;
  thirdPartyServices.track('error', params);
}

// Set proper locale
moment.locale(getState().application.locale.toLowerCase());

// Analytics
thirdPartyServices.trackWithCurrentApplicationState('Visit');

// do not display onboarding when we've seen it or we're embedded
if (!getState().application.onboardingSeen && !getState().application.isEmbedded) {
  onboardingModal = new OnboardingModal('#main');
  thirdPartyServices.trackWithCurrentApplicationState('onboardingModalShown');
}

// Display embedded warning
// d3.select('#embedded-error').style('display', isEmbedded ? 'block' : 'none');

// Display randomly alternating header campaign message
const randomBoolean = Math.random() >= 0.5;

d3.select('.api-ad').classed('visible', randomBoolean);
d3.select('.database-ad').classed('visible', !randomBoolean);

// Set up co2 scales
let co2color;
let co2Colorbars;
function updateCo2Scale() {
  if (getState().application.colorBlindModeEnabled) {
    co2color = d3.scaleLinear()
      .domain(themes.colorblindScale.steps)
      .range(themes.colorblindScale.colors)
      .clamp(true);
  } else {
    co2color = d3.scaleLinear()
      .domain(themes.co2Scale.steps)
      .range(themes.co2Scale.colors)
      .clamp(true);
  }

  co2color.clamp(true);
  co2Colorbars = co2Colorbars || [];
  co2Colorbars.push(new HorizontalColorbar('.floating-legend-container .co2-colorbar', co2color, null, [0, 400, 800])
    .markerColor('white')
    .domain([0, scales.maxCo2])
    .render());
  if (typeof zoneMap !== 'undefined') zoneMap.setCo2color(co2color, theme);
  if (countryTable) countryTable.co2color(co2color).render();
  if (countryHistoryCarbonGraph) countryHistoryCarbonGraph.yColorScale(co2color);
  if (countryHistoryMixGraph) countryHistoryMixGraph.co2color(co2color);

  zoneList.setCo2ColorScale(co2color);
  zoneList.render();
}
d3.select('#checkbox-colorblind').node().checked = getState().application.colorBlindModeEnabled;
d3.select('#checkbox-colorblind').on('change', () => {
  dispatchApplication('colorBlindModeEnabled', !getState().application.colorBlindModeEnabled);
});


// Start initialising map
try {
  zoneMap = new ZoneMap('zones', { zoom: 1.5, theme })
    .setCo2color(co2color)
    .onDragEnd(() => {
      // Somehow there is a drag event sent before the map data is loaded.
      // We want to ignore it.
      if (!mapDraggedSinceStart && getState().data.grid.datetime) {
        mapDraggedSinceStart = true;
      }
    })
    .onMapLoaded((map) => {
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
    dispatchApplication('tooltipDisplayMode', mode);
  })
  .onProductionMouseMove(() =>
    countryTableProductionTooltip.update(currentEvent.clientX, currentEvent.clientY))
  .onProductionMouseOut(() => {
    if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(undefined); });
    countryTableProductionTooltip.hide();
    dispatchApplication('tooltipDisplayMode', null);
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
    dispatchApplication('tooltipDisplayMode', mode);
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
    dispatchApplication('tooltipDisplayMode', mode);
    dispatchApplication('selectedZoneTimeIndex', i);
  })
  .onLayerMouseOut((mode, countryData, i) => {
    if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(undefined); });
    const isExchange = modeOrder.indexOf(mode) === -1;
    const ttp = isExchange ?
      countryTableExchangeTooltip : countryTableProductionTooltip;
    ttp.hide();
    dispatchApplication('tooltipDisplayMode', null);
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
        'country-history.emissionsorigin24h' : 'country-history.electricityorigin24h');
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
      console.log(`Centering on selectedZoneName ${selectedZoneName}`);
      centerOnZoneName(state, selectedZoneName, 4);
      hasCenteredMap = true;
    } else if (callerLocation) {
      console.log('Centering on browser location @', callerLocation);
      zoneMap.setCenter(callerLocation);
      hasCenteredMap = true;
    } else {
      zoneMap.setCenter([0, 50]);
    }
  }

  // Render Wind
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

  // Render Solar
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
  // Warning: this causes a flicker
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

function dataLoaded(err, clientVersion, callerLocation, state, argSolar, argWind) {
  if (err) {
    console.error(err);
    return;
  }

  // Track pageview
  thirdPartyServices.trackWithCurrentApplicationState('pageview');

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
        tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars, tooltipLowCarbonGauge, tooltipRenewableGauge);
      })
      .onZoneMouseMove((d, i, clientX, clientY) => {
        // TODO: Check that i changed before calling showMapCountry
        tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars, tooltipLowCarbonGauge, tooltipRenewableGauge);
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

// BrightMode
const electricityMapHeader = d3.select('#header-content');
const tmrowWatermark = d3.select('#watermark');

function toggleBright() {
  dispatchApplication('brightModeEnabled', !getState().application.brightModeEnabled);
  electricityMapHeader.classed('brightmode', !electricityMapHeader.classed('brightmode'));
  tmrowWatermark.classed('brightmode', !tmrowWatermark.classed('brightmode'));
}

d3.select('.brightmode-button').on('click', toggleBright);

const brightModeButtonTooltip = d3.select('#brightmode-layer-button-tooltip');

if (!getState().application.isMobile) {
  // Mouseovers will trigger on click on mobile and is therefore only set on desktop
  d3.select('.brightmode-button').on('mouseover', () => {
    brightModeButtonTooltip.classed('hidden', false);

  });
  d3.select('.brightmode-button').on('mouseout', () => {
    brightModeButtonTooltip.classed('hidden', true);
  });
}

// Wind
function toggleWind() {
  if (typeof windLayer === 'undefined') { return; }
  dispatchApplication('windEnabled', !getState().application.windEnabled);
}
d3.select('.wind-button').on('click', toggleWind);

const windLayerButtonTooltip = d3.select('#wind-layer-button-tooltip');

if (!getState().application.isMobile) {
  // Mouseovers will trigger on click on mobile and is therefore only set on desktop
  d3.select('.wind-button').on('mouseover', () => {
    windLayerButtonTooltip.classed('hidden', false);
  });
  d3.select('.wind-button').on('mouseout', () => {
    windLayerButtonTooltip.classed('hidden', true);
  });
}


// Solar
function toggleSolar() {
  if (typeof solarLayer === 'undefined') { return; }
  dispatchApplication('solarEnabled', !getState().application.solarEnabled);
}
d3.select('.solar-button').on('click', toggleSolar);

const solarLayerButtonTooltip = d3.select('#solar-layer-button-tooltip');

if (!getState().application.isMobile) {
  // Mouseovers will trigger on click on mobile and is therefore only set on desktop
  d3.select('.solar-button').on('mouseover', () => {
    solarLayerButtonTooltip.classed('hidden', false);
  });
  d3.select('.solar-button').on('mouseout', () => {
    solarLayerButtonTooltip.classed('hidden', true);
  });
}


// Legend 
function toggleLegend() {
  dispatchApplication('legendVisible', !getState().application.legendVisible);
}
d3.selectAll('.toggle-legend-button').on('click', toggleLegend);

// Collapse button
document.getElementById('left-panel-collapse-button').addEventListener('click', () =>
  dispatchApplication('isLeftPanelCollapsed', !getState().application.isLeftPanelCollapsed));

// Map click
// TODO(olc): make sure to assign even if map is not ready yet
if (typeof zoneMap !== 'undefined') {
  zoneMap
    .onSeaClick(() => {
      dispatchApplication('showPageState', 'map'); // TODO(olc): infer in reducer?
      if (getState().application.selectedZoneName !== null) {
        dispatch({type: 'UPDATE_SELECTED_ZONE', payload: {selectedZoneName: null}});
      }
    })
    .onCountryClick((d) => {
      dispatchApplication('isLeftPanelCollapsed', false);
      dispatchApplication('showPageState', 'country'); // TODO(olc): infer in reducer?
      if (getState().application.selectedZoneName !== d.countryCode) {
        dispatch({type: 'UPDATE_SELECTED_ZONE', payload: {selectedZoneName: d.countryCode}});
      }
    });
}

// * Left panel *

// Search bar
zoneSearchBar.onSearch(query => dispatchApplication('searchQuery', query));
zoneSearchBar.onEnterKeypress(() => zoneList.clickSelectedItem());

// Back button

function goBackToZoneListFromZoneDetails() {
  dispatchApplication('selectedZoneName', undefined);
  dispatchApplication('showPageState', getState().application.pageToGoBackTo || 'map'); // TODO(olc): infer in reducer
}

d3.selectAll('.left-panel-back-button')
  .on('click', () => {
    goBackToZoneListFromZoneDetails();
  });

// Zone list
zoneList.setClickHandler((selectedCountry) => {
  dispatchApplication('showPageState', 'country');
  dispatchApplication('selectedZoneName', selectedCountry.countryCode);
  if (zoneMap !== 'undefined') {
    centerOnZoneName(getState(), selectedCountry.countryCode, 4);
  }
});

// Keyboard navigation
document.addEventListener('keyup', (e) => {
  const currentPage = getState().application.showPageState;
  if (currentPage === 'map') {
    if (e.key === 'Enter') {
      zoneList.clickSelectedItem();
    } else if (e.key === 'ArrowUp') {
      zoneList.selectPreviousItem();
    } else if (e.key === 'ArrowDown') {
      zoneList.selectNextItem();
    } else if (e.key === '/') {
      zoneSearchBar.clearInputAndFocus();
    } else if (e.key.match(/^[A-z]$/)) {
      zoneSearchBar.focusWithInput(e.key);
    } else {
      zoneSearchBar.focusWithInput('');
    }
  } else if (currentPage === 'country') {
    if (e.key === 'Backspace') {
      goBackToZoneListFromZoneDetails();
    } else if (e.key === '/') {
      goBackToZoneListFromZoneDetails();
      zoneSearchBar.clearInputAndFocus();
    }
  }
});

// FAQ link
d3.selectAll('.faq-link')
  .on('click', () => {
    dispatchApplication('selectedZoneName', undefined);
    dispatchApplication('showPageState', 'faq');
  });


// Mobile toolbar buttons
d3.selectAll('.map-button').on('click', () => dispatchApplication('showPageState', 'map'));
d3.selectAll('.info-button').on('click', () => dispatchApplication('showPageState', 'info'));
d3.selectAll('.highscore-button')
  .on('click', () => dispatchApplication('showPageState', 'highscore'));

// Onboarding modal
if (onboardingModal) {
  onboardingModal.onDismiss(() => {
    Cookies.set('onboardingSeen', true, { expires: 365 });
    dispatchApplication('onboardingSeen', true);
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
  contributorList.setContributors((zonesConfig[selectedZoneName] || {}).contributors || []);
  contributorList.render();
}

function renderCountryTable(state) {
  const d = getCurrentZoneData(state);
  if (!d) {
    // In this case there's nothing to do,
    // as the countryTable doesn't support receiving null data
  } else {
    countryTable.data(d).render(true);

    const zoneIsMissingParser = d.hasParser === undefined || !d.hasParser;
    countryTable.showNoParserMessageIf(zoneIsMissingParser);
    const zoneHasProductionDataAtTimestamp = !d.production || !Object.keys(d.production).length;
    const dataIsMostRecentDatapoint = state.application.selectedZoneTimeIndex === null;
    countryTable.showNoDataMessageIf(zoneHasProductionDataAtTimestamp && !zoneIsMissingParser, dataIsMostRecentDatapoint);
  }
}


function renderOpenTooltips(state) {

  const zoneData = getCurrentZoneData(state);
  const tooltipMode = state.application.tooltipDisplayMode;
  if (tooltipMode) {
    const isExchange = modeOrder.indexOf(tooltipMode) === -1;
    const fun = isExchange ?
      tooltipHelper.showExchange : tooltipHelper.showProduction;
    const ttp = isExchange ?
      countryTableExchangeTooltip : countryTableProductionTooltip;
    fun(ttp,
        tooltipMode, zoneData, tableDisplayEmissions,
        co2color, co2Colorbars,
      );
  }

  if (countryTooltip.isVisible) {
    tooltipHelper.showMapCountry(countryTooltip, zoneData, co2color, co2Colorbars);
  }

  if (priceTooltip.isVisible) {
    const tooltip = d3.select(priceTooltip._selector);
    tooltip.select('.value').html((zoneData.price || {}).value || '?');
    tooltip.select('.currency').html(getSymbolFromCurrency((zoneData.price || {}).currency) || '?');
    priceTooltip.show();
  }

}


function renderHistory(state) {
  const { selectedZoneName } = state.application;
  const history = state.data.histories[selectedZoneName];

  if (!history) {
    countryHistoryCarbonGraph.data([]).render();
    countryHistoryPricesGraph.data([]).render();
    countryHistoryMixGraph.data([]).render();
    zoneDetailsTimeSlider.data([]).render();
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
  
  zoneDetailsTimeSlider.data(history);

  // Update country table with all possible exchanges
  countryTable
    .exchangeKeys(countryHistoryMixGraph.exchangeKeysSet.values())
    .render();


  zoneDetailsTimeSlider.onChange((selectedZoneTimeIndex) => {
    if (getState().application.selectedZoneTimeIndex !== selectedZoneTimeIndex) {
      dispatch({type: 'UPDATE_SLIDER_SELECTED_ZONE_TIME', payload: {selectedZoneTimeIndex: selectedZoneTimeIndex}})
    }
  }).render();

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
          tooltipHelper.showMapCountry(countryTooltip, d, co2color, co2Colorbars, tooltipLowCarbonGauge, tooltipRenewableGauge);
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
function renderLeftPanelCollapseButton(state) {
  const { isLeftPanelCollapsed } = state.application;
  d3.select('.left-panel')
    .classed('collapsed', isLeftPanelCollapsed);
  d3.select('#left-panel-collapse-button')
    .classed('collapsed', isLeftPanelCollapsed)
  if (typeof zoneMap !== 'undefined') {
    zoneMap.map.resize();
  }
}
function routeToPage(pageName, state) {


  d3.selectAll('.left-panel .left-panel-zone-list').classed('small-screen-hidden', pageName !== 'highscore');

  d3.selectAll('.left-panel .left-panel-zone-list').classed('large-screen-hidden', pageName === 'country' || pageName === 'faq');

  d3.selectAll('.left-panel .mobile-info-tab').classed('small-screen-hidden', pageName !== 'info');

  d3.selectAll('.left-panel .faq-panel').classed('all-screens-hidden', pageName !== 'faq');

  d3.selectAll('.left-panel .left-panel-zone-details').classed('all-screens-hidden', pageName !== 'country');
  
    
  // Hide map on small screens
  // It's important we show the map before rendering it to make sure
  // sizes are set properly
  d3.selectAll('#map-container').classed('small-screen-hidden', pageName !== 'map');

  if (pageName === 'map') {
    d3.select('.left-panel').classed('small-screen-hidden', true);
    renderMap(state);
    if (state.application.windEnabled && typeof windLayer !== 'undefined') { windLayer.show(); }
    if (state.application.solarEnabled && typeof solarLayer !== 'undefined') { solarLayer.show(); }
    if (co2Colorbars) co2Colorbars.forEach((d) => { d.render(); });
    if (state.application.windEnabled && windColorbar) windColorbar.render();
    if (state.application.solarEnabled && solarColorbar) solarColorbar.render();
  } else {
    d3.select('.left-panel').classed('small-screen-hidden', false);
    d3.selectAll(`.left-panel-${pageName}`).style('display', undefined);
    if (pageName === 'info') {
      if (co2Colorbars) co2Colorbars.forEach((d) => { d.render(); });
      if (state.application.windEnabled) if (windColorbar) windColorbar.render();
      if (state.application.solarEnabled) if (solarColorbar) solarColorbar.render();
    }
  }

  d3.selectAll('#tab .list-item:not(.wind-toggle):not(.solar-toggle)').classed('active', false);
  d3.selectAll(`#tab .${pageName}-button`).classed('active', true);
  if (pageName === 'country') {
    d3.selectAll('#tab .highscore-button').classed('active', true);
  }
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
function centerOnZoneName(state, zoneName, zoomLevel) {
  if (typeof zoneMap === 'undefined') { return; }
  const selectedZone = state.data.grid.zones[zoneName];
  const selectedZoneCoordinates = [];
  selectedZone.geometry.coordinates.forEach((geojson) => {
    // selectedZoneCoordinates.push(geojson[0]);
    geojson[0].forEach((coord) => {
      selectedZoneCoordinates.push(coord);
    });
  });
  const maxLon = d3.max(selectedZoneCoordinates, d => d[0]);
  const minLon = d3.min(selectedZoneCoordinates, d => d[0]);
  const maxLat = d3.max(selectedZoneCoordinates, d => d[1]);
  const minLat = d3.min(selectedZoneCoordinates, d => d[1]);
  const lon = d3.mean([minLon, maxLon]);
  const lat = d3.mean([minLat, maxLat]);

  zoneMap.setCenter([lon, lat]);
  if (zoomLevel) {
    // Remember to set center and zoom in case the map wasn't loaded yet
    zoneMap.setZoom(zoomLevel);
    // If the panel is open the zoom doesn't appear perfectly centered because 
    // it centers on the whole window and not just the visible map part.
    // something one could fix in the future. It's tricky because one has to project, unproject
    // and project again taking both starting and ending zoomlevel into account
    zoneMap.map.easeTo({ center: [lon, lat], zoom: zoomLevel });
  }
}

// Observe for grid zones change
observe(state => state.data.grid.zones, (zones, state) => {
  if (typeof zoneMap !== 'undefined') {
    zoneMap.setData(Object.values(zones));
  }
  zoneList.setZones(zones);
  zoneList.render();
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

  // Analytics
  // Note: `selectedZoneName` will not yet be changed here
  thirdPartyServices.trackWithCurrentApplicationState('pageview');
});
// Observe for zone change (for example after map click)
observe(state => state.application.selectedZoneName, (selectedZoneName, state) => {
  if (!selectedZoneName) { return; }
  // Analytics
  thirdPartyServices.track('countryClick', { countryCode: selectedZoneName });

  // Render
  renderCountryTable(state);
  renderGauges(state);
  renderContributors(state);
  renderHistory(state);
  zoneDetailsTimeSlider.selectedIndex(null, null);

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
  renderOpenTooltips(state);
  [countryHistoryCarbonGraph, countryHistoryMixGraph, countryHistoryPricesGraph, zoneDetailsTimeSlider].forEach((g) => {
    g.selectedIndex(i, state.application.previousSelectedZoneTimeIndex);
  });
});
// Observe for color blind mode changes
observe(state => state.application.colorBlindModeEnabled, (colorBlindModeEnabled) => {
  Cookies.set('colorBlindModeEnabled', colorBlindModeEnabled);
  updateCo2Scale();
});

// Observe for bright mode changes
observe(state => state.application.brightModeEnabled, (brightModeEnabled) => {
  d3.selectAll('.brightmode-button').classed('active', brightModeEnabled);
  Cookies.set('brightdModeEnabled', brightModeEnabled);
  // update Theme
  if (getState().application.brightModeEnabled) {
    theme = themes.bright;
  } else {
    theme = themes.dark;
  }
  if (typeof zoneMap !== 'undefined') zoneMap.setTheme(theme);
});

// Observe for solar settings change
observe(state => state.application.solarEnabled, (solarEnabled, state) => {
  d3.selectAll('.solar-button').classed('active', solarEnabled);
  d3.select('.solar-potential-legend').classed('visible', solarEnabled);
  Cookies.set('solarEnabled', solarEnabled);

  solarLayerButtonTooltip.select('.tooltip-text').text(translation.translate(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer'));

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

  windLayerButtonTooltip.select('.tooltip-text').text(translation.translate(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer'));

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
// Observe for datetime chanes
observe(state => state.data.grid, (grid) => {
  if (grid && grid.datetime) {
    setLastUpdated();
  }
});
// Observe for legend visibility change
observe(state => state.application.legendVisible, (legendVisible) => {
  d3.selectAll('.floating-legend').classed('mobile-collapsed', !legendVisible);
  d3.select('.floating-legend-container').classed('mobile-collapsed', !legendVisible);
  d3.select('.toggle-legend-button.up').classed('visible', !legendVisible);
  d3.select('.toggle-legend-button.down').classed('visible', legendVisible);
});
// Observe for left panel collapse
observe(state => state.application.isLeftPanelCollapsed, (_, state) =>
  renderLeftPanelCollapseButton(state));

// Observe for search query change
observe(state => state.application.searchQuery, (searchQuery, state) => {
  zoneList.filterZonesByQuery(searchQuery);
});


// ** START

// Start a fetch and show loading screen
fetch(true, () => {
  if (!getState().application.customDate) {
    // Further calls to `fetch` won't show loading screen
    setInterval(fetch, REFRESH_TIME_MINUTES * 60 * 1000);
  }
});
