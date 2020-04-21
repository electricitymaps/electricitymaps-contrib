import moment from 'moment';
import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { Provider } from 'react-redux';
import { event as currentEvent, select } from 'd3-selection';
import { max as d3Max, min as d3Min, mean as d3Mean } from 'd3-array';

// Components
import ZoneMap from './components/map';
import ExchangeLayer from './components/layers/exchange';
import SolarLayer from './components/layers/solar';
import WindLayer from './components/layers/wind';

// Services
import thirdPartyServices from './services/thirdparty';

// State management
import {
  dispatch,
  dispatchApplication,
  getState,
  observe,
  store,
} from './store';

// Helpers
import grib from './helpers/grib';
import { themes } from './helpers/themes';
import { getCo2Scale, windColor } from './helpers/scales';
import { hasSolarDataExpired, hasWindDataExpired } from './helpers/gfs';
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

import global from './global';

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
let exchangeLayer;
let windLayer;
let solarLayer;

// Set proper locale
moment.locale(window.locale.toLowerCase());

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
    if (global.zoneMap) {
      global.zoneMap.map.resize();
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
      select('#header')
        .style('padding-top', `${extraPadding}px`);
      select('#mobile-header')
        .style('padding-top', `${extraPadding}px`);

      select('.prodcons-toggle-container')
        .style('margin-top', `${extraPadding}px`);

      select('.flash-message .inner')
        .style('padding-top', `${extraPadding}px`);

      select('.mapboxgl-ctrl-top-right')
        .style('transform', `translate(0,${extraPadding}px)`);
      select('.layer-buttons-container')
        .style('transform', `translate(0,${extraPadding}px)`);
      if (global.zoneMap) {
        global.zoneMap.map.resize();
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

function renderWind(state) {
  if (windLayer) {
    const { wind } = state.data;
    if (isWindEnabled() && wind && wind.forecasts[0] && wind.forecasts[1]) {
      windLayer.draw(
        getCustomDatetime() ? moment(getCustomDatetime()) : moment(new Date()),
        wind.forecasts[0],
        wind.forecasts[1],
        windColor,
      );
      windLayer.show();
    } else {
      windLayer.hide();
    }
  }
}

function renderSolar(state) {
  if (solarLayer) {
    const { solar } = state.data;
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
  if (!global.zoneMap) { return; }

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
      global.zoneMap.setCenter(callerLocation);
      hasCenteredMap = true;
    } else {
      global.zoneMap.setCenter([0, 50]);
    }
  }

  // Resize map to make sure it takes all container space
  // Warning: this causes a flicker
  global.zoneMap.map.resize();
}

function mapMouseOver(lonlat) {
  const { solar, wind } = getState().data;
  const now = getCustomDatetime() ? moment(getCustomDatetime()) : (new Date()).getTime();

  if (lonlat && isWindEnabled() && !hasWindDataExpired(now, getState())) {
    const u = grib.getInterpolatedValueAtLonLat(lonlat, now, wind.forecasts[0][0], wind.forecasts[1][0]);
    const v = grib.getInterpolatedValueAtLonLat(lonlat, now, wind.forecasts[0][1], wind.forecasts[1][1]);
    dispatchApplication('windColorbarValue', Math.sqrt(u * u + v * v));
  } else {
    dispatchApplication('windColorbarValue', null);
  }

  if (lonlat && isSolarEnabled() && !hasSolarDataExpired(now, getState())) {
    const value = grib.getInterpolatedValueAtLonLat(lonlat, now, solar.forecasts[0], solar.forecasts[1]);
    dispatchApplication('solarColorbarValue', value);
  } else {
    dispatchApplication('solarColorbarValue', null);
  }
}

function centerOnZoneName(state, zoneName, zoomLevel) {
  if (!global.zoneMap) { return; }

  const selectedZone = state.data.grid.zones[zoneName];
  const selectedZoneCoordinates = [];
  selectedZone.geometry.coordinates.forEach((geojson) => {
    // selectedZoneCoordinates.push(geojson[0]);
    geojson[0].forEach((coord) => {
      selectedZoneCoordinates.push(coord);
    });
  });
  const maxLon = d3Max(selectedZoneCoordinates, d => d[0]);
  const minLon = d3Min(selectedZoneCoordinates, d => d[0]);
  const maxLat = d3Max(selectedZoneCoordinates, d => d[1]);
  const minLat = d3Min(selectedZoneCoordinates, d => d[1]);
  const lon = d3Mean([minLon, maxLon]);
  const lat = d3Mean([minLat, maxLat]);

  global.zoneMap.setCenter([lon, lat]);
  if (zoomLevel) {
    // Remember to set center and zoom in case the map wasn't loaded yet
    global.zoneMap.setZoom(zoomLevel);
    // If the panel is open the zoom doesn't appear perfectly centered because
    // it centers on the whole window and not just the visible map part.
    // something one could fix in the future. It's tricky because one has to project, unproject
    // and project again taking both starting and ending zoomlevel into account
    global.zoneMap.map.easeTo({ center: [lon, lat], zoom: zoomLevel });
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
  if (global.zoneMap) {
    global.zoneMap.setData(electricityMixMode === 'consumption'
      ? Object.values(zones)
      : Object.values(zones)
        .map(d => Object.assign({}, d, { co2intensity: d.co2intensityProduction })));
  }
}

// Start initialising map
try {
  global.zoneMap = new ZoneMap('zones', { zoom: 1.5, theme: themes.bright })
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
      exchangeLayer = new ExchangeLayer('arrows-layer')
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

  windLayer = new WindLayer('wind');
  solarLayer = new SolarLayer('solar');
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
  // Refresh map in the next render cycle (after the page transition) to make
  // sure it gets displayed correctly. Do it only on mobile as otherwise the
  // map is being displayed the whole time (on every page).
  if (currentPage === 'map' && state.application.isMobile) {
    setTimeout(() => {
      renderMap(state);
      renderWind(state);
      renderSolar(state);
    }, 0);
  }

  // Analytics
  thirdPartyServices.trackWithCurrentApplicationState('pageview');
});

// Observe for color blind mode changes
observe(state => state.application.colorBlindModeEnabled, (colorBlindModeEnabled) => {
  if (global.zoneMap) {
    global.zoneMap.setCo2color(getCo2Scale(colorBlindModeEnabled));
  }
  if (exchangeLayer) {
    exchangeLayer
      .setColorblindMode(colorBlindModeEnabled)
      .render();
  }
});

// Observe for bright mode changes
observe(state => state.application.brightModeEnabled, (brightModeEnabled) => {
  if (global.zoneMap) {
    global.zoneMap.setTheme(brightModeEnabled ? themes.bright : themes.dark);
  }
});

observe(state => state.application.centeredZoneName, (centeredZoneName, state) => {
  if (centeredZoneName) {
    centerOnZoneName(state, centeredZoneName, 4);
  }
});

// Observe for left panel collapse
observe(state => state.application.isLeftPanelCollapsed, (_, state) => {
  if (global.zoneMap) {
    global.zoneMap.map.resize();
  }
});

// Observe for solar data change
observe(state => state.data.solar, (_, state) => { renderSolar(state); });

// Observe for wind data change
observe(state => state.data.wind, (_, state) => { renderWind(state); });
