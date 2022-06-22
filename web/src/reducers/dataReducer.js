import * as translation from '../helpers/translation';
import { createReducer } from '@reduxjs/toolkit';
import {
  GRID_DATA_FETCH_FAILED,
  GRID_DATA_FETCH_REQUESTED,
  GRID_DATA_FETCH_SUCCEEDED,
  initDataState,
  SOLAR_DATA_FETCH_FAILED,
  SOLAR_DATA_FETCH_REQUESTED,
  SOLAR_DATA_FETCH_SUCCEDED,
  WIND_DATA_FETCH_FAILED,
  WIND_DATA_FETCH_REQUESTED,
  WIND_DATA_FETCH_SUCCEDED,
  ZONE_HISTORY_FETCH_FAILED,
  ZONE_HISTORY_FETCH_REQUESTED,
  ZONE_HISTORY_FETCH_SUCCEEDED,
} from '../helpers/redux';

const initialState = initDataState();

const reducer = createReducer(initialState, (builder) => {
  builder
    .addCase(GRID_DATA_FETCH_SUCCEEDED, (state, action) => {
      const { countries, datetimes, exchanges, stateAggregation } = action.payload;
      Object.entries(countries).map(([zoneId, zoneData]) => {
        if (!state.zones[zoneId]) {
          return;
        }
        state.zones[zoneId][stateAggregation].overviews = zoneData;
      });
      Object.keys(state.exchanges).forEach((key) => {
        state.exchanges[key].netFlow = undefined;
      });
      Object.entries(exchanges).forEach((entry) => {
        const [key, value] = entry;
        const exchange = state.exchanges[key];
        if (!exchange || !exchange.lonlat) {
          console.warn(`Missing exchange configuration for ${key}. Ignoring..`);
          return;
        }
        // Assign all data
        Object.keys(value).forEach((k) => {
          exchange[k] = value[k];
        });
      });

      state.zoneDatetimes = { ...state.zoneDatetimes, [stateAggregation]: datetimes.map((dt) => new Date(dt)) };
      state.isLoadingGrid = false;
      state.hasInitializedGrid = true;
    })
    .addCase(GRID_DATA_FETCH_REQUESTED, (state) => {
      state.isLoadingGrid = true;
      state.hasConnectionWarning = false;
    })
    .addCase(GRID_DATA_FETCH_FAILED, (state) => {
      state.hasConnectionWarning = true;
      state.isLoadingGrid = false;
    })
    .addCase(ZONE_HISTORY_FETCH_SUCCEEDED, (state, action) => {
      const { stateAggregation, zoneStates, zoneId } = action.payload;
      state.isLoadingHistories = false;
      state.zones[zoneId][stateAggregation] = {
        ...state.zones[zoneId][stateAggregation],
        details: zoneStates,
        hasDetailedData: true,
        hasData: Object.values(zoneStates).some((v) => v.co2intensity !== null),
      };
    })
    .addCase(ZONE_HISTORY_FETCH_FAILED, (state) => {
      state.isLoadingHistories = false;
    })
    .addCase(ZONE_HISTORY_FETCH_REQUESTED, (state) => {
      state.isLoadingHistories = true;
    })
    .addCase(SOLAR_DATA_FETCH_SUCCEDED, (state, action) => {
      state.isLoadingSolar = false;
      state.solar = action.payload;
    })
    .addCase(SOLAR_DATA_FETCH_REQUESTED, (state) => {
      state.isLoadingSolar = true;
      state.solarDataError = null;
    })
    .addCase(SOLAR_DATA_FETCH_FAILED, (state) => {
      state.isLoadingSolar = false;
      state.solar = null;
      state.solarDataError = translation.translate('solarDataError');
    })
    .addCase(WIND_DATA_FETCH_SUCCEDED, (state, action) => {
      state.isLoadingWind = false;
      state.wind = action.payload;
    })
    .addCase(WIND_DATA_FETCH_REQUESTED, (state) => {
      state.isLoadingWind = true;
      state.windDataError = null;
    })
    .addCase(WIND_DATA_FETCH_FAILED, (state) => {
      state.isLoadingWind = false;
      state.wind = null;
      state.windDataError = translation.translate('windDataError');
    });
});

export default reducer;
