class FacebookThirdParty {
    constructor() {
        this.events = [];
        this.hasLoaded = false;

        window.fbAsyncInit = () => {
            FB.init({
                appId      : '1267173759989113',
                xfbml      : true,
                version    : 'v2.10'
            });

            FB.Event.subscribe('edge.create', function(e) {
                // This will happen when they like the page
                if (e == 'https://www.facebook.com/tmrowco') {
                    var thirdPartyService = require('../services/thirdparty');
                    thirdPartyService.track('like');
                    thirdPartyService.ga('event', 'facebook', {
                      category: 'social',
                      label: 'like',
                    });
                }
            })
            FB.Event.subscribe('edge.remove', function(e) {
                // This will happen when they unlike the page
                if (e == 'https://www.facebook.com/tmrowco') {
                    require('../services/thirdparty').track('unlike');
                    thirdPartyService.ga('event', 'facebook', {
                      category: 'social',
                      label: 'unlike',
                    });
                }
            })

            this.hasLoaded = true;

            this.events.forEach((eventPair) => {
                this.track(...eventPair);
            });
        };

        (function(d, s, id){
            var js, fjs = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) {return;}
            js = d.createElement(s); js.id = id;
            //js.src = "https://connect.facebook.net/" + FBLocale + "/sdk.js";
            // Do not translate facebook because we fixed the size of buttons
            // because of a cordova bug serving from file://
            js.src = "https://connect.facebook.net/en_US/sdk.js";
            fjs.parentNode.insertBefore(js, fjs);
        }(document, 'script', 'facebook-jssdk'));
    }

    track(event, data){
        if(!this.hasLoaded) { // still loading
            this.events.push([event, data]);
        } else {
            // Quick hack
           if (event === 'pageview') {
                window.FB.AppEvents.logPageView();
            } else {
                window.FB.AppEvents.logEvent(event, undefined, data);
            }
        }
    }
}

module.exports = new FacebookThirdParty();
