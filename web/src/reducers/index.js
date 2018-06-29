import { combineReducers } from 'redux';

const Cookies = require('js-cookie');
const dataReducer = require('./dataReducer');

const isLocalhost = window.location.href.indexOf('electricitymap') !== -1 ||
  window.location.href.indexOf('192.') !== -1;

const initialApplicationState = {
  // Here we will store non-data specific state (to be sent in analytics and crash reporting)
  bundleHash: window.bundleHash,
  callerLocation: null,
  clientType: window.isCordova ? 'mobileapp' : 'web',
  colorBlindModeEnabled: Cookies.get('colorBlindModeEnabled') === 'true' || false,
  brightModeEnabled: Cookies.get('brightModeEnabled') === 'true' || true,
  customDate: null,
  isCordova: window.isCordova,
  isEmbedded: window.top !== window.self,
  isLeftPanelCollapsed: false,
  isMobile:
  (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent),
  isProduction: window.location.href.indexOf('electricitymap') !== -1,
  isLocalhost,
  legendVisible: false,
  locale: window.locale,
  onboardingSeen: Cookies.get('onboardingSeen') === 'true' || false,
  tooltipDisplayMode: null,
  searchQuery: null,
  selectedZoneName: null,
  selectedZoneTimeIndex: null,
  previousSelectedZoneTimeIndex: null,
  solarEnabled: Cookies.get('solarEnabled') === 'true' || false,
  useRemoteEndpoint: document.domain === '' || isLocalhost,
  windEnabled: Cookies.get('windEnabled') === 'true' || false,

  // TODO(olc): refactor this state
  showPageState: 'map',
  pageToGoBackTo: null,
};

const applicationReducer = (state = initialApplicationState, action) => {
  switch (action.type) {
    case 'APPLICATION_STATE_UPDATE': {
      const { key, value } = action;
      const newState = Object.assign({}, state);
      newState[key] = value;

      // Disabled for now (see TODO in main.js)
      // if (key === 'selectedZoneName') {
      //   newState.showPageState = value ? 'country' : 'map';
      // }
      if (key === 'showPageState' &&
          state.showPageState !== 'country') {
        newState.pageToGoBackTo = state.showPageState;
      }

      return newState;
    }

    case 'GRID_DATA': {
      const selectedZoneNameExists =
        Object.keys(action.payload.countries).indexOf(state.selectedZoneName) !== -1;
      if (state.selectedZoneName != null && !selectedZoneNameExists) {
        // The selectedZoneName doesn't exist anymore, we need to reset it
        // TODO(olc): the page state should be inferred from selectedZoneName
        return Object.assign(state, {
          selectedZoneName: undefined,
          showPageState: state.pageToGoBackTo || 'map',
        });
      }
      return state;
    }

    case 'UPDATE_SELECTED_ZONE': {
      const { selectedZoneName } = action.payload;
      return Object.assign(state, {
        selectedZoneName,
        selectedZoneTimeIndex: null,
        previousSelectedZoneTimeIndex: null,
      });
    }

    case 'UPDATE_SLIDER_SELECTED_ZONE_TIME': {
      const { selectedZoneTimeIndex } = action.payload;
      return Object.assign(state, {
        selectedZoneTimeIndex,
        previousSelectedZoneTimeIndex: selectedZoneTimeIndex,
      });
    }

    default:
      return state;
  }
};

module.exports = combineReducers({
  application: applicationReducer,
  data: dataReducer,
});
