/* eslint-disable camelcase */
/* eslint-disable prefer-template */
// TODO(olc): Remove after refactor

// see https://stackoverflow.com/questions/36887428/d3-event-is-null-in-a-reactjs-d3js-component
import { event as currentEvent } from 'd3-selection';
import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';

// Components
import OnboardingModal from './components/onboardingmodal';
import ZoneMap from './components/map';
import HorizontalColorbar from './components/horizontalcolorbar';

// Layer Components
import ExchangeLayer from './components/layers/exchange';
import SolarLayer from './components/layers/solar';
import WindLayer from './components/layers/wind';

// Services
import * as DataService from './services/dataservice';
import * as LoadingService from './services/loadingservice';
import thirdPartyServices from './services/thirdparty';

// Utils
import { getCurrentZoneData, getSelectedZoneExchangeKeys } from './selectors';
import { getCo2Scale } from './helpers/scales';

import {
  CARBON_GRAPH_LAYER_KEY,
  PRICES_GRAPH_LAYER_KEY,
  MAP_EXCHANGE_TOOLTIP_KEY,
  MAP_COUNTRY_TOOLTIP_KEY,
} from './helpers/constants';

// Layout
import Main from './layout/main';

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
const moment = require('moment');
const getSymbolFromCurrency = require('currency-symbol-map');

// State management
const {
  dispatch,
  dispatchApplication,
  getState,
  observe,
  store,
} = require('./store');

// Helpers
const { modeOrder, modeColor } = require('./helpers/constants');
const grib = require('./helpers/grib');
const HistoryState = require('./helpers/historystate');
const scales = require('./helpers/scales');
const { saveKey } = require('./helpers/storage');
const translation = require('./helpers/translation');
const { themes } = require('./helpers/themes');

// Configs
const zonesConfig = require('../../config/zones.json');

// Constants
// TODO(olc): should this be moved to constants.js?
const REMOTE_ENDPOINT = 'https://api.electricitymap.org';
const LOCAL_ENDPOINT = 'http://localhost:9000';

/*
  ****************************************************************
  This file is quite horrible. We are in the progress of migrating
  all logic of this file into React components.
  Help is appreciated ;-)
  ****************************************************************
  TODO:
  - turn all files in components/ into React components
  - move style from styles.css to individual components
  - instantiate components properly in the DOM in layout/ files
  - remove all observers and turn into react/redux flows
*/

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
  if (k === 'selectedZoneName'
    && Object.keys(getState().data.grid.zones).indexOf(applicationState[k]) === -1) {
    // The selectedZoneName doesn't exist, so don't update it
    return;
  }
  dispatchApplication(k, applicationState[k]);
});

// TODO(olc): should be stored in redux?
const ENDPOINT = getState().application.useRemoteEndpoint
  ? REMOTE_ENDPOINT : LOCAL_ENDPOINT;

// TODO(olc) move those to redux state
// or to component state
let currentMoment;
let mapDraggedSinceStart = false;
let wind;
let solar;
let hasCenteredMap = false;

// Set up objects
let exchangeLayer = null;
let initLoading = true;
LoadingService.startLoading('#loading');
LoadingService.startLoading('#small-loading');
let zoneMap;
let windLayer;
let solarLayer;
let onboardingModal;

// Render DOM
ReactDOM.render(
  <Provider store={store}>
    <Main />
  </Provider>,
  document.querySelector('#app'),
  () => {
    // Called when rendering is done
    if (typeof zoneMap !== 'undefined') {
      zoneMap.map.resize();
    }
  }
);

// Set standard theme
let theme = themes.bright;

const windColorbar = new HorizontalColorbar('.wind-potential-bar', scales.windColor)
  .markerColor('black');
const solarColorbarColor = d3.scaleLinear()
  .domain([0, 0.5 * scales.maxSolarDSWRF, scales.maxSolarDSWRF])
  .range(['black', 'white', 'gold']);
const solarColorbar = new HorizontalColorbar('.solar-potential-bar', solarColorbarColor)
  .markerColor('red');

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
      // TODO(olc): What about Xr and Xs?
      const extraPadding = (device.model === 'iPhone10,3' || device.model === 'iPhone10,6')
        ? 30
        : 20;
      d3.select('#header')
        .style('padding-top', `${extraPadding}px`);
      d3.select('#mobile-header')
        .style('padding-top', `${extraPadding}px`);

      d3.select('.prodcons-toggle-container')
        .style('margin-top', `${extraPadding}px`);

      d3.select('.flash-message .inner')
        .style('padding-top', `${extraPadding}px`);

      d3.select('.mapboxgl-ctrl-top-right')
        .style('transform', `translate(0,${extraPadding}px)`);
      d3.select('.layer-buttons-container')
        .style('transform', `translate(0,${extraPadding}px)`);
      if (typeof zoneMap !== 'undefined') {
        zoneMap.map.resize();
      }
    }

    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
    universalLinks.subscribe(null, (eventData) => {
      HistoryState.parseInitial(eventData.url.split('?')[1] || eventData.url);
      // In principle we should only do the rest of the app loading
      // after this point, instead of dispating a new event
      // eslint-disable-next-line no-shadow
      const applicationState = HistoryState.getStateFromHistory();
      Object.keys(applicationState).forEach((k) => {
        dispatchApplication(k, applicationState[k]);
      });
    });
  },

  onResume() {
    // Count a pageview
    thirdPartyServices.trackWithCurrentApplicationState('Visit');
    codePush.sync(null, { installMode: InstallMode.ON_NEXT_RESUME });
  },
};

if (getState().application.isCordova) {
  app.initialize();
}

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
  onboardingModal = new OnboardingModal('#app');
  thirdPartyServices.trackWithCurrentApplicationState('onboardingModalShown');
}

// Display randomly alternating header campaign message
const randomBoolean = Math.random() >= 0.5;

d3.select('.api-ad').classed('visible', randomBoolean);
d3.select('.database-ad').classed('visible', !randomBoolean);

// Set up co2 scales
let co2ColorScale;
let co2Colorbars = [];
function updateCo2Scale() {
  co2ColorScale = getCo2Scale(getState().application.colorBlindModeEnabled);
  co2Colorbars = [
    new HorizontalColorbar('.floating-legend-container .co2-colorbar', co2ColorScale, null, [0, 400, 800])
      .markerColor('white')
      .domain([0, scales.maxCo2])
      .render(),
  ];
  if (typeof zoneMap !== 'undefined') zoneMap.setCo2color(co2ColorScale, theme);
}

d3.select('#checkbox-colorblind').node().checked = getState().application.colorBlindModeEnabled;
d3.select('#checkbox-colorblind').on('change', () => {
  dispatchApplication('colorBlindModeEnabled', !getState().application.colorBlindModeEnabled);
});

// `finishLoading` will be invoked whenever we've finished loading the map, it could be triggered by a map-rerender
// or a first-time-ever loading of the webpage.
function finishLoading() {
  // if we're done with loading the map for the first ever render, toggle the state and wrapping up
  // with cleanup actions.
  if (initLoading) {
    // toggle the initial loading state. since this is a one-time on/off state, there's no need to manage it
    // with the redux state store.
    initLoading = false;
  }

  // map loading is done or aborted, hide the "map loading" overlay
  LoadingService.stopLoading('#loading');
  LoadingService.stopLoading('#small-loading');
}

// Start initialising map
try {
  zoneMap = new ZoneMap('zones', { zoom: 1.5, theme })
    .setCo2color(co2ColorScale)
    .setScrollZoom(!getState().application.isEmbedded)
    .onDragEnd(() => {
      dispatchApplication('centeredZoneName', null);
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
        .onExchangeMouseMove((zoneData) => {
          const { co2intensity } = zoneData;
          if (co2intensity) {
            dispatch({ type: 'SET_CO2_COLORBAR_MARKER', payload: { marker: co2intensity } });
          }
          dispatch({
            type: 'SHOW_TOOLTIP',
            payload: {
              data: zoneData,
              displayMode: MAP_EXCHANGE_TOOLTIP_KEY,
              position: { x: currentEvent.clientX, y: currentEvent.clientY },
            },
          });
        })
        .onExchangeMouseOut((d) => {
          dispatch({ type: 'UNSET_CO2_COLORBAR_MARKER' });
          dispatch({ type: 'HIDE_TOOLTIP' });
        })
        .onExchangeClick((d) => {
          console.log(d);
        })
        .setData(getState().application.electricityMixMode === 'consumption'
          ? Object.values(getState().data.grid.exchanges)
          : [])
        .setColorblindMode(getState().application.colorBlindModeEnabled)
        .render();

      // map loading is finished, lower the overlay shield
      finishLoading();

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

    // map loading is finished, lower the overlay shield
    finishLoading();
  } else {
    throw e;
  }
}

d3.select('.country-show-emissions-wrap a#emissions')
  .classed('selected', getState().application.tableDisplayEmissions);
d3.select('.country-show-emissions-wrap a#production')
  .classed('selected', !getState().application.tableDisplayEmissions);

function mapMouseOver(lonlat) {
  if (getState().application.windEnabled && wind && lonlat && typeof windLayer !== 'undefined') {
    const now = getState().application.customDate
      ? moment(getState().application.customDate) : (new Date()).getTime();
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
    const now = getState().application.customDate
      ? moment(getState().application.customDate) : (new Date()).getTime();
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
      // eslint-disable-next-line no-use-before-define
      dispatchApplication('centeredZoneName', selectedZoneName);
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
    saveKey('windEnabled', false);
    windLayer.draw(
      getState().application.customDate
        ? moment(getState().application.customDate) : moment(new Date()),
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
    saveKey('windEnabled', getState().application.windEnabled);
    LoadingService.stopLoading('#loading');
  } else if (typeof windLayer !== 'undefined') {
    windLayer.hide();
  }

  // Render Solar
  if (getState().application.solarEnabled && solar && solar['forecasts'][0] && solar['forecasts'][1] && typeof solarLayer !== 'undefined') {
    LoadingService.startLoading('#loading');
    // Make sure to disable solar if the drawing goes wrong
    saveKey('solarEnabled', false);
    solarLayer.draw(
      getState().application.customDate
        ? moment(getState().application.customDate) : moment(new Date()),
      solar.forecasts[0],
      solar.forecasts[1],
      scales.solarColor,
      (err) => {
        if (err) {
          console.error(err.message);
        } else {
          if (getState().application.solarEnabled) {
            solarLayer.show();
          } else {
            solarLayer.hide();
          }
          // Restore setting
          saveKey('solarEnabled', getState().application.solarEnabled);
        }
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
  currentMoment = getState().application.customDate
    ? moment(getState().application.customDate)
    : moment((getState().data.grid || {}).datetime);
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

function dataLoaded(err, clientVersion, callerLocation, callerZone, state, argSolar, argWind) {
  if (err) {
    console.error(err);
    return;
  }

  // Track pageview
  thirdPartyServices.trackWithCurrentApplicationState('pageview');

  // Is there a new version?
  d3.select('#new-version')
    .classed('active', (
      clientVersion !== getState().application.version
      && !getState().application.isLocalhost && !getState().application.isCordova
    ));

  const node = document.getElementById('map-container');
  if (typeof zoneMap !== 'undefined') {
    // Assign country map data
    zoneMap
      .onMouseMove((lonlat) => {
        mapMouseOver(lonlat);
      })
      .onZoneMouseMove((zoneData, i, clientX, clientY) => {
        dispatch({
          type: 'SET_CO2_COLORBAR_MARKER',
          payload: {
            marker: getState().application.electricityMixMode === 'consumption'
              ? zoneData.co2intensity
              : zoneData.co2intensityProduction,
          },
        });
        dispatch({
          type: 'SHOW_TOOLTIP',
          payload: {
            data: zoneData,
            displayMode: MAP_COUNTRY_TOOLTIP_KEY,
            position: {
              x: node.getBoundingClientRect().left + clientX,
              y: node.getBoundingClientRect().top + clientY,
            },
          },
        });
      })
      .onZoneMouseOut(() => {
        dispatch({ type: 'UNSET_CO2_COLORBAR_MARKER' });
        dispatch({ type: 'HIDE_TOOLTIP' });
        mapMouseOver(undefined);
      });
  }

  // Render weather if provided
  // Do not overwrite with null/undefined
  if (argWind) wind = argWind;
  if (argSolar) solar = argSolar;

  dispatchApplication('callerLocation', callerLocation);
  dispatchApplication('callerZone', callerZone);
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
          'HTTPError '
          + err.target.status + ' ' + err.target.statusText + ' at '
          + err.target.responseURL + ': '
          + err.target.responseText
        ));
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
  // eslint-disable-next-line no-shadow
  Q.await((err, clientVersion, state, solar, wind) => {
    handleConnectionReturnCode(err);
    if (!err) {
      dataLoaded(err, clientVersion, state.data.callerLocation, state.data.callerZone, state.data, solar, wind);
    }
    if (showLoading) {
      LoadingService.stopLoading('#loading');
    }
    LoadingService.stopLoading('#small-loading');
    if (callback) callback();
  });
}

window.addEventListener('resize', () => {
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
function toggleBright() {
  dispatchApplication('brightModeEnabled', !getState().application.brightModeEnabled);
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

// Production/Consumption
function toggleElectricityMixMode() {
  dispatchApplication('electricityMixMode', getState().application.electricityMixMode === 'consumption'
    ? 'production'
    : 'consumption');
}
d3.select('.production-toggle').on('click', toggleElectricityMixMode);

const prodConsButtonTootltip = d3.select('#production-toggle-tooltip');
d3.select('.production-toggle-info').on('click', () => {
  prodConsButtonTootltip.classed('hidden', !prodConsButtonTootltip.classed('hidden'));
});

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
        dispatch({
          type: 'UPDATE_SELECTED_ZONE',
          payload: { selectedZoneName: null },
        });
      }
    })
    .onCountryClick((d) => {
      // Analytics
      dispatchApplication('isLeftPanelCollapsed', false);
      dispatchApplication('showPageState', 'country'); // TODO(olc): infer in reducer?
      if (getState().application.selectedZoneName !== d.countryCode) {
        dispatch({
          type: 'UPDATE_SELECTED_ZONE',
          payload: { selectedZoneName: d.countryCode },
        });
      }
      thirdPartyServices.trackWithCurrentApplicationState('countryClick');
    });
}

// * Left panel *

// Back button
function goBackToZoneListFromZoneDetails() {
  dispatchApplication('selectedZoneName', undefined);
  dispatchApplication('showPageState', getState().application.pageToGoBackTo || 'map'); // TODO(olc): infer in reducer
}

d3.selectAll('.left-panel-back-button')
  .on('click', () => {
    goBackToZoneListFromZoneDetails();
  });

// Keyboard navigation
document.addEventListener('keyup', (e) => {
  if (e.key == null) { return; }
  const currentPage = getState().application.showPageState;
  if (currentPage === 'country') {
    if (e.key === 'Backspace') {
      goBackToZoneListFromZoneDetails();
    } else if (e.key === '/') {
      goBackToZoneListFromZoneDetails();
    }
  }
});

// Mobile toolbar buttons
d3.selectAll('.map-button').on('click touchend', () => dispatchApplication('showPageState', 'map'));
d3.selectAll('.info-button').on('click touchend', () => dispatchApplication('showPageState', 'info'));
d3.selectAll('.highscore-button')
  .on('click touchend', () => dispatchApplication('showPageState', 'highscore'));

// Onboarding modal
if (onboardingModal) {
  onboardingModal.onDismiss(() => {
    saveKey('onboardingSeen', true);
    dispatchApplication('onboardingSeen', true);
  });
}

// *** OBSERVERS ***
// Declare and attach all listeners that will react
// to state changes and cause a side-effect

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
    co2Colorbars.forEach((d) => { d.render(); });
    if (state.application.windEnabled && windColorbar) windColorbar.render();
    if (state.application.solarEnabled && solarColorbar) solarColorbar.render();
  } else {
    d3.select('.left-panel').classed('small-screen-hidden', false);
    d3.selectAll(`.left-panel-${pageName}`).style('display', undefined);
    if (pageName === 'info') {
      co2Colorbars.forEach((d) => { d.render(); });
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

function renderExchanges(state) {
  const { exchanges } = state.data.grid;
  const { electricityMixMode } = state.application;
  if (exchangeLayer) {
    exchangeLayer
      .setData(electricityMixMode === 'consumption'
        ? Object.values(exchanges)
        : [])
      .render();
  }
}

function renderZones(state) {
  const { zones } = state.data.grid;
  const { electricityMixMode } = state.application;
  if (typeof zoneMap !== 'undefined') {
    zoneMap.setData(electricityMixMode === 'consumption'
      ? Object.values(zones)
      : Object.values(zones)
        .map(d => Object.assign({}, d, { co2intensity: d.co2intensityProduction })));
  }
}

observe(state => state.application.co2ColorbarMarker, (co2ColorbarMarker, state) => {
  co2Colorbars.forEach((c) => { c.currentMarker(co2ColorbarMarker); });
});

// Observe for electricityMixMode change
observe(state => state.application.electricityMixMode, (electricityMixMode, state) => {
  renderExchanges(state);
  renderZones(state);
  renderMap(state);
});

// Observe for grid zones change
observe(state => state.data.grid.zones, (zones, state) => {
  renderZones(state);
});

// Observe for grid exchanges change
observe(state => state.data.grid.exchanges, (exchanges, state) => {
  renderExchanges(state);
});

// Observe for grid change
observe(state => state.data.grid, (grid, state) => {
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

  // Fetch history if needed
  tryFetchHistory(state);
});

// Observe for history change
observe(state => state.data.histories, (histories, state) => {
  // If history was cleared by the grid data for the currently selected country,
  // try to refetch it.
  const { selectedZoneName } = state.application;
  if (selectedZoneName && !state.data.histories[selectedZoneName]) {
    tryFetchHistory(state);
  }
});

// Observe for color blind mode changes
observe(state => state.application.colorBlindModeEnabled, (colorBlindModeEnabled) => {
  saveKey('colorBlindModeEnabled', colorBlindModeEnabled);
  updateCo2Scale();
  if (exchangeLayer) {
    exchangeLayer
      .setColorblindMode(colorBlindModeEnabled)
      .render();
  }
});

// Observe for bright mode changes
observe(state => state.application.brightModeEnabled, (brightModeEnabled) => {
  d3.selectAll('.brightmode-button').classed('active', brightModeEnabled);
  saveKey('brightModeEnabled', brightModeEnabled);
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
  saveKey('solarEnabled', solarEnabled);

  solarLayerButtonTooltip.select('.tooltip-text').text(translation.translate(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer'));

  const now = state.customDate
    ? moment(state.customDate) : (new Date()).getTime();
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

  saveKey('windEnabled', windEnabled);

  const now = state.customDate
    ? moment(state.customDate) : (new Date()).getTime();
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

observe(state => state.application.centeredZoneName, (centeredZoneName, state) => {
  if (centeredZoneName) {
    centerOnZoneName(state, centeredZoneName, 4);
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

// Observe for left panel collapse
observe(state => state.application.isLeftPanelCollapsed, (_, state) => {
  if (typeof zoneMap !== 'undefined') {
    zoneMap.map.resize();
  }
});

// Observe
observe(state => state.application.tableDisplayEmissions, (tableDisplayEmissions, state) => {
  if (getCurrentZoneData(state)) {
    thirdPartyServices.track(
      tableDisplayEmissions ? 'switchToCountryEmissions' : 'switchToCountryProduction',
      { countryCode: getCurrentZoneData(state).countryCode },
    );
  }
});


// ** START

// Start a fetch and show loading screen
fetch(true, () => {
  if (!getState().application.customDate) {
    // Further calls to `fetch` won't show loading screen
    setInterval(fetch, REFRESH_TIME_MINUTES * 60 * 1000);
  }
});
