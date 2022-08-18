import { createAction } from '@reduxjs/toolkit';
import { TIME } from './constants';
import constructTopos from './topos';
// @ts-expect-error TS(2732): Cannot find module '../../../config/zones.json'. C... Remove this comment to see the full error message
import zonesConfig from '../../../config/zones.json';
// @ts-expect-error TS(2732): Cannot find module '../../../config/exchanges.json... Remove this comment to see the full error message
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

function initDataState() {
  const geographies = constructTopos();
  const zones = {};

  Object.keys(zonesConfig).forEach((key) => {
    const zone = {};
    const zoneConfig = zonesConfig[key];
    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    if (!geographies[key]) {
      return;
    }
    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    (zone as any).geography = geographies[key];
    (zone as any).config = {};
    Object.keys(TIME).forEach((agg) => {
      // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      zone[TIME[agg]] = { details: [], overviews: [], isExpired: true };
    });

    (zone as any).config.capacity = zoneConfig.capacity;
    (zone as any).config.contributors = zoneConfig.contributors;
    (zone as any).config.timezone = zoneConfig.timezone;
    // hasParser is true if parser exists, or if estimation method exists
    (zone as any).config.hasParser =
      zoneConfig.parsers?.production !== undefined || zoneConfig.estimation_method !== undefined;
    (zone as any).config.delays = zoneConfig.delays;
    (zone as any).config.disclaimer = zoneConfig.disclaimer;
    (zone as any).config.countryCode = key;

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
    return { ...overview, ...details[idx], hasParser, hasData, center };
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
