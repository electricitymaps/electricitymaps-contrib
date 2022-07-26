/**
 * @jest-environment jsdom
 */
import { GRID_DATA_FETCH_SUCCEEDED, ZONE_HISTORY_FETCH_SUCCEEDED } from '../helpers/redux';
import reducer from './dataReducer';
import historyData from '../../../mockserver/public/v5/history/DK-DK2/daily.json';
import historyDataHourly from '../../../mockserver/public/v5/history/DK-DK2/hourly.json';
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

test('grid fetch updates correctly', async () => {
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

test('history contains required properties', async () => {
  const payload = { ...historyData.data, zoneId: 'DK-DK2' };
  const action = ZONE_HISTORY_FETCH_SUCCEEDED(payload);
  const state = reducer(undefined, action);

  expect(state.zones['DK-DK2'].daily.details[0]).toHaveProperty('totalCo2Production');
});

test('Histories are expired', () => {
  let state = undefined;
  state = reducer.getInitialState();
  expect(state.zones['DK-DK2'].hourly.isExpired).toBe(true);
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED({ ...historyDataHourly.data, zoneId: 'DK-DK2' }));
  expect(state.zones['DK-DK2'].hourly.isExpired).toBe(false);

  const futureZonePayload = { ...historyDataHourly.data, zoneId: 'NO-NO1' };
  futureZonePayload.zoneStates[0].stateDatetime = '2050-06-26T09:00:00Z';
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED(futureZonePayload));
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED({ ...historyData.data, zoneId: 'DK-DK2' }));

  const gridPayload = gridData.data;
  gridPayload.datetimes[24] = '2030-06-26T09:00:00Z';

  const updatedState = reducer(state, GRID_DATA_FETCH_SUCCEEDED(gridPayload));
  expect(updatedState.isGridExpired.hourly).toBe(false);

  // Does not expire other aggregate
  expect(updatedState.zones['DK-DK2'].daily.isExpired).toBe(false);
  expect(updatedState.zones['NO-NO1'].hourly.isExpired).toBe(false);

  // Expires relevant data
  expect(updatedState.zones['DK-DK2'].hourly.isExpired).toBe(true);
});

test('Grid is expired', () => {
  let state = undefined;
  state = reducer.getInitialState();
  expect(state.isGridExpired.hourly).toBe(true);

  state = reducer(undefined, GRID_DATA_FETCH_SUCCEEDED(gridData.data));
  expect(state.isGridExpired.hourly).toBe(false);

  const zonePayload = { ...historyDataHourly.data, zoneId: 'DK-DK2' };
  zonePayload.zoneStates[0].stateDatetime = '2050-06-26T09:00:00Z';

  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED(zonePayload));
  expect(state.isGridExpired.hourly).toBe(true);
});

test('Exchange data is fetched', () => {
  let state = undefined;
  state = reducer.getInitialState();
  expect(state.exchanges['DK-DK2->SE-SE4'].config).toHaveProperty('sortedCountryCodes');
  expect(state.exchanges['DK-DK2->SE-SE4'].data).toHaveLength(0);

  state = reducer(undefined, GRID_DATA_FETCH_SUCCEEDED(gridData.data));

  const expectedExchange = {
    co2intensity: expect.any(Number),
    netFlow: expect.any(Number),
  };
  expect(state.exchanges['DK-DK2->SE-SE4'].data).toHaveLength(25);
  expect(state.exchanges['DK-DK2->SE-SE4'].data[0]).toMatchObject(expectedExchange);
});
