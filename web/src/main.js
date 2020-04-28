import moment from 'moment';
import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { Provider } from 'react-redux';
import { event as currentEvent, select } from 'd3-selection';
import { max as d3Max, min as d3Min, mean as d3Mean } from 'd3-array';

// Components
import ZoneMap from './components/map';

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
  MAP_COUNTRY_TOOLTIP_KEY,
} from './helpers/constants';

// Layout
import Main from './layout/main';
import GlobalStyle from './globalstyle';
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
      <GlobalStyle />
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
// *** MAP ***
//

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

// Start initialising map
global.zoneMap = new ZoneMap('zones', { zoom: 1.5, theme: themes.bright })
  .onDragEnd(() => {
    dispatchApplication('centeredZoneName', null);
    // Somehow there is a drag event sent before the map data is loaded.
    // We want to ignore it.
    if (!mapDraggedSinceStart && getState().data.grid.datetime) {
      mapDraggedSinceStart = true;
    }
  })
  .onMouseMove((lonlat) => {
    mapMouseOver(lonlat);
  });

//
// *** OBSERVERS ***
//
// Declare and attach all listeners that will react
// to state changes and cause a side-effect

// Observe for page change
observe(state => state.application.currentPage, (currentPage, state) => {
  // Analytics
  thirdPartyServices.trackWithCurrentApplicationState('pageview');
});

observe(state => state.application.centeredZoneName, (centeredZoneName, state) => {
  if (centeredZoneName) {
    centerOnZoneName(state, centeredZoneName, 4);
  }
});
