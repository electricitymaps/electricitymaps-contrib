/**
 * @jest-environment jsdom
 */
import { protectedJsonRequest } from '../helpers/api';
import { reducer, GRID_DATA_FETCH_SUCCEEDED, ZONE_DETAILS_FETCH_SUCCEDED } from './dataReducerForHistoryFeature';

/*
NOTES:
- We do not want to store config values in state, keep state minimal and only for dynamic values
- We do not need to store geographies in state

*/

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
        hasData: true,
        capacity: {
          nuclear: 0,
        },
        contributors: expect.arrayContaining(['corradio']),
        timezone: 'Europe/Copenhagen',
      },
    },
  };

  expect(state.grid.zones).toMatchObject(expectedZones);
});

test('grid fetch updates correctly', async () => {
  const payload = await protectedJsonRequest('/v5/state/hourly');
  const action = GRID_DATA_FETCH_SUCCEEDED({ payload });
  const state = reducer(undefined, action);

  const expectedZones = {
    'DK-DK2': {
      hourly: expect.any(Object),
      daily: expect.any(Object),
      monthly: expect.any(Object),
      yearly: expect.any(Object),
      geography: expect.any(Object),
      config: {
        hasParser: true,
        hasData: true,
        capacity: {
          nuclear: 0,
        },
        contributors: expect.arrayContaining(['corradio']),
        timezone: 'Europe/Copenhagen',
      },
    },
  };

  const expectedHourly = {
    co2intensity: expect.any(Number),
    countryCode: expect.stringContaining('DK-DK2'),
    details: {},
  };

  expect(state.grid.zones).toMatchObject(expectedZones);
  expect(state.grid.zones['DK-DK2'].hourly[0]).toMatchObject(expectedHourly);
  expect(state.grid.zones['DK-DK2'].hourly).toHaveLength(24);
  expect(state.grid.zones['DK-DK2'].daily).toHaveLength(0);
  expect(state.grid.zones['DK-DK2'].monthly).toHaveLength(0);
  expect(state.grid.zones['DK-DK2'].yearly).toHaveLength(0);
});

test('history', async () => {
  const payload = await protectedJsonRequest('/v5/history_DK-DK2_daily');
  const action = ZONE_DETAILS_FETCH_SUCCEDED({ payload, zoneId: 'DK-DK2' });
  const state = reducer(undefined, action);
  expect(state.grid.zones['DK-DK2'].daily.details[0]).toHaveProperty('totalCo2Production');
});
