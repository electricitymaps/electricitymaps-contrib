const store = require('../store');

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
  reportError() {
    if (this._stackdriver !== undefined) {
      try {
        this._stackdriver.report(...arguments);
      } catch(err) {
        console.error('Error while reporting error: ' + err);
      }
    }
  }
}

module.exports = new ConnectionsService(); // singleton
