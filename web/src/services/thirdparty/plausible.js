class PlausibleThirdParty {
    constructor() {
        window.plausible = window.plausible 
        || function() { (window.plausible.q = window.plausible.q || []).push(arguments)}
    }

    track(event, props) {
        console.log("pls ", event);
        window.plausible(event, {props})
    }
}

export default PlausibleThirdParty;