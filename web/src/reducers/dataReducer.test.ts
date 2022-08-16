/**
 * @jest-environment jsdom
 */
import { GRID_DATA_FETCH_SUCCEEDED, ZONE_HISTORY_FETCH_SUCCEEDED } from '../helpers/redux';
import reducer from './dataReducer';
// @ts-expect-error TS(2732): Cannot find module '../../../mockserver/public/v5/... Remove this comment to see the full error message
import historyData from '../../../mockserver/public/v5/history/DK-DK2/daily.json';
// @ts-expect-error TS(2732): Cannot find module '../../../mockserver/public/v5/... Remove this comment to see the full error message
import historyDataHourly from '../../../mockserver/public/v5/history/DK-DK2/hourly.json';
// @ts-expect-error TS(2732): Cannot find module '../../../mockserver/public/v5/... Remove this comment to see the full error message
import gridData from '../../../mockserver/public/v5/state/hourly.json';

test('zones should have initial state with correct structure', () => {
  const state = reducer.getInitialState();

  const expectedZones = {
    'DK-DK2': {
      hourly: (expect as any).any(Object),
      daily: (expect as any).any(Object),
      monthly: (expect as any).any(Object),
      yearly: (expect as any).any(Object),
      geography: (expect as any).any(Object),
      config: {
        hasParser: true,
        capacity: {
          nuclear: 0,
        },
        contributors: (expect as any).arrayContaining(['corradio']),
        timezone: 'Europe/Copenhagen',
      },
    },
  };

  (expect(state.zones) as any).toMatchObject(expectedZones);
});

test('grid fetch updates correctly', async () => {
  const payload = gridData.data;
  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  const action = GRID_DATA_FETCH_SUCCEEDED(payload);
  const state = reducer(undefined, action);

  const expectedHourly = {
    co2intensity: (expect as any).any(Number),
    countryCode: (expect as any).stringContaining('DK-DK2'),
  };

  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(state.zones['DK-DK2'].hourly.overviews[0]) as any).toMatchObject(expectedHourly);
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(state.zones['DK-DK2'].hourly.overviews) as any).toHaveLength(25);
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(state.zones['DK-DK2'].daily.overviews) as any).toHaveLength(0);
});

test('history contains required properties', async () => {
  const payload = { ...historyData.data, zoneId: 'DK-DK2' };
  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  const action = ZONE_HISTORY_FETCH_SUCCEEDED(payload);
  const state = reducer(undefined, action);

  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  expect(state.zones['DK-DK2'].daily.details[0]).toHaveProperty('totalCo2Production');
});

test('Histories are expired', () => {
  let state = undefined;
  state = reducer.getInitialState();
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(state.zones['DK-DK2'].hourly.isExpired) as any).toBe(true);
  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED({ ...historyDataHourly.data, zoneId: 'DK-DK2' }));
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(state.zones['DK-DK2'].hourly.isExpired) as any).toBe(false);

  const futureZonePayload = { ...historyDataHourly.data, zoneId: 'NO-NO1' };
  futureZonePayload.zoneStates[0].stateDatetime = '2050-06-26T09:00:00Z';
  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED(futureZonePayload));
  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED({ ...historyData.data, zoneId: 'DK-DK2' }));

  const gridPayload = gridData.data;
  gridPayload.datetimes[24] = '2030-06-26T09:00:00Z';

  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  const updatedState = reducer(state, GRID_DATA_FETCH_SUCCEEDED(gridPayload));
  (expect((updatedState.isGridExpired as any).hourly) as any).toBe(false);

  // Does not expire other aggregate
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(updatedState.zones['DK-DK2'].daily.isExpired) as any).toBe(false);
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(updatedState.zones['NO-NO1'].hourly.isExpired) as any).toBe(false);

  // Expires relevant data
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(updatedState.zones['DK-DK2'].hourly.isExpired) as any).toBe(true);
});

test('Grid is expired', () => {
  let state = undefined;
  state = reducer.getInitialState();
  (expect((state.isGridExpired as any).hourly) as any).toBe(true);

  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  state = reducer(undefined, GRID_DATA_FETCH_SUCCEEDED(gridData.data));
  (expect((state.isGridExpired as any).hourly) as any).toBe(false);

  const zonePayload = { ...historyDataHourly.data, zoneId: 'DK-DK2' };
  zonePayload.zoneStates[0].stateDatetime = '2050-06-26T09:00:00Z';

  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  state = reducer(state, ZONE_HISTORY_FETCH_SUCCEEDED(zonePayload));
  (expect((state.isGridExpired as any).hourly) as any).toBe(true);
});

test('Exchange data is fetched', () => {
  let state = undefined;
  state = reducer.getInitialState();
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  expect(state.exchanges['DE->DK-DK1'].config).toHaveProperty('sortedCountryCodes');
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(state.exchanges['DE->DK-DK1'].data) as any).toHaveLength(0);

  // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
  state = reducer(undefined, GRID_DATA_FETCH_SUCCEEDED(gridData.data));

  const expectedExchange = {
    co2intensity: (expect as any).any(Number),
    netFlow: (expect as any).any(Number),
  };
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(state.exchanges['DE->DK-DK1'].data) as any).toHaveLength(25);
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  (expect(state.exchanges['DE->DK-DK1'].data[0]) as any).toMatchObject(expectedExchange);
});
