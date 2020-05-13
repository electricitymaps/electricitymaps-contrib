import createSagaMiddleware from 'redux-saga';
import { createStore, applyMiddleware } from 'redux';
import { logger } from 'redux-logger';

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
  dispatch({ type: 'APPLICATION_STATE_UPDATE', key, value });
};
