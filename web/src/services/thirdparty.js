import bugsnag from 'bugsnag-js';
import * as Sentry from '@sentry/browser';

const store = require('../store');

const bugsnagClient = bugsnag({
  apiKey: 'ab57d4f7207c97344bc61a8c2e48d176',
  appVersion: store.getState().application.bundleHash,
});

Sentry.init({
  dsn: 'https://bdda83aba5724206bf02a880b14c56d1@sentry.io/1295430',
  release: store.getState().application.bundleHash,
});

class ConnectionsService {
  constructor() {
    this.connections = [];
    if (store.getState().application.isProduction) {
      this.addConnection(require('./thirdparty/twitter'));
      this.addConnection(require('./thirdparty/facebook'));
      this._ga = this.addConnection(require('./thirdparty/ga'));
      this.addConnection(require('./thirdparty/mixpanel'));
      this._stackdriver = this.addConnection(require('./thirdparty/stackdriver'));
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
      } catch(err) { console.error('External connection error: ' + err); }
    });
  }

  trackWithCurrentApplicationState(eventName) {
    const params = store.getState().application;
    params.bundleVersion = params.bundleHash;
    params.embeddedUri = params.isEmbedded ? document.referrer : null;
    this.track(eventName, params);
  }

  // track google analytics if is available
  ga(){
    if(this._ga !== undefined){
      try {
        this._ga.ga(...arguments);
      } catch(err) { console.error('Google analytics track error: ' + err); }
    }
  }

  // track errors
  reportError(e) {
    if (this._stackdriver !== undefined) {
      try {
        this._stackdriver.report(...arguments);
      } catch(err) {
        console.error('Error while reporting error: ' + err);
      }
    }
    if (bugsnagClient !== undefined) {
      try {
        bugsnagClient.notify(e);
      } catch (err) {
        console.error('Error while reporting error: ' + err);
      }
    }
    if (Sentry !== undefined) {
      try {
        Sentry.captureException(e);
      } catch (err) {
        console.error('Error while reporting error: ' + err);
      }
    }
  }
}

module.exports = new ConnectionsService(); // singleton
