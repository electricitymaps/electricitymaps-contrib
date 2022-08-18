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
      // @ts-expect-error TS(2339): Property 'countries' does not exist on type 'undef... Remove this comment to see the full error message
      const { countries, datetimes, exchanges, stateAggregation } = action.payload;
      state.zoneDatetimes = { ...state.zoneDatetimes, [stateAggregation]: datetimes.map((dt: any) => new Date(dt)) };
      // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      const maxGridDatetime = state.zoneDatetimes[stateAggregation].at(-1);

      Object.entries(countries).map(([zoneId, zoneData]) => {
        // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        if (!state.zones[zoneId]) {
          return;
        }
        // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        state.zones[zoneId][stateAggregation].overviews = zoneData;
        const maxHistoryDatetime = new Date(
          // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
          Math.max(...state.zones[zoneId][stateAggregation].details.map((x: any) => x.stateDatetime))
        );

        if (maxGridDatetime > maxHistoryDatetime) {
          // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
          state.zones[zoneId][stateAggregation].isExpired = true;
        }
      });

      if (stateAggregation === TIME.HOURLY) {
        Object.entries(exchanges).forEach((entry: any) => {
          const [key, value] = entry;
          // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
          if (state.exchanges[key]) {
            // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
            state.exchanges[key].data = value;
          }
        });
      }

      state.zoneDatetimes = { ...state.zoneDatetimes, [stateAggregation]: datetimes.map((dt: any) => new Date(dt)) };
      state.isLoadingGrid = false;
      state.failedRequestType = null;
      state.hasInitializedGrid = true;
      // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      state.isGridExpired[stateAggregation] = false;
    })
    .addCase(GRID_DATA_FETCH_REQUESTED, (state) => {
      state.isLoadingGrid = true;
    })
    .addCase(GRID_DATA_FETCH_FAILED, (state) => {
      // @ts-expect-error TS(2322): Type 'string' is not assignable to type 'null'.
      state.failedRequestType = failedRequestType.GRID;
      state.isLoadingGrid = false;
    })
    .addCase(ZONE_HISTORY_FETCH_SUCCEEDED, (state, action) => {
      // @ts-expect-error TS(2339): Property 'stateAggregation' does not exist on type... Remove this comment to see the full error message
      const { stateAggregation, zoneStates, zoneId, hasData } = action.payload;
      state.isLoadingHistories = false;
      state.failedRequestType = null;
      // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      state.zones[zoneId][stateAggregation] = {
        // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        ...state.zones[zoneId][stateAggregation],
        // TODO: Fix sources in DBT instead of here
        details: zoneStates.map((v: any) => ({
          ...v,
          source: removeDuplicateSources(v.source),
          stateDatetime: new Date(v.stateDatetime),
        })),
        isExpired: false,
        hasData,
      };

      // Check if any of the zoneStates contains a datetime greater than the most recent gridDatetime. If so, expire the grid.
      // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      if (!state.zoneDatetimes[stateAggregation]) {
        return;
      }
      // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      const maxGridDatetime = state.zoneDatetimes[stateAggregation].at(-1);
      zoneStates.forEach((zoneState: any) => {
        if (new Date(zoneState.stateDatetime) > maxGridDatetime) {
          // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
          state.isGridExpired[stateAggregation] = true;
        }
      });
    })
    .addCase(ZONE_HISTORY_FETCH_FAILED, (state) => {
      // @ts-expect-error TS(2322): Type 'string' is not assignable to type 'null'.
      state.failedRequestType = failedRequestType.ZONE;
      state.isLoadingHistories = false;
    })
    .addCase(ZONE_HISTORY_FETCH_REQUESTED, (state) => {
      state.isLoadingHistories = true;
    })
    .addCase(SOLAR_DATA_FETCH_SUCCEDED, (state, action) => {
      state.isLoadingSolar = false;
      // @ts-expect-error TS(2322): Type 'undefined' is not assignable to type 'null'.
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
      // @ts-expect-error TS(2322): Type 'undefined' is not assignable to type 'null'.
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
