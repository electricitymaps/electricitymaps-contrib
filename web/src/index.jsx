/* eslint-disable no-console */
import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { Provider } from 'react-redux';

import 'mapbox-gl/dist/mapbox-gl.css'; // Required for map zooming buttons

import { history } from './helpers/router';
import { store, sagaMiddleware } from './store';
import { cordovaApp } from './cordova';
import sagas from './sagas';

import Main from './layout/main';
import GlobalStyle from './globalstyle';

// init styling
import './scss/styles.scss';

// init localisation
import './helpers/i18n';

// Initial greeting message for curious people
console.log(
  `%cWelcome to electricityMap!
🌍 %cReady to work on fixing the climate full-time?
  https://electricitymap.org/jobs
🐙 Got comments or want to contribute?
  https://github.com/electricitymap/electricitymap-contrib`,
  'color: green; font-weight: bold',
  'color: #666; font-style: italic'
);

// Plug in the sagas
sagaMiddleware.run(sagas);

// Render DOM
ReactDOM.render(
  <React.Suspense fallback={<div />}>
    <Provider store={store}>
      {/* TODO: Switch to BrowserRouter once we don't need to manipulate */}
      {/* the route history outside of React components anymore */}
      <Router history={history}>
        <GlobalStyle />
        <Main />
      </Router>
    </Provider>
  </React.Suspense>,
  document.querySelector('#app')
);

// Initialise mobile app (cordova)
if (window.isCordova) {
  cordovaApp.initialize();
}

// Hot Module Replacement (HMR) - Remove this snippet to remove HMR.
// Learn more: https://www.snowpack.dev/concepts/hot-module-replacement
// eslint-disable-next-line
if (undefined /* [snowpack] import.meta.hot */) {
  undefined /* [snowpack] import.meta.hot */
    .accept();
}
