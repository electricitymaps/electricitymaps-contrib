export const updateSelectedZoneTimeIndex = (store) => (next) => (action) => {
  // We want to update application state when data state is updated
  // Since those reducers are separated, this middleware is able to dispatch
  // an update to zoneTimeIndex when data is updated

  if (action.type === 'GRID_DATA_FETCH_SUCCEEDED') {
    store.dispatch({
      type: 'APPLICATION_STATE_UPDATE',
      key: 'selectedZoneTimeIndex',
      value: action.payload.datetimes.length - 1,
    });
  }
  return next(action);
};
