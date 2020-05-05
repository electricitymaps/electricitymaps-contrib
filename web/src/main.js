import React from 'react';
import ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { Provider } from 'react-redux';
import moment from 'moment';

import thirdPartyServices from './services/thirdparty';
import { history } from './helpers/router';
import { store } from './store';
import { cordovaApp } from './cordova';

import Main from './layout/main';
import GlobalStyle from './globalstyle';

// Track how long it took to start executing the JS code
if (thirdPartyServices._ga) {
  thirdPartyServices._ga.timingMark('start_executing_js');
}

// Set proper locale
moment.locale(window.locale.toLowerCase());

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
