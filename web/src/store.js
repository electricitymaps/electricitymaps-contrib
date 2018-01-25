const redux = require('redux');
const reduxLogger = require('redux-logger').logger;
const reducer = require('./reducers/main');

const store = redux.createStore(
  reducer,
  window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
  redux.applyMiddleware(reduxLogger),
);

// Utility to react to store changes
const observe = (select, onChange) => {
  let currentState;

  function handleChange() {
    const nextState = select(store.getState());
    if (nextState !== currentState) {
      currentState = nextState;
      onChange(currentState);
    }
  }

  const unsubscribe = store.subscribe(handleChange);
  handleChange();
  return unsubscribe;
};

const { dispatch, getState } = store;

module.exports = {
  dispatch,
  getState,
  observe,
};
