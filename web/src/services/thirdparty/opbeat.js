require('opbeat-js/opbeat.min'); // does not return object
const store = require('../../store');

class OpbeatThirdParty {
  constructor() {
    if (store.getState().application.isProduction) {
      _opbeat = window._opbeat || function () {
        (window._opbeat.q = window._opbeat.q || []).push(arguments);
      };
      if (_opbeat !== undefined) {
        _opbeat('config', {
          orgId: '093c53b0da9d43c4976cd0737fe0f2b1',
          appId: 'f40cef4b37'
        });
        _opbeat('setExtraContext', {
          bundleHash
        });
      } else {
        console.warn('Opbeat could not be initialized!');
      }
    } else {
      console.warn('Opbeat disabled in development mode');
    }
  }

  track(event, data) {} // no-op

  opbeat() {
    _opbeat(...arguments);
  }
}

module.exports = new OpbeatThirdParty();
