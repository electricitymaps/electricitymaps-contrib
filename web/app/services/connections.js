var application = require('./application');

class ConnectionsService {
    constructor() {
        this.connections = [];
        if(application.isProduction()){
            this.addConnection(require('../connections/twitter'));
            this.addConnection(require('../connections/facebook'));
            this._ga = this.addConnection(require('../connections/ga'));
            this.addConnection(require('../connections/mixpanel'));
            this._opbeat = this.addConnection(require('../connections/opbeat'));
        }
    }

    addConnection(i) {
        this.connections.push(i);
        return i;
    }

    track(eventName, paramObj) {
        this.connections.forEach((conn) => {
            try {
                conn.track(eventName, paramObj)
            } catch(err) { console.error('External connection error: ' + err); }
        });
    }

    // track google analytics if is available
    ga () {
        if(this._ga !== undefined){
            try {
                this._ga.ga(...arguments)
            } catch(err) { console.error('Google analytics track error: ' + err); }
        }
    }

    // track opbeat
    opbeat () {
        if(this._opbeat !== undefined){
            try {
                this._opbeat.opbeat(...arguments)
            } catch(err) { console.error('Opbeat analytics track error: ' + err); }
        }
    }

}

module.exports = new ConnectionsService(); // singleton
