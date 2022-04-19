class PlausibleThirdParty {
    constructor() {
        window.plausible = window.plausible 
        || function() { (window.plausible.q = window.plausible.q || []).push(arguments)}
    }

    track(event, data) {
        console.log(event, data);
        // window.plausible(event, {props})
    }
}

export default PlausibleThirdParty;