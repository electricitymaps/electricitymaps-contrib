class GoogleAnalyticsThirdParty {
    constructor() {
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('config', 'UA-79729918-1');
        // Remember to add
        // <script async src="https://www.googletagmanager.com/gtag/js?id=UA-79729918-1"></script>
        // in head
        this.inst = gtag;

        window.onerror = function(message, url, line, col, errObject) {
            gtag('event', 'exception', {
                description: errObject,
                fatal: true,  // set to true if the exception is fatal
            });
        };
    }

    track(event, data) {
        this.inst('event', event, data, { send_to: 'UA-79729918-1' });
    }

    config() {
        // Disabled for now as this creates a double tracking warning
        // in the chrome extension
        // this.inst('config', 'UA-79729918-1', ...arguments);
    }

    ga(){
        this.inst(...arguments);
    }
}

module.exports = new GoogleAnalyticsThirdParty();
