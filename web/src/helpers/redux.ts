import { createAction } from '@reduxjs/toolkit';
import { TIME } from './constants';
import constructTopos from './topos';
import zonesConfig from '../../../config/zones.json';
import exchangesConfig from '../../../config/exchanges.json';

interface ExchangeConfigTypes {
  lonlat: [number, number];
  parsers: {
    exchange: string;
  };
  rotation: number;
}

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

export interface Zone {
  type?: string;
  config?: any;
  features?: {
    type: string;
    geometry: any;
    properties: {
      color: undefined;
      zoneData: any;
      zoneId: string;
    };
  };
}

export interface Zones {
  type?: string;
  name?: string;
  crs?: { type: string; properties: { name: string } };
  features?: [Zone];
}

interface ZoneConfig {
  bounding_box?: [[number, number], [number, number]];
  capacity?: {
    hydro?: number;
    nuclear?: number;
  };
  contributors?: [string];
  timezone?: any;
}
interface ZonesConfig {
  [key: string]: ZoneConfig;
}

function initDataState() {
  const geographies = constructTopos();
  const zones: Zones = {};

  Object.keys(zonesConfig).forEach((key) => {
    const zone: Zone = {};
    //@ts-ignore
    const zoneConfig = zonesConfig[key];
    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    if (!geographies[key]) {
      return;
    }
    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    zone.geography = geographies[key];
    zone.config = {};
    Object.keys(TIME).forEach((agg) => {
      // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      zone[TIME[agg]] = { details: [], overviews: [], isExpired: true };
    });

    zone.config.capacity = zoneConfig.capacity;
    zone.config.contributors = zoneConfig.contributors;
    zone.config.timezone = zoneConfig.timezone;
    // hasParser is true if parser exists, or if estimation method exists
    zone.config.hasParser = zoneConfig.parsers?.production !== undefined || zoneConfig.estimation_method !== undefined;
    zone.config.delays = zoneConfig.delays;
    zone.config.disclaimer = zoneConfig.disclaimer;
    zone.config.countryCode = key;

    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    zones[key] = zone;
  });

  const isGridExpired = {};
  Object.keys(TIME).forEach((agg) => {
    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    isGridExpired[TIME[agg]] = true;
  });

  const exchanges = {};

  Object.entries(exchangesConfig).forEach(([key, value]) => {
    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    exchanges[key] = {
      config: { ...(value as ExchangeConfigTypes), sortedCountryCodes: key.split('->').sort() },
      data: [],
    };
  });

  return {
    failedRequestType: null,
    hasInitializedGrid: false,
    isLoadingHistories: false,
    isLoadingGrid: false,
    isGridExpired,
    isLoadingSolar: false,
    isLoadingWind: false,
    solar: null,
    wind: null,
    solarDataError: null,
    windDataError: null,
    zoneDatetimes: {},
    zones,
    exchanges,
  };
}

function combineZoneData(zoneData: any, aggregate: any) {
  // Combines details and overviews and other relevant keys
  // from zoneData for a specific aggregate into a single object
  const { overviews, details, hasData } = zoneData[aggregate];
  const { hasParser } = zoneData.config;
  const { center } = zoneData.geography.properties;

  if (!overviews.length) {
    // if there is no data available return one entry with static data
    return [{ hasData, hasParser, center }];
  }

  const combined = overviews.map((overview: any, idx: any) => {
    return { ...overview, ...details[idx], hasParser, center };
  });

  return combined;
}

function removeDuplicateSources(source: any) {
  if (!source) {
    return null;
  }
  const sources = [
    ...new Set(
      source
        .split('","')
        .map((x: any) => x.split(',').map((x: any) => x.replace('\\', '').replace('"', '')))
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
  initDataState,
  combineZoneData,
  removeDuplicateSources,
};
