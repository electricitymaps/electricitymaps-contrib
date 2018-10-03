import { compose, createStore, applyMiddleware } from 'redux';
import { logger } from 'redux-logger';
import reducer from './reducers';


const middlewares = [];

if (process.env.NODE_ENV === 'development') {
  middlewares.push(logger);
}

const store = createStore(
  reducer,
  compose(
    applyMiddleware(...middlewares),
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
  )
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
