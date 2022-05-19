import { combineReducers } from 'redux';

import { getKey } from '../helpers/storage';
import { isLocalhost, isProduction } from '../helpers/environment';

import dataReducer from './dataReducer';
import dataReducerForHistoryFeature from './dataReducerForHistoryFeature';

const getStorageBool = (key, defaultValue) => {
  const val = getKey(key);
  if (val == null) {
    return defaultValue;
  }
  return val === 'true';
};

const initialApplicationState = {
  // Here we will store non-data specific state (to be sent in analytics and crash reporting)
  bundleHash: window.bundleHash,
  callerLocation: null,
  clientType: window.isCordova ? 'mobileapp' : 'web',
  co2ColorbarValue: null,
  colorBlindModeEnabled: getStorageBool('colorBlindModeEnabled', false),
  brightModeEnabled: getStorageBool('brightModeEnabled', true),
  electricityMixMode: 'consumption',
  isCordova: window.isCordova,
  isEmbedded: window.top !== window.self,
  // We have to track this here because map layers currently can't
  // be stopped from propagating mouse move events to the map.
  // See https://github.com/visgl/react-map-gl/blob/master/docs/advanced/custom-components.md
  isHoveringExchange: false,
  isLeftPanelCollapsed: false,
  isMovingMap: false,
  isLoadingMap: true,
  isMobile: /android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i.test(navigator.userAgent),
  isProduction: isProduction(),
  isLocalhost: isLocalhost(),
  legendVisible: true,
  mapViewport: {
    width: window.innerWidth,
    height: window.innerHeight,
    latitude: 50,
    longitude: 0,
    zoom: 1.5,
  },
  onboardingSeen: getStorageBool('onboardingSeen', false),
  searchQuery: null,
  selectedZoneTimeIndex: null,
  solarColorbarValue: null,
  webGLSupported: true,
  windColorbarValue: null,
  selectedTimeAggregate: 'day',

  // TODO(olc): move this to countryPanel once all React components have been made
  tableDisplayEmissions: false,
};

const applicationReducer = (state = initialApplicationState, action) => {
  switch (action.type) {
    case 'APPLICATION_STATE_UPDATE': {
      const { key, value } = action;

      // Do nothing if the value is unchanged
      if (state[key] === value) {
        return state;
      }

      // Throw an error if electricity mode is of the wrong format
      if (key === 'electricityMixMode' && !['consumption', 'production'].includes(value)) {
        throw Error(`Unknown electricityMixMode "${value}"`);
      }

      return { ...state, [key]: value };
    }

    default:
      return state;
  }
};

const urlSearchParams = new URLSearchParams(window.location.search);
const isHistoryFeatureEnabled = Object.fromEntries(urlSearchParams.entries())?.feature === 'history';
const dataReducerInUse = isHistoryFeatureEnabled ? dataReducerForHistoryFeature : dataReducer;

export default combineReducers({
  application: applicationReducer,
  data: dataReducerInUse,
});
