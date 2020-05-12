import createSagaMiddleware from 'redux-saga';
import { createStore, applyMiddleware } from 'redux';
import { logger } from 'redux-logger';

import { updateApplication } from './actioncreators';
import reducer from './reducers';

export const sagaMiddleware = createSagaMiddleware();

export const store = process.env.NODE_ENV === 'production'
  ? createStore(
    reducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
    applyMiddleware(sagaMiddleware),
  )
  : createStore(
    reducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
    applyMiddleware(sagaMiddleware),
    applyMiddleware(logger),
  );

export const { dispatch, getState } = store;

// TODO: Deprecate and use actioncreators instead
export const dispatchApplication = (key, value) => {
  // Do not dispatch unnecessary events
  // TODO: warn: getState() might be out of sync
  // by the time the event gets dispatched.
  if (getState().application[key] === value) {
    return;
  }
  dispatch(updateApplication(key, value));
};
