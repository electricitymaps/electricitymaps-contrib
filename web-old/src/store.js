import createSagaMiddleware from 'redux-saga';
import { createStore, applyMiddleware, compose } from 'redux';

import reducer from './reducers';

export const sagaMiddleware = createSagaMiddleware();
const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
export const store = createStore(reducer, composeEnhancers(applyMiddleware(sagaMiddleware)));

// TODO: Deprecate and use actioncreators instead
export const dispatchApplication = (key, value) => {
  store.dispatch({ type: 'APPLICATION_STATE_UPDATE', key, value });
};
