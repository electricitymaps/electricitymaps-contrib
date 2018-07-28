const redux = require('redux');
const reduxLogger = require('redux-logger').logger;
const reducer = require('./reducers');

const isProduction = window.location.href.indexOf('electricitymap') !== -1;

const store = isProduction ?
  redux.createStore(
    reducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
  )
  :
  redux.createStore(
    reducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
    redux.applyMiddleware(reduxLogger),
  );

// Utility to react to store changes
const observe = (select, onChange) => {
  let currentSelectedState;

  function handleChange() {
    const nextState = store.getState();
    const nextSelectedState = select(nextState);
    if (nextSelectedState !== currentSelectedState) {
      currentSelectedState = nextSelectedState;
      onChange(currentSelectedState, nextState);
    }
  }

  const unsubscribe = store.subscribe(handleChange);
  handleChange();
  return unsubscribe;
};

const { dispatch, getState } = store;

const dispatchApplication = (key, value) => {
  // Do not dispatch unnecessary events
  if (getState().application[key] === value) {
    return;
  }
  dispatch({
    key,
    value,
    type: 'APPLICATION_STATE_UPDATE',
  });
};

module.exports = {
  dispatch,
  dispatchApplication,
  getState,
  observe,
};
