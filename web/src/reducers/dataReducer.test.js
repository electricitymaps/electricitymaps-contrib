/**
 * @jest-environment jsdom
 */
import { protectedJsonRequest } from '../helpers/api';
import { GRID_DATA_FETCH_SUCCEEDED, ZONE_HISTORY_FETCH_SUCCEEDED } from '../helpers/redux';
import reducer from './dataReducer';

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

  expect(state.zones).toMatchObject(expectedZones);
});

/** The following tests assumes the mockserver is running */

test('grid fetch updates correctly', async () => {
  const payload = await protectedJsonRequest('/v5/state/hourly');
  const action = GRID_DATA_FETCH_SUCCEEDED(payload);
  const state = reducer(undefined, action);

  const expectedHourly = {
    co2intensity: expect.any(Number),
    countryCode: expect.stringContaining('DK-DK2'),
  };

  expect(state.zones['DK-DK2'].hourly.overviews[0]).toMatchObject(expectedHourly);
  expect(state.zones['DK-DK2'].hourly.overviews).toHaveLength(24);
  expect(state.zones['DK-DK2'].daily.overviews).toHaveLength(0);
});

test('history contains required properties', async () => {
  const payload = await protectedJsonRequest('/v5/history_DK-DK2_daily');
  const action = ZONE_HISTORY_FETCH_SUCCEEDED({ ...payload, zoneId: 'DK-DK2' });
  const state = reducer(undefined, action);

  expect(state.zones['DK-DK2'].daily.details[0]).toHaveProperty('totalCo2Production');
});
