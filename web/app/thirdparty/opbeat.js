require('opbeat-js/opbeat.min'); // does not return object

class OpbeatThirdParty {
    constructor() {
        _opbeat = window._opbeat || function () {
            (window._opbeat.q = window._opbeat.q || []).push(arguments)
        };
        if (_opbeat !== undefined) {
            _opbeat('config', {
                orgId: '093c53b0da9d43c4976cd0737fe0f2b1',
                appId: 'f40cef4b37'
            });
            _opbeat('setExtraContext', {
                bundleHash: bundleHash
            });
        } else {
            console.warn('Opbeat could not be initialized!');
        }
    }

    track(event, data) {} // no-op

    opbeat() {
        _opbeat(...arguments)
    }
}

module.exports = new OpbeatThirdParty();
