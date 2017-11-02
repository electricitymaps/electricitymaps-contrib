class TwitterThirdParty {
    constructor() {
        this.inst = (function (d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0],
                t = window.twttr || {};
            if (d.getElementById(id)) return t;
            js = d.createElement(s);
            js.id = id;
            js.src = "https://platform.twitter.com/widgets.js";
            fjs.parentNode.insertBefore(js, fjs);

            t._e = [];
            t.ready = function (f) {
                t._e.push(f);
            };

            return t;
        }(document, "script", "twitter-wjs"))

        this.inst.ready(function (e) {
            this.inst.events.bind('click', function (event) {
                // event.region is {tweet,follow}
                var thirdPartyService = require('../services/thirdparty');
                thirdPartyService.track(event.region);
                thirdPartyService.ga('send', 'social', 'twitter', event.region);
            })
        });
    }

    track(name, data) {} //no-op
}


module.exports = new TwitterThirdParty();