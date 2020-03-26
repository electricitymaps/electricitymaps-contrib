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
  co2ColorbarValue: null,
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
  solarColorbarValue: null,
  solarEnabled: cookieGetBool('solarEnabled', false),
  useRemoteEndpoint: false,
  windColorbarMarker: null,
  windEnabled: cookieGetBool('windEnabled', false),

  // TODO(olc): refactor this state
  currentPage: null,
  // TODO(olc): move this to countryPanel once all React components have been made
  tableDisplayEmissions: false,
};

const applicationReducer = (state = initialApplicationState, action) => {
  switch (action.type) {
    case 'APPLICATION_STATE_UPDATE': {
      const { key, value } = action;
      const newState = Object.assign({}, state);
      newState[key] = value;

      if (key === 'electricityMixMode' && ['consumption', 'production'].indexOf(value) === -1) {
        throw Error(`Unknown electricityMixMode "${value}"`);
      }

      return newState;
    }

    case 'GRID_DATA': {
      const selectedZoneNameExists = Object.keys(action.payload.countries)
        .indexOf(state.selectedZoneName) !== -1;
      if (state.selectedZoneName && !selectedZoneNameExists) {
        // The selectedZoneName doesn't exist anymore, we need to reset it
        // TODO(olc): the page state should be inferred from selectedZoneName
        return Object.assign({}, state, {
          selectedZoneName: null,
          currentPage: null,
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

    case 'UPDATE_STATE_FROM_URL': {
      const { pathname, searchParams } = new URL(action.payload.url);
      const currentPageFallback = (searchParams.get('page') || '')
        .replace('country', 'zone')
        .replace('highscore', 'ranking');

      return Object.assign({}, state, {
        customDate: searchParams.get('datetime'),
        solarEnabled: searchParams.get('solar') === 'true',
        useRemoteEndpoint: searchParams.get('remote') === 'true',
        windEnabled: searchParams.get('wind') === 'true',
        // Prioritize route pathname but fall back to search params for backwards compatibility
        currentPage: pathname.split('/')[1] || currentPageFallback || 'map', // Default to map view if page was not specified
        selectedZoneName: pathname.split('/')[2] || searchParams.get('countryCode') || null,
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
