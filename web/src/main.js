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
import thirdPartyServices from './services/thirdparty';

// Utils
import { getCo2Scale } from './helpers/scales';
import {
  history,
  isSolarEnabled,
  isWindEnabled,
  navigateTo,
  getCurrentPage,
  getCustomDatetime,
  getZoneId,
} from './helpers/router';

import {
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

// State management
const {
  dispatch,
  dispatchApplication,
  getState,
  observe,
  store,
} = require('./store');

// Helpers
const grib = require('./helpers/grib');
const scales = require('./helpers/scales');
const { themes } = require('./helpers/themes');

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

// TODO(olc) move those to redux state
// or to component state
let mapDraggedSinceStart = false;
let hasCenteredMap = false;

// Set up objects
let exchangeLayer = null;
let zoneMap;
let windLayer;
let solarLayer;

// Set standard theme
let theme = themes.bright;

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

function renderWind() {
  if (windLayer) {
    const { wind } = getState().data;
    if (isWindEnabled() && wind && wind.forecasts[0] && wind.forecasts[1]) {
      windLayer.draw(
        getCustomDatetime() ? moment(getCustomDatetime()) : moment(new Date()),
        wind.forecasts[0],
        wind.forecasts[1],
        scales.windColor,
      );
      windLayer.show();
    } else {
      windLayer.hide();
    }
  }
}

function renderSolar() {
  if (solarLayer) {
    const { solar } = getState().data;
    if (isSolarEnabled() && solar && solar.forecasts[0] && solar.forecasts[1]) {
      solarLayer.draw(
        getCustomDatetime() ? moment(getCustomDatetime()) : (new Date()).getTime(),
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
        },
      );
    } else {
      solarLayer.hide();
    }
  }
}

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
  renderWind();

  // Render Solar
  renderSolar();

  // Resize map to make sure it takes all container space
  // Warning: this causes a flicker
  zoneMap.map.resize();
}

function mapMouseOver(lonlat) {
  const { solar, wind } = getState().data;

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
      dispatchApplication('isLoadingMap', false);

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
    dispatchApplication('isLoadingMap', false);
  } else {
    throw e;
  }
}

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

// Observe for solar data change
observe(state => state.data.solar, () => { renderSolar(); });

// Observe for wind data change
observe(state => state.data.wind, () => { renderWind(); });
