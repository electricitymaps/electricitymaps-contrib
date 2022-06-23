/**
 * @jest-environment jsdom
 */
import { GRID_DATA_FETCH_SUCCEEDED, ZONE_HISTORY_FETCH_SUCCEEDED } from '../helpers/redux';
import reducer from './dataReducer';
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
