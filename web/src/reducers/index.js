import { combineReducers } from 'redux';

import { getKey } from '../helpers/storage';

import dataReducer from './dataReducer';

const isProduction = () => window.location.href.includes('electricitymap');
const isLocalhost = () => !isProduction() && !window.location.href.includes('192.');

const cookieGetBool = (key, defaultValue) => {
  const val = getKey(key);
  if (val == null) {
    return defaultValue;
  }
  return val === 'true';
};

const initialApplicationState = {
  // Here we will store non-data specific state (to be sent in analytics and crash reporting)
  bundleHash: window.bundleHash,
  version: VERSION,
  callerLocation: null,
  callerZone: null,
  centeredZoneName: null,
  clientType: window.isCordova ? 'mobileapp' : 'web',
  co2ColorbarMarker: null,
  colorBlindModeEnabled: cookieGetBool('colorBlindModeEnabled', false),
  brightModeEnabled: cookieGetBool('brightModeEnabled', true),
  customDate: null,
  electricityMixMode: 'consumption',
  isCordova: window.isCordova,
  isEmbedded: window.top !== window.self,
  isLeftPanelCollapsed: false,
  isMobile:
  (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent),
  isProduction: isProduction(),
  isLocalhost: isLocalhost(),
  legendVisible: true,
  locale: window.locale,
  onboardingSeen: cookieGetBool('onboardingSeen', false),
  tooltipData: null,
  tooltipDisplayMode: null,
  tooltipPosition: { x: 0, y: 0 },
  searchQuery: null,
  selectedZoneName: null,
  selectedZoneTimeIndex: null,
  solarColorbarMarker: null,
  solarEnabled: cookieGetBool('solarEnabled', false),
  useRemoteEndpoint: false,
  windEnabled: cookieGetBool('windEnabled', false),

  // TODO(olc): refactor this state
  showPageState: 'map',
  pageToGoBackTo: null,
  // TODO(olc): move this to countryPanel once all React components have been made
  tableDisplayEmissions: false,
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
      if (key === 'showPageState'
          && state.showPageState !== 'country') {
        newState.pageToGoBackTo = state.showPageState;
      }

      if (key === 'electricityMixMode' && ['consumption', 'production'].indexOf(value) === -1) {
        throw Error(`Unknown electricityMixMode "${value}"`);
      }

      return newState;
    }

    case 'GRID_DATA': {
      const selectedZoneNameExists = Object.keys(action.payload.countries)
        .indexOf(state.selectedZoneName) !== -1;
      if (state.selectedZoneName != null && !selectedZoneNameExists) {
        // The selectedZoneName doesn't exist anymore, we need to reset it
        // TODO(olc): the page state should be inferred from selectedZoneName
        return Object.assign({}, state, {
          selectedZoneName: undefined,
          showPageState: state.pageToGoBackTo || 'map',
        });
      }
      return state;
    }

    case 'SHOW_TOOLTIP': {
      return Object.assign({}, state, {
        tooltipData: action.payload.data,
        tooltipDisplayMode: action.payload.displayMode,
        tooltipPosition: action.payload.position,
      });
    }

    case 'HIDE_TOOLTIP': {
      return Object.assign({}, state, {
        tooltipDisplayMode: null,
      });
    }

    case 'UPDATE_SELECTED_ZONE': {
      const { selectedZoneName } = action.payload;
      return Object.assign({}, state, {
        selectedZoneName,
        selectedZoneTimeIndex: null,
      });
    }

    case 'UPDATE_STATE_FROM_URL': {
      const { searchParams } = new URL(action.payload.url);
      return Object.assign({}, state, {
        customDate: searchParams.get('datetime'),
        selectedZoneName: searchParams.get('countryCode'),
        showPageState: searchParams.get('page'),
        solarEnabled: searchParams.get('solar') === 'true',
        useRemoteEndpoint: searchParams.get('remote') === 'true',
        windEnabled: searchParams.get('wind') === 'true',
      });
    }

    case 'UPDATE_SLIDER_SELECTED_ZONE_TIME': {
      const { selectedZoneTimeIndex } = action.payload;
      // Update the selection only if it has changed
      if (selectedZoneTimeIndex !== state.selectedZoneTimeIndex) {
        return Object.assign({}, state, { selectedZoneTimeIndex });
      }
      return state;
    }

    default:
      return state;
  }
};

export default combineReducers({
  application: applicationReducer,
  data: dataReducer,
});
