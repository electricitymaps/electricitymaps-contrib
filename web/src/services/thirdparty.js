/* eslint-disable global-require */
/* eslint-disable prefer-rest-params */
// TODO: remove once refactored

import { getState } from '../store';
import { history } from '../helpers/router';

class ConnectionsService {
  constructor() {
    this.connections = [];
    if (getState().application.isProduction) {
      this.addConnection(require('./thirdparty/twitter'));
      this.addConnection(require('./thirdparty/facebook'));
      this._ga = this.addConnection(require('./thirdparty/ga'));
      this.addConnection(require('./thirdparty/mixpanel'));
    }
  }

  addConnection(i) {
    this.connections.push(i);
    return i;
  }

  track(eventName, paramObj) {
    this.connections.forEach((conn) => {
      try {
        conn.track(eventName, paramObj);
      } catch (err) { console.error(`External connection error: ${err}`); }
    });
  }

  trackWithCurrentApplicationState(eventName) {
    const appState = getState().application;
    this.track(eventName, {
      ...appState,
      bundleVersion: appState.bundleHash,
      embeddedUri: appState.isEmbedded ? document.referrer : null,
      currentPage: history.location.pathname.split('/')[1],
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

  reportToSentry(e) {
    if (window.Sentry !== undefined) {
      try {
        window.Sentry.captureException(e);
      } catch (err) {
        console.error(`Error while reporting error to Sentry: ${err}`);
      }
    }
  }

  // track errors
  trackError(e) {
    console.error(`Error Caught! ${e}`);
    this.track('error', { ...getState().application, name: e.name, stack: e.stack });
    this.ga('event', 'exception', { description: e, fatal: false });
    this.reportToSentry(e);
  }
}

export default new ConnectionsService(); // singleton
