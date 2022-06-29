import { createAction } from '@reduxjs/toolkit';
import { TIME } from './constants';
import constructTopos from './topos';
import zonesConfig from '../../../config/zones.json';
import exchangesConfig from '../../../config/exchanges.json';

const GRID_DATA_FETCH_REQUESTED = createAction('data/grid-fetch-requested');
const GRID_DATA_FETCH_SUCCEEDED = createAction('data/grid-fetch-succeded');
const GRID_DATA_FETCH_FAILED = createAction('data/grid-fetch-failed');

const ZONE_HISTORY_FETCH_REQUESTED = createAction('data/zones-fetch-requested');
const ZONE_HISTORY_FETCH_SUCCEEDED = createAction('data/zones-fetch-succeded');
const ZONE_HISTORY_FETCH_FAILED = createAction('data/zones-fetch-failed');

const WIND_DATA_FETCH_FAILED = createAction('weather/wind-fetch-failed');
const WIND_DATA_FETCH_SUCCEDED = createAction('weather/wind-fetch-succeded');
const WIND_DATA_FETCH_REQUESTED = createAction('weather/wind-fetch-requested');

const SOLAR_DATA_FETCH_FAILED = createAction('weather/solar-fetch-failed');
const SOLAR_DATA_FETCH_SUCCEDED = createAction('weather/solar-fetch-succeded');
const SOLAR_DATA_FETCH_REQUESTED = createAction('weather/solar-fetch-requested');

const GRID_STATUS = {
  INVALID: 'invalid',
  EXPIRED: 'expired',
  LOADING: 'loading',
  READY: 'ready',
  DEFAULT: 'default',
};

const ZONE_STATUS = {
  EXPIRED: 'expired',
  READY: 'ready',
  INVALID: 'invalid',
  LOADING: 'loading',
};

function initDataState() {
  const geographies = constructTopos();
  const zones = {};

  Object.keys(zonesConfig).forEach((key) => {
    const zone = {};
    const zoneConfig = zonesConfig[key];
    if (!geographies[key]) {
      return;
    }
    zone.geography = geographies[key];
    zone.config = {};
    Object.keys(TIME).forEach((agg) => {
      zone[TIME[agg]] = { details: [], overviews: [], dataStatus: ZONE_STATUS.INVALID };
    });

    zone.config.capacity = zoneConfig.capacity;
    zone.config.contributors = zoneConfig.contributors;
    zone.config.timezone = zoneConfig.timezone;
    // hasParser is true if parser exists, or if estimation method exists
    zone.config.hasParser = zoneConfig.parsers?.production !== undefined || zoneConfig.estimation_method !== undefined;
    zone.config.delays = zoneConfig.delays;
    zone.config.disclaimer = zoneConfig.disclaimer;
    zone.config.countryCode = key;

    zones[key] = zone;
  });

  const gridStatus = {};
  Object.keys(TIME).forEach((agg) => {
    gridStatus[TIME[agg]] = GRID_STATUS.DEFAULT;
  });
  const exchanges = Object.assign({}, exchangesConfig);
  Object.entries(exchanges).forEach((entry) => {
    const [key, value] = entry;
    value.countryCodes = key.split('->').sort();
    if (key.split('->')[0] !== value.countryCodes[0]) {
      console.warn(`Exchange sorted key pair ${key} is not sorted alphabetically`);
    }
  });

  return {
    hasConnectionWarning: false,
    isLoadingHistories: false,
    isLoadingSolar: false,
    isLoadingWind: false,
    solar: null,
    wind: null,
    solarDataError: null,
    windDataError: null,
    zoneDatetimes: {},
    gridStatus,
    zones,
    exchanges,
  };
}

function combineZoneData(zoneData, aggregate) {
  // Combines details and overviews and other relevant keys
  // from zoneData for a specific aggregate into a single object
  const { overviews, details, hasData } = zoneData[aggregate];
  const { hasParser } = zoneData.config;
  const { center } = zoneData.geography.properties;

  if (!overviews.length) {
    // if there is no data available return one entry with static data
    return [{ hasData, hasParser, center }];
  }

  const combined = overviews.map((overview, idx) => {
    return { ...overview, ...details[idx], hasParser, hasData, center };
  });

  return combined;
}

function removeDuplicateSources(source) {
  if (!source) {
    return null;
  }
  const sources = [
    ...new Set(
      source
        .split('","')
        .map((x) => x.split(',').map((x) => x.replace('\\', '').replace('"', '')))
        .flat()
    ),
  ].join();

  return sources;
}

export {
  GRID_DATA_FETCH_FAILED,
  GRID_DATA_FETCH_SUCCEEDED,
  GRID_DATA_FETCH_REQUESTED,
  ZONE_HISTORY_FETCH_FAILED,
  ZONE_HISTORY_FETCH_SUCCEEDED,
  ZONE_HISTORY_FETCH_REQUESTED,
  SOLAR_DATA_FETCH_FAILED,
  SOLAR_DATA_FETCH_SUCCEDED,
  SOLAR_DATA_FETCH_REQUESTED,
  WIND_DATA_FETCH_FAILED,
  WIND_DATA_FETCH_SUCCEDED,
  WIND_DATA_FETCH_REQUESTED,
  GRID_STATUS,
  ZONE_STATUS,
  initDataState,
  combineZoneData,
  removeDuplicateSources,
};
