var initialState = {
    application: {
        isProduction: window.location.href.indexOf('electricitymap') !== -1
    }
}

module.exports = (state = initialState, action) => {
    switch (action.type) {
        case 'ZONE_DATA':
            return Object.assign({}, state, {
                countryData: action.payload,
                countryDataIndex: 0,
            })

        case 'SELECT_DATA':
            return Object.assign({}, state, {
                countryData: action.payload.countryData,
                countryDataIndex: action.payload.index,
            })

        default:
            return state
    }
};