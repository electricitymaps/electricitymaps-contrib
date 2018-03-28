const { dispatch, getState } = require('../store');

export default function dispatchApplication(key, value) {
  // Do not dispatch unnecessary events
  if (getState().application[key] === value) {
    return;
  }
  dispatch({
    key,
    value,
    type: 'APPLICATION_STATE_UPDATE',
  });
}

