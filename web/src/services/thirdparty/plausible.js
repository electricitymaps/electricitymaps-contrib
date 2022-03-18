class PlausibleThirdParty {
    constructor() {
        window.plausible = window.plausible 
        || function() { (window.plausible.q = window.plausible.q || []).push(arguments)}
    }

    track(event, data) {
        // Filter invalid and unimportant data (eg. null | undefined)
        const toRemove = ['mapViewport']; // Plausible only accepts scalar values
        const props = Object.keys(data)
        .filter(key => !toRemove.includes(key) && data[key] !== undefined && data[key] !== null)
        .reduce((obj, key) => {
            return {
            ...obj,
            [key]: data[key]
            };
        }, {});
        
        window.plausible(event, {props})
    }
}

export default PlausibleThirdParty;