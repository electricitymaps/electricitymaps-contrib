import { createStore, applyMiddleware } from 'redux';
import reducer from './reducers';

const store = process.env.NODE_ENV === 'production'
  ? createStore(
    reducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
  )
  : createStore(
    reducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
    applyMiddleware(require('redux-logger').logger),
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

export {
  dispatch,
  dispatchApplication,
  getState,
  observe,
  store,
};
