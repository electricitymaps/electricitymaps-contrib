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

// Start initialising map
global.zoneMap = new ZoneMap('zones', { zoom: 1.5, theme: themes.bright })
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
