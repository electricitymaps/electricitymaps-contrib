import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { Provider } from 'react-redux';
import moment from 'moment';

import 'mapbox-gl/dist/mapbox-gl.css'; // Required for map zooming buttons
import 'url-search-params-polyfill'; // For IE 11 support

import thirdPartyServices from './services/thirdparty';
import { history } from './helpers/router';
import { store, sagaMiddleware } from './store';
import { cordovaApp } from './cordova';
import sagas from './sagas';

import Main from './layout/main';
import GlobalStyle from './globalstyle';

import './scss/styles.scss';

// Track how long it took to start executing the JS code
if (thirdPartyServices._ga) {
  thirdPartyServices._ga.timingMark('start_executing_js');
}

// Set proper locale
moment.locale(window.locale.toLowerCase());

// Plug in the sagas
sagaMiddleware.run(sagas);

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
);

// Initialise mobile app (cordova)
if (window.isCordova) {
  cordovaApp.initialize();
}

// Hot Module Replacement (HMR) - Remove this snippet to remove HMR.
// Learn more: https://www.snowpack.dev/concepts/hot-module-replacement
if (undefined /* [snowpack] import.meta.hot */ ) {
  undefined /* [snowpack] import.meta.hot */ .accept();
}
