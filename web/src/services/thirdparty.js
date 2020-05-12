/* eslint-disable global-require */
/* eslint-disable prefer-rest-params */
// TODO: remove once refactored

import { getState } from '../store';
import { history, getSearchParams } from '../helpers/router';

function reportToSentry(e) {
  if (window.Sentry !== undefined) {
    try {
      window.Sentry.captureException(e);
    } catch (err) {
      console.error(`Error while reporting error to Sentry: ${err}`);
    }
  }
}

class ConnectionsService {
  constructor() {
    this.connections = [];
    if (getState().application.isProduction) {
      this.addConnection(require('./thirdparty/twitter'));
      this.addConnection(require('./thirdparty/facebook'));
      this._ga = this.addConnection(require('./thirdparty/ga'));
      this.addConnection(require('./thirdparty/mixpanel'));
    } else {
      this.addConnection(require('./thirdparty/debugconsole'));
    }
  }

  addConnection(i) {
    this.connections.push(i);
    return i;
  }

  // TODO: Use sagas for this instead.
  trackWithCurrentApplicationState(eventName, additionalData) {
    const appState = getState().application;
    const data = {
      ...appState,
      bundleVersion: appState.bundleHash,
      embeddedUri: appState.isEmbedded ? document.referrer : null,
      currentPage: history.location.pathname.split('/')[1],
      selectedZoneName: history.location.pathname.split('/')[2],
      solarEnabled: getSearchParams().get('solar') === 'true',
      windEnabled: getSearchParams().get('wind') === 'true',
      ...additionalData,
    };
    this.connections.forEach((conn) => {
      try {
        conn.track(eventName, data);
      } catch (err) { console.error(`External connection error: ${err}`); }
    });
  }

  // track google analytics if is available
  ga() {
    if (this._ga !== undefined) {
      try {
        this._ga.ga(...arguments);
      } catch (err) { console.error(`Google analytics track error: ${err}`); }
    }
  }

  // track errors
  trackError(e) {
    console.error(`Error Caught! ${e}`);
    this.trackWithCurrentApplicationState('error', { name: e.name, stack: e.stack });
    this.ga('event', 'exception', { description: e, fatal: false });
    reportToSentry(e);
  }
}

export default new ConnectionsService(); // singleton
