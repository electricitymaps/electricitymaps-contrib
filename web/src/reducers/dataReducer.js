import * as translation from '../helpers/translation';
import { createReducer } from '@reduxjs/toolkit';
import {
  GRID_DATA_FETCH_FAILED,
  GRID_DATA_FETCH_REQUESTED,
  GRID_DATA_FETCH_SUCCEEDED,
  initDataState,
  removeDuplicateSources,
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
import { TIME, failedRequestType } from '../helpers/constants';

const initialState = initDataState();

const reducer = createReducer(initialState, (builder) => {
  builder
    .addCase(GRID_DATA_FETCH_SUCCEEDED, (state, action) => {
      const { countries, datetimes, exchanges, stateAggregation } = action.payload;
      state.zoneDatetimes = { ...state.zoneDatetimes, [stateAggregation]: datetimes.map((dt) => new Date(dt)) };
      const maxGridDatetime = state.zoneDatetimes[stateAggregation].at(-1);

      Object.entries(countries).map(([zoneId, zoneData]) => {
        if (!state.zones[zoneId]) {
          return;
        }
        state.zones[zoneId][stateAggregation].overviews = zoneData;
        const maxHistoryDatetime = new Date(
          Math.max(...state.zones[zoneId][stateAggregation].details.map((x) => x.stateDatetime))
        );

        if (maxGridDatetime > maxHistoryDatetime) {
          state.zones[zoneId][stateAggregation].isExpired = true;
        }
      });

      // Populate exchanges. Only available on hourly.
      if (stateAggregation === TIME.HOURLY) {
        Object.entries(exchanges).forEach((entry) => {
          const [key, value] = entry;
          if (state.exchanges[key]) {
            state.exchanges[key].data = value;
          }
        });
      }

      state.zoneDatetimes = { ...state.zoneDatetimes, [stateAggregation]: datetimes.map((dt) => new Date(dt)) };
      state.isLoadingGrid = false;
      state.failedRequestType = null;
      state.hasInitializedGrid = true;
      state.isGridExpired[stateAggregation] = false;
    })
    .addCase(GRID_DATA_FETCH_REQUESTED, (state) => {
      state.isLoadingGrid = true;
    })
    .addCase(GRID_DATA_FETCH_FAILED, (state) => {
      state.failedRequestType = failedRequestType.GRID;
      state.isLoadingGrid = false;
    })
    .addCase(ZONE_HISTORY_FETCH_SUCCEEDED, (state, action) => {
      const { stateAggregation, zoneStates, zoneId, hasData } = action.payload;
      state.isLoadingHistories = false;
      state.failedRequestType = null;
      state.zones[zoneId][stateAggregation] = {
        ...state.zones[zoneId][stateAggregation],
        // TODO: Fix sources in DBT instead of here
        details: zoneStates.map((v) => ({
          ...v,
          source: removeDuplicateSources(v.source),
          stateDatetime: new Date(v.stateDatetime),
        })),
        isExpired: false,
        hasData,
      };

      // Check if any of the zoneStates contains a datetime greater than the most recent gridDatetime. If so, expire the grid.
      if (!state.zoneDatetimes[stateAggregation]) {
        return;
      }
      const maxGridDatetime = state.zoneDatetimes[stateAggregation].at(-1);
      zoneStates.forEach((zoneState) => {
        if (new Date(zoneState.stateDatetime) > maxGridDatetime) {
          state.isGridExpired[stateAggregation] = true;
        }
      });
    })
    .addCase(ZONE_HISTORY_FETCH_FAILED, (state) => {
      state.failedRequestType = failedRequestType.ZONE;
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
