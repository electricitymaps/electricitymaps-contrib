import * as translation from '../helpers/translation';
import { createReducer } from '@reduxjs/toolkit';
import {
  GRID_DATA_FETCH_FAILED,
  GRID_DATA_FETCH_REQUESTED,
  GRID_DATA_FETCH_SUCCEEDED,
  GRID_STATUS,
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
  ZONE_STATUS,
} from '../helpers/redux';
import { TIME } from '../helpers/constants';

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
        // if maxGridDatetime greater than maxDetailsDatetime
        const maxDetailsDatetime = new Date(
          Math.max(...state.zones[zoneId][stateAggregation].details.map((x) => x.stateDatetime))
        );

        if (maxGridDatetime > maxDetailsDatetime) {
          state.zones[zoneId][stateAggregation].dataStatus = ZONE_STATUS.EXPIRED;
        }
      });

      if (stateAggregation === TIME.HOURLY) {
        Object.keys(state.exchanges).forEach((key) => {
          state.exchanges[key].netFlow = undefined;
        });
        Object.entries(exchanges).forEach((entry) => {
          const [key, value] = entry;
          const exchange = state.exchanges[key];
          if (!exchange || !exchange.lonlat) {
            return;
          }
          // Assign all data
          Object.keys(value).forEach((k) => {
            exchange[k] = value[k];
          });
        });
      }

      state.hasInitializedGrid = true;

      // Expire any outdated zone histories
      state.gridStatus[stateAggregation] = GRID_STATUS.READY;
    })
    .addCase(GRID_DATA_FETCH_REQUESTED, (state, action) => {
      const { selectedTimeAggregate: stateAggregation } = action.payload;
      state.hasConnectionWarning = false;
      state.gridStatus[stateAggregation] = GRID_STATUS.LOADING;
    })
    .addCase(GRID_DATA_FETCH_FAILED, (state, action) => {
      const { selectedTimeAggregate: stateAggregation } = action.payload;
      state.hasConnectionWarning = true;
      state.gridStatus[stateAggregation] = GRID_STATUS.INVALID;
    })
    .addCase(ZONE_HISTORY_FETCH_SUCCEEDED, (state, action) => {
      const { stateAggregation, zoneStates, zoneId, hasData } = action.payload;
      state.isLoadingHistories = false;
      state.zones[zoneId][stateAggregation] = {
        ...state.zones[zoneId][stateAggregation],
        // TODO: Fix sources in DBT instead of here
        details: zoneStates.map((v) => ({
          ...v,
          source: removeDuplicateSources(v.source),
          stateDatetime: new Date(v.stateDatetime),
        })),
        dataStatus: hasData ? ZONE_STATUS.READY : ZONE_STATUS.INVALID,
        hasDetailedData: true,
        hasData,
      };

      // Check if any of the zoneStates contains a datetime greater than the most recent gridDatetime. If so, expire the grid.
      if (!state.zoneDatetimes[stateAggregation]) {
        return;
      }
      const maxGridDatetime = state.zoneDatetimes[stateAggregation].at(-1);
      zoneStates.forEach((zoneState) => {
        if (new Date(zoneState.stateDatetime) > maxGridDatetime) {
          state.gridStatus[stateAggregation] = GRID_STATUS.EXPIRED;
        }
      });
    })
    .addCase(ZONE_HISTORY_FETCH_FAILED, (state, action) => {
      const { zoneId, selectedTimeAggregate } = action.payload;
      state.zones[zoneId][selectedTimeAggregate].dataStatus = ZONE_STATUS.INVALID;
    })
    .addCase(ZONE_HISTORY_FETCH_REQUESTED, (state, action) => {
      const { zoneId, selectedTimeAggregate } = action.payload;
      state.zones[zoneId][selectedTimeAggregate].dataStatus = ZONE_STATUS.LOADING;
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
