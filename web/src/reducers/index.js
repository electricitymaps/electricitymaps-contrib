import { combineReducers } from 'redux';

import { getKey } from '../helpers/storage';
import { isLocalhost, isProduction } from '../helpers/environment';

import dataReducer from './dataReducer';

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
  clientType: window.isCordova ? 'mobileapp' : 'web',
  co2ColorbarValue: null,
  colorBlindModeEnabled: cookieGetBool('colorBlindModeEnabled', false),
  brightModeEnabled: cookieGetBool('brightModeEnabled', true),
  customDatetime: null,
  electricityMixMode: 'consumption',
  isCordova: window.isCordova,
  isEmbedded: window.top !== window.self,
  isLeftPanelCollapsed: false,
  isLoadingMap: true,
  isMobile:
  (/android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i).test(navigator.userAgent),
  isProduction: isProduction(),
  isLocalhost: isLocalhost(),
  legendVisible: true,
  locale: window.locale,
  mapViewport: {
    latitude: 50,
    longitude: 0,
    zoom: 1.5,
  },
  onboardingSeen: cookieGetBool('onboardingSeen', false),
  tooltipData: null,
  tooltipDisplayMode: null,
  tooltipPosition: { x: 0, y: 0 },
  searchQuery: null,
  selectedZoneName: null,
  selectedZoneTimeIndex: null,
  solarColorbarValue: null,
  solarEnabled: false,
  webGLSupported: false,
  windColorbarMarker: null,
  windEnabled: false,

  // TODO(olc): refactor this state
  currentPage: null,
  // TODO(olc): move this to countryPanel once all React components have been made
  tableDisplayEmissions: false,
};

const applicationReducer = (state = initialApplicationState, action) => {
  switch (action.type) {
    case 'APPLICATION_STATE_UPDATE': {
      const { key, value } = action;
      if (state[key] === value) {
        return state;
      }

      const newState = Object.assign({}, state);
      newState[key] = value;

      if (key === 'electricityMixMode' && ['consumption', 'production'].indexOf(value) === -1) {
        throw Error(`Unknown electricityMixMode "${value}"`);
      }

      return newState;
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

    case 'UPDATE_STATE_FROM_URL': {
      return Object.assign({}, state, action.payload);
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
