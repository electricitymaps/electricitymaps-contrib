import { store } from '../store';
import { isProduction } from '../helpers/environment';
import twitterConnection from './thirdparty/twitter';
import plausibleConnection from './thirdparty/plausible';
import debugConsoleConnection from './thirdparty/debugconsole';

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
    if (isProduction()) {
      this.addConnection(new twitterConnection());
      this.addConnection(new plausibleConnection());
    } else {
      this.addConnection(new debugConsoleConnection());
    }
  }

  addConnection(i) {
    this.connections.push(i);
    return i;
  }

  trackEvent(eventName, context) {
    console.log(`Tracking event ${eventName}`); // eslint-disable-line no-console
    this.connections.forEach((conn) => {
      try {
        conn.track(eventName, context);
      } catch (err) {
        console.error(`External connection error: ${err}`);
      }
    });
  }

  // track errors
  trackError(e) {
    console.error(`Error Caught! ${e}`);
    store.dispatch({
      type: 'TRACK_EVENT',
      payload: {
        eventName: 'error',
        context: { name: e.name, stack: e.stack },
      },
    });
    reportToSentry(e);
  }
}

export default new ConnectionsService(); // singleton
