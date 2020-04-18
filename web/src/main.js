/* eslint-disable camelcase */
/* eslint-disable prefer-template */
// TODO(olc): Remove after refactor

// see https://stackoverflow.com/questions/36887428/d3-event-is-null-in-a-reactjs-d3js-component
import { event as currentEvent } from 'd3-selection';
import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { Provider } from 'react-redux';

// Components
import ZoneMap from './components/map';

// Layer Components
import ExchangeLayer from './components/layers/exchange';
import SolarLayer from './components/layers/solar';
import WindLayer from './components/layers/wind';

// Services
import * as DataService from './services/dataservice';
import * as LoadingService from './services/loadingservice';
import thirdPartyServices from './services/thirdparty';

// Utils
import { getCo2Scale } from './helpers/scales';
import { getEndpoint, handleConnectionReturnCode } from './helpers/api';
import {
  history,
  isSolarEnabled,
  isWindEnabled,
  navigateTo,
  getCurrentPage,
  getCustomDatetime,
  getZoneId,
} from './helpers/router';

import { MAP_EXCHANGE_TOOLTIP_KEY, MAP_COUNTRY_TOOLTIP_KEY } from './helpers/constants';

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
const scales = require('./helpers/scales');
const { saveKey } = require('./helpers/storage');
const translation = require('./helpers/translation');
const { themes } = require('./helpers/themes');

// Configs
const zonesConfig = require('../../config/zones.json');

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

// TODO(olc) move those to redux state
// or to component state
let mapDraggedSinceStart = false;
let wind;
let solar;
let hasCenteredMap = false;

// Set up objects
let exchangeLayer = null;
let initLoading = true;
let zoneMap;
let windLayer;
let solarLayer;

// Set standard theme
let theme = themes.bright;

LoadingService.startLoading('#loading');
LoadingService.startLoading('#small-loading');

// Set proper locale
moment.locale(getState().application.locale.toLowerCase());

// Analytics
thirdPartyServices.trackWithCurrentApplicationState('Visit');

// Render DOM
ReactDOM.render(
  <Provider store={store}>
    {/* TODO: Switch to BrowserRouter once we don't need to manipulate */}
    {/* the route history outside of React components anymore */}
    <Router history={history}>
      <Main />
    </Router>
  </Provider>,
  document.querySelector('#app'),
  () => {
    // Called when rendering is done
    if (typeof zoneMap !== 'undefined') {
      zoneMap.map.resize();
    }
  }
);

//
// *** CORDOVA ***
//

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
    if (['zone', 'faq'].includes(getCurrentPage())) {
      navigateTo({ pathname: '/map', search: history.location.search });
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

//
// *** MAP & LAYERS ***
//

// Only center once
function renderMap(state) {
  if (typeof zoneMap === 'undefined') { return; }

  if (!mapDraggedSinceStart && !hasCenteredMap) {
    const { callerLocation } = state.application;
    const zoneId = getZoneId();
    if (zoneId) {
      console.log(`Centering on zone ${zoneId}`);
      // eslint-disable-next-line no-use-before-define
      dispatchApplication('centeredZoneName', zoneId);
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
  if (isWindEnabled() && wind && wind['forecasts'][0] && wind['forecasts'][1] && typeof windLayer !== 'undefined') {
    LoadingService.startLoading('#loading');
    windLayer.draw(
      getCustomDatetime()
        ? moment(getCustomDatetime()) : moment(new Date()),
      wind.forecasts[0],
      wind.forecasts[1],
      scales.windColor,
    );
    if (isWindEnabled()) {
      windLayer.show();
    } else {
      windLayer.hide();
    }
    LoadingService.stopLoading('#loading');
  } else if (typeof windLayer !== 'undefined') {
    windLayer.hide();
  }

  // Render Solar
  if (isSolarEnabled() && solar && solar['forecasts'][0] && solar['forecasts'][1] && typeof solarLayer !== 'undefined') {
    LoadingService.startLoading('#loading');
    solarLayer.draw(
      getCustomDatetime()
        ? moment(getCustomDatetime()) : moment(new Date()),
      solar.forecasts[0],
      solar.forecasts[1],
      (err) => {
        if (err) {
          console.error(err.message);
        } else if (isSolarEnabled()) {
          solarLayer.show();
        } else {
          solarLayer.hide();
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

function mapMouseOver(lonlat) {
  if (isWindEnabled() && wind && lonlat && typeof windLayer !== 'undefined') {
    const now = getCustomDatetime()
      ? moment(getCustomDatetime()) : (new Date()).getTime();
    if (!windLayer.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
      const u = grib.getInterpolatedValueAtLonLat(lonlat,
        now, wind.forecasts[0][0], wind.forecasts[1][0]);
      const v = grib.getInterpolatedValueAtLonLat(lonlat,
        now, wind.forecasts[0][1], wind.forecasts[1][1]);
      dispatchApplication('windColorbarValue', Math.sqrt(u * u + v * v));
    }
  } else {
    dispatchApplication('windColorbarValue', null);
  }
  if (isSolarEnabled() && solar && lonlat && typeof solarLayer !== 'undefined') {
    const now = getCustomDatetime()
      ? moment(getCustomDatetime()) : (new Date()).getTime();
    if (!solarLayer.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
      dispatchApplication(
        'solarColorbarValue',
        grib.getInterpolatedValueAtLonLat(lonlat, now, solar.forecasts[0], solar.forecasts[1])
      );
    }
  } else {
    dispatchApplication('solarColorbarValue', null);
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
            dispatchApplication('co2ColorbarValue', co2intensity);
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
          dispatchApplication('co2ColorbarValue', null);
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
    })
    .onSeaClick(() => {
      navigateTo({ pathname: '/map', search: history.location.search });
    })
    .onCountryClick((d) => {
      // Analytics
      navigateTo({ pathname: `/zone/${d.countryCode}`, search: history.location.search });
      dispatchApplication('isLeftPanelCollapsed', false);
      thirdPartyServices.trackWithCurrentApplicationState('countryClick');
    })
    .onMouseMove((lonlat) => {
      mapMouseOver(lonlat);
    })
    .onZoneMouseMove((zoneData, i, clientX, clientY) => {
      const node = document.getElementById('map-container');
      dispatchApplication(
        'co2ColorbarValue',
        getState().application.electricityMixMode === 'consumption'
          ? zoneData.co2intensity
          : zoneData.co2intensityProduction
      );
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
      dispatchApplication('co2ColorbarValue', null);
      dispatch({ type: 'HIDE_TOOLTIP' });
      mapMouseOver(undefined);
    });

  windLayer = new WindLayer('wind', zoneMap);
  solarLayer = new SolarLayer('solar', zoneMap);
  dispatchApplication('webglsupported', true);
} catch (e) {
  if (e === 'WebGL not supported') {
    // Redirect and notify if WebGL is not supported
    dispatchApplication('webglsupported', false);
    navigateTo({ pathname: '/ranking', search: history.location.search });

    // map loading is finished, lower the overlay shield
    finishLoading();
  } else {
    throw e;
  }
}

//
// *** DATA MANAGEMENT ***
//

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

  const datetime = getCustomDatetime();
  const now = datetime || new Date();

  dispatch({ type: 'GRID_DATA_FETCH_REQUESTED', payload: { datetime, showLoading } });

  if (isSolarEnabled()) {
    if (!solar || solarLayer.isExpired(now, solar.forecasts[0], solar.forecasts[1])) {
      Q.defer(ignoreError(DataService.fetchGfs), getEndpoint(), 'solar', now);
    } else {
      Q.defer(cb => cb(null, solar));
    }
  } else {
    Q.defer(DataService.fetchNothing);
  }

  if (isWindEnabled()) {
    if (!wind || windLayer.isExpired(now, wind.forecasts[0], wind.forecasts[1])) {
      Q.defer(ignoreError(DataService.fetchGfs), getEndpoint(), 'wind', now);
    } else {
      Q.defer(cb => cb(null, wind));
    }
  } else {
    Q.defer(DataService.fetchNothing);
  }

  // eslint-disable-next-line no-shadow
  Q.await((err, clientVersion, argSolar, argWind) => {
    handleConnectionReturnCode(err, getState().application);
    if (!err) {
      // Render weather if provided
      // Do not overwrite with null/undefined
      if (argWind) wind = argWind;
      if (argSolar) solar = argSolar;

      // Is there a new version?
      d3.select('#new-version').classed('active', (
        clientVersion !== getState().application.version
        && !getState().application.isLocalhost && !getState().application.isCordova
      ));
    }
    if (showLoading) {
      LoadingService.stopLoading('#loading');
    }
    LoadingService.stopLoading('#small-loading');
    if (callback) callback();
  });
}

// Only for debugging purposes
window.retryFetch = () => {
  dispatchApplication('showConnectionWarning', false);
  fetch(false);
};

//
// *** OBSERVERS ***
//
// Declare and attach all listeners that will react
// to state changes and cause a side-effect

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
observe(state => state.application.currentPage, (currentPage, state) => {
  if (currentPage === 'map') {
    // Refresh map in the next render cycle (after the page
    // transition) to make sure it gets displayed correctly.
    setTimeout(() => { renderMap(state); }, 0);
    if (isWindEnabled() && typeof windLayer !== 'undefined') { windLayer.show(); }
    if (isSolarEnabled() && typeof solarLayer !== 'undefined') { solarLayer.show(); }
  }

  // Analytics
  thirdPartyServices.trackWithCurrentApplicationState('pageview');
});

// Observe for color blind mode changes
observe(state => state.application.colorBlindModeEnabled, (colorBlindModeEnabled) => {
  if (zoneMap) {
    zoneMap.setCo2color(getCo2Scale(colorBlindModeEnabled));
  }
  if (exchangeLayer) {
    exchangeLayer
      .setColorblindMode(colorBlindModeEnabled)
      .render();
  }
});

// Observe for bright mode changes
observe(state => state.application.brightModeEnabled, (brightModeEnabled) => {
  // update Theme
  if (brightModeEnabled) {
    theme = themes.bright;
  } else {
    theme = themes.dark;
  }
  if (typeof zoneMap !== 'undefined') zoneMap.setTheme(theme);
});

// Observe for solar settings change
// TODO: Remove this after solar layer is moved to React, so that this
// bool can be removed from Redux and managed through the URL state.
// See https://github.com/tmrowco/electricitymap-contrib/issues/2310
observe(state => state.application.solarEnabled, (solarEnabled, state) => {
  const now = getCustomDatetime() ? moment(getCustomDatetime()) : (new Date()).getTime();
  if (solarEnabled && typeof solarLayer !== 'undefined') {
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
// TODO: Remove this after wind layer is moved to React, so that this
// bool can be removed from Redux and managed through the URL state.
// See https://github.com/tmrowco/electricitymap-contrib/issues/2310
observe(state => state.application.windEnabled, (windEnabled, state) => {
  const now = getCustomDatetime() ? moment(getCustomDatetime()) : (new Date()).getTime();
  if (windEnabled && typeof windLayer !== 'undefined') {
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

// Observe for left panel collapse
observe(state => state.application.isLeftPanelCollapsed, (_, state) => {
  if (typeof zoneMap !== 'undefined') {
    zoneMap.map.resize();
  }
});

//
// *** START ***
//

// Start a fetch and show loading screen
fetch(true, () => {
  if (!getCustomDatetime()) {
    // Further calls to `fetch` won't show loading screen
    setInterval(fetch, REFRESH_TIME_MINUTES * 60 * 1000);
  }
});
