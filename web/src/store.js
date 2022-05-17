import createSagaMiddleware from 'redux-saga';
import { createStore, applyMiddleware } from 'redux';
import { logger } from 'redux-logger';

import reducer from './reducers';
import { isProduction } from './helpers/environment';

export const sagaMiddleware = createSagaMiddleware();

export const store = isProduction()
  ? createStore(
      reducer,
      window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
      applyMiddleware(sagaMiddleware)
    )
  : createStore(
      reducer,
      window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__(),
      applyMiddleware(sagaMiddleware),
      applyMiddleware(logger)
    );

// TODO: Deprecate and use actioncreators instead
export const dispatchApplication = (key, value) => {
  store.dispatch({ type: 'APPLICATION_STATE_UPDATE', key, value });
};
