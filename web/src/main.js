import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { Provider } from 'react-redux';

import 'mapbox-gl/dist/mapbox-gl.css'; // Required for map zooming buttons
import 'url-search-params-polyfill'; // For IE 11 support

import { history } from './helpers/router';
import { store, sagaMiddleware } from './store';
import { cordovaApp } from './cordova';
import sagas from './sagas';

import Main from './layout/main';
import GlobalStyle from './globalstyle';


// init localisation
import './helpers/i18n';

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
  document.querySelector('#app'),
);

// Initialise mobile app (cordova)
if (window.isCordova) {
  cordovaApp.initialize();
}
