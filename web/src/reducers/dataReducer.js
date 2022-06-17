import constructTopos from '../helpers/topos';
import * as translation from '../helpers/translation';

import exchangesConfig from '../../../config/exchanges.json';
import zonesConfig from '../../../config/zones.json';
import { TIME } from '../helpers/constants';

// ** Prepare initial zone data
const zones = constructTopos();
Object.entries(zonesConfig).forEach((d) => {
  const [key, zoneConfig] = d;
  const zone = zones[key];
  if (!zone) {
    console.warn(`Zone ${key} from configuration is not found. Ignoring..`);
    return;
  }
  // copy attributes ("capacity", "contributors"...)
  zone.capacity = zoneConfig.capacity;
  zone.contributors = zoneConfig.contributors;
  zone.timezone = zoneConfig.timezone;
  zone.hasParser = (zoneConfig.parsers || {}).production !== undefined;
  zone.hasData = zone.hasParser;
  zone.delays = zoneConfig.delays;
  zone.disclaimer = zoneConfig.disclaimer;
});
// Add id to each zone
Object.keys(zones).forEach((k) => {
  zones[k].countryCode = k;
});

// ** Prepare initial exchange data
const exchanges = Object.assign({}, exchangesConfig);
Object.entries(exchanges).forEach((entry) => {
  const [key, value] = entry;
  value.countryCodes = key.split('->').sort();
  if (key.split('->')[0] !== value.countryCodes[0]) {
    console.warn(`Exchange sorted key pair ${key} is not sorted alphabetically`);
  }
});

function constructInitialState() {
  const geographies = constructTopos();
  const result = {};

  Object.keys(zonesConfig).forEach((key) => {
    const zone = {};
    const zoneConfig = zonesConfig[key];
    if (!geographies[key]) {
      return;
    }
    zone.geography = geographies[key];
    zone.config = {};
    Object.keys(TIME).forEach((k) => {
      zone[TIME[k]] = { details: [], overviews: [] };
    });

    zone.config.capacity = zoneConfig.capacity;
    zone.config.contributors = zoneConfig.contributors;
    zone.config.timezone = zoneConfig.timezone;
    zone.config.hasParser = (zoneConfig.parsers || {}).production !== undefined;
    zone.config.hasData = zone.config.hasParser;
    zone.config.delays = zoneConfig.delays;
    zone.config.disclaimer = zoneConfig.disclaimer;

    result[key] = zone;
  });
  return result;
}

const initialDataState = {
  // Here we will store data items
  hasConnectionWarning: false,
  hasInitializedGrid: false,
  histories: {},
  isLoadingHistories: false,
  isLoadingGrid: false,
  isLoadingSolar: false,
  isLoadingWind: false,
  solar: null,
  wind: null,
  solarDataError: null,
  windDataError: null,
  zoneDatetimes: [],
  zones: constructInitialState(),
  exchanges,
};

const reducer = (state = initialDataState, action) => {
  switch (action.type) {
    case 'GRID_DATA_FETCH_REQUESTED': {
      return { ...state, hasConnectionWarning: false, isLoadingGrid: true };
    }

    case 'GRID_DATA_FETCH_SUCCEEDED': {
      const newState = Object.assign({}, state);
      const newExchanges = { ...state.exchanges };
      const newZones = { ...state.zones };
      const { stateAggregation } = action.payload;

      Object.keys(newExchanges).forEach((key) => {
        newExchanges[key].netFlow = undefined;
      });

      Object.entries(action.payload.countries).map(([zoneId, zoneData]) => {
        if (!newZones[zoneId]) {
          return;
        }
        newZones[zoneId][stateAggregation].overviews = zoneData;
      });

      newState.exchanges = newExchanges;
      newState.zones = newZones;
      newState.zoneDatetimes[stateAggregation] = action.payload.datetimes.map((dt) => new Date(dt));

      Object.entries(action.payload.exchanges).forEach((entry) => {
        const [key, value] = entry;
        const exchange = newExchanges[key];
        if (!exchange || !exchange.lonlat) {
          console.warn(`Missing exchange configuration for ${key}. Ignoring..`);
          return;
        }
        // Assign all data
        Object.keys(value).forEach((k) => {
          newExchanges[k] = value[k];
        });
      });

      newState.hasInitializedGrid = true;
      newState.isLoadingGrid = false;
      newState.zones = newZones;
      newState.exchanges = newExchanges;
      return newState;
    }

    case 'GRID_DATA_FETCH_FAILED': {
      // TODO: Implement error handling
      return { ...state, hasConnectionWarning: true, isLoadingGrid: false };
    }

    case 'ZONE_HISTORY_FETCH_REQUESTED': {
      return { ...state, isLoadingHistories: true };
    }

    case 'ZONE_HISTORY_FETCH_SUCCEEDED': {
      return {
        ...state,
        isLoadingHistories: false,
        zones: {
          ...state.zones,
          [action.zoneId]: {
            ...state.zones[action.zoneId],
            [action.payload.stateAggregation]: {
              ...state.zones[action.zoneId][action.payload.stateAggregation],
              details: action.payload.zoneStates,
              hasDetailedData: true,
              hasData: true, // TODO: fix
              hasParser: true,
              aggregation: action.payload.stateAggregation,
            },
          },
        },
      };
    }

    case 'ZONE_HISTORY_FETCH_FAILED': {
      // TODO: Implement error handling
      return { ...state, isLoadingHistories: false };
    }

    case 'SOLAR_DATA_FETCH_REQUESTED': {
      return { ...state, isLoadingSolar: true, solarDataError: null };
    }

    case 'SOLAR_DATA_FETCH_SUCCEEDED': {
      return { ...state, isLoadingSolar: false, solar: action.payload };
    }

    case 'SOLAR_DATA_FETCH_FAILED': {
      // TODO: create specialized messages based on http error response
      return { ...state, isLoadingSolar: false, solar: null, solarDataError: translation.translate('solarDataError') };
    }

    case 'WIND_DATA_FETCH_REQUESTED': {
      return { ...state, isLoadingWind: true, windDataError: null };
    }

    case 'WIND_DATA_FETCH_SUCCEEDED': {
      return { ...state, isLoadingWind: false, wind: action.payload };
    }

    case 'WIND_DATA_FETCH_FAILED': {
      // TODO: create specialized messages based on http error response
      return { ...state, isLoadingWind: false, wind: null, windDataError: translation.translate('windDataError') };
    }

    default:
      return state;
  }
};

export default reducer;
