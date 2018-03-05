const Cookies = require('js-cookie');

const isLocalhost = window.location.href.indexOf('electricitymap') !== -1;

const initialState = {
  application: {
    // Here we will store non-data specific state (to be sent in analytics and crash reporting)
    bundleHash: window.bundleHash,
    clientType: window.isCordova ? 'mobileapp' : 'web',
    colorBlindModeEnabled: Cookies.get('colorBlindModeEnabled') === 'true' || false,
    customDate: null,
    isCordova: window.isCordova,
    isEmbedded: window.top !== window.self,
    isProduction: window.location.href.indexOf('electricitymap') !== -1,
    isLocalhost,
    locale: window.locale,
    selectedZoneName: null,
    selectedZoneTimeIndex: null,
    solarEnabled: Cookies.get('solarEnabled') === 'true' || false,
    useRemoteEndpoint: document.domain === '' || isLocalhost,
    windEnabled: Cookies.get('windEnabled') === 'true' || false,

    // TODO(olc): refactor this state
    showPageState: 'map',
    pageToGoBackTo: null,
  },
  data: {
    // Here we will store data items
    grid: null,
    solar: null,
    wind: null,
  },
};

module.exports = (state = initialState, action) => {
  switch (action.type) {
    case 'APPLICATION_STATE_UPDATE': {
      const { key, value } = action.payload;
      const newState = Object.assign({}, state);
      // Note Object.assign only does shallow copies!
      // We need to clone application also.
      newState.application = Object.assign({}, state.application);
      newState.application[key] = value;

      // Disabled for now (see TODO in main.js)
      // if (key === 'selectedZoneName') {
      //   newState.application.showPageState = value ? 'country' : 'map';
      // }
      if (key === 'showPageState' &&
          state.application.showPageState !== 'country') {
        newState.application.pageToGoBackTo = state.application.showPageState;
      }

      return newState;
    }
    case 'GRID_DATA': {
      return Object.assign({}, state, {
        data: Object.assign({}, state.data, {
          grid: action.payload,
        }),
      });
    }

    default:
      return state;
  }
};
