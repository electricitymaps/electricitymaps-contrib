/**
 * @jest-environment jsdom
 */
import {
  GRID_DATA_FETCH_FAILED,
  GRID_DATA_FETCH_REQUESTED,
  GRID_DATA_FETCH_SUCCEEDED,
  GRID_STATUS,
  ZONE_HISTORY_FETCH_SUCCEEDED,
  ZONE_STATUS,
} from '../helpers/redux';
import reducer from './dataReducer';
import hourlyHistoryData from '../../../mockserver/public/v5/history/DK-DK2/hourly.json';
import historyData from '../../../mockserver/public/v5/history/DK-DK2/daily.json';
import gridData from '../../../mockserver/public/v5/state/hourly.json';

test('zones should have initial state with correct structure', () => {
  const state = reducer.getInitialState();

  const expectedZones = {
    'DK-DK2': {
      hourly: expect.any(Object),
      daily: expect.any(Object),
      monthly: expect.any(Object),
      yearly: expect.any(Object),
      geography: expect.any(Object),
      config: {
        hasParser: true,
        capacity: {
          nuclear: 0,
        },
        contributors: expect.arrayContaining(['corradio']),
        timezone: 'Europe/Copenhagen',
      },
    },
  };

  expect(state.zones).toMatchObject(expectedZones);
});

test('grid fetch updates correctly', () => {
  const payload = gridData.data;
  const action = GRID_DATA_FETCH_SUCCEEDED(payload);
  const state = reducer(undefined, action);

  const expectedHourly = {
    co2intensity: expect.any(Number),
    countryCode: expect.stringContaining('DK-DK2'),
  };

  expect(state.zones['DK-DK2'].hourly.overviews[0]).toMatchObject(expectedHourly);
  expect(state.zones['DK-DK2'].hourly.overviews).toHaveLength(25);
  expect(state.zones['DK-DK2'].daily.overviews).toHaveLength(0);
});

test('history contains required properties', () => {
  const payload = { ...historyData.data, zoneId: 'DK-DK2' };
  const action = ZONE_HISTORY_FETCH_SUCCEEDED(payload);
  const state = reducer(undefined, action);

  expect(state.zones['DK-DK2'].daily.details[0]).toHaveProperty('totalCo2Production');
});

test('Grid status is updated', () => {
  // Ensures gridStatus is updated accordingly

  const defaultState = reducer.getInitialState();
  expect(defaultState.gridStatus.hourly).toEqual(GRID_STATUS.INVALID);

  const loadingState = reducer(undefined, GRID_DATA_FETCH_REQUESTED({ selectedTimeAggregate: 'hourly' }));
  expect(loadingState.gridStatus.hourly).toEqual(GRID_STATUS.LOADING);
  expect(loadingState.gridStatus.yearly).toEqual(GRID_STATUS.INVALID);

  const readyState = reducer(undefined, GRID_DATA_FETCH_SUCCEEDED(gridData.data));
  expect(readyState.gridStatus.hourly).toEqual(GRID_STATUS.READY);
  expect(readyState.gridStatus.daily).toEqual(GRID_STATUS.INVALID);

  const invalidState = reducer(readyState, GRID_DATA_FETCH_FAILED({ selectedTimeAggregate: 'hourly' }));
  expect(invalidState.gridStatus.hourly).toEqual(GRID_STATUS.INVALID);
});
test('Zone data status is updated', () => {
  // Ensures gridStatus is updated accordingly
  const payload = { ...historyData.data, zoneId: 'DK-DK2' };
  const action = ZONE_HISTORY_FETCH_SUCCEEDED(payload);
  const state = reducer(undefined, action);

  expect(state.zones['DK-DK2'].daily.dataStatus).toEqual(ZONE_STATUS.READY);
  expect(state.zones['DK-DK2'].hourly.dataStatus).toEqual(ZONE_STATUS.INVALID);
  expect(state.zones['DK-DK2'].yearly.dataStatus).toEqual(ZONE_STATUS.INVALID);
  expect(state.zones['DK-DK2'].monthly.dataStatus).toEqual(ZONE_STATUS.INVALID);
});

test('Grid fetch expires zone data', () => {
  let state = undefined;
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED({ ...hourlyHistoryData.data, zoneId: 'DK-DK2' }));

  const futureZonePayload = { ...hourlyHistoryData.data, zoneId: 'NO-NO1' };
  futureZonePayload.zoneStates[0].stateDatetime = '2050-06-26T09:00:00Z';
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED(futureZonePayload));
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED({ ...historyData.data, zoneId: 'DK-DK2' }));

  const gridPayload = gridData.data;
  gridPayload.datetimes[24] = '2030-06-26T09:00:00Z';

  const updatedState = reducer(state, GRID_DATA_FETCH_SUCCEEDED(gridPayload));
  expect(updatedState.gridStatus.hourly).toEqual(GRID_STATUS.READY);

  // Does not expire other aggregate
  expect(updatedState.zones['DK-DK2'].daily.dataStatus).toEqual(ZONE_STATUS.READY);
  expect(updatedState.zones['NO-NO1'].hourly.dataStatus).toEqual(ZONE_STATUS.READY);

  // Expires relevant data
  expect(updatedState.zones['DK-DK2'].hourly.dataStatus).toEqual(ZONE_STATUS.EXPIRED);
});

test('Zone fetch expires grid data sync', () => {
  const readyState = reducer(undefined, GRID_DATA_FETCH_SUCCEEDED(gridData.data));
  expect(readyState.gridStatus.hourly).toEqual(GRID_STATUS.READY);

  const zonePayload = { ...hourlyHistoryData.data, zoneId: 'DK-DK2' };
  zonePayload.zoneStates[0].stateDatetime = '2050-06-26T09:00:00Z';

  const state = reducer(readyState, ZONE_HISTORY_FETCH_SUCCEEDED(zonePayload));
  expect(state.gridStatus.hourly).toEqual(GRID_STATUS.EXPIRED);
});
